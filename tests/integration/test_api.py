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


def test_municipal_matrix_is_reproducible_filter(client):
    """Función analítica CAM × capa oficial: el filtro por densidad (CAM-02) y ≥65 (CAM-01) se aplica de verdad."""
    allm = client.get("/v1/analysis/municipal-matrix").json()
    assert allm["count"] == 179 and set(allm["sources"]) >= {"CAM-01", "CAM-02"}
    f = client.get("/v1/analysis/municipal-matrix", params={"max_density": 100, "min_age65_share": 0.25}).json()
    assert 0 < f["count"] < 179
    assert all(r["density_hab_km2"] <= 100 and r["age_65_plus_share"] >= 0.25 for r in f["rows"])
    assert "No es un índice de riesgo propio" in f["caveat"]


def _auth(client, email: str) -> dict:
    r = client.post("/v1/auth/login", json={"email": email, "password": "demo-escudo-2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_flow_B_municipal_sees_only_authorized_areas(client, auth_a):
    """Flujo B: el ayuntamiento ve solo ámbitos de su término COMPARTIDOS por su organización; solo lectura."""
    muni = _auth(client, "municipal@demo.escudo.local")
    ov = client.get("/v1/municipal/overview", headers=muni)
    assert ov.status_code == 200, ov.text
    d = ov.json()
    assert d["municipality"]["ine_code"] == "28131"
    names = [a["name"] for a in d["areas"]]
    assert "Urbanización Ejemplo Los Pinos (FICTICIA)" in names
    assert not any("no compartido" in n for n in names)          # mismo municipio, sin autorización
    assert not any("organización B" in n for n in names)          # otro municipio
    assert "population" not in json.dumps(d["areas"])             # T04: sin población de ámbito
    a = next(x for x in d["areas"] if x["name"].startswith("Urbanización Ejemplo"))
    assert a["actions_total"] > 0 and a["scenario"]["is_demo_budget"] is True
    file = client.get(f"/v1/municipal/areas/{a['area_id']}", headers=muni)
    assert file.status_code == 200 and file.json()["plan"]["actions"]
    pdf = client.get(f"/v1/municipal/areas/{a['area_id']}/report.pdf", headers=muni)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    # el ámbito no compartido no es accesible ni por id
    c = _auth(client, "gestor-c@demo.escudo.local")
    c_area = client.get("/v1/areas", headers=c).json()[0]
    assert client.get(f"/v1/municipal/areas/{c_area['id']}", headers=muni).status_code == 404
    # sin rol municipal → 403; el municipal no accede a las rutas privadas de la organización
    assert client.get("/v1/municipal/overview", headers=auth_a).status_code == 403
    assert client.get(f"/v1/areas/{a['area_id']}", headers=muni).status_code == 404
    # revocar la autorización la retira al instante; volver a autorizar la restablece
    assert client.patch(f"/v1/areas/{a['area_id']}/sharing", headers=auth_a,
                        json={"shared_with_municipality": False}).status_code == 200
    assert client.get(f"/v1/municipal/areas/{a['area_id']}", headers=muni).status_code == 404
    assert client.patch(f"/v1/areas/{a['area_id']}/sharing", headers=auth_a,
                        json={"shared_with_municipality": True}).status_code == 200
    # solo la gestión de la organización puede autorizar
    tech = _auth(client, "tecnico@demo.escudo.local")
    assert client.patch(f"/v1/areas/{a['area_id']}/sharing", headers=tech,
                        json={"shared_with_municipality": False}).status_code == 403


def test_housing_indicators_trace_to_processed_census(client):
    """Fase 2 (CAM-09/10/11): la ficha muestra el valor exacto del procesado, con estado y fuente; null → no disponible."""
    rows = {r["ine_code"]: r for r in csv.DictReader((ROOT / "data/processed/cam/municipal_housing.csv").open(encoding="utf-8"))}
    h = client.get("/v1/municipalities/28131/profile").json()["housing"]
    ind = {i["indicator_id"]: i for i in h["indicators"]}
    assert len(ind) == 6 and h["census_year"] == 2021
    nm = ind["municipality_non_main_share"]
    assert nm["value"] == pytest.approx(float(rows["28131"]["non_main_share"]))
    assert nm["status"] == "derived" and nm["source_id"] == "CAM-09" and "urbanización" in nm["caveat"]
    assert ind["municipality_dwellings_total"]["status"] == "official"
    missing = next(c for c, r in rows.items() if r["empty_electricity_share"] == "")
    e = {i["indicator_id"]: i for i in client.get(f"/v1/municipalities/{missing}/profile").json()["housing"]["indicators"]}
    assert e["municipality_empty_electricity_share"]["value"] is None
    assert e["municipality_empty_electricity_share"]["status"] == "unavailable"


def test_matrix_filters_by_non_main_share_and_export_has_census(client):
    f = client.get("/v1/analysis/municipal-matrix", params={"min_non_main_share": 0.4, "sort": "non_main"}).json()
    assert 0 < f["count"] < 179 and "CAM-09" in f["sources"]
    vals = [r["non_main_share"] for r in f["rows"]]
    assert all(v >= 0.4 for v in vals) and vals == sorted(vals, reverse=True)
    rows = list(csv.DictReader(client.get("/v1/exports/municipalities.csv").text.splitlines()))
    assert rows[0]["non_main_source"] == "CAM-09" and "non_main_share_2021" in rows[0]


def test_fire_plan_zar_and_municipal_fires_are_literal(client):
    """DOC-01: ZAR (Anexo II, pág. 59) y siniestros 2015–2024 (Anexo I) tal cual el documento oficial."""
    zar = {r["ine_code"] for r in csv.DictReader((ROOT / "data/processed/plan/zar_municipalities.csv").open(encoding="utf-8"))}
    fires = {r["ine_code"]: r for r in csv.DictReader(
        (ROOT / "data/processed/plan/municipal_fires_2015_2024.csv").open(encoding="utf-8"))}
    p = client.get("/v1/municipalities/28131/profile").json()["fire_plan"]
    assert p["source_id"] == "DOC-01" and p["pages"]["zar"] == 59
    assert p["zar"]["value"] == ("Sí" if "28131" in zar else "No") and p["zar"]["status"] == "official"
    assert p["fires_total"]["value"] == int(fires["28131"]["total_published"])
    assert len(p["fires_by_cause"]) == 5
    madrid = client.get("/v1/municipalities/28079/profile").json()["fire_plan"]
    assert madrid["zar"]["value"] == "No"
    pozuelo = client.get("/v1/municipalities/28115/profile").json()["fire_plan"]
    assert pozuelo["fires_total"]["value"] is None and pozuelo["fires_total"]["status"] == "unavailable"
    m = client.get("/v1/analysis/municipal-matrix", params={"zar_only": True, "min_high_share": 0}).json()
    assert m["count"] == 59 and all(r["zar_declared"] for r in m["rows"]) and "DOC-01" in m["sources"]


def test_sources_expose_refresh_check_and_log(client):
    """2.4: cada fuente indica su última comprobación contra el origen; el registro de ejecuciones es público."""
    src = {s["source_id"]: s for s in client.get("/v1/sources").json()}
    assert {"last_checked_at", "last_check_result", "versions_count"} <= set(src["CAM-01"])
    assert src["CAM-01"]["versions_count"] >= 1
    log = client.get("/v1/sources/refresh-log").json()
    assert log["status"] in {"ok", "unavailable"} and "SHA-256" in log["method"]
    if log["last_run"]:
        assert all(r["result"] in {"unchanged", "changed", "failed"} for r in log["last_run"]["results"])


def test_satellite_burnt_areas_profile_and_layer(client):
    """2.6 (EFF-01): perímetros EFFIS literales en el mapa; reparto municipal derivado con método y avisos."""
    rows = [r for r in csv.DictReader((ROOT / "data/processed/effis/municipal_burnt_areas.csv").open(encoding="utf-8"))]
    ine = rows[0]["ine_code"]
    expected = round(sum(float(r["area_ha_in_municipality"]) for r in rows if r["ine_code"] == ine), 1)
    p = client.get(f"/v1/municipalities/{ine}/profile").json()["satellite_burnt"]
    assert p["source_id"] == "EFF-01" and p["status"] == "derived"
    assert p["total_ha_in_municipality"] == pytest.approx(expected, abs=0.2)
    assert "prescritas" in p["caveat"] and "EPSG:25830" in p["method"]
    layers = {x["name"]: x for x in client.get("/v1/layers").json()}
    assert layers["burnt_areas"]["overlay"] and layers["burnt_areas"]["available"]
    g = client.get("/v1/layers/burnt_areas/geojson").json()
    assert g["source_id"] == "EFF-01" and len(g["features"]) == layers["burnt_areas"]["features"]


def test_validation_accounts_see_both_cases_with_draft_scenarios(client):
    """3.1: la organización de validación tiene los casos A y B con inspección y escenario EN BORRADOR (sin resolver)."""
    h = _auth(client, "validacion1@demo.escudo.local")
    names = sorted(a["name"] for a in client.get("/v1/areas", headers=h).json())
    assert len(names) == 2 and names[0].startswith("Caso A") and names[1].startswith("Caso B")
    scen = client.get("/v1/scenarios", headers=h).json()
    assert len(scen) == 2 and all(s["budget_eur"] == 30000 and s["is_demo_budget"] for s in scen)
    assert all(not s.get("latest_result") for s in scen)
    # aislamiento: el gestor de la demo no ve los casos de validación
    demo = _auth(client, "gestor@demo.escudo.local")
    assert not any(a["name"].startswith("Caso ") for a in client.get("/v1/areas", headers=demo).json())


def test_calendar_m16_actions_reviews_and_official_danger_periods(client, auth_a):
    """M16: vencimientos del plan (propios), revisión anual sugerida y épocas de peligro oficiales (DOC-01, pág. 18)."""
    c = client.get("/v1/calendar", params={"from": "2026-11-01", "to": "2027-12-31"}, headers=auth_a).json()
    kinds = {e["kind"] for e in c["events"]}
    assert {"action_due", "inspection_review", "danger_period"} <= kinds and "no son alertas" in c["notice"].lower()
    alto = [e for e in c["events"] if e["kind"] == "danger_period" and e["level"] == "alto"]
    assert alto and alto[0]["start"] == "2027-06-15" and alto[0]["end"] == "2027-09-30" and alto[0]["status"] == "official"
    review = next(e for e in c["events"] if e["kind"] == "inspection_review")
    assert review["start"] == "2027-11-05" or review["start"] > "2027-11-04"  # inspección ficticia 05/11/2026 + 365 d
    assert review["status"] == "derived"
    # aislamiento: B no ve vencimientos ni ámbitos de A
    b = _auth(client, "gestor-b@demo.escudo.local")
    cb = client.get("/v1/calendar", params={"from": "2026-11-01", "to": "2027-12-31"}, headers=b).json()
    assert not any("Los Pinos" in (e.get("area_name") or "") for e in cb["events"])
    ics = client.get("/v1/calendar.ics", params={"from": "2026-11-01", "to": "2027-12-31"}, headers=auth_a)
    assert ics.status_code == 200 and ics.text.startswith("BEGIN:VCALENDAR\r\n") and "DTSTART;VALUE=DATE:20270615" in ics.text
    assert all(len(line.encode("utf-8")) <= 75 for line in ics.text.split("\r\n"))
    assert client.get("/v1/calendar").status_code == 401
    assert client.get("/v1/calendar", params={"from": "2026-01-01", "to": "2020-01-01"}, headers=auth_a).status_code == 422


def test_dossier_m15_checklist_isolation_roles_and_plan_links(client, auth_a, auth_b):
    """M15: expediente INFOMA por ámbito; solo la organización lo ve y edita; enlaza con el plan; nunca aprueba."""
    area = next(a for a in client.get("/v1/areas", headers=auth_a).json() if "Los Pinos" in a["name"])
    d = client.get(f"/v1/areas/{area['id']}/dossier", headers=auth_a).json()
    assert d["source_id"] == "DOC-02" and len(d["items"]) == 15 and "no aprueba" in d["notice"]
    faja = next(i for i in d["items"] if i["code"] == "A6-1.2-FAJA")
    assert faja["status"] == "pending" and faja["data_status"] == "unavailable" and "BOCM pág. 75" in faja["citation"]
    assert any(x["measure_code"] == "FAJA-30" and x["in_plan"] for x in faja["linked_actions"])  # plan del caso guiado
    # otra organización: ni lectura ni escritura (404, sin revelar existencia)
    assert client.get(f"/v1/areas/{area['id']}/dossier", headers=auth_b).status_code == 404
    assert client.patch(f"/v1/areas/{area['id']}/dossier/A5-2.1", headers=auth_b,
                        json={"status": "available"}).status_code == 404
    r = client.patch(f"/v1/areas/{area['id']}/dossier/A5-2.1", headers=auth_a,
                     json={"status": "in_progress", "note": "Borrador del técnico (ficticio)"})
    assert r.status_code == 200 and r.json()["status"] == "in_progress" and r.json()["data_status"] == "user_reported"
    assert client.patch(f"/v1/areas/{area['id']}/dossier/NO-EXISTE", headers=auth_a,
                        json={"status": "available"}).status_code == 404
    assert client.patch(f"/v1/areas/{area['id']}/dossier/A5-2.1", headers=auth_a,
                        json={"status": "aprobado"}).status_code == 422
    ev = client.get("/v1/audit", headers=auth_a).json()
    assert any(e["action"] == "dossier_update" for e in ev)
    # restaurar
    client.patch(f"/v1/areas/{area['id']}/dossier/A5-2.1", headers=auth_a, json={"status": "pending"})


def test_m17_comments_and_decisions_are_private_immutable_and_audited(client, auth_a, auth_b):
    """M17: hilo por actuación/inspección y registro de decisiones del ámbito; aislado (T08), saneado y auditado."""
    area = next(a for a in client.get("/v1/areas", headers=auth_a).json() if "Los Pinos" in a["name"])
    scen_ids = {s["id"] for s in client.get("/v1/scenarios", params={"area_id": area["id"]}, headers=auth_a).json()}
    plan = next(x for x in client.get("/v1/action-plans", headers=auth_a).json() if x["scenario_id"] in scen_ids)
    action = plan["actions"][0]
    ins = client.get("/v1/inspections", params={"area_id": area["id"]}, headers=auth_a).json()[0]
    r = client.post("/v1/comments", headers=auth_a, json={"entity_type": "plan_action", "entity_id": action["id"],
                                                          "kind": "decision", "body": "Se prioriza la faja\r\nnorte\x07"})
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["body"] == "Se prioriza la faja\nnorte" and c["author_name"] and c["status"] == "user_reported"
    assert client.post("/v1/comments", headers=auth_a, json={"entity_type": "inspection", "entity_id": ins["id"],
                                                             "body": "Revisar hidrantes en marzo"}).status_code == 201
    thread = client.get("/v1/comments", params={"entity_type": "plan_action", "entity_id": action["id"]},
                        headers=auth_a).json()
    assert any(x["id"] == c["id"] for x in thread)
    log = client.get(f"/v1/areas/{area['id']}/decisions", headers=auth_a).json()
    assert log["count"] >= 1 and all(e["kind"] == "decision" for e in log["entries"]) and "inmutable" in log["notice"]
    assert client.get(f"/v1/areas/{area['id']}/decisions", params={"kind": "all"}, headers=auth_a).json()["count"] >= 2
    # aislamiento: otra organización no lee ni escribe (404)
    assert client.get("/v1/comments", params={"entity_type": "plan_action", "entity_id": action["id"]},
                      headers=auth_b).status_code == 404
    assert client.post("/v1/comments", headers=auth_b, json={"entity_type": "area", "entity_id": area["id"],
                                                             "body": "intruso"}).status_code == 404
    assert client.get(f"/v1/areas/{area['id']}/decisions", headers=auth_b).status_code == 404
    # validación: vacío tras sanear, tipo desconocido, sin sesión
    assert client.post("/v1/comments", headers=auth_a, json={"entity_type": "area", "entity_id": area["id"],
                                                             "body": " \x07 "}).status_code == 422
    assert client.post("/v1/comments", headers=auth_a, json={"entity_type": "scenario", "entity_id": area["id"],
                                                             "body": "x"}).status_code == 422
    assert client.get("/v1/comments", params={"entity_type": "area", "entity_id": area["id"]}).status_code == 401
    # inmutable: no hay ruta de edición ni de borrado
    assert client.delete(f"/v1/comments/{c['id']}", headers=auth_a).status_code in (404, 405)
    assert any(e["action"] == "decision_create" for e in client.get("/v1/audit", headers=auth_a).json())


def test_m19_docs_search_is_extractive_public_and_bounded(client):
    r = client.get("/v1/docs/search", params={"q": "¿Cuándo es la época de peligro alto de incendios forestales?"}).json()
    assert r["status"] == "official" and "no redactar respuestas" in r["disclaimer"].lower().replace("sin ", "no ")
    assert any("15 de junio hasta el 30 de septiembre" in x["text"] for x in r["results"][:3])
    assert all(x["url"].startswith("https://") and "#page=" in x["url"] for x in r["results"])
    assert client.get("/v1/docs/search", params={"q": "ab"}).status_code == 422
    assert client.get("/v1/docs/search", params={"q": "x" * 301}).status_code == 422
    ev = client.get("/v1/docs/evaluation").json()
    assert ev["total"] == 20 and ev["hits"] >= 18


def test_m18_public_progress_respects_consent_threshold_and_never_leaks_private_data(client):
    """M18: agregados públicos solo de ámbitos autorizados, con umbral (≥3 ámbitos, ≥2 organizaciones), sin nombres."""
    r = client.get("/v1/public/progress")  # sin autenticación
    assert r.status_code == 200
    d = r.json()
    t = d["thresholds"]
    assert t["min_areas"] == 3 and t["min_organizations"] == 3 and t["max_org_share"] == 0.5 and "no de riesgo" in d["notice"]
    pub = {m["ine_code"]: m for m in d["published"]}
    m = pub["28047"]
    assert m["synthetic"] is True and m["zar_declared"] is True and m["areas_band"] == "3 o más"
    # anti-diferencias: valores gruesos y sin recuentos exactos de organizaciones, ámbitos ni puntos del expediente
    for k in ("actions_done_share", "actions_documented_share", "actions_overdue_share", "areas_inspected_last_12m_share"):
        assert m[k] is None or abs(m[k] * 10 - round(m[k] * 10)) < 1e-9, (k, m[k])
    assert m["actions_total_approx"] % 5 == 0
    assert not {"organizations", "areas", "actions_total", "dossier_points_available"} & set(m)
    # 28131 solo tiene 1 ámbito autorizado: no se publica ninguna cifra
    w = {m["ine_code"]: m for m in d["withheld"]}
    assert "28131" in w and set(w["28131"]) == {"ine_code", "name", "reason"}
    flat = json.dumps(d, ensure_ascii=False)
    for private in ("Los Pinos", "DEMO D", "Ámbito D", "Gestora", "budget", "cost_eur", "area_id", "organization_id",
                    "no compartido"):
        assert private not in flat, private


def test_m21_offline_sync_is_idempotent_for_inspections_and_photos(client, auth_a):
    """M21: reenviar una inspección (mismo client_uuid) o la misma foto no duplica; el uuid no salta de ámbito."""
    import uuid as _uuid

    areas = client.get("/v1/areas", headers=auth_a).json()
    area = next(a for a in areas if "Los Pinos" in a["name"])
    cu = str(_uuid.uuid4())
    body = {"area_id": area["id"], "inspected_on": "2026-11-10", "inspector_name": "Campo (ficticio)",
            "items": [{"checklist_code": "hidrantes", "answer": "parcial", "observation": "sin conexión"}],
            "client_uuid": cu}
    r1 = client.post("/v1/inspections", headers=auth_a, json=body)
    r2 = client.post("/v1/inspections", headers=auth_a, json=body)
    assert r1.status_code == 201 and r2.status_code == 200 and r2.json()["replayed"] is True
    assert r1.json()["id"] == r2.json()["id"]
    n = sum(1 for i in client.get("/v1/inspections", params={"area_id": area["id"]}, headers=auth_a).json()
            if i["inspector_name"] == "Campo (ficticio)")
    assert n == 1
    files = {"file": ("foto.png", PNG_1PX, "image/png")}
    e1 = client.post(f"/v1/inspections/{r1.json()['id']}/evidence", headers=auth_a, files=files)
    e2 = client.post(f"/v1/inspections/{r1.json()['id']}/evidence", headers=auth_a,
                     files={"file": ("foto.png", PNG_1PX, "image/png")})
    assert e1.status_code == 201 and e2.json()["replayed"] is True and e1.json()["id"] == e2.json()["id"]
    other = next((a for a in areas if a["id"] != area["id"]), None)
    if other:
        assert client.post("/v1/inspections", headers=auth_a, json={**body, "area_id": other["id"]}).status_code == 409
    assert client.post("/v1/inspections", headers=auth_a, json={**body, "client_uuid": "no-es-uuid"}).status_code == 422
