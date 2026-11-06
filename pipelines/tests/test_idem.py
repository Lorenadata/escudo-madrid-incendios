"""Tests A3 GIS — T02 (cruce territorial) y T03 (riesgo oficial = capa fuente).

Dos bloques:
  1. Unitarios con un ráster SINTÉTICO generado en tmp_path (no son datos reales).
  2. Validación de las salidas reales en data/processed/idem (se omiten si no se han generado).
"""

from __future__ import annotations

import csv
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest
import rasterio
import shapely
from rasterio.transform import from_origin
from shapely.geometry import box, shape

from escudo_pipelines.fetch import RAW_DIR, REPO_ROOT
from escudo_pipelines.idem import transform as T
from escudo_pipelines.idem.fetch import parse_iso_metadata, parse_legend
from escudo_pipelines.idem.sources import IDEM_LAYERS

OUT = REPO_ROOT / "data" / "processed" / "idem"
LAYERS = [lyr.layer for lyr in IDEM_LAYERS]

SYNTH_LEGEND = {"Legend": [{"layerName": "synthetic", "rules": [{"symbolizers": [{"Raster": {"colormap": {
    "entries": [
        {"label": "Clase sintética cero", "quantity": "0", "color": "#000000", "opacity": "0.0"},
        {"label": "Clase sintética uno", "quantity": "1", "color": "#111111"},
        {"label": "Clase sintética dos", "quantity": "2", "color": "#222222"},
    ]}}}]}]}]}


# ------------------------------------------------------------------ unitarios
def test_parse_legend_keeps_literal_labels():
    classes = parse_legend(SYNTH_LEGEND)
    assert [c["class_code"] for c in classes] == [0, 1, 2]
    assert classes[1]["class_label"] == "Clase sintética uno"
    assert classes[0]["transparent_in_official_style"] is True


def test_parse_iso_metadata_minimal():
    xml = """<gmd:dateStamp><gco:Date>2026-07-07</gco:Date></gmd:dateStamp>
    <gmd:CI_Date><gmd:date><gco:Date>2025-12-01</gco:Date></gmd:date>
    <gmd:dateType><gmd:CI_DateTypeCode codeListValue="revision"/></gmd:dateType></gmd:CI_Date>
    <gmd:code>http://www.opengis.net/def/crs/EPSG/0/25830">EPSG:25830</gmd:code>
    <a href="http://creativecommons.org/licenses/by/4.0/deed.es">CC BY 4.0 Comunidad de Madrid</a>"""
    m = parse_iso_metadata(xml)
    assert m["metadata_date_stamp"] == "2026-07-07"
    assert m["citation_dates"]["revision"] == "2025-12-01"
    assert m["crs_declared"] == "EPSG:25830"
    assert m["license_title"] == "CC BY 4.0 Comunidad de Madrid"


@pytest.fixture
def synthetic_raster(tmp_path: Path) -> str:
    """Ráster SINTÉTICO 20×20 celdas de 5 m: mitad izquierda clase 1, derecha clase 2, una fila nodata."""
    data = np.ones((20, 20), dtype=np.uint8)
    data[:, 10:] = 2
    data[0, :] = T.NODATA
    tif = tmp_path / "synthetic.tif"
    with rasterio.open(tif, "w", driver="GTiff", width=20, height=20, count=1, dtype="uint8",
                       crs="EPSG:25830", transform=from_origin(400000, 4500100, 5, 5), nodata=T.NODATA) as ds:
        ds.write(data, 1)
    z = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(tif, "synthetic.tif")
    return f"zip://{z.as_posix()}!synthetic.tif"


def test_municipal_counts_exact_on_synthetic(synthetic_raster):
    # municipio A = columnas 0..9 completas (incluida la fila nodata), B = columnas 10..19
    a = box(400000, 4500000, 400050, 4500100)
    b = box(400050, 4500000, 400100, 4500100)
    munis = [{"ine_code": "99001", "name": "Sintético A", "geom": a},
             {"ine_code": "99002", "name": "Sintético B", "geom": b}]
    counts, px = T.municipal_class_counts({"x": synthetic_raster}, munis, strip_rows=7)
    assert px == 25.0
    c = counts["x"]
    assert c[1, 1] == 19 * 10 and c[1, 2] == 0 and c[1, T.NODATA] == 10
    assert c[2, 2] == 19 * 10 and c[2, 1] == 0
    rows = T.shares_rows("x", c, px, munis, parse_legend(SYNTH_LEGEND))
    by = {(r["ine_code"], r["class_code"]): r for r in rows}
    assert by[("99001", 1)]["area_ha"] == round(190 * 25 / 10_000, 2)
    assert by[("99001", 1)]["area_share"] == pytest.approx(0.95)
    assert by[("99001", 1)]["class_label"] == "Clase sintética uno"
    assert ("99001", 2) not in by


