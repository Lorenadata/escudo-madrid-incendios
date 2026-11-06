"""Proveedores AEMET y caché con TTL por producto.

Proveedores:
  - `XmlPublicProvider`: https://www.aemet.es/xml/municipios/localidad_<INE>.xml (sin clave).
  - `OpenDataProvider`: https://opendata.aemet.es/opendata (cabecera `api_key`, patrón de dos pasos:
    la primera llamada devuelve `{"estado","datos","metadatos"}` y `datos` es la URL del contenido).

Solo se usa OpenData si existe `AEMET_API_KEY`; sin clave nunca se le hace ninguna petición.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from .parsers import AemetParseError, ParsedForecast, parse_localidad_xml, parse_opendata_daily

XML_URL = "https://www.aemet.es/xml/municipios/localidad_{ine}.xml"
OPENDATA_BASE = "https://opendata.aemet.es/opendata"
OD_DAILY = OPENDATA_BASE + "/api/prediccion/especifica/municipio/diaria/{ine}"
OD_FIRE_ESTIMATED = OPENDATA_BASE + "/api/incendios/mapasriesgo/estimado/area/{area}"
USER_AGENT = "escudo-madrid-etl/0.1 (DATAMAD 2026)"

# TTL de caché de red por tipo de producto (segundos). La vigencia de la predicción se
# evalúa aparte (ver context.py); la caché solo evita repetir peticiones.
TTL_SECONDS = {
    "forecast_municipal": 3 * 3600,  # AEMET reelabora la predicción municipal varias veces al día
    "fire_danger_map": 6 * 3600,  # mapa diario de niveles de riesgo meteorológico
}


class AemetUnavailable(RuntimeError):
    """No se ha podido obtener un producto válido (red, HTTP, cuota, parseo)."""


@dataclass
class CacheEntry:
    fetched_at: float
    payload: bytes


class TTLCache:
    """Caché en memoria con persistencia opcional en disco (`ESCUDO_AEMET_CACHE_DIR`)."""

    def __init__(self, disk_dir: str | Path | None = None) -> None:
        self._mem: dict[str, CacheEntry] = {}
        self._dir = Path(disk_dir) if disk_dir else None
        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path | None:
        return self._dir / (key.replace("/", "_").replace(":", "_") + ".bin") if self._dir else None

    def get(self, key: str, ttl: float, now: float) -> bytes | None:
        e = self._mem.get(key)
        if e is None and (p := self._path(key)) and p.exists():
            e = CacheEntry(p.stat().st_mtime, p.read_bytes())
            self._mem[key] = e
        if e and now - e.fetched_at <= ttl:
            return e.payload
        return None

    def put(self, key: str, payload: bytes, now: float) -> None:
        self._mem[key] = CacheEntry(now, payload)
        if p := self._path(key):
            p.write_bytes(payload)
            os.utime(p, (now, now))

    def clear(self) -> None:
        self._mem.clear()


_default_cache = TTLCache(os.environ.get("ESCUDO_AEMET_CACHE_DIR"))


def default_cache() -> TTLCache:
    return _default_cache


def _client(client: httpx.Client | None) -> tuple[httpx.Client, bool]:
    if client is not None:
        return client, False
    return httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}), True


class XmlPublicProvider:
    name = "aemet_xml_public"

    def fetch_forecast(self, ine: str, client: httpx.Client | None, cache: TTLCache, now: float) -> ParsedForecast:
        key = f"xml:{ine}"
        raw = cache.get(key, TTL_SECONDS["forecast_municipal"], now)
        if raw is None:
            c, owned = _client(client)
            try:
                r = c.get(XML_URL.format(ine=ine))
                r.raise_for_status()
                raw = r.content
            except httpx.HTTPError as exc:
                raise AemetUnavailable(f"XML AEMET: {exc}") from exc
            finally:
                if owned:
                    c.close()
            try:
                parsed = parse_localidad_xml(raw, ine)
            except AemetParseError as exc:
                raise AemetUnavailable(str(exc)) from exc
            cache.put(key, raw, now)
            return parsed
        return parse_localidad_xml(raw, ine)

    @staticmethod
    def source_url(ine: str) -> str:
        return XML_URL.format(ine=ine)


class OpenDataProvider:
    name = "aemet_opendata"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("OpenDataProvider requiere AEMET_API_KEY")
        self._key = api_key

    def _two_step(self, url: str, c: httpx.Client) -> tuple[bytes, dict]:
        r = c.get(url, headers={"api_key": self._key, "Accept": "application/json"})
        if r.status_code in (401, 403, 429) or not r.content:
            raise AemetUnavailable(f"OpenData HTTP {r.status_code} (clave, cuota o servicio)")
        r.raise_for_status()
        meta = r.json()
        if int(meta.get("estado", 0)) != 200 or not meta.get("datos"):
            raise AemetUnavailable(f"OpenData estado={meta.get('estado')} {meta.get('descripcion')}")
        d = c.get(meta["datos"])
        d.raise_for_status()
        return d.content, meta

    def fetch_forecast(self, ine: str, client: httpx.Client | None, cache: TTLCache, now: float) -> ParsedForecast:
        key = f"od:{ine}"
        raw = cache.get(key, TTL_SECONDS["forecast_municipal"], now)
        fetched = raw is None
        if raw is None:
            c, owned = _client(client)
            try:
                raw, _ = self._two_step(OD_DAILY.format(ine=ine), c)
            except (httpx.HTTPError, ValueError) as exc:
                raise AemetUnavailable(f"OpenData: {exc}") from exc
            finally:
                if owned:
                    c.close()
        try:
            parsed = parse_opendata_daily(json.loads(raw.decode("latin-1")), ine)
        except (AemetParseError, ValueError) as exc:
            raise AemetUnavailable(str(exc)) from exc
        if fetched:
            cache.put(key, raw, now)
        return parsed

    def fetch_fire_map_url(self, client: httpx.Client | None, cache: TTLCache, now: float, area: str = "p") -> str:
        """Devuelve la URL `datos` del último mapa de riesgo estimado (imagen peninsular)."""
        key = f"odfire:{area}"
        raw = cache.get(key, TTL_SECONDS["fire_danger_map"], now)
        if raw is None:
            c, owned = _client(client)
            try:
                r = c.get(OD_FIRE_ESTIMATED.format(area=area), headers={"api_key": self._key})
                if r.status_code in (401, 403, 429) or not r.content:
                    raise AemetUnavailable(f"OpenData HTTP {r.status_code}")
                meta = r.json()
                if int(meta.get("estado", 0)) != 200 or not meta.get("datos"):
                    raise AemetUnavailable(f"OpenData estado={meta.get('estado')}")
                raw = meta["datos"].encode()
            except (httpx.HTTPError, ValueError) as exc:
                raise AemetUnavailable(f"OpenData mapa incendios: {exc}") from exc
            finally:
                if owned:
                    c.close()
            cache.put(key, raw, now)
        return raw.decode()

    @staticmethod
    def source_url(ine: str) -> str:
        return OD_DAILY.format(ine=ine)


def now_epoch() -> float:
    return time.time()
