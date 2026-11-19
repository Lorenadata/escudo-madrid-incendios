"""Riesgo estimado hoy: cruza el mapa oficial de riesgo con el tiempo previsto por AEMET en las próximas 24 horas.

Estimación de ESCUDO, no un dato oficial ni una probabilidad de incendio. Es el producto de dos factores: así no hace
falta elegir pesos y, si uno de ellos es nulo, el resultado también lo es. Método: docs/current-risk.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

BANDS: tuple[tuple[int, str, str], ...] = (
    (80, "very_high", "Muy alto"),
    (60, "high", "Alto"),
    (40, "medium", "Moderado"),
    (20, "low", "Bajo"),
    (0, "very_low", "Muy bajo"),
)
SOURCES = ["GEO-01", "AEMET-PRED-HOR"]
DEFINITION = (
    "Producto de dos factores de 0 a 1, expresado de 0 a 100. Territorio: parte del término en las clases 4 y 5 del mapa oficial de "
    "riesgo. Meteorología: máximo de las próximas 24 horas del índice de Fosberg (1978) dividido entre 100, calculado "
    "con la temperatura, la humedad relativa y el viento medio previstos por AEMET para el municipio. Solo cuentan las "
    "horas anteriores a que la lluvia prevista acumulada llegue a 0,5 mm."
)
CAVEAT = (
    "Estimación de ESCUDO, no un dato oficial de AEMET ni de la Comunidad de Madrid. No es una probabilidad de incendio "
    "ni una alerta. No conoce el estado real de la vegetación ni la lluvia ya caída, el índice no está calibrado para "
    "Madrid, y el umbral de lluvia y los tramos de color son decisiones de ESCUDO."
)


def band_for(score: float | None) -> dict[str, str]:
    if score is None:
        return {"id": "unavailable", "label": "No disponible"}
    return next({"id": bid, "label": label} for floor, bid, label in BANDS if score >= floor)


def risk_score(high_share: float | None, ffwi: float | None) -> float | None:
    """Territorio (0–1) × índice de Fosberg (0–100). Sin alguno de los dos factores no hay estimación."""
    if high_share is None or ffwi is None:
        return None
    return round(max(0.0, min(1.0, high_share)) * max(0.0, min(100.0, ffwi)), 1)


def _n(v: float, digits: int = 0) -> str:
    return f"{v:.{digits}f}".replace(".", ",")


def _reasons(high: float | None, w: dict[str, Any]) -> list[str]:
    out: list[str] = []
    if high is not None:
        out.append(f"{_n(high * 100)} % del término en riesgo alto o muy alto en el mapa oficial")
    if w.get("ffwi_max_24h") is not None and w.get("ffwi_max_at"):
        at = datetime.fromisoformat(w["ffwi_max_at"]).strftime("%d/%m a las %H:%M")
        out.append(f"Índice de Fosberg de {_n(w['ffwi_max_24h'], 1)} sobre 100, máximo previsto el {at}: "
                   f"{_n(w['ffwi_temp_c'])} °C, humedad del {_n(w['ffwi_rh_pct'])} % y viento de {_n(w['ffwi_wind_kmh'])} km/h")
    if w.get("ffwi_rain_from"):
        at = datetime.fromisoformat(w["ffwi_rain_from"]).strftime("%d/%m a las %H:%M")
        out.append(f"Lluvia prevista desde el {at} ({_n(w.get('precip_24h_mm') or 0, 1)} mm en 24 horas): "
                   "esa hora y las siguientes no cuentan")
    return out


def compute_current_risk(inputs: list[dict[str, Any]], weather_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filas ordenadas de mayor a menor. Solo se usa predicción vigente (`status: ok`), nunca una caducada."""
    weather = {r["ine_code"]: r for r in weather_rows if r.get("status") == "ok"}
    rows = []
    for m in inputs:
        high, w = m.get("high_share"), weather.get(m["ine_code"], {})
        fire = w.get("ffwi_max_24h")
        score = risk_score(high, fire)
        rows.append({
            "ine_code": m["ine_code"], "name": m["name"], "high_share": high, "ffwi_max_24h": fire,
            "ffwi_max_at": w.get("ffwi_max_at"), "rain_from": w.get("ffwi_rain_from"), "temp_c": w.get("ffwi_temp_c"), "rh_pct": w.get("ffwi_rh_pct"),
            "wind_kmh": w.get("ffwi_wind_kmh"), "precip_24h_mm": w.get("precip_24h_mm"),
            "gust_max_24h_kmh": w.get("gust_max_24h_kmh"), "ffwi_hourly": w.get("ffwi_hourly", []),
            "score": score, "band": band_for(score),
            "limiting": None if score is None else ("territory" if high < fire / 100 else "weather"),
            "reasons": _reasons(high, w),
        })
    rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0), r["ine_code"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i if r["score"] is not None else None
    return rows
