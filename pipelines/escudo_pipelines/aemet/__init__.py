"""Conector AEMET de ESCUDO MADRID (A4). Ver docs/aemet.md."""

from .client import AemetUnavailable, OpenDataProvider, TTLCache, XmlPublicProvider
from .context import DISCLAIMER, SOURCE_ID, get_weather_context, reset_state
from .parsers import AemetParseError, parse_localidad_xml, parse_opendata_daily

__all__ = [
    "AemetParseError",
    "AemetUnavailable",
    "DISCLAIMER",
    "OpenDataProvider",
    "SOURCE_ID",
    "TTLCache",
    "XmlPublicProvider",
    "get_weather_context",
    "parse_localidad_xml",
    "parse_opendata_daily",
    "reset_state",
]
