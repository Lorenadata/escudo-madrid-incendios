"""Tests de integración API + PostGIS (PRD §9.2: T01, T04, T05, T06, T07, T08, T09)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.db
ROOT = Path(__file__).resolve().parents[2]
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


def test_health_and_sources(client):
    h = client.get("/health").json()
    assert h["db"] == "ok"
    src = {s["source_id"]: s for s in client.get("/v1/sources").json()}
    cam = [s for s in src.values() if s["portal"] == "CAM"]
    assert len(cam) >= 2, "requisito de admisión: al menos un dataset del Portal CAM"
    for sid in ("CAM-01", "CAM-02", "CAM-08"):  # T01: checksum, fecha y licencia
        s = src[sid]
        assert s["status"] == "ok" and len(s["sha256"]) == 64 and s["last_extracted_at"] and s["license"]
    manifest = json.loads((ROOT / "data/raw/CAM-01/manifest.json").read_text(encoding="utf-8"))
    assert src["CAM-01"]["sha256"] == manifest["sha256"]


def test_profile_values_trace_to_processed_cam_data(client):
    """El valor mostrado es exactamente el del fichero procesado del Portal CAM (sin cifras inventadas)."""
    rows = {r["ine_code"]: r for r in csv.DictReader((ROOT / "data/processed/cam/municipal_indicators.csv").open(encoding="utf-8"))}
    p = client.get("/v1/municipalities/28131/profile").json()
    assert p["population"]["value"] == int(rows["28131"]["population_total"])
    assert p["population"]["source_id"] == "CAM-01" and p["population"]["status"] == "official"
    assert p["density"]["value"] == pytest.approx(float(rows["28131"]["density_hab_km2"]))
    assert p["age_65_plus_share"]["status"] == "derived"
    assert p["forest_share"]["status"] == "unavailable"  # CAM-07 es regional: no se inventa


def test_density_filter_changes_with_cam02(client):
    """Función analítica (b) del PRD §4.1: filtro regional dependiente de CAM-02."""
    dense = client.get("/v1/municipalities", params={"min_density": 1000}).json()
    assert dense and all(m["density"]["value"] >= 1000 for m in dense)
    assert len(dense) < 179
    cmp = client.get("/v1/compare", params={"a": "28079", "b": "28131"}).json()
    assert cmp["a"]["density"]["value"] > cmp["b"]["density"]["value"]


def test_unknown_municipality_404(client):
    assert client.get("/v1/municipalities/99999/profile").status_code == 404


def test_T04_no_population_for_areas(client, auth_a):
    areas = client.get("/v1/areas", headers=auth_a).json()
    detail = client.get(f"/v1/areas/{areas[0]['id']}", headers=auth_a).json()
    flat = json.dumps({k: v for k, v in detail.items() if k != "municipality_profile"})
    assert "population" not in flat.replace("population_notice", "")
    assert detail["municipality_profile"]["population"]["spatial_scope"] == "municipio"


def test_T05_weather_unavailable_when_connector_fails(client, monkeypatch):
    import escudo_pipelines.aemet as aemet

    def boom(*a, **k):
        raise ConnectionError("AEMET caído (simulado en test)")

    monkeypatch.setattr(aemet, "get_weather_context", boom)
    w = client.get("/v1/weather/context", params={"municipality_code": "28131"}).json()
    assert w["status"] == "unavailable" and w["variables"] == [] and w["fire_danger"] is None
    assert "no es" in w["disclaimer"].lower()


def test_T08_isolation_between_organizations(client, auth_a, auth_b):
    a_areas = client.get("/v1/areas", headers=auth_a).json()
    b_areas = client.get("/v1/areas", headers=auth_b).json()
    assert {x["organization_id"] for x in a_areas}.isdisjoint({x["organization_id"] for x in b_areas})
    a_id = a_areas[0]["id"]
    assert client.get(f"/v1/areas/{a_id}", headers=auth_b).status_code == 404
    scen = client.get("/v1/scenarios", headers=auth_a).json()[0]
    assert client.get(f"/v1/scenarios/{scen['id']}", headers=auth_b).status_code == 404
    assert client.post(f"/v1/scenarios/{scen['id']}/solve", headers=auth_b).status_code == 404
    assert client.get(f"/v1/reports/scenario/{scen['id']}.pdf", headers=auth_b).status_code == 404
    assert client.get("/v1/scenarios", headers=auth_b).json() == []
    insp = client.get("/v1/inspections", headers=auth_a).json()[0]
    r = client.post(f"/v1/inspections/{insp['id']}/evidence", headers=auth_b,
                    files={"file": ("x.png", PNG_1PX, "image/png")})
    assert r.status_code == 404
    assert client.get("/v1/areas").status_code == 401


def test_flow_A_end_to_end(client, auth_a):
    """Flujo A: área → inspección → evidencia → escenario → solve → plan → acción → informe → KPIs."""
    area = client.post("/v1/areas", headers=auth_a, json={
        "name": "Ámbito de test (ficticio)", "municipality_code": "28131"}).json()
    insp = client.post("/v1/inspections", headers=auth_a, json={
        "area_id": area["id"], "inspected_on": "2026-11-06", "inspector_name": "Test",
        "items": [{"checklist_code": "hidrantes", "answer": "no", "observation": "test"}]})
    assert insp.status_code == 201, insp.text
    ev = client.post(f"/v1/inspections/{insp.json()['id']}/evidence", headers=auth_a,
                     files={"file": ("foto.png", PNG_1PX, "image/png")})
    assert ev.status_code == 201 and len(ev.json()["sha256"]) == 64
    bad = client.post(f"/v1/inspections/{insp.json()['id']}/evidence", headers=auth_a,
                      files={"file": ("x.png", b"not an image", "image/png")})
    assert bad.status_code == 415
    sc = client.post("/v1/scenarios", headers=auth_a, json={
        "area_id": area["id"], "name": "Test", "budget_eur": 1000, "is_demo_budget": True,
        "options": [
            {"measure_code": "HIDR-REV", "quantity": 4, "unit_cost_eur": 100, "technical_priority": 5, "coverage_weight": 1},
            {"measure_code": "INFO-POB", "quantity": 1, "unit_cost_eur": 500, "technical_priority": 3, "coverage_weight": 1},
            {"measure_code": "SENAL-CALLES", "quantity": 2, "unit_cost_eur": 300, "technical_priority": 2, "coverage_weight": 1},
        ]})
    assert sc.status_code == 201, sc.text
    sid = sc.json()["id"]
    r1 = client.post(f"/v1/scenarios/{sid}/solve", headers=auth_a).json()
    r2 = client.post(f"/v1/scenarios/{sid}/solve", headers=auth_a).json()
    # T06: presupuesto respetado y reproducible
    for st in r1["strategies"]:
        assert st["total_cost_eur"] <= 1000 + 1e-6
    assert r1["strategies"] == r2["strategies"] and r1["input_hash"] == r2["input_hash"]
    opt = next(s for s in r1["strategies"] if s["strategy"] == "optimized")
    assert sorted(opt["selected"]) == ["HIDR-REV", "INFO-POB"]  # 400+500 ≤ 1000, máximo objetivo
    # T07: sin «% riesgo evitado»
    assert "no" in r1["disclaimer"].lower() and r1["objective_definition"]
    assert "%" not in json.dumps([s for s in r1["strategies"]])  # coberturas como proporción calculada, sin claims
    assert {s["strategy"] for s in r1["strategies"]} == {"manual", "cheapest_first", "optimized"}
    plan = client.post("/v1/action-plans", headers=auth_a, json={"scenario_id": sid}).json()
    act = plan["actions"][0]
    upd = client.patch(f"/v1/action-plans/{plan['id']}/actions/{act['id']}", headers=auth_a,
                       json={"status": "done", "actual_cost_eur": 380, "responsible": "Test", "note": "hecho"})
    assert upd.status_code == 200 and upd.json()["status"] == "done" and len(upd.json()["history"]) == 2
    pdf = client.get(f"/v1/reports/scenario/{sid}.pdf", headers=auth_a)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF") and pdf.headers["X-Report-SHA256"]
    kpis = {k["indicator_id"]: k for k in client.get("/v1/impact", headers=auth_a).json()["kpis"]}
    assert kpis["actions_total"]["value"] >= 2
    audit = client.get("/v1/audit", headers=auth_a).json()
    assert {"solve", "report", "update"} <= {e["action"] for e in audit}


def test_T09_report_text(client):
    import io

    pdf = client.get("/v1/demo/report.pdf")
    assert pdf.status_code == 200
    from pypdf import PdfReader
    text = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf.content)).pages)
    for needle in ("FICTICIOS", "CAM-01", "Validación profesional", "PENDIENTE", "Función objetivo",
                   "PRESUPUESTO DE DEMOSTRACIÓN", "SHA-256", "no es un PAIF"):
        assert needle in text, needle


def test_demo_guided_is_public_and_labeled(client):
    d = client.get("/v1/demo/guided").json()
    assert "FICTICIOS" in d["notice"]
    assert d["area"]["record_status"] == "synthetic" and d["scenario"]["is_demo_budget"] is True
    assert d["scenario"]["latest_result"]["status"] == "OPTIMAL"


def test_csv_export_matches_processed(client):
    r = client.get("/v1/exports/municipalities.csv")
    assert r.status_code == 200
    rows = list(csv.DictReader(r.text.splitlines()))
    assert len(rows) == 179 and rows[0]["population_source"] == "CAM-01"


def test_review_requires_verified_technician(client, auth_a):
    tech = client.post("/v1/auth/login", json={"email": "tecnico@demo.escudo.local", "password": "demo-escudo-2026"}).json()
    h = {"Authorization": f"Bearer {tech['access_token']}"}
    insp = client.get("/v1/inspections", headers=h).json()[0]
    # el técnico demo NO tiene cualificación verificada → 403
    assert client.post(f"/v1/inspections/{insp['id']}/reviews", headers=h, json={"verdict": "util"}).status_code == 403
    # el gestor tampoco puede revisar
    assert client.post(f"/v1/inspections/{insp['id']}/reviews", headers=auth_a, json={"verdict": "util"}).status_code == 403


def test_dataset_version_tracking_on_source_update(loaded_db, tmp_path, monkeypatch):
    """PRD §4.1: al actualizarse un recurso CAM (nuevo SHA-256) se registra una versión nueva y
    la API expone la última; re-cargar el mismo fichero no duplica versiones."""
    import shutil

    from sqlalchemy import func, select

    from escudo_api import etl_load
    from escudo_api.db import SessionLocal
    from escudo_api.models import DatasetVersion, IngestionRun

    fake_data = tmp_path / "data"
    shutil.copytree(ROOT / "data" / "raw", fake_data / "raw", ignore=shutil.ignore_patterns("*.csv", "*.zip", "*.shp",
                                                                                            "*.dbf", "*.shx", "*.sbn",
                                                                                            "*.sbx", "*.prj", "*.xml"))
    m_path = fake_data / "raw" / "CAM-02" / "manifest.json"
    m = json.loads(m_path.read_text(encoding="utf-8"))
    m["sha256"] = "f" * 64
    m["extracted_at"] = "2026-11-20T10:00:00+00:00"
    m_path.write_text(json.dumps(m), encoding="utf-8")
    monkeypatch.setattr(etl_load, "DATA", fake_data)

    def versions(session):
        return session.scalar(select(func.count()).select_from(DatasetVersion).where(DatasetVersion.source_id == "CAM-02"))

    with SessionLocal() as s:
        before = versions(s)
        run = IngestionRun(status="test")
        s.add(run)
        s.flush()
        etl_load.load_sources(s, run)
        etl_load.load_sources(s, run)  # idempotente
        assert versions(s) == before + 1
        s.rollback()  # no contaminar el resto de tests


def test_area_geojson_export_is_private(client, auth_a, auth_b):
    poly = {"type": "Polygon", "coordinates": [[[-4.15, 40.58], [-4.14, 40.58], [-4.14, 40.59], [-4.15, 40.59], [-4.15, 40.58]]]}
    area = client.post("/v1/areas", headers=auth_a, json={"name": "Ámbito con geometría (ficticio, test)",
                                                          "municipality_code": "28131", "geometry": poly}).json()
    r = client.get(f"/v1/areas/{area['id']}.geojson", headers=auth_a)
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/geo+json")
    fc = r.json()
    assert fc["features"][0]["geometry"]["type"] == "MultiPolygon"
    assert "population" not in json.dumps(fc)
    for layer in fc["features"][0]["properties"]["official_layers"].values():
        assert layer["status"] in ("derived", "unavailable")  # nunca «official»: es la generalización web de 200 m
    assert client.get(f"/v1/areas/{area['id']}.geojson", headers=auth_b).status_code == 404
    assert client.get(f"/v1/areas/{area['id']}.geojson").status_code == 401
