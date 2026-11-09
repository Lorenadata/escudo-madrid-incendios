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


FIRE_CAUSE_LABELS = {
    "rayo": "Rayo",
    "negligencia_accidente": "Negligencias y causas accidentales",
    "intencionado": "Intencionado",
    "desconocida": "Causa desconocida",
    "reproducido": "Incendio reproducido",
}
PLAN_URL = "https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf"


def fire_plan_for(session: Session, ine_code: str) -> dict[str, Any]:
    """DOC-01: declaración ZAR (Anexo II, pág. 59) y siniestros 2015–2024 por causa (Anexo I, págs. 54–58)."""
    from .models import MunicipalSeries

    ids = ["municipality_zar_declared", "municipality_fires_total_2015_2024"] + [
        f"municipality_fires_{c}_2015_2024" for c in FIRE_CAUSE_LABELS]
    rows = {r.indicator_id: r.value for r in session.scalars(
        select(MunicipalSeries).where(MunicipalSeries.ine_code == ine_code, MunicipalSeries.indicator_id.in_(ids)))}
    zar_v = rows.get("municipality_zar_declared")
    zar = indicator("municipality_zar_declared", None if zar_v is None else ("Sí" if zar_v == 1 else "No"), 2026)
    total_v = rows.get("municipality_fires_total_2015_2024")
    total = indicator("municipality_fires_total_2015_2024", None if total_v is None else int(total_v), "2015–2024")
    causes = []
    for key, label in FIRE_CAUSE_LABELS.items():
        v = rows.get(f"municipality_fires_{key}_2015_2024")
        causes.append(indicator("municipality_fires_cause_2015_2024", None if v is None else int(v), "2015–2024",
                                label=label))
    cause_values = [c["value"] for c in causes]
    matches = (None if total["value"] is None or None in cause_values else sum(cause_values) == total["value"])
    return {
        "source_id": "DOC-01", "document_url": PLAN_URL,
        "pages": {"zar": 59, "fires": "54–58"},
        "zar": zar, "fires_total": total, "fires_by_cause": causes,
        "total_matches_causes": matches,
        "note": ("Valores literales del documento oficial. La suma de causas no coincide con el total en este "
                 "municipio; el documento no lo explica y no se corrige.") if matches is False else None,
    }


def satellite_burnt_for(session: Session, ine_code: str) -> dict[str, Any]:
    """EFF-01: perímetros EFFIS que tocan el municipio, con superficie dentro del término (derivada) y literal EFFIS."""
    from .models import SatelliteBurntArea as A
    from .models import SatelliteBurntAreaMunicipality as M

    total_layer = session.scalar(select(func.count()).select_from(A)) or 0
    rows = session.execute(select(A, M.area_ha).join(M, M.effis_id == A.effis_id)
                           .where(M.ine_code == ine_code).order_by(A.fire_date.desc())).all()
    events = [{"effis_id": a.effis_id, "fire_date": a.fire_date.isoformat() if a.fire_date else None,
               "year": a.year, "area_ha_in_municipality": round(ha, 1), "area_ha_effis_perimeter": a.area_ha_effis,
               "commune_literal": a.commune_literal, "province_literal": a.province_literal,
               "status": "derived"} for a, ha in rows]
    years = sorted({a.year for (a,) in session.execute(select(A))})
    return {
        "source_id": "EFF-01", "status": "derived" if total_layer else "unavailable",
        "period": f"{years[0]}–{years[-1]}" if years else None,
        "events": events, "total_ha_in_municipality": round(sum(e["area_ha_in_municipality"] for e in events), 1),
        "method": ("Intersección de cada perímetro EFFIS con el límite municipal (CAM-08) en EPSG:25830. La superficie "
                   "del perímetro completo y el municipio asignado por EFFIS se muestran literales."),
        "caveat": ("Estimación por satélite (MODIS, 250 m): áreas de unas 30 ha o más; no distingue incendios "
                   "forestales de quemas agrícolas o prescritas; fechas aproximadas. Sin perímetros no significa "
                   "que no haya habido incendios. Fuente: EFFIS (Copernicus EMS, JRC), CC BY 4.0."),
    }


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
    prof["fire_plan"] = fire_plan_for(session, m.ine_code)
    prof["satellite_burnt"] = satellite_burnt_for(session, m.ine_code)
    prof["official_fire"] = official_layers_for(session, m.ine_code)
    prof["weather"] = weather_context(session, m.ine_code) if with_weather else None
    prof["sources"] = ["CAM-01", "CAM-02", "CAM-03", "CAM-08", "CAM-09", "CAM-10", "CAM-11", "DOC-01", "EFF-01", "GEO-01", "GEO-02", "GEO-03", "AEMET"]
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
