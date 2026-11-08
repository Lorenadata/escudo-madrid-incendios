"""Lógica de dominio compartida por routers, demo e informes."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .indicators import indicator
from .models import (
    AuditEvent,
    DataSource,
    Municipality,
    OfficialLayerMunicipalShare,
    WeatherSnapshot,
)

log = logging.getLogger("escudo.services")

OFFICIAL_LAYERS = {
    "risk": {"source_id": "GEO-01", "label": "Riesgo por incendios forestales (oficial)"},
    "hazard": {"source_id": "GEO-02", "label": "Peligrosidad por incendios forestales (oficial)"},
    "vulnerability": {"source_id": "GEO-03", "label": "Vulnerabilidad por incendios forestales (oficial)"},
}

SCALE_NOTICE = (
    "Los indicadores demográficos y territoriales son de escala MUNICIPAL (Portal de Datos Abiertos CAM). "
    "No describen urbanizaciones, parcelas ni viviendas concretas."
)

WEATHER_DISCLAIMER = "Predicción meteorológica oficial de AEMET, solo informativa: no es un índice de peligro de incendio, ni pronóstico de ignición, ni alerta operativa."


def municipality_summary(m: Municipality) -> dict[str, Any]:
    return {
        "ine_code": m.ine_code,
        "name": m.name,
        "population": indicator("municipality_population_total", m.population_total, m.population_year),
        "density": indicator("municipality_density", m.density_hab_km2, m.density_year),
        "altitude_m": indicator("municipality_altitude", m.altitude_m, m.altitude_year),
        "age_65_plus_share": indicator("municipality_age_65_plus_share", m.age_65_plus_share, m.population_year),
    }


def official_layers_for(session: Session, ine_code: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for layer, meta in OFFICIAL_LAYERS.items():
        rows = session.scalars(
            select(OfficialLayerMunicipalShare)
            .where(OfficialLayerMunicipalShare.ine_code == ine_code, OfficialLayerMunicipalShare.layer == layer)
            .order_by(OfficialLayerMunicipalShare.area_share.desc())
        ).all()
        src = session.get(DataSource, meta["source_id"])
        if not rows:
            out[layer] = {"source_id": meta["source_id"], "label": meta["label"], "status": "unavailable",
                          "classes": [], "dominant_class": None,
                          "version": None, "reason": "Capa oficial no ingerida o sin intersección con el municipio"}
            continue
        out[layer] = {
            "source_id": meta["source_id"],
            "label": meta["label"],
            "status": "official",
            "classes": [{"class_label": r.class_label, "class_code": r.class_code,
                         "area_share": round(r.area_share, 4), "area_ha": round(r.area_ha, 1)} for r in rows],
            "dominant_class": rows[0].class_label,
            "version": src.versions[-1].portal_modified_at if src and src.versions else None,
            "method": "Reparto de superficie municipal por clase oficial (intersección en EPSG:25830). Clases literales de la fuente.",
        }
    return out


def weather_context(session: Session, ine_code: str) -> dict[str, Any]:
    """Contexto AEMET vía conector A4. Ante cualquier fallo → unavailable, nunca dato inventado."""
    last_ok = session.scalar(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.ine_code == ine_code, WeatherSnapshot.status == "ok")
        .order_by(WeatherSnapshot.fetched_at.desc())
    )
    last_valid_at = last_ok.payload.get("issued_at") if last_ok else None
    try:
        from escudo_pipelines.aemet import get_weather_context  # type: ignore[attr-defined]
    except ImportError:
        return _weather_unavailable(ine_code, "Conector AEMET no instalado", last_valid_at)
    try:
        ctx = get_weather_context(ine_code)
    except Exception as exc:  # el conector no debe tumbar la ficha
        log.warning("AEMET falló para %s: %s", ine_code, exc)
        return _weather_unavailable(ine_code, f"Error del conector: {type(exc).__name__}", last_valid_at)
    if ctx.get("status") == "ok":
        session.add(WeatherSnapshot(ine_code=ine_code, status="ok", payload=json.loads(json.dumps(ctx, default=str))))
        session.commit()
    elif not ctx.get("last_valid_at"):
        ctx["last_valid_at"] = last_valid_at
    ctx.setdefault("disclaimer", WEATHER_DISCLAIMER)
    return ctx


def _weather_unavailable(ine_code: str, reason: str, last_valid_at: str | None) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "issued_at": None,
        "valid_from": None,
        "valid_to": None,
        "reference_location": {"ine_code": ine_code},
        "variables": [],
        "fire_danger": None,
        "disclaimer": WEATHER_DISCLAIMER,
        "last_valid_at": last_valid_at,
        "source_id": "AEMET",
    }


HOUSING_INDICATORS = (
    "municipality_dwellings_total", "municipality_non_main_dwellings", "municipality_non_main_share",
    "municipality_single_dwelling_building_share", "municipality_empty_electricity_share",
    "municipality_sporadic_electricity_share",
)


def housing_for(session: Session, ine_code: str) -> dict[str, Any]:
    """Exposición residencial municipal (CAM-09/10/11, Censo 2021): siempre los 6 indicadores, null → «no disponible»."""
    from .models import MunicipalSeries

    rows = {r.indicator_id: r for r in session.scalars(
        select(MunicipalSeries).where(MunicipalSeries.ine_code == ine_code,
                                      MunicipalSeries.indicator_id.in_(HOUSING_INDICATORS)))}
    items = [indicator(i, rows[i].value if i in rows else None, rows[i].year if i in rows else 2021)
             for i in HOUSING_INDICATORS]
    return {"census_year": 2021, "sources": ["CAM-09", "CAM-10", "CAM-11"], "indicators": items,
            "caveat": ("Escala municipal (Censo 2021): describe el parque de viviendas del municipio, no el de una "
                       "urbanización. Contexto de exposición residencial; no es un índice de riesgo.")}


def municipality_profile(session: Session, m: Municipality, *, with_weather: bool = True) -> dict[str, Any]:
    prof = municipality_summary(m)
    prof["area_km2"] = indicator("municipality_area_km2", m.area_km2, None)
    prof["forest_share"] = {
        "indicator_id": "municipality_forest_share",
        "label": "Superficie forestal del municipio",
        "value": None,
        "unit": "proporción",
        "spatial_scope": "municipio",
        "temporal_scope": None,
        "status": "unavailable",
        "source_id": "CAM-07",
        "method": "CAM-07 (Distribución de la superficie por usos) solo se publica como agregado REGIONAL.",
        "caveat": "No existe desagregación municipal verificada en el Portal CAM; no se estima.",
    }
    prof["housing"] = housing_for(session, m.ine_code)
    prof["official_fire"] = official_layers_for(session, m.ine_code)
    prof["weather"] = weather_context(session, m.ine_code) if with_weather else None
    prof["sources"] = ["CAM-01", "CAM-02", "CAM-03", "CAM-08", "CAM-09", "CAM-10", "CAM-11", "GEO-01", "GEO-02", "GEO-03", "AEMET"]
    prof["scale_notice"] = SCALE_NOTICE
    return prof


def audit(session: Session, *, org_id: str | None, user_id: str | None, action: str, entity: str,
          entity_id: str, detail: dict | None = None) -> None:
    session.add(AuditEvent(organization_id=org_id, user_id=user_id, action=action, entity=entity,
                           entity_id=str(entity_id), detail=detail or {}))


def sources_health(session: Session) -> tuple[int, int]:
    total = session.scalar(select(func.count()).select_from(DataSource)) or 0
    ok = session.scalar(select(func.count()).select_from(DataSource).where(DataSource.status == "ok")) or 0
    return ok, total


def utcnow() -> datetime:
    return datetime.now(UTC)