def test_unknown_value_raises(synthetic_raster):
    munis = [{"ine_code": "99001", "name": "A", "geom": box(400000, 4500000, 400100, 4500100)}]
    counts, px = T.municipal_class_counts({"x": synthetic_raster}, munis)
    bad_legend = {"Legend": [{"rules": [{"symbolizers": [{"Raster": {"colormap": {"entries": [
        {"label": "solo uno", "quantity": "1"}]}}}]}]}]}
    with pytest.raises(ValueError, match="sin etiqueta"):
        T.shares_rows("x", counts["x"], px, munis, parse_legend(bad_legend))


def test_vectorize_synthetic_is_valid_wgs84(synthetic_raster):
    fc, fixed, info = T.vectorize_for_web(synthetic_raster, parse_legend(SYNTH_LEGEND), cell_m=5, simplify_tol_m=0,
                                         coord_decimals=7)
    codes = {f["properties"]["class_code"] for f in fc["features"]}
    assert codes == {1, 2}
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid
        lon, lat = g.representative_point().coords[0]
        assert -10 < lon < 5 and 35 < lat < 45  # EPSG:4326, no metros
    back = sum(shapely.transform(shape(f["geometry"]), T._vec(T.TO_25830)).area for f in fc["features"])
    assert back == pytest.approx(19 * 20 * 25, rel=0.01)


def test_fix_geometry_repairs_bowtie():
    bowtie = shape({"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]})
    g, fixed = T.fix_geometry(bowtie)
    assert fixed and g.is_valid


# ------------------------------------------------- salidas reales (T02/T03)
real = pytest.mark.skipif(not (OUT / "layers_meta.json").exists(), reason="ejecutar escudo_pipelines.idem.transform")


def _raw_legend(layer: str) -> dict[int, str]:
    lyr = next(x for x in IDEM_LAYERS if x.layer == layer)
    m = json.loads((RAW_DIR / lyr.spec.source_id / "manifest.json").read_text(encoding="utf-8"))
    return {c["class_code"]: c["class_label"] for c in m["legend_classes"]}


@real
@pytest.mark.parametrize("layer", LAYERS)
def test_real_geojson_classes_equal_source(layer):
    fc = json.loads((OUT / f"{layer}.geojson").read_text(encoding="utf-8"))
    legend = _raw_legend(layer)
    assert fc["features"], "capa vacía"
    for f in fc["features"]:
        p = f["properties"]
        assert legend[p["class_code"]] == p["class_label"], "etiqueta distinta de la fuente oficial"
    assert (OUT / f"{layer}.geojson").stat().st_size < 8_500_000


@real
@pytest.mark.parametrize("layer", LAYERS)
def test_real_geojson_valid_and_wgs84(layer):
    fc = json.loads((OUT / f"{layer}.geojson").read_text(encoding="utf-8"))
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and not g.is_empty
        minx, miny, maxx, maxy = g.bounds
        assert -4.7 < minx and maxx < -3.0 and 39.8 < miny and maxy < 41.25  # Comunidad de Madrid en lon/lat


@real
def test_real_meta_classes_equal_legend():
    meta = json.loads((OUT / "layers_meta.json").read_text(encoding="utf-8"))
    for layer in LAYERS:
        lm = meta["layers"][layer]
        assert {c["class_code"]: c["class_label"] for c in lm["classes"]} == _raw_legend(layer)
        assert lm["crs_original"] == "EPSG:25830"
        assert lm["license"].startswith("CC BY 4.0")


@real
def test_real_shares_bounds_and_coverage():
    rows = list(csv.DictReader((OUT / "municipal_class_shares.csv").open(encoding="utf-8")))
    assert rows
    sums: dict[tuple[str, str], float] = defaultdict(float)
    for r in rows:
        s = float(r["area_share"])
        assert 0 <= s <= 1 + T.SHARE_EPSILON
        assert float(r["area_ha"]) >= 0
        assert r["ine_code"].startswith("28") and len(r["ine_code"]) == 5
        sums[(r["ine_code"], r["layer"])] += s
    assert all(v <= 1 + T.SHARE_EPSILON for v in sums.values()), max(sums.values())
    munis = json.loads(T.MUNICIPALITIES.read_text(encoding="utf-8"))["features"]
    for layer in LAYERS:
        covered = {k[0] for k in sums if k[1] == layer}
        assert len(covered) == len(munis), f"{layer}: municipios sin cobertura"
    # labels literal
    for layer in LAYERS:
        legend = _raw_legend(layer)
        for r in rows:
            if r["layer"] == layer:
                assert legend[int(r["class_code"])] == r["class_label"]


@real
def test_real_regional_area_close_to_municipal_sum():
    """Cruce territorial: la superficie con dato del ráster ≈ suma de municipios (control de malla/CRS)."""
    munis = json.loads(T.MUNICIPALITIES.read_text(encoding="utf-8"))["features"]
    total_muni_ha = sum(shapely.transform(shape(f["geometry"]), T._vec(T.TO_25830)).area for f in munis) / 10_000
    meta = json.loads((OUT / "layers_meta.json").read_text(encoding="utf-8"))
    for layer in LAYERS:
        raster_ha = sum(c["regional_area_ha"] for c in meta["layers"][layer]["classes"])
        assert raster_ha == pytest.approx(total_muni_ha, rel=0.02), layer
