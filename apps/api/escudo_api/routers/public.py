"""Endpoints públicos (visitante y evaluador, Flujo C/D)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_session
from ..indicators import INDICATORS
from ..models import (
    DataQualityCheck,
    DataSource,
    IngestionRun,
    MeasureCatalog,
    Municipality,
    OfficialLayerPolygon,
    ProtectedSpace,
    RegionalSeries,
)
from ..services import OFFICIAL_LAYERS, municipality_profile, municipality_summary, sources_health

router = APIRouter()


@router.get("/health", tags=["sistema"])
def health(session: Session = Depends(get_session)) -> dict[str, Any]:
    try:
        session.execute(text("SELECT 1"))
        db = "ok"
        ok, total = sources_health(session)
    except Exception:
        db, ok, total = "error", 0, 0
    return {"status": "ok" if db == "ok" else "degraded", "db": db, "version": settings.version,
            "sources_ok": ok, "sources_total": total}


def _source_dict(s: DataSource) -> dict[str, Any]:
    v = s.versions[-1] if s.versions else None
    return {
        "source_id": s.source_id, "portal": s.portal, "title": s.title, "producer": s.producer,
        "catalog_url": s.catalog_url, "license": s.license, "spatial_scope": s.spatial_scope,
        "temporal_scope": s.temporal_scope, "use_in_product": s.use_in_product, "caveats": s.caveats,
        "status": s.status,
        "last_extracted_at": v.extracted_at.isoformat() if v else None,
        "portal_modified_at": v.portal_modified_at if v else None,
        "sha256": v.sha256 if v else None,
        "resource_url": v.resource_url if v else None,
    }


@router.get("/v1/sources", tags=["procedencia"])
def list_sources(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return [_source_dict(s) for s in session.scalars(select(DataSource).order_by(DataSource.source_id))]


@router.get("/v1/sources/{source_id}", tags=["procedencia"])
def get_source(source_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    s = session.get(DataSource, source_id)
    if s is None:
        raise HTTPException(404, "Fuente no encontrada")
    last_run = session.scalar(select(IngestionRun).order_by(IngestionRun.id.desc()))
    checks = []
    if last_run:
        checks = [{"check": c.check, "passed": c.passed, "detail": c.detail} for c in session.scalars(
            select(DataQualityCheck).where(DataQualityCheck.run_id == last_run.id, DataQualityCheck.source_id == source_id))]
    return {**_source_dict(s), "quality_checks": checks,
            "versions": [{"sha256": v.sha256, "extracted_at": v.extracted_at.isoformat(), "bytes": v.bytes}
                         for v in s.versions]}


@router.get("/v1/indicators", tags=["procedencia"])
def list_indicators() -> list[dict[str, Any]]:
    return [{"indicator_id": k, **v} for k, v in INDICATORS.items()]


@router.get("/v1/municipalities", tags=["territorio"])
def list_municipalities(
    q: str | None = None,
    min_density: float | None = Query(None, ge=0),
    max_density: float | None = Query(None, ge=0),
    sort: str = Query("name", pattern="^(name|density|population|age65)$"),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    stmt = select(Municipality)
    if q:
        stmt = stmt.where(func.unaccent(Municipality.name).ilike(func.unaccent(f"%{q}%")))
    if min_density is not None:
        stmt = stmt.where(Municipality.density_hab_km2 >= min_density)
    if max_density is not None:
        stmt = stmt.where(Municipality.density_hab_km2 <= max_density)
    order = {"name": Municipality.name, "density": Municipality.density_hab_km2.desc(),
             "population": Municipality.population_total.desc(), "age65": Municipality.age_65_plus_share.desc()}[sort]
    return [municipality_summary(m) for m in session.scalars(stmt.order_by(order))]


def _get_muni(session: Session, ine_code: str) -> Municipality:
    m = session.get(Municipality, ine_code)
    if m is None:
        raise HTTPException(404, f"Municipio {ine_code} no encontrado")
    return m


@router.get("/v1/municipalities/{ine_code}/profile", tags=["territorio"])
def get_profile(ine_code: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    return municipality_profile(session, _get_muni(session, ine_code))


@router.get("/v1/municipalities/{ine_code}/series", tags=["territorio"])
def get_series(ine_code: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    from ..models import MunicipalSeries

    _get_muni(session, ine_code)
    rows = session.scalars(select(MunicipalSeries).where(MunicipalSeries.ine_code == ine_code)
                           .order_by(MunicipalSeries.indicator_id, MunicipalSeries.year)).all()
    series: dict[str, list] = {}
    for r in rows:
        series.setdefault(r.indicator_id, []).append({"year": r.year, "value": r.value, "source_id": r.source_id})
    return {"ine_code": ine_code, "status": "official", "series": series}


@router.get("/v1/compare", tags=["territorio"])
def compare(a: str, b: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    pa = municipality_profile(session, _get_muni(session, a), with_weather=False)
    pb = municipality_profile(session, _get_muni(session, b), with_weather=False)
    same = all(pa[k]["temporal_scope"] == pb[k]["temporal_scope"] for k in ("population", "density"))
    return {"a": pa, "b": pb, "same_reference_year": same}


@router.get("/v1/layers", tags=["capas"])
def list_layers(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    layers = [{"name": "municipalities", "label": "Municipios (Portal CAM)", "source_id": "CAM-08",
               "status": "official", "available": True, "geometry": "polygon",
               "properties": ["ine_code", "name", "population", "density", "age_65_plus_share", "altitude_m"]}]
    meta_path = settings.data_dir / "processed" / "idem" / "layers_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    for name, m in OFFICIAL_LAYERS.items():
        n = session.scalar(select(func.count()).select_from(OfficialLayerPolygon).where(OfficialLayerPolygon.layer == name)) or 0
        lm = (meta.get("layers", meta) if isinstance(meta, dict) else {}).get(name, {})
        layers.append({"name": name, "label": m["label"], "source_id": m["source_id"],
                       "status": "official" if n else "unavailable", "available": bool(n), "features": n,
                       "classes": lm.get("classes", []), "license": lm.get("license"),
                       "version": lm.get("version_or_date")})
    return layers


@router.get("/v1/layers/{name}/geojson", tags=["capas"])
def layer_geojson(name: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    if name == "municipalities":
        rows = session.execute(select(Municipality, func.ST_AsGeoJSON(Municipality.geom, 5))).all()
        feats = [{"type": "Feature", "geometry": json.loads(g) if g else None,
                  "properties": {"ine_code": m.ine_code, "name": m.name, "population": m.population_total,
                                 "density": m.density_hab_km2, "age_65_plus_share": m.age_65_plus_share,
                                 "altitude_m": m.altitude_m, "population_year": m.population_year,
                                 "density_year": m.density_year}} for m, g in rows]
        return {"type": "FeatureCollection", "source_id": "CAM-08", "features": feats}
    if name not in OFFICIAL_LAYERS:
        raise HTTPException(404, "Capa desconocida")
    rows = session.execute(select(OfficialLayerPolygon.class_code, OfficialLayerPolygon.class_label,
                                  func.ST_AsGeoJSON(OfficialLayerPolygon.geom, 5))
                           .where(OfficialLayerPolygon.layer == name)).all()
    if not rows:
        raise HTTPException(404, "Capa oficial no disponible (no ingerida)")
    return {"type": "FeatureCollection", "source_id": OFFICIAL_LAYERS[name]["source_id"],
            "features": [{"type": "Feature", "geometry": json.loads(g),
                          "properties": {"class_code": c, "class_label": lbl}} for c, lbl, g in rows]}


@router.get("/v1/weather/context", tags=["meteorología"])
def weather(municipality_code: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    from ..services import weather_context

    _get_muni(session, municipality_code)
    return weather_context(session, municipality_code)


@router.get("/v1/fire-history", tags=["histórico"])
def fire_history(session: Session = Depends(get_session)) -> dict[str, Any]:
    rows = session.scalars(select(RegionalSeries).where(RegionalSeries.source_id == "CAM-05")
                           .order_by(RegionalSeries.year)).all()
    by_year: dict[int, dict] = {}
    for r in rows:
        by_year.setdefault(r.year, {"year": r.year})[r.concept] = r.value
    return {"source_id": "CAM-05", "status": "official", "scope": "Comunidad de Madrid (agregado regional)",
            "caveat": "Serie regional: no hay desagregación municipal en este recurso.",
            "series": list(by_year.values())}


@router.get("/v1/regional-series/{source_id}", tags=["histórico"])
def regional_series(source_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    rows = session.scalars(select(RegionalSeries).where(RegionalSeries.source_id == source_id)
                           .order_by(RegionalSeries.concept, RegionalSeries.year)).all()
    if not rows:
        raise HTTPException(404, "Serie no disponible")
    return {"source_id": source_id, "scope": "Comunidad de Madrid (agregado regional)",
            "series": [{"concept": r.concept, "year": r.year, "value": r.value, "unit": r.unit} for r in rows]}


@router.get("/v1/protected-spaces", tags=["territorio"])
def protected_spaces(session: Session = Depends(get_session)) -> dict[str, Any]:
    rows = session.scalars(select(ProtectedSpace).order_by(ProtectedSpace.category, ProtectedSpace.name)).all()
    return {"source_id": "CAM-04", "status": "official", "caveat": "Listado sin geometría: no se cruza espacialmente.",
            "items": [{"category": r.category, "figure": r.figure, "name": r.name, "area_ha": r.area_ha,
                       "declared_on": r.declared_on, "norm_url": r.norm_url} for r in rows]}


def measure_dict(m: MeasureCatalog) -> dict[str, Any]:
    return {"code": m.code, "name": m.name, "description": m.description, "unit": m.unit,
            "reference_unit_cost_eur": float(m.reference_unit_cost_eur) if m.reference_unit_cost_eur is not None else None,
            "cost_status": m.cost_status, "cost_source": m.cost_source, "normative_refs": m.normative_refs,
            "prerequisites": m.prerequisites, "excludes": m.excludes,
            "requires_professional": m.requires_professional, "review_status": "pending_technical_review"}


@router.get("/v1/measures", tags=["medidas"])
def list_measures(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    return [measure_dict(m) for m in session.scalars(select(MeasureCatalog).order_by(MeasureCatalog.code))]


@router.get("/v1/exports/municipalities.csv", tags=["exportación"])
def export_municipalities_csv(session: Session = Depends(get_session)):
    """Export reproducible (M10/M20) de los indicadores municipales con fuente y periodo por columna."""
    import csv
    import io

    from fastapi.responses import Response

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ine_code", "name", "population_total", "population_year", "population_source", "age_65_plus_share",
                "density_hab_km2", "density_year", "density_source", "altitude_m", "altitude_source", "area_km2_derived",
                "area_source"])
    for m in session.scalars(select(Municipality).order_by(Municipality.ine_code)):
        w.writerow([m.ine_code, m.name, m.population_total, m.population_year, "CAM-01", m.age_65_plus_share,
                    m.density_hab_km2, m.density_year, "CAM-02", m.altitude_m, "CAM-03", m.area_km2, "CAM-08"])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="escudo-municipios.csv"'})


@router.get("/v1/analysis/municipal-matrix", tags=["análisis"])
def municipal_matrix(
    layer: str = Query("risk", pattern="^(risk|hazard|vulnerability)$"),
    min_high_share: float = Query(0, ge=0, le=1),
    max_density: float | None = Query(None, ge=0),
    min_age65_share: float = Query(0, ge=0, le=1),
    sort: str = Query("high_share", pattern="^(high_share|density|age65|population)$"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Matriz municipal reproducible: datos CAM (CAM-01/02) junto al reparto de la capa oficial elegida.

    `high_share` = suma LITERAL de la proporción de superficie municipal en las clases oficiales 4 y 5
    («alto» y «muy alto»). No es un índice propio ni una probabilidad: es un filtro sobre valores publicados.
    """
    from ..models import OfficialLayerMunicipalShare as S

    high = dict(session.execute(
        select(S.ine_code, func.sum(S.area_share)).where(S.layer == layer, S.class_code.in_(["4", "5"]))
        .group_by(S.ine_code)).all())
    has_layer = bool(session.scalar(select(func.count()).select_from(S).where(S.layer == layer)))
    rows = []
    for m in session.scalars(select(Municipality)):
        hs = high.get(m.ine_code, 0.0 if has_layer else None)
        if hs is not None and hs < min_high_share:
            continue
        if max_density is not None and (m.density_hab_km2 is None or m.density_hab_km2 > max_density):
            continue
        if min_age65_share and (m.age_65_plus_share is None or m.age_65_plus_share < min_age65_share):
            continue
        rows.append({"ine_code": m.ine_code, "name": m.name,
                     "high_share": round(hs, 4) if hs is not None else None,
                     "density_hab_km2": m.density_hab_km2, "density_year": m.density_year,
                     "age_65_plus_share": m.age_65_plus_share, "population_total": m.population_total,
                     "population_year": m.population_year})
    key = {"high_share": "high_share", "density": "density_hab_km2", "age65": "age_65_plus_share",
           "population": "population_total"}[sort]
    rows.sort(key=lambda r: (r[key] is None, -(r[key] or 0), r["ine_code"]))
    src = OFFICIAL_LAYERS[layer]["source_id"]
    return {
        "layer": layer, "layer_source_id": src, "status": "derived" if has_layer else "unavailable",
        "sources": ["CAM-01", "CAM-02", src],
        "definition": (f"high_share: proporción de superficie municipal en clases 4 y 5 de {src} (suma literal de "
                       "clases oficiales, calculada sobre el ráster de 5 m). Densidad y % ≥65 del Portal CAM."),
        "caveat": ("Filtro comparativo a escala municipal. No es un índice de riesgo propio ni prioriza "
                   "actuaciones: la priorización corresponde a personal técnico."),
        "filters": {"min_high_share": min_high_share, "max_density": max_density, "min_age65_share": min_age65_share},
        "count": len(rows), "rows": rows,
    }
