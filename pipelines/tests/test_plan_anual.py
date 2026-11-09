"""Tests de DOC-01 (Plan Anual 2026): extracción literal de ZAR (Anexo II) y siniestros municipales (Anexo I)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from escudo_pipelines.plan_anual import column_totals, norm, parse_fire_rows, parse_zar

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "plan"


def test_norm_articles_accents_and_document_typos():
    assert norm("Acebeda, La") == norm("Acebeda (La)") == "la acebeda"
    assert norm("ÁLAMO, EL") == norm("Álamo (El)")
    assert norm("Torredolones") == "torrelodones"            # errata del documento, registrada
    assert norm("San María de la Alameda") == norm("Santa María de la Alameda")


def test_parse_zar_two_columns():
    text = "1 Acebeda, La 31 Molinos, Los \n2 Aldea del Fresno 32 Montejo de la Sierra \n30 Miraflores de la Sierra \n"
    assert parse_zar(text) == [(1, "Acebeda, La"), (2, "Aldea del Fresno"), (30, "Miraflores de la Sierra"),
                               (31, "Molinos, Los"), (32, "Montejo de la Sierra")]


def test_parse_fire_rows_complete_incomplete_and_no_population():
    """Fixture con el formato del Anexo I (texto sintético, no datos reales)."""
    text = ("ACEBEDA, LA 62 0  0  0  0  0  0  \nALCALÁ DE HENARES 196.888 1  51  46  7  1  97  \n"
            "FUENTE EL SAZ DE JARAMA 7.034 0  11  1  8  2  21  \nPOZUELO DE ALARCÓN 87.728   1          \n"
            "MONTEJO DE LA SIERRA 372             \nREAL SITIO DE SAN ILDEFONSO  0  0  1  0  0  1\n"
            "TOTALES  117  1160 1013 586 36 2641 \nFUENTE EGIF")
    rows = {r["name_literal"]: r for r in parse_fire_rows(text)}
    assert rows["ALCALÁ DE HENARES"]["values"] == [1, 51, 46, 7, 1, 97]
    assert rows["FUENTE EL SAZ DE JARAMA"]["complete"]          # no confundir con «FUENTE EGIF»
    assert rows["REAL SITIO DE SAN ILDEFONSO"]["values"] == [0, 0, 1, 0, 0, 1]  # sin población
    assert not rows["POZUELO DE ALARCÓN"]["complete"] and rows["POZUELO DE ALARCÓN"]["loose"] == 1
    assert not rows["MONTEJO DE LA SIERRA"]["complete"] and rows["MONTEJO DE LA SIERRA"]["loose"] == 0
    assert "TOTALES" not in rows and "FUENTE EGIF" not in rows
    assert column_totals(text) == [117, 1160, 1013, 586, 36, 2641]


@pytest.mark.skipif(not (OUT / "quality.json").exists(), reason="ejecute escudo_pipelines.plan_anual")
def test_T02_plan_outputs():
    q = json.loads((OUT / "quality.json").read_text(encoding="utf-8"))
    assert q["all_passed"], [c for c in q["checks"] if not c["passed"]]
    zar = list(csv.DictReader((OUT / "zar_municipalities.csv").open(encoding="utf-8")))
    assert len(zar) == 59 and len({r["ine_code"] for r in zar}) == 59
    assert all(r["page"] == "59" and r["source_id"] == "DOC-01" for r in zar)
    fires = {r["ine_code"]: r for r in csv.DictReader((OUT / "municipal_fires_2015_2024.csv").open(encoding="utf-8"))}
    assert len(fires) == 179
    assert fires["28059"]["total_published"] == "21" and fires["28059"]["cam_name"] == "Fuente el Saz de Jarama"
    assert {r["cam_name"] for r in fires.values() if r["row_complete"] == "False"} == {"Montejo de la Sierra",
                                                                                     "Pozuelo de Alarcón"}
    manifest = json.loads((ROOT / "data/raw/DOC-01/manifest.json").read_text(encoding="utf-8"))
    assert manifest["resource_url"].startswith("https://www.comunidad.madrid/") and len(manifest["sha256"]) == 64
