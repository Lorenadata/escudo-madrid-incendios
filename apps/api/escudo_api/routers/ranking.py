"""Ranking municipal de atención preventiva y predicción horaria de AEMET."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..attention import BANDS, TOP_N, WEIGHTS, compute_ranking, gap_summary
from ..current_risk import BANDS as RISK_BANDS
from ..current_risk import CAVEAT, DEFINITION, SOURCES, compute_current_risk
from ..db import get_session
from ..models import (
    Municipality,
    MunicipalSeries,
    OfficialLayerMunicipalShare,
    SatelliteBurntAreaMunicipality,
)
from ..weather_regional import regional_weather

router = APIRouter()

_SERIES = {
    "municipality_zar_declared": "zar",
    "municipality_fires_total_2015_2024": "fires_total",
    "municipality_pamif_required": "plan_required",
    "municipality_pamif_approved": "plan_approved",
    "municipality_non_main_share": "non_main_share",
    "municipality_single_dwelling_building_share": "single_dwelling_building_share",
}
_BOOLEAN = {"zar", "plan_required", "plan_approved"}


def _inputs(session: Session) -> list[dict[str, Any]]:
    S = OfficialLayerMunicipalShare
    classes: dict[str, list[dict[str, Any]]] = {}
    for s in session.scalars(select(S).where(S.layer == "risk")):
        classes.setdefault(s.ine_code, []).append({"code": s.class_code, "label": s.class_label, "share": round(s.area_share, 4)})
    burnt = dict(session.execute(select(SatelliteBurntAreaMunicipality.ine_code, func.sum(SatelliteBurntAreaMunicipality.area_ha))
                                 .group_by(SatelliteBurntAreaMunicipality.ine_code)).all())
    series: dict[str, dict[str, Any]] = {}
    for r in session.scalars(select(MunicipalSeries).where(MunicipalSeries.indicator_id.in_(_SERIES))):
        key = _SERIES[r.indicator_id]
        series.setdefault(r.ine_code, {})[key] = (None if r.value is None else r.value == 1) if key in _BOOLEAN else r.value
    has_risk = bool(classes)
    out = []
    for m in session.scalars(select(Municipality)):
        cl = sorted(classes.get(m.ine_code, []), key=lambda c: str(c["code"]))
        high = sum(c["share"] for c in cl if c["code"] in ("4", "5")) if has_risk else None
        out.append({
            "ine_code": m.ine_code, "name": m.name, "area_km2": m.area_km2, "population_total": m.population_total,
            "age_65_plus_share": m.age_65_plus_share, "high_share": None if high is None else round(high, 4),
            "risk_classes": cl, "burnt_ha": round(float(burnt.get(m.ine_code, 0)), 1),
            **{k: series.get(m.ine_code, {}).get(k) for k in _SERIES.values()},
        })
    return out


@router.get("/v1/analysis/attention-ranking", tags=["análisis"])
def attention_ranking(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Puntuación de atención preventiva de los 179 municipios, con componentes, motivos y estabilidad."""
    rows = compute_ranking(_inputs(session))
    available = any(r["score"] is not None for r in rows)
    return {
        "indicator_id": "municipality_attention_score",
        "status": "derived" if available else "unavailable",
        "weights": WEIGHTS,
        "bands": [{"min": lo, "id": bid, "label": label} for lo, bid, label in BANDS],
        "top_n": TOP_N,
        "sources": ["GEO-01", "DOC-01", "EFF-01", "CAM-01", "CAM-09", "CAM-10"],
        "definition": ("Media ponderada de cuatro bloques en escala 0–1. Territorio: parte del término en clases 4 y 5 de "
                       "GEO-01. Historial: posición entre municipios en siniestros y en superficie quemada por km². "
                       "Contexto residencial: posición en % de 65 años o más, viviendas no principales y edificio "
                       "unifamiliar. Planificación: territorio en esas clases si no consta plan municipal aprobado."),
        "caveat": ("Orden de revisión con pesos elegidos por ESCUDO y modificables. No es riesgo de incendio ni una "
                   "probabilidad, no incluye meteorología y no sustituye al mapa oficial ni a personal técnico."),
        "gap": gap_summary(rows),
        "count": len(rows),
        "rows": rows,
    }


@router.get("/v1/analysis/current-risk", tags=["análisis"])
def current_risk(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Riesgo estimado hoy por municipio: mapa oficial × índice de Fosberg con la predicción de AEMET."""
    inputs = _inputs(session)
    regional_weather.ensure([(r["ine_code"], r["name"]) for r in inputs])
    snap = regional_weather.snapshot()
    rows = compute_current_risk(inputs, snap["rows"])
    scored = [r for r in rows if r["score"] is not None]
    return {
        "indicator_id": "municipality_current_risk_estimate",
        "status": "derived" if scored else ("warming" if snap["status"] == "warming" else "unavailable"),
        "refreshing": snap["refreshing"], "coverage": len(scored), "received": snap["received"], "total": snap["total"],
        "issued_at_latest": snap["issued_at_latest"], "hours": snap["hours"],
        "bands": [{"min": lo, "id": bid, "label": label} for lo, bid, label in RISK_BANDS],
        "sources": SOURCES, "definition": DEFINITION, "caveat": CAVEAT, "attribution": snap["attribution"],
        "reference": "Fosberg, M. A. (1978). Weather in wildland fire management: the fire weather index.",
        "rows": rows,
    }


@router.get("/v1/weather/hourly", tags=["meteorología"])
def weather_hourly(municipality_code: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Predicción horaria y diaria de AEMET para un municipio. Si AEMET falla, `status: unavailable`."""
    from escudo_pipelines.aemet import get_hourly_forecast

    m = session.get(Municipality, municipality_code)
    if m is None:
        raise HTTPException(404, "Municipio no encontrado")
    return {**get_hourly_forecast(municipality_code), "municipality_name": m.name}


@router.get("/v1/weather/regional", tags=["meteorología"])
def weather_regional(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Rachas, lluvia, humedad y temperatura previstas en los 179 municipios (se completa en segundo plano)."""
    regional_weather.ensure(list(session.execute(select(Municipality.ine_code, Municipality.name)).tuples()))
    return regional_weather.snapshot()
