"""Tests de EFF-01 (EFFIS, áreas quemadas por satélite): salidas procesadas trazables y reparto municipal coherente."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "effis"


@pytest.mark.skipif(not (OUT / "quality.json").exists(), reason="ejecute escudo_pipelines.effis")
def test_T02_effis_outputs():
    q = json.loads((OUT / "quality.json").read_text(encoding="utf-8"))
    assert q["all_passed"], [c for c in q["checks"] if not c["passed"]]
    fc = json.loads((OUT / "burnt_areas_madrid.geojson").read_text(encoding="utf-8"))
    assert fc["source_id"] == "EFF-01" and "CC BY 4.0" in fc["license"] and "30 ha" in fc["producer_notes"]
    feats = {f["properties"]["effis_id"]: f["properties"] for f in fc["features"]}
    assert len(feats) == q["features"] > 0
    rows = list(csv.DictReader((OUT / "municipal_burnt_areas.csv").open(encoding="utf-8")))
    assert rows and all(r["effis_id"] in feats for r in rows)
    by_fire = defaultdict(float)
    for r in rows:
        by_fire[r["effis_id"]] += float(r["area_ha_in_municipality"])
    for fid, ha in by_fire.items():  # el reparto municipal nunca supera la parte del perímetro dentro de la región
        assert ha <= feats[fid]["area_ha_in_region_derived"] * 1.01 + 1


def test_effis_spec_declares_license_and_producer_notes():
    from escudo_pipelines.effis import SPEC

    assert SPEC.source_id == "EFF-01" and len(SPEC.license) <= 64
    assert "prescritas" in SPEC.caveats and "250 m" in SPEC.caveats
