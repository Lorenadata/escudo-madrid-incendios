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


def _hrow(code, cat, val, col="Tipo", year="2021", tipo="Municipios"):
    return {"Año": year, "Tipo territorio": tipo, "Código territorio": code, "Territorio": "X", col: cat, "Valor": val,
            "Estado dato": "Provisional" if col == "Consumo" else ""}


def test_build_housing_fixture():
    """Fixture sintética mínima: cocientes de valores publicados, nulos explícitos y control de universo."""
    from escudo_pipelines.cam_transform import build_housing

    cam09 = [_hrow("0014", "Total", "100"), _hrow("0014", "Principales", "60"), _hrow("0014", "No principales", "40"),
             _hrow("", "Total", "999", tipo="Comunidad de Madrid"),  # agregado regional: se ignora
             _hrow("0029", "Total", "50"), _hrow("0029", "Principales", "50"), _hrow("0029", "No principales", "0")]
    cam10 = [_hrow("0014", "Residencial con una vivienda", "75.13"), _hrow("0029", "Residencial con una vivienda", "-")]
    cam11 = [_hrow("0014", c, v, col="Consumo") for c, v in
             [("Viviendas vacias", "20"), ("Uso esporádico", "30"), ("Uso esporádico entre 251 y 500 kwh", "10"),
              ("Uso esporádico entre 501y 750 kwh", "20"), ("Mayor de 10.000 kwh", "50")]]
    cam11 += [_hrow("0029", "Viviendas vacias", "5", col="Consumo"), _hrow("0029", "Mayor de 10.000 kwh", "40", col="Consumo")]
    rows, stats = build_housing(cam09, cam10, cam11, ["28001", "28002"])
    a, b = rows
    assert a["non_main_share"] == 0.4 and a["single_dwelling_building_share"] == pytest.approx(0.7513)
    assert a["empty_electricity_share"] == 0.2 and a["sporadic_electricity_share"] == 0.3
    assert b["non_main_share"] == 0 and b["single_dwelling_building_share"] == ""  # '-' → no disponible
    assert b["empty_electricity_share"] == "" and stats["universe_mismatch_11"] == ["28002"]  # 45 ≠ 50: no se calcula
    assert not stats["sum_mismatch_09"] and stats["years"] == [2021]


@pytest.mark.skipif(not (OUT / "municipal_housing.csv").exists(), reason="ejecute escudo_pipelines.cam_transform")
def test_T02_housing_outputs_trace_to_raw_cam09():
    rows = {r["ine_code"]: r for r in csv.DictReader((OUT / "municipal_housing.csv").open(encoding="utf-8"))}
    assert len(rows) == 179
    for r in rows.values():
        for k in ("non_main_share", "single_dwelling_building_share", "empty_electricity_share", "sporadic_electricity_share"):
            assert r[k] == "" or 0 <= float(r[k]) <= 1
    raw = sorted((RAW / "CAM-09").glob("*.csv"))
    if raw:  # el crudo no se versiona; si existe, el procesado coincide con él
        from escudo_pipelines.cam_transform import _read

        t = {x["Tipo"]: x["Valor"] for x in _read(raw[0]) if x["Código territorio"] == "1258"}
        assert int(rows["28125"]["dwellings_total"]) == int(t["Total"])
        assert int(rows["28125"]["dwellings_non_main"]) == int(t["No principales"])
