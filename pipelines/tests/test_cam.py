"""Tests del pipeline CAM (PRD §9.2 T01, T02, T04)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from escudo_pipelines.cam_transform import _is_65_plus, build_population, cam_code_to_ine, parse_number
from escudo_pipelines.fetch import sha256_file
from escudo_pipelines.sources import ALL_SOURCES

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "cam"


def test_cam_code_to_ine():
    assert cam_code_to_ine("0796") == "28079"  # Madrid: 079 + dígito de control 6
    assert cam_code_to_ine("0014") == "28001"
    with pytest.raises(ValueError):
        cam_code_to_ine("28079")


@pytest.mark.parametrize("raw,expected", [("12.5", 12.5), ("3,2", 3.2), ("-", None), ("", None), ("..", None)])
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


def test_65_plus_groups():
    assert _is_65_plus("De 65-69 años") and _is_65_plus("De 100 y más años")
    assert not _is_65_plus("De 60-64 años") and not _is_65_plus("Total")


def test_build_population_fixture():
    """Fixture sintética mínima (no son datos reales)."""
    rows = [
        {"Año": "2025", "Tipo territorio": "Municipios", "Código territorio": "0014", "Territorio": "X",
         "Edad": e, "Nacionalidad": "Total", "Sexo": "Total", "Valor": v}
        for e, v in [("Total", "100"), ("De 60-64 años", "10"), ("De 65-69 años", "7"), ("De 100 y más años", "1")]
    ] + [{"Año": "2025", "Tipo territorio": "Municipios", "Código territorio": "0014", "Territorio": "X",
          "Edad": "De 65-69 años", "Nacionalidad": "Españoles", "Sexo": "Total", "Valor": "999"}]
    names, pop = build_population(rows)
    assert names == {"28001": "X"}
    assert pop[("28001", 2025)] == {"total": 100.0, "age65": 8.0}


def _manifests():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAW.glob("CAM-*/manifest.json"))]


@pytest.mark.skipif(not (RAW / "CAM-01" / "manifest.json").exists(), reason="ejecute escudo_pipelines.fetch")
def test_T01_manifests_checksums_and_licenses():
    ms = _manifests()
    assert {m["source_id"] for m in ms} >= {"CAM-01", "CAM-02", "CAM-08"}
    for m in ms:
        assert m["license_id"] == "cc-by" and m["extracted_at"] and m["resource_url"].startswith("https://datos.comunidad.madrid/")
        assert m["source_id"] in ALL_SOURCES
        f = RAW / m["source_id"] / m["file"]
        if f.exists():  # los binarios crudos no se versionan; el manifest sí
            assert sha256_file(f) == m["sha256"]


@pytest.mark.skipif(not (OUT / "quality.json").exists(), reason="ejecute escudo_pipelines.cam_transform")
def test_T02_processed_outputs():
    q = json.loads((OUT / "quality.json").read_text(encoding="utf-8"))
    assert q["all_passed"], [c for c in q["checks"] if not c["passed"]]
    rows = list(csv.DictReader((OUT / "municipal_indicators.csv").open(encoding="utf-8")))
    assert len(rows) == 179 and len({r["ine_code"] for r in rows}) == 179
    assert all(r["ine_code"].startswith("28") and len(r["ine_code"]) == 5 for r in rows)
    geo = json.loads((OUT / "municipalities.geojson").read_text(encoding="utf-8"))
    assert len(geo["features"]) == 179
    from shapely.geometry import shape

    for f in geo["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type in ("Polygon", "MultiPolygon")
        minx, miny, maxx, maxy = g.bounds
        assert -4.7 < minx and maxx < -2.9 and 39.8 < miny and maxy < 41.2  # caja de la Comunidad de Madrid (lon/lat)


@pytest.mark.skipif(not (OUT / "fire_history.csv").exists(), reason="ejecute escudo_pipelines.cam_transform")
def test_regional_series_are_labeled_regional():
    rows = list(csv.DictReader((OUT / "fire_history.csv").open(encoding="utf-8")))
    assert rows and all("regional" in r["scope"] for r in rows)
