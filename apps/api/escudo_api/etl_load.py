"""Carga idempotente de datos procesados en PostGIS + seed de demostración FICTICIO.

Uso: python -m escudo_api.etl_load [--no-seed] [--reset]
Requisitos previos: escudo_pipelines.fetch, escudo_pipelines.cam_transform (y opcionalmente idem.transform).
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from shapely.geometry import MultiPolygon, shape
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, SessionLocal, engine
from .indicators import INDICATORS
from .models import (
    DataQualityCheck,
    DatasetVersion,
    DataSource,
    IndicatorDefinition,
    IngestionRun,
    MeasureCatalog,
    Membership,
    Municipality,
    MunicipalSeries,
    OfficialLayerMunicipalShare,
    OfficialLayerPolygon,
    Organization,
    ProtectedSpace,
    RegionalSeries,
    SatelliteBurntArea,
    SatelliteBurntAreaMunicipality,
    User,
)

log = logging.getLogger("escudo.etl")
DATA = settings.data_dir
CAM = DATA / "processed" / "cam"
IDEM = DATA / "processed" / "idem"
SEED = settings.data_dir.parent / "fixtures" / "synthetic" / "demo_seed.json"


def _f(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def _i(v: str) -> int | None:
    return int(float(v)) if v not in ("", None) else None


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _multi_wkt(geojson_geom: dict) -> str:
    g = shape(geojson_geom)
    if g.geom_type == "Polygon":
        g = MultiPolygon([g])
    elif g.geom_type == "GeometryCollection":
        polys = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon")]
        flat = [q for p in polys for q in (p.geoms if p.geom_type == "MultiPolygon" else [p])]
        g = MultiPolygon(flat)
    return f"SRID=4326;{g.wkt}"


def all_source_specs() -> list:
    from escudo_pipelines.sources import CAM_SOURCES

    specs = list(CAM_SOURCES)
    from escudo_pipelines.plan_anual import SPEC as PLAN_SPEC

    specs.append(PLAN_SPEC)
    from escudo_pipelines.effis import SPEC as EFFIS_SPEC
    from escudo_pipelines.infoma import SPEC as INFOMA_SPEC

    specs += [EFFIS_SPEC, INFOMA_SPEC]
    try:
        from escudo_pipelines.idem.sources import IDEM_SOURCES

        specs += list(IDEM_SOURCES)
    except ImportError:
        log.warning("Fuentes IDEM no disponibles")
    return specs


def ensure_schema() -> None:
    """Crea el esquema si falta y deja la base marcada en la última migración de Alembic.

    Si la base nunca se migró (instalación siguiendo el README sin `alembic upgrade`), `create_all` construye el
    esquema actual y se marca como `head`; así un `alembic upgrade head` posterior no intenta recrear tablas.
    """
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        had_version = conn.execute(text("SELECT to_regclass('alembic_version') IS NOT NULL")).scalar() and \
            conn.execute(text("SELECT count(*) FROM alembic_version")).scalar() > 0
    Base.metadata.create_all(engine)
    if not had_version:
        try:
            from alembic import command
            from alembic.config import Config

            ini = Path(__file__).resolve().parents[3] / "alembic.ini"
            if ini.exists():
                command.stamp(Config(str(ini)), "head")
                log.info("Esquema creado desde los modelos y marcado en la migración más reciente (alembic stamp head)")
        except Exception as exc:  # sin Alembic disponible la carga sigue siendo válida
            log.warning("No se pudo marcar la versión del esquema: %s", exc)


def load_sources(session: Session, run: IngestionRun) -> None:
    from dataclasses import asdict

    specs = all_source_specs()
    aemet = {
        "source_id": "AEMET", "portal": "AEMET", "ckan_id": None,
        "title": "AEMET — Predicción municipal (XML público) / AEMET OpenData",
        "producer": "Agencia Estatal de Meteorología", "catalog_url": "https://www.aemet.es/es/datos_abiertos/AEMET_OpenData",
        "license": "Reutilización AEMET (cita «Fuente: AEMET»)", "spatial_scope": "municipio (punto de referencia)",
        "temporal_scope": "predicción diaria (consulta en tiempo real con TTL)",
        "use_in_product": "Contexto meteorológico diario informativo con fecha de emisión y caducidad",
        "caveats": "No es alerta operativa ni pronóstico de ignición. Si falla: no disponible.",
    }
    rows = [{k: v for k, v in asdict(s).items() if k in DataSource.__table__.columns} for s in specs] + [aemet]
    for r in rows:
        src = session.get(DataSource, r["source_id"]) or DataSource(source_id=r["source_id"])
        for k, v in r.items():
            setattr(src, k, v)
        session.add(src)
        manifest = DATA / "raw" / r["source_id"] / "manifest.json"
        if manifest.exists():
            m = json.loads(manifest.read_text(encoding="utf-8"))
            exists = session.scalar(select(DatasetVersion).where(DatasetVersion.source_id == r["source_id"],
                                                                 DatasetVersion.sha256 == m["sha256"]))
            if not exists:
                session.add(DatasetVersion(source_id=r["source_id"], resource_url=m.get("resource_url") or m.get("url", ""),
                                           file_name=m.get("file", ""), sha256=m["sha256"], bytes=m.get("bytes", 0),
                                           portal_modified_at=m.get("portal_metadata_modified") or m.get("resource_last_modified"),
                                           extracted_at=datetime.fromisoformat(m["extracted_at"])))
            src.status = "ok"
        elif r["source_id"] == "AEMET":
            src.status = "ok"  # consulta en tiempo real; la salud se refleja por petición
        else:
            src.status = "not_ingested"
    session.flush()


def load_quality(session: Session, run: IngestionRun) -> None:
    q = json.loads((CAM / "quality.json").read_text(encoding="utf-8"))
    owner = {"municipios_cam01": "CAM-01", "municipios_geometria": "CAM-08", "codigos_coinciden": "CAM-08",
             "geometrias_validas": "CAM-08", "coherencia_densidad": "CAM-02", "rango_share65": "CAM-01",
             "cam05_conceptos_conocidos": "CAM-05", "cam04_sin_geometria": "CAM-04"}
    for c in q["checks"]:
        session.add(DataQualityCheck(run_id=run.id, source_id=owner.get(c["check"]), check=c["check"],
                                     passed=c["passed"], detail=c["detail"]))
    for sid, qpath in (("DOC-01", DATA / "processed" / "plan" / "quality.json"),
                       ("EFF-01", DATA / "processed" / "effis" / "quality.json")):
        if qpath.exists():
            for c in json.loads(qpath.read_text(encoding="utf-8")).get("checks", []):
                session.add(DataQualityCheck(run_id=run.id, source_id=sid, check=c["check"][:64],
                                             passed=bool(c["passed"]), detail=str(c.get("detail", ""))))
    idem_q = IDEM / "quality.json"
    if idem_q.exists():
        for c in json.loads(idem_q.read_text(encoding="utf-8")).get("checks", []):
            session.add(DataQualityCheck(run_id=run.id, source_id=c.get("source_id"), check=c["check"][:64],
                                         passed=bool(c["passed"]), detail=str(c.get("detail", ""))))


def load_municipalities(session: Session) -> int:
    geo = json.loads((CAM / "municipalities.geojson").read_text(encoding="utf-8"))
    geoms = {f["properties"]["ine_code"]: _multi_wkt(f["geometry"]) for f in geo["features"]}
    n = 0
    for r in _csv(CAM / "municipal_indicators.csv"):
        m = session.get(Municipality, r["ine_code"]) or Municipality(ine_code=r["ine_code"])
        m.name = r["name"]
        m.population_total = _i(r["population_total"])
        m.population_65_plus = _i(r["population_65_plus"])
        m.age_65_plus_share = _f(r["age_65_plus_share"])
        m.population_year = _i(r["population_year"])
        m.density_hab_km2 = _f(r["density_hab_km2"])
        m.density_year = _i(r["density_year"])
        m.altitude_m = _f(r["altitude_m"])
        m.altitude_year = _i(r["altitude_year"])
        m.area_km2 = _f(r["area_km2"])
        m.geom = geoms.get(r["ine_code"])
        session.add(m)
        n += 1
    session.flush()
    session.execute(delete(MunicipalSeries))
    for r in _csv(CAM / "municipal_population_series.csv"):
        session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id="municipality_population_total",
                                    year=int(r["year"]), value=_f(r["population_total"]), source_id="CAM-01"))
        tot, a65 = _f(r["population_total"]), _f(r["population_65_plus"])
        session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id="municipality_age_65_plus_share",
                                    year=int(r["year"]), value=(a65 / tot) if tot else None, source_id="CAM-01"))
    for r in _csv(CAM / "municipal_density_series.csv"):
        session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id="municipality_density", year=int(r["year"]),
                                    value=_f(r["density_hab_km2"]), source_id="CAM-02"))
    housing = CAM / "municipal_housing.csv"
    if housing.exists():  # CAM-09/10/11 (Censo 2021); nulos se guardan como null → «no disponible»
        for r in _csv(housing):
            for col, ind in HOUSING_COLUMNS.items():
                session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id=ind, year=int(r["year"]),
                                            value=_f(r[col]), source_id=INDICATORS[ind]["source_id"]))
    else:
        log.warning("Sin %s: ejecute escudo_pipelines.cam_transform (indicadores de vivienda no disponibles)", housing)
    load_plan(session)
    return n


PLAN = DATA / "processed" / "plan"
FIRE_CAUSES = ("rayo", "negligencia_accidente", "intencionado", "desconocida", "reproducido")


def load_plan(session: Session) -> None:
    """DOC-01 (Plan Anual 2026): ZAR (1/0 para los 179 municipios) y siniestros 2015–2024 por causa (literal)."""
    zar_csv, fires_csv = PLAN / "zar_municipalities.csv", PLAN / "municipal_fires_2015_2024.csv"
    if not zar_csv.exists() or not fires_csv.exists():
        log.warning("Sin %s: ejecute escudo_pipelines.plan_anual (ZAR y siniestros municipales no disponibles)", PLAN)
        return
    zar = {r["ine_code"] for r in _csv(zar_csv)}
    codes = [c for (c,) in session.execute(select(Municipality.ine_code))]
    for c in codes:
        session.add(MunicipalSeries(ine_code=c, indicator_id="municipality_zar_declared", year=2026,
                                    value=1.0 if c in zar else 0.0, source_id="DOC-01"))
    for r in _csv(fires_csv):
        if r["ine_code"] not in codes:
            continue
        session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id="municipality_fires_total_2015_2024",
                                    year=2024, value=_f(r["total_published"]), source_id="DOC-01"))
        for cause in FIRE_CAUSES:
            session.add(MunicipalSeries(ine_code=r["ine_code"], indicator_id=f"municipality_fires_{cause}_2015_2024",
                                        year=2024, value=_f(r[cause]), source_id="DOC-01"))


# columna de data/processed/cam/municipal_housing.csv → indicador trazable
HOUSING_COLUMNS = {
    "dwellings_total": "municipality_dwellings_total",
    "dwellings_non_main": "municipality_non_main_dwellings",
    "non_main_share": "municipality_non_main_share",
    "single_dwelling_building_share": "municipality_single_dwelling_building_share",
    "empty_electricity_share": "municipality_empty_electricity_share",
    "sporadic_electricity_share": "municipality_sporadic_electricity_share",
}


EFFIS = DATA / "processed" / "effis"


def load_effis(session: Session) -> int:
    """EFF-01: perímetros EFFIS que intersecan la región (literales) y su reparto municipal (derivado)."""
    gj, csv_path = EFFIS / "burnt_areas_madrid.geojson", EFFIS / "municipal_burnt_areas.csv"
    session.execute(delete(SatelliteBurntAreaMunicipality))
    session.execute(delete(SatelliteBurntArea))
    if not gj.exists() or not csv_path.exists():
        log.warning("Sin %s: ejecute escudo_pipelines.effis (áreas quemadas no disponibles)", EFFIS)
        return 0
    fc = json.loads(gj.read_text(encoding="utf-8"))
    for f in fc["features"]:
        p = f["properties"]
        session.add(SatelliteBurntArea(
            effis_id=p["effis_id"], source_id="EFF-01", year=p["year"],
            fire_date=date.fromisoformat(p["fire_date"]) if p.get("fire_date") else None,
            last_update=date.fromisoformat(p["last_update"]) if p.get("last_update") else None,
            area_ha_effis=p["area_ha_effis"], area_ha_in_region=p["area_ha_in_region_derived"],
            commune_literal=p.get("commune_literal"), province_literal=p.get("province_literal"),
            attributes={k: v for k, v in p.items() if k.startswith("lc_") or k in ("natura2000_pct", "class",
                                                                                    "final_date", "country")},
            geom=_multi_wkt(f["geometry"])))
    session.flush()
    codes = {c for (c,) in session.execute(select(Municipality.ine_code))}
    for r in _csv(csv_path):
        if r["ine_code"] in codes:
            session.add(SatelliteBurntAreaMunicipality(effis_id=r["effis_id"], ine_code=r["ine_code"],
                                                       area_ha=float(r["area_ha_in_municipality"])))
    return len(fc["features"])


def load_regional(session: Session) -> None:
    session.execute(delete(RegionalSeries))
    for r in _csv(CAM / "fire_history.csv"):
        for k, v in r.items():
            if k in ("year", "scope"):
                continue
            session.add(RegionalSeries(source_id="CAM-05", concept=k, year=int(r["year"]), value=_f(v),
                                       unit="ha" if k.endswith("_ha") else "nº"))
    seen = set()
    for r in _csv(CAM / "land_use_regional.csv"):
        key = (r["concept"][:128], int(r["year"]))
        if key in seen:
            continue
        seen.add(key)
        session.add(RegionalSeries(source_id="CAM-07", concept=key[0], year=key[1], value=_f(r["value_ha"]), unit="ha"))
    for r in _csv(CAM / "reforestation.csv"):
        session.add(RegionalSeries(source_id="CAM-06", concept=r["vegetation_group"], year=int(r["year"]),
                                   value=_f(r["area_ha"]), unit="ha"))
    session.execute(delete(ProtectedSpace))
    for r in _csv(CAM / "protected_spaces.csv"):
        session.add(ProtectedSpace(category=r["category"], figure=r["figure"], name=r["name"], area_ha=_f(r["area_ha"]),
                                   declared_on=r["declared_on"] or None, norm_url=r["norm_url"] or None))


LAYER_FILES = {"risk": "GEO-01", "hazard": "GEO-02", "vulnerability": "GEO-03"}


def load_idem(session: Session) -> dict[str, int]:
    out: dict[str, int] = {}
    session.execute(delete(OfficialLayerPolygon))
    session.execute(delete(OfficialLayerMunicipalShare))
    for layer, sid in LAYER_FILES.items():
        path = IDEM / f"{layer}.geojson"
        if not path.exists():
            out[layer] = 0
            continue
        fc = json.loads(path.read_text(encoding="utf-8"))
        n = 0
        for f in fc["features"]:
            if not f.get("geometry"):
                continue
            p = f["properties"]
            session.add(OfficialLayerPolygon(layer=layer, source_id=sid, class_code=str(p.get("class_code")),
                                             class_label=str(p.get("class_label")), geom=_multi_wkt(f["geometry"])))
            n += 1
        out[layer] = n
    shares = IDEM / "municipal_class_shares.csv"
    if shares.exists():
        for r in _csv(shares):
            session.add(OfficialLayerMunicipalShare(ine_code=r["ine_code"], layer=r["layer"], class_label=r["class_label"],
                                                    class_code=r.get("class_code") or None, area_ha=float(r["area_ha"]),
                                                    area_share=float(r["area_share"]), source_id=LAYER_FILES[r["layer"]]))
    return out


def load_indicators(session: Session) -> None:
    for k, v in INDICATORS.items():
        session.merge(IndicatorDefinition(indicator_id=k, **v))


def load_measures(session: Session) -> int:
    path = DATA / "reference" / "measures_catalog.json"
    if not path.exists():
        log.warning("Catálogo de medidas no encontrado")
        return 0
    doc = json.loads(path.read_text(encoding="utf-8"))
    core = {"code", "name", "description", "unit", "reference_unit_cost_eur", "cost_status", "cost_source",
            "normative_refs", "prerequisites", "excludes", "requires_professional"}
    for m in doc["measures"]:
        session.merge(MeasureCatalog(**{k: m.get(k) for k in core}, extra={k: v for k, v in m.items() if k not in core}))
    return len(doc["measures"])


def seed_demo(session: Session) -> dict:
    """Seed FICTICIO etiquetado (record_status='synthetic'). Idempotente: borra y recrea lo sintético."""
    from .models import (
        ActionPlan,
        AreaOfInterest,
        AuditEvent,
        Comment,
        DossierItem,
        EvidenceFile,
        Inspection,
        InspectionItem,
        PlanAction,
        Report,
        Scenario,
        ScenarioOption,
        ScenarioResultRow,
    )
    from .routers.private import create_plan_from, solve_scenario
    from .security import hash_password

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    synth_orgs = [o.id for o in session.scalars(select(Organization).where(Organization.record_status == "synthetic"))]
    if synth_orgs:
        scen_ids = list(session.scalars(select(Scenario.id).where(Scenario.organization_id.in_(synth_orgs))))
        plan_ids = list(session.scalars(select(ActionPlan.id).where(ActionPlan.organization_id.in_(synth_orgs))))
        insp_ids = list(session.scalars(select(Inspection.id).where(Inspection.organization_id.in_(synth_orgs))))
        session.execute(delete(EvidenceFile).where(EvidenceFile.organization_id.in_(synth_orgs)))
        session.execute(delete(PlanAction).where(PlanAction.plan_id.in_(plan_ids)))
        session.execute(delete(ActionPlan).where(ActionPlan.id.in_(plan_ids)))
        session.execute(delete(Report).where(Report.scenario_id.in_(scen_ids)))
        session.execute(delete(ScenarioResultRow).where(ScenarioResultRow.scenario_id.in_(scen_ids)))
        session.execute(delete(ScenarioOption).where(ScenarioOption.scenario_id.in_(scen_ids)))
        session.execute(delete(Scenario).where(Scenario.id.in_(scen_ids)))
        session.execute(delete(InspectionItem).where(InspectionItem.inspection_id.in_(insp_ids)))
        session.execute(delete(Inspection).where(Inspection.id.in_(insp_ids)))
        session.execute(delete(DossierItem).where(DossierItem.organization_id.in_(synth_orgs)))
        session.execute(delete(Comment).where(Comment.organization_id.in_(synth_orgs)))
        session.execute(delete(AreaOfInterest).where(AreaOfInterest.organization_id.in_(synth_orgs)))
        session.execute(delete(AuditEvent).where(AuditEvent.organization_id.in_(synth_orgs)))
        session.execute(delete(Membership).where(Membership.organization_id.in_(synth_orgs)))
        session.execute(delete(User).where(User.record_status == "synthetic"))
        session.execute(delete(Organization).where(Organization.id.in_(synth_orgs)))
        session.flush()

    orgs, areas = {}, {}
    for o in seed["organizations"]:
        org = Organization(name=o["name"], kind=o["kind"], municipality_code=o.get("municipality_code"),
                           record_status="synthetic")
        session.add(org)
        session.flush()
        orgs[o["key"]] = org
        for u in o["users"]:
            user = User(email=u["email"], full_name=u["full_name"], password_hash=hash_password(u["password"]),
                        record_status="synthetic")
            session.add(user)
            session.flush()
            session.add(Membership(user_id=user.id, organization_id=org.id, role=u["role"],
                                   technical_qualification_verified=False))
    for a in seed["areas"]:
        area = AreaOfInterest(organization_id=orgs[a["org"]].id, name=a["name"], municipality_code=a["municipality_code"],
                              description=a["description"], record_status="synthetic",
                              shared_with_municipality=a.get("shared_with_municipality", False))
        session.add(area)
        session.flush()
        areas[a["key"]] = area
    for i in seed["inspections"]:
        area = areas[i["area"]]
        session.add(Inspection(organization_id=area.organization_id, area_id=area.id,
                               inspected_on=date.fromisoformat(i["inspected_on"]), inspector_name=i["inspector_name"],
                               record_status="synthetic", items=[InspectionItem(**it) for it in i["items"]]))
    session.flush()
    summary = {}
    for s in seed["scenarios"]:
        area = areas[s["area"]]
        sc = Scenario(organization_id=area.organization_id, area_id=area.id, name=s["name"], budget_eur=s["budget_eur"],
                      is_demo_budget=s["is_demo_budget"], record_status="synthetic",
                      options=[ScenarioOption(position=k, cost_status="scenario", **o) for k, o in enumerate(s["options"])])
        session.add(sc)
        session.flush()
        if s.get("solve", True) is False:  # escenario en borrador (sesiones de validación): lo resuelve el participante
            summary[s["name"]] = {"status": "draft"}
            continue
        res = solve_scenario(session, sc)
        session.flush()
        session.refresh(sc)
        plan = create_plan_from(session, sc, "optimized", None)
        for upd in s.get("plan_updates", seed.get("plan_updates", [])):
            for a in plan.actions:
                if a.measure_code == upd["measure_code"]:
                    a.status = upd["status"]
                    a.responsible = upd["responsible"]
                    a.due_date = date.fromisoformat(upd["due_date"])
                    if "actual_cost_eur" in upd:
                        a.actual_cost_eur = upd["actual_cost_eur"]
                    a.history = [*a.history, {"at": datetime.now(UTC).isoformat(), "by": "seed", "change": "update",
                                              "note": upd["note"]}]
        summary[s["name"]] = {"status": res.get("status"),
                              "strategies": {x["strategy"]: x["total_cost_eur"] for x in res.get("strategies", [])}}
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-seed", action="store_true")
    ap.add_argument("--skip-idem", action="store_true", help="No recargar capas IDEM (conserva las existentes)")
    ap.add_argument("--reset", action="store_true", help="DROP de todas las tablas antes de cargar (solo desarrollo)")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO)
    if args.reset:
        Base.metadata.drop_all(engine)
    ensure_schema()
    with SessionLocal() as session:
        run = IngestionRun(status="running")
        session.add(run)
        session.flush()
        load_sources(session, run)
        load_quality(session, run)
        n_muni = load_municipalities(session)
        load_regional(session)
        n_effis = load_effis(session)
        idem = {} if args.skip_idem else load_idem(session)
        for layer, sid in LAYER_FILES.items():
            src = session.get(DataSource, sid)
            if src is not None and idem.get(layer, 0) == 0:
                src.status = "not_ingested" if src.status != "ok" else "ok"
        load_indicators(session)
        n_meas = load_measures(session)
        session.flush()
        seed = seed_demo(session) if not args.no_seed and n_meas else {}
        run.status = "ok"
        run.finished_at = datetime.now(UTC)
        run.summary = {"municipalities": n_muni, "effis_perimeters": n_effis, "idem_polygons": idem, "measures": n_meas, "seed": seed}
        session.commit()
        print(json.dumps(run.summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
