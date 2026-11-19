"""Resumen regional de la predicción horaria de AEMET para los 179 municipios.

Se descarga en segundo plano (6 peticiones simultáneas) y se conserva 3 horas: la primera visita nunca espera a
AEMET y recibe el avance. Los municipios que fallan quedan `unavailable`; jamás se rellenan con otro dato.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any

log = logging.getLogger("escudo.weather")
REFRESH_SECONDS = 3 * 3600
RETRY_SECONDS = 120  # los municipios que fallaron se reintentan antes que el refresco completo
WORKERS = 6
HORIZON_HOURS = 48


def _default_fetch(ine: str) -> dict[str, Any]:
    from escudo_pipelines.aemet import get_hourly_forecast

    return get_hourly_forecast(ine, with_daily=False)


def row_from_forecast(code: str, name: str, fc: dict[str, Any]) -> dict[str, Any]:
    s = fc.get("summary") or {}
    return {
        "ine_code": code, "name": name, "status": fc.get("status", "unavailable"), "issued_at": fc.get("issued_at"),
        "gust_max_24h_kmh": s.get("gust_max_24h_kmh"), "gust_max_at": s.get("gust_max_at"),
        "wind_dir_at_gust_max": s.get("wind_dir_at_gust_max"), "precip_24h_mm": s.get("precip_24h_mm"),
        "precip_total_mm": s.get("precip_total_mm"), "rh_min_24h_pct": s.get("rh_min_24h_pct"),
        "temp_max_24h_c": s.get("temp_max_24h_c"),
        "ffwi_max_24h": s.get("ffwi_max_24h"), "ffwi_max_at": s.get("ffwi_max_at"),
        "ffwi_rain_from": s.get("ffwi_rain_from"), "ffwi_temp_c": s.get("ffwi_temp_c"),
        "ffwi_rh_pct": s.get("ffwi_rh_pct"), "ffwi_wind_kmh": s.get("ffwi_wind_kmh"),
        "_gust": {p["t"]: p.get("gust_kmh") for p in fc.get("points", [])},
        "_ffwi": {p["t"]: p.get("ffwi") for p in fc.get("points", [])},
    }


class RegionalWeather:
    def __init__(self, fetch: Callable[[str], dict[str, Any]] | None = None) -> None:
        self._fetch = fetch or _default_fetch
        self._lock = threading.Lock()
        self._rows: dict[str, dict[str, Any]] = {}
        self._total = 0
        self._running = False
        self._finished_at: float | None = None

    def _run(self, municipalities: list[tuple[str, str]]) -> None:
        def one(item: tuple[str, str]) -> None:
            code, name = item
            try:
                row = row_from_forecast(code, name, self._fetch(code))
            except Exception as exc:  # un municipio no debe parar a los demás
                log.warning("AEMET horario falló para %s: %s", code, type(exc).__name__)
                row = row_from_forecast(code, name, {"status": "unavailable"})
            with self._lock:
                self._rows[code] = row

        try:
            with ThreadPoolExecutor(max_workers=WORKERS, thread_name_prefix="aemet") as pool:
                list(pool.map(one, municipalities))
        finally:
            with self._lock:
                self._running = False
                self._finished_at = time.time()

    def ensure(self, municipalities: list[tuple[str, str]]) -> None:
        with self._lock:
            if self._running or not municipalities:
                return
            age = None if self._finished_at is None else time.time() - self._finished_at
            pending = municipalities
            if age is not None and age < REFRESH_SECONDS:
                failed = {c for c, r in self._rows.items() if r["status"] == "unavailable"}
                pending = [m for m in municipalities if m[0] in failed]  # solo se reintenta lo que falló
                if not pending or age < RETRY_SECONDS:
                    return
            self._running = True
            self._total = len(municipalities)
        self._start(pending)

    def _start(self, municipalities: list[tuple[str, str]]) -> None:
        threading.Thread(target=self._run, args=(municipalities,), daemon=True, name="aemet-regional").start()

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        from escudo_pipelines.aemet.context import ATTRIBUTION, DISCLAIMER
        from escudo_pipelines.aemet.parsers import MADRID_TZ

        now = (now or datetime.now(UTC)).astimezone(MADRID_TZ).replace(minute=0, second=0, microsecond=0)
        hours = [(now + timedelta(hours=i)).isoformat() for i in range(HORIZON_HOURS)]
        with self._lock:
            raw = list(self._rows.values())
            running, total, finished = self._running, self._total, self._finished_at
        rows = []
        for r in raw:
            pub = {k: v for k, v in r.items() if k not in ("_gust", "_ffwi")}
            pub["gust_hourly_kmh"] = [r["_gust"].get(h) for h in hours]
            pub["ffwi_hourly"] = [r["_ffwi"].get(h) for h in hours]
            rows.append(pub)
        ok = [r for r in rows if r["status"] == "ok"]
        rows.sort(key=lambda r: (r["gust_max_24h_kmh"] is None, -(r["gust_max_24h_kmh"] or 0), r["ine_code"]))
        issued = max((r["issued_at"] for r in ok if r["issued_at"]), default=None)
        status = "warming" if running and not ok else "ok" if ok else "unavailable" if finished else "warming"
        return {
            "status": status, "refreshing": running, "coverage": len(ok), "received": len(rows), "total": total,
            "source_id": "AEMET-PRED-HOR", "issued_at_latest": issued, "hours": hours, "rows": rows,
            "disclaimer": DISCLAIMER, "attribution": ATTRIBUTION,
            "method": ("Máximos y sumas calculados por ESCUDO sobre los valores horarios publicados por AEMET para cada "
                       "término municipal. No se interpola ni se combina con ningún otro dato."),
        }


regional_weather = RegionalWeather()
