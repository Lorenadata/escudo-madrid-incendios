"""Predicción municipal HORARIA de AEMET (XML público, sin clave): viento, rachas, precipitación, humedad y temperatura.

Cada valor es el publicado por AEMET para esa hora. Un valor vacío queda como `None`; «Ip» (precipitación
inapreciable) se conserva como `precip_trace=True` con 0 mm. Máximos y sumas de ventana son derivados y así se rotulan.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta

import httpx

from .client import USER_AGENT, AemetUnavailable, TTLCache, XmlPublicProvider, default_cache
from .context import ATTRIBUTION, DISCLAIMER, MAX_FORECAST_AGE, SCALE_CAVEAT
from .fire_weather import ffwi
from .parsers import MADRID_TZ, AemetParseError, _num, _parse_local_dt

SOURCE_ID = "AEMET-PRED-HOR"
XML_H_URL = "https://www.aemet.es/xml/municipios_h/localidad_h_{ine}.xml"
TTL_HOURLY = 3 * 3600
RAIN_CUTOFF_MM = 0.5  # decisión de ESCUDO; ver docs/current-risk.md


@dataclass
class HourPoint:
    t: str  # ISO con zona, hora oficial peninsular
    temp_c: float | None = None
    rh_pct: float | None = None
    wind_kmh: float | None = None
    wind_dir: str | None = None
    gust_kmh: float | None = None
    precip_mm: float | None = None
    precip_trace: bool = False
    snow_mm: float | None = None
    sky: str | None = None


@dataclass
class ParsedHourly:
    ine_code: str
    name: str | None
    issued_at: datetime
    points: list[HourPoint] = field(default_factory=list)
    precip_prob: list[dict] = field(default_factory=list)


def _hour_dt(day: date, period: str) -> datetime | None:
    if not (period.isdigit() and len(period) == 2 and int(period) < 24):
        return None
    return datetime(day.year, day.month, day.day, int(period), tzinfo=MADRID_TZ)


def _precip(text: str | None) -> tuple[float | None, bool]:
    t = (text or "").strip()
    return (0.0, True) if t.lower() == "ip" else (_num(t), False)


def parse_hourly_xml(content: bytes, ine_code: str) -> ParsedHourly:
    """Parsea `localidad_h_<INE>.xml`. Rechaza DTD/entidades como el parser diario."""
    if b"<!DOCTYPE" in content[:4096].upper() or b"<!ENTITY" in content.upper():
        raise AemetParseError("documento con DTD/entidades rechazado")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise AemetParseError(f"XML mal formado: {exc}") from exc
    if root.tag != "root":
        raise AemetParseError("raíz inesperada")
    if root.get("id") and root.get("id") != ine_code:
        raise AemetParseError(f"el XML corresponde a {root.get('id')}, no a {ine_code}")
    elaborado = root.findtext("elaborado")
    if not elaborado:
        raise AemetParseError("falta <elaborado>")
    hours: dict[datetime, HourPoint] = {}
    probs: list[dict] = []

    def at(day: date, el: ET.Element) -> HourPoint | None:
        ts = _hour_dt(day, el.get("periodo") or "")
        if ts is None:
            return None
        return hours.setdefault(ts, HourPoint(t=ts.isoformat()))

    for dia in root.iter("dia"):
        f = dia.get("fecha")
        if not f:
            continue
        day = date.fromisoformat(f)
        for el in dia.findall("temperatura"):
            if p := at(day, el):
                p.temp_c = _num(el.text)
        for el in dia.findall("humedad_relativa"):
            if p := at(day, el):
                p.rh_pct = _num(el.text)
        for el in dia.findall("viento"):
            if p := at(day, el):
                p.wind_kmh = _num(el.findtext("velocidad"))
                p.wind_dir = (el.findtext("direccion") or "").strip() or None
        for el in dia.findall("racha_max"):
            if p := at(day, el):
                p.gust_kmh = _num(el.text)
        for el in dia.findall("precipitacion"):
            if p := at(day, el):
                p.precip_mm, p.precip_trace = _precip(el.text)
        for el in dia.findall("nieve"):
            if p := at(day, el):
                p.snow_mm = _precip(el.text)[0]
        for el in dia.findall("estado_cielo"):
            if p := at(day, el):
                p.sky = el.get("descripcion") or None
        for el in dia.findall("prob_precipitacion"):
            per = el.get("periodo") or ""
            if len(per) == 4 and per.isdigit():
                probs.append({"date": f, "from_hour": int(per[:2]), "to_hour": int(per[2:]), "pct": _num(el.text)})
    return ParsedHourly(ine_code=ine_code, name=root.findtext("nombre"), issued_at=_parse_local_dt(elaborado),
                        points=[hours[k] for k in sorted(hours)], precip_prob=probs)


def fetch_hourly(ine: str, client: httpx.Client | None, cache: TTLCache, epoch: float) -> ParsedHourly:
    key = f"xmlh:{ine}"
    raw = cache.get(key, TTL_HOURLY, epoch)
    if raw is not None:
        try:
            return parse_hourly_xml(raw, ine)
        except AemetParseError:
            raw = None
    owned = client is None
    c = client or httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    try:
        r = c.get(XML_H_URL.format(ine=ine))
        r.raise_for_status()
        parsed = parse_hourly_xml(r.content, ine)
    except httpx.HTTPError as exc:
        raise AemetUnavailable(f"XML horario AEMET: {exc}") from exc
    except AemetParseError as exc:
        raise AemetUnavailable(str(exc)) from exc
    finally:
        if owned:
            c.close()
    cache.put(key, r.content, epoch)
    return parsed


def _peak(points: list[HourPoint], attr: str) -> tuple[float | None, HourPoint | None]:
    best: tuple[float | None, HourPoint | None] = (None, None)
    for p in points:
        v = getattr(p, attr)
        if v is not None and (best[0] is None or v > best[0]):
            best = (v, p)
    return best


def _total(points: list[HourPoint]) -> float | None:
    vals = [p.precip_mm for p in points if p.precip_mm is not None]
    return round(sum(vals), 1) if vals else None


def dry_ffwi(points: list[HourPoint]) -> tuple[list[float | None], str | None]:
    """Índice de cada hora hasta que la lluvia prevista acumulada alcanza el umbral, y hora en que lo alcanza.

    Fosberg no contempla la lluvia: desde ese momento el índice se deja vacío para no puntuar un temporal húmedo.
    """
    total = 0.0
    rain_from: str | None = None
    out: list[float | None] = []
    for p in points:
        total += p.precip_mm or 0
        if rain_from is None and total >= RAIN_CUTOFF_MM:
            rain_from = p.t
        out.append(None if rain_from else ffwi(p.temp_c, p.rh_pct, p.wind_kmh))
    return out, rain_from


def summarize(points: list[HourPoint], now: datetime) -> dict:
    """Valores DERIVADOS de las próximas 24 h y de todo el horizonte publicado."""
    next24 = [p for p in points if datetime.fromisoformat(p.t) < now + timedelta(hours=24)]
    gust, at = _peak(next24, "gust_kmh")
    rh = [p.rh_pct for p in next24 if p.rh_pct is not None]
    temp = [p.temp_c for p in next24 if p.temp_c is not None]
    values, rain_from = dry_ffwi(next24)
    scored = [(v, p) for v, p in zip(values, next24, strict=True) if v is not None]
    fire_max, fire_at = max(scored, key=lambda x: x[0]) if scored else (None, None)
    if fire_max is None and rain_from == (next24[0].t if next24 else None) and rain_from:
        fire_max = 0.0  # llueve desde la primera hora: no hay horas secas que puntuar
    return {
        "ffwi_max_24h": fire_max,
        "ffwi_max_at": fire_at.t if fire_at else None,
        "ffwi_rain_from": rain_from,
        "ffwi_temp_c": fire_at.temp_c if fire_at else None,
        "ffwi_rh_pct": fire_at.rh_pct if fire_at else None,
        "ffwi_wind_kmh": fire_at.wind_kmh if fire_at else None,
        "gust_max_24h_kmh": gust,
        "gust_max_at": at.t if at else None,
        "wind_dir_at_gust_max": at.wind_dir if at else None,
        "precip_24h_mm": _total(next24),
        "precip_total_mm": _total(points),
        "rh_min_24h_pct": min(rh) if rh else None,
        "temp_max_24h_c": max(temp) if temp else None,
        "horizon_hours": len(points),
    }


def _daily(ine: str, client: httpx.Client | None, cache: TTLCache, epoch: float, today: date) -> list[dict]:
    """Predicción diaria a 7 días (XML público). Si falla, lista vacía: la vista horaria no depende de ella."""
    try:
        fc = XmlPublicProvider().fetch_forecast(ine, client, cache, epoch)
    except AemetUnavailable:
        return []
    return [{"date": d.day.isoformat(), "temp_max_c": d.temp_max_c, "temp_min_c": d.temp_min_c, "rh_min_pct": d.rh_min_pct,
             "precip_prob_pct": d.precip_prob_24h_pct if d.precip_prob_24h_pct is not None else d.precip_prob_periods_max_pct,
             "wind_max_kmh": d.wind_max_kmh, "wind_dir": d.wind_dir_at_max, "gust_max_kmh": d.gust_max_kmh, "sky": d.sky_24h}
            for d in fc.days if d.day >= today]


def get_hourly_forecast(
    ine_code: str,
    *,
    now: datetime | None = None,
    client: httpx.Client | None = None,
    cache: TTLCache | None = None,
    with_daily: bool = True,
) -> dict:
    """Predicción horaria de un municipio. Ante cualquier fallo → `unavailable`, nunca datos inventados."""
    if not (len(ine_code) == 5 and ine_code.isdigit()):
        raise ValueError("ine_code debe tener 5 dígitos")
    now = (now or datetime.now(UTC)).astimezone(MADRID_TZ)
    cache = cache or default_cache()
    epoch = now.timestamp()
    base = {"source_id": SOURCE_ID, "source_url": XML_H_URL.format(ine=ine_code), "ine_code": ine_code,
            "disclaimer": DISCLAIMER, "attribution": ATTRIBUTION, "caveat": SCALE_CAVEAT}
    try:
        fc = fetch_hourly(ine_code, client, cache, epoch)
    except AemetUnavailable as exc:
        return {**base, "status": "unavailable", "name": None, "issued_at": None, "points": [], "precip_prob": [],
                "daily": [], "summary": None, "message": "Datos meteorológicos no disponibles", "errors": [str(exc)]}
    floor = now.replace(minute=0, second=0, microsecond=0)
    points = [p for p in fc.points if datetime.fromisoformat(p.t) >= floor]
    fresh = bool(points) and now - fc.issued_at <= MAX_FORECAST_AGE
    return {
        **base,
        "status": "ok" if fresh else "stale",
        "name": fc.name,
        "issued_at": fc.issued_at.isoformat(),
        "points": [{**asdict(p), "ffwi": v} for p, v in zip(points, dry_ffwi(points)[0], strict=True)],
        "precip_prob": fc.precip_prob,
        "daily": _daily(ine_code, client, cache, epoch, now.date()) if with_daily else [],
        "summary": summarize(points, floor) if points else None,
        "message": None if fresh else "Predicción desactualizada: no representa las próximas horas",
        "errors": [],
    }
