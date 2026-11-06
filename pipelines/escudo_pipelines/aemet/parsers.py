"""Parsers de predicción municipal AEMET (XML público y JSON de OpenData).

Ambos producen la misma estructura neutra `ParsedForecast`. No se interpolan ni
inventan valores: un campo vacío en origen queda como `None`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

MADRID_TZ = ZoneInfo("Europe/Madrid")


class AemetParseError(ValueError):
    """El documento de AEMET no tiene la estructura esperada."""


@dataclass
class DayForecast:
    day: date
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    rh_max_pct: float | None = None
    rh_min_pct: float | None = None
    precip_prob_24h_pct: float | None = None  # valor del periodo 00-24 publicado
    precip_prob_periods_max_pct: float | None = None  # máximo de subperiodos (derivado)
    wind_max_kmh: float | None = None  # máximo de velocidad media entre periodos (derivado)
    wind_dir_at_max: str | None = None
    gust_max_kmh: float | None = None  # racha máxima publicada (máximo entre periodos)
    sky_24h: str | None = None


@dataclass
class ParsedForecast:
    ine_code: str
    name: str | None
    issued_at: datetime  # aware, Europe/Madrid
    days: list[DayForecast] = field(default_factory=list)
    copyright: str | None = None
    product_url: str | None = None

    def day_for(self, d: date) -> DayForecast | None:
        return next((x for x in self.days if x.day == d), None)


def _num(text: str | None) -> float | None:
    if text is None:
        return None
    t = text.strip()
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _parse_local_dt(text: str) -> datetime:
    dt = datetime.fromisoformat(text.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MADRID_TZ)  # AEMET publica `elaborado` en hora oficial peninsular
    return dt


def _max_with_key(pairs: list[tuple[float | None, str | None]]) -> tuple[float | None, str | None]:
    best: tuple[float | None, str | None] = (None, None)
    for v, k in pairs:
        if v is not None and (best[0] is None or v > best[0]):
            best = (v, k)
    return best


def parse_localidad_xml(content: bytes, ine_code: str) -> ParsedForecast:
    """Parsea `https://www.aemet.es/xml/municipios/localidad_<INE>.xml` (ISO-8859-15)."""
    # Endurecimiento: AEMET no usa DTD; rechazarlo evita XXE / billion laughs con el parser stdlib.
    head = content[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in content.upper():
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
    days: list[DayForecast] = []
    for dia in root.iter("dia"):
        f = dia.get("fecha")
        if not f:
            continue
        d = DayForecast(day=date.fromisoformat(f))
        d.temp_max_c = _num(dia.findtext("temperatura/maxima"))
        d.temp_min_c = _num(dia.findtext("temperatura/minima"))
        d.rh_max_pct = _num(dia.findtext("humedad_relativa/maxima"))
        d.rh_min_pct = _num(dia.findtext("humedad_relativa/minima"))
        probs = {p.get("periodo"): _num(p.text) for p in dia.findall("prob_precipitacion")}
        d.precip_prob_24h_pct = probs.get("00-24") if "00-24" in probs else probs.get(None)
        d.precip_prob_periods_max_pct = _max_with_key([(v, k) for k, v in probs.items()])[0]
        winds = [(_num(v.findtext("velocidad")), (v.findtext("direccion") or "").strip() or None) for v in dia.findall("viento")]
        d.wind_max_kmh, d.wind_dir_at_max = _max_with_key(winds)
        d.gust_max_kmh = _max_with_key([(_num(r.text), None) for r in dia.findall("racha_max")])[0]
        for ec in dia.findall("estado_cielo"):
            if ec.get("periodo") in ("00-24", None) and ec.get("descripcion"):
                d.sky_24h = ec.get("descripcion")
        days.append(d)
    if not days:
        raise AemetParseError("sin días de predicción")
    return ParsedForecast(
        ine_code=ine_code,
        name=root.findtext("nombre"),
        issued_at=_parse_local_dt(elaborado),
        days=days,
        copyright=root.findtext("origen/copyright"),
        product_url=root.findtext("origen/enlace"),
    )


def parse_opendata_daily(payload: list | dict, ine_code: str) -> ParsedForecast:
    """Parsea el JSON de `prediccion/especifica/municipio/diaria/{municipio}` (contenido de `datos`)."""
    try:
        doc = payload[0] if isinstance(payload, list) else payload
        elaborado = doc["elaborado"]
        dias = doc["prediccion"]["dia"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AemetParseError(f"JSON OpenData inesperado: {exc}") from exc
    days: list[DayForecast] = []
    for dia in dias:
        d = DayForecast(day=datetime.fromisoformat(dia["fecha"]).date())
        t = dia.get("temperatura") or {}
        h = dia.get("humedadRelativa") or {}
        d.temp_max_c, d.temp_min_c = _num(str(t.get("maxima", ""))), _num(str(t.get("minima", "")))
        d.rh_max_pct, d.rh_min_pct = _num(str(h.get("maxima", ""))), _num(str(h.get("minima", "")))
        probs = {p.get("periodo"): _num(str(p.get("value", ""))) for p in dia.get("probPrecipitacion", [])}
        d.precip_prob_24h_pct = probs.get("00-24") if "00-24" in probs else probs.get(None)
        d.precip_prob_periods_max_pct = _max_with_key([(v, k) for k, v in probs.items()])[0]
        winds = [(_num(str(v.get("velocidad", ""))), v.get("direccion") or None) for v in dia.get("viento", [])]
        d.wind_max_kmh, d.wind_dir_at_max = _max_with_key(winds)
        d.gust_max_kmh = _max_with_key([(_num(str(r.get("value", ""))), None) for r in dia.get("rachaMax", [])])[0]
        days.append(d)
    if not days:
        raise AemetParseError("sin días de predicción")
    return ParsedForecast(
        ine_code=ine_code,
        name=doc.get("nombre"),
        issued_at=_parse_local_dt(elaborado),
        days=days,
        copyright=(doc.get("origen") or {}).get("copyright"),
        product_url=(doc.get("origen") or {}).get("enlace"),
    )
