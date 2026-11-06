"""`get_weather_context`: contexto meteorológico diario según el contrato `WeatherContext`.

Política de caducidad (PRD §4.3, prueba T05):
  - Sin dato obtenible ahora (red, HTTP, cuota, parseo) → `status="unavailable"`, `variables=[]`,
    `last_valid_at` = fecha de elaboración del último dato válido conocido (o null).
  - Dato obtenido pero elaborado hace más de `MAX_FORECAST_AGE` o que no cubre el día actual
    → `status="stale"`; cada variable lleva `status="stale"` y su fecha real. Nunca se presenta como actual.
  - En otro caso → `status="ok"`.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any

import httpx

from .client import AemetUnavailable, OpenDataProvider, TTLCache, XmlPublicProvider, default_cache
from .parsers import MADRID_TZ, DayForecast, ParsedForecast

SOURCE_ID = "AEMET-PRED-MUN"
MAX_FORECAST_AGE = timedelta(hours=24)
DISCLAIMER = "Índice de peligro meteorológico; no es pronóstico de ignición ni alerta operativa."
ATTRIBUTION = (
    "Fuente: AEMET. Información elaborada utilizando, entre otras, la obtenida de la "
    "Agencia Estatal de Meteorología. AEMET no participa ni patrocina este uso."
)
SCALE_CAVEAT = "Predicción AEMET para el término municipal; no es un valor medido en una urbanización concreta."

_last_valid: dict[str, str] = {}


def _last_valid_path() -> Path | None:
    d = os.environ.get("ESCUDO_AEMET_CACHE_DIR")
    return Path(d) / "last_valid.json" if d else None


def _remember_valid(ine: str, issued_at: datetime) -> None:
    _last_valid[ine] = issued_at.isoformat()
    if p := _last_valid_path():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_last_valid), encoding="utf-8")


def _recall_valid(ine: str) -> str | None:
    if ine not in _last_valid and (p := _last_valid_path()) and p.exists():
        _last_valid.update(json.loads(p.read_text(encoding="utf-8")))
    return _last_valid.get(ine)


def reset_state() -> None:
    """Solo para tests: vacía caché y registro de últimos datos válidos en memoria."""
    _last_valid.clear()
    default_cache().clear()


def _indicator(
    indicator_id: str,
    label: str,
    value: Any,
    unit: str,
    day: str,
    status: str,
    method: str,
    caveat: str = SCALE_CAVEAT,
) -> dict:
    return {
        "indicator_id": indicator_id,
        "label": label,
        "value": value,
        "unit": unit,
        "spatial_scope": "municipio (predicción AEMET)",
        "temporal_scope": day,
        "status": status if value is not None else "unavailable",
        "source_id": SOURCE_ID,
        "method": method,
        "caveat": caveat,
    }


def _variables(d: DayForecast, base_status: str) -> list[dict]:
    day = d.day.isoformat()
    pub = "Valor publicado por AEMET sin transformación."
    der = "Máximo de los valores publicados por AEMET para los periodos del día."
    derived = "stale" if base_status == "stale" else "derived"
    return [
        _indicator("weather_temp_max_c", "Temperatura máxima prevista", d.temp_max_c, "°C", day, base_status, pub),
        _indicator("weather_temp_min_c", "Temperatura mínima prevista", d.temp_min_c, "°C", day, base_status, pub),
        _indicator("weather_rh_min_pct", "Humedad relativa mínima prevista", d.rh_min_pct, "%", day, base_status, pub),
        _indicator("weather_rh_max_pct", "Humedad relativa máxima prevista", d.rh_max_pct, "%", day, base_status, pub),
        _indicator(
            "weather_precip_prob_24h_pct", "Probabilidad de precipitación (00-24 h)", d.precip_prob_24h_pct, "%", day, base_status, pub
        ),
        _indicator(
            "weather_precip_prob_max_pct", "Probabilidad máxima de precipitación (periodos)", d.precip_prob_periods_max_pct, "%", day, derived, der
        ),
        _indicator("weather_wind_max_kmh", "Viento medio máximo previsto", d.wind_max_kmh, "km/h", day, derived, der),
        _indicator(
            "weather_wind_dir_at_max", "Dirección del viento en el periodo de viento máximo", d.wind_dir_at_max, "rumbo", day, derived, der
        ),
        _indicator("weather_gust_max_kmh", "Racha máxima prevista", d.gust_max_kmh, "km/h", day, derived, der),
    ]


def _select_day(fc: ParsedForecast, today) -> tuple[DayForecast | None, bool]:
    d = fc.day_for(today)
    if d:
        return d, True
    past = [x for x in fc.days if x.day <= today]
    return (max(past, key=lambda x: x.day) if past else None), False


def get_weather_context(
    ine_code: str,
    *,
    now: datetime | None = None,
    client: httpx.Client | None = None,
    api_key: str | None = None,
    cache: TTLCache | None = None,
) -> dict:
    """Contexto meteorológico para un municipio (código INE de 5 dígitos, p. ej. "28079")."""
    if not (len(ine_code) == 5 and ine_code.isdigit()):
        raise ValueError("ine_code debe tener 5 dígitos")
    now = (now or datetime.now(UTC)).astimezone(MADRID_TZ)
    cache = cache or default_cache()
    epoch = now.timestamp()
    key = api_key if api_key is not None else os.environ.get("AEMET_API_KEY", "")

    providers: list = []
    if key:
        providers.append(OpenDataProvider(key))
    providers.append(XmlPublicProvider())

    forecast: ParsedForecast | None = None
    used = None
    errors: list[str] = []
    for p in providers:
        try:
            forecast = p.fetch_forecast(ine_code, client, cache, epoch)
            used = p
            break
        except AemetUnavailable as exc:
            errors.append(f"{p.name}: {exc}")

    base: dict[str, Any] = {
        "source_id": SOURCE_ID,
        "disclaimer": DISCLAIMER,
        "attribution": ATTRIBUTION,
        "fire_danger": None,
    }

    if forecast is None:
        return {
            **base,
            "status": "unavailable",
            "provider": None,
            "source_url": XmlPublicProvider.source_url(ine_code),
            "issued_at": None,
            "valid_from": None,
            "valid_to": None,
            "reference_location": {"ine_code": ine_code, "name": None, "type": "municipio"},
            "variables": [],
            "last_valid_at": _recall_valid(ine_code),
            "message": "Datos meteorológicos no disponibles",
            "errors": errors,
        }

    day, covers_today = _select_day(forecast, now.date())
    too_old = now - forecast.issued_at > MAX_FORECAST_AGE
    status = "ok" if (covers_today and not too_old and day is not None) else "stale"
    if status == "ok":
        _remember_valid(ine_code, forecast.issued_at)

    valid_from = valid_to = None
    if day is not None:
        valid_from = datetime.combine(day.day, time.min, MADRID_TZ).isoformat()
        valid_to = datetime.combine(day.day + timedelta(days=1), time.min, MADRID_TZ).isoformat()

    fire = None
    if isinstance(used, OpenDataProvider):
        fire = _fire_indicator(used, client, cache, epoch, now)

    return {
        **base,
        "fire_danger": fire,
        "status": status,
        "provider": used.name,
        "source_url": used.source_url(ine_code),
        "issued_at": forecast.issued_at.isoformat(),
        "valid_from": valid_from,
        "valid_to": valid_to,
        "reference_location": {
            "ine_code": ine_code,
            "name": forecast.name,
            "type": "municipio (predicción AEMET para el término municipal)",
            "aemet_url": forecast.product_url,
        },
        "variables": _variables(day, "official" if status == "ok" else "stale") if day else [],
        "last_valid_at": forecast.issued_at.isoformat() if status == "ok" else _recall_valid(ine_code),
        "message": None if status == "ok" else "Predicción desactualizada: no representa el día actual",
        "errors": errors,
    }


def _fire_indicator(p: OpenDataProvider, client, cache, epoch: float, now: datetime) -> dict:
    caveat = (
        "Mapa ráster oficial de AEMET para Península y Baleares. No se extrae un valor por municipio "
        "ni por urbanización. Índice de peligro, no pronóstico de ignición."
    )
    try:
        url = p.fetch_fire_map_url(client, cache, epoch)
        value, status = url, "official"
    except AemetUnavailable:
        value, status = None, "unavailable"
    return {
        "indicator_id": "aemet_fire_danger_map_estimated",
        "label": "Mapa de niveles de riesgo meteorológico de incendios (estimado)",
        "value": value,
        "unit": "URL de imagen (mapa)",
        "spatial_scope": "Península y Baleares (mapa)",
        "temporal_scope": now.date().isoformat(),
        "status": status,
        "source_id": "AEMET-INC-MAPA",
        "method": "Último mapa publicado por AEMET (api/incendios/mapasriesgo/estimado/area/p).",
        "caveat": caveat,
    }
