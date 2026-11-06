"""Tests del conector AEMET (A4). Cubre T05 (meteo offline) del PRD §9.2."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from escudo_pipelines.aemet import (
    DISCLAIMER,
    AemetParseError,
    TTLCache,
    get_weather_context,
    parse_localidad_xml,
    reset_state,
)
from escudo_pipelines.aemet.parsers import MADRID_TZ

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "aemet"
XML_28079 = (FIX / "localidad_28079.xml").read_bytes()  # captura real 06/11/2026, elaborado 17:15:10
NOW_OK = datetime(2026, 11, 6, 20, 0, tzinfo=MADRID_TZ)


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    monkeypatch.delenv("AEMET_API_KEY", raising=False)
    monkeypatch.delenv("ESCUDO_AEMET_CACHE_DIR", raising=False)
    reset_state()
    yield
    reset_state()


class Recorder:
    def __init__(self, handler):
        self.handler = handler
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)


def client_for(handler) -> tuple[httpx.Client, Recorder]:
    rec = Recorder(handler)
    return httpx.Client(transport=httpx.MockTransport(rec)), rec


def serve_xml(request: httpx.Request) -> httpx.Response:
    assert request.url.host == "www.aemet.es"
    return httpx.Response(200, content=XML_28079, headers={"content-type": "application/xml"})


def network_down(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("red caída (simulada)", request=request)


# --- Parseo de captura real -------------------------------------------------------------

def test_parse_real_fixture():
    fc = parse_localidad_xml(XML_28079, "28079")
    assert fc.name == "Madrid"
    assert fc.issued_at == datetime(2026, 11, 6, 17, 15, 10, tzinfo=MADRID_TZ)
    d = fc.day_for(NOW_OK.date())
    # Valores literales del XML real (temperatura 16/6, humedad 70/40, prob. 12-24 = 10)
    assert (d.temp_max_c, d.temp_min_c, d.rh_max_pct, d.rh_min_pct) == (16, 6, 70, 40)
    assert d.precip_prob_24h_pct is None  # periodo 00-24 vacío en origen: no se inventa
    assert d.precip_prob_periods_max_pct == 10
    assert d.wind_max_kmh == 10 and d.wind_dir_at_max == "NE"
    assert d.gust_max_kmh is None
    assert len(fc.days) == 7
    assert "AEMET" in (fc.copyright or "")


def test_parse_rejects_wrong_municipality_and_dtd():
    with pytest.raises(AemetParseError):
        parse_localidad_xml(XML_28079, "28131")
    evil = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY a "x">]><root id="28079"><elaborado>2026-11-06T00:00:00</elaborado></root>'
    with pytest.raises(AemetParseError):
        parse_localidad_xml(evil, "28079")
    with pytest.raises(AemetParseError):
        parse_localidad_xml(b"<root", "28079")


# --- Contexto OK ------------------------------------------------------------------------

def test_context_ok_from_public_xml():
    c, rec = client_for(serve_xml)
    ctx = get_weather_context("28079", now=NOW_OK, client=c, cache=TTLCache())
    assert ctx["status"] == "ok"
    assert ctx["provider"] == "aemet_xml_public"
    assert ctx["issued_at"].startswith("2026-11-06T17:15:10")
    assert ctx["valid_from"].startswith("2026-11-06T00:00")
    assert ctx["valid_to"].startswith("2026-11-07T00:00")
    assert ctx["disclaimer"] == DISCLAIMER
    assert ctx["fire_danger"] is None  # sin clave no hay producto oficial de peligro
    assert ctx["reference_location"]["ine_code"] == "28079"
    v = {x["indicator_id"]: x for x in ctx["variables"]}
    assert v["weather_temp_max_c"]["value"] == 16 and v["weather_temp_max_c"]["status"] == "official"
    assert v["weather_wind_max_kmh"]["status"] == "derived"
    assert v["weather_gust_max_kmh"]["value"] is None and v["weather_gust_max_kmh"]["status"] == "unavailable"
    for ind in ctx["variables"]:
        assert set(ind) >= {"indicator_id", "label", "value", "unit", "spatial_scope", "temporal_scope", "status", "source_id", "method", "caveat"}
    assert ctx["last_valid_at"] == ctx["issued_at"]
    assert len(rec.requests) == 1


def test_cache_avoids_second_request_within_ttl():
    cache = TTLCache()
    c, rec = client_for(serve_xml)
    get_weather_context("28079", now=NOW_OK, client=c, cache=cache)
    get_weather_context("28079", now=NOW_OK + timedelta(minutes=30), client=c, cache=cache)
    assert len(rec.requests) == 1


# --- T05: red caída ---------------------------------------------------------------------

def test_network_down_without_history_is_unavailable():
    c, _ = client_for(network_down)
    ctx = get_weather_context("28079", now=NOW_OK, client=c, cache=TTLCache())
    assert ctx["status"] == "unavailable"
    assert ctx["variables"] == []
    assert ctx["issued_at"] is None
    assert ctx["last_valid_at"] is None
    assert ctx["message"] == "Datos meteorológicos no disponibles"


def test_network_down_after_valid_data_reports_last_valid_but_no_values():
    cache = TTLCache()
    ok, _ = client_for(serve_xml)
    first = get_weather_context("28079", now=NOW_OK, client=ok, cache=cache)
    down, _ = client_for(network_down)
    later = NOW_OK + timedelta(hours=4)  # supera el TTL de caché (3 h): obliga a ir a red
    ctx = get_weather_context("28079", now=later, client=down, cache=cache)
    assert ctx["status"] == "unavailable"
    assert ctx["variables"] == []  # nunca reutilizar silenciosamente el dato antiguo
    assert ctx["last_valid_at"] == first["issued_at"]


def test_http_error_and_garbage_are_unavailable():
    c, _ = client_for(lambda r: httpx.Response(503))
    assert get_weather_context("28079", now=NOW_OK, client=c, cache=TTLCache())["status"] == "unavailable"
    c, _ = client_for(lambda r: httpx.Response(200, content=b"<html>error</html>"))
    assert get_weather_context("28079", now=NOW_OK, client=c, cache=TTLCache())["status"] == "unavailable"


# --- Caducidad --------------------------------------------------------------------------

def test_outdated_forecast_is_stale_not_current():
    c, _ = client_for(serve_xml)  # el servidor devuelve un XML elaborado el 06/11
    now = datetime(2026, 11, 9, 12, 0, tzinfo=MADRID_TZ)
    ctx = get_weather_context("28079", now=now, client=c, cache=TTLCache())
    assert ctx["status"] == "stale"
    assert ctx["message"].startswith("Predicción desactualizada")
    assert ctx["variables"] and all(v["status"] in ("stale", "unavailable") for v in ctx["variables"])
    assert ctx["last_valid_at"] is None  # nunca hubo un dato vigente en este proceso


def test_forecast_not_covering_today_is_stale():
    c, _ = client_for(serve_xml)
    now = datetime(2026, 11, 20, 9, 0, tzinfo=MADRID_TZ)
    ctx = get_weather_context("28079", now=now, client=c, cache=TTLCache())
    assert ctx["status"] == "stale"
    assert all(v["temporal_scope"] != "2026-11-20" for v in ctx["variables"])


def test_invalid_ine_code():
    with pytest.raises(ValueError):
        get_weather_context("2807", now=NOW_OK, cache=TTLCache())


# --- Proveedor OpenData -----------------------------------------------------------------

def test_without_key_never_calls_opendata():
    c, rec = client_for(serve_xml)
    get_weather_context("28079", now=NOW_OK, client=c, cache=TTLCache())
    assert all(r.url.host != "opendata.aemet.es" for r in rec.requests)


# Respuesta SINTÉTICA (no capturada): reproduce la estructura documentada en
# https://opendata.aemet.es/AEMET_OpenData_specification.json para probar el patrón de dos pasos.
SYNTHETIC_OD_DAILY = [
    {
        "elaborado": "2026-11-06T17:15:10",
        "nombre": "Madrid",
        "origen": {"copyright": "© AEMET (sintético de test)"},
        "prediccion": {
            "dia": [
                {
                    "fecha": "2026-11-06T00:00:00",
                    "temperatura": {"maxima": 99, "minima": -9},
                    "humedadRelativa": {"maxima": 88, "minima": 11},
                    "probPrecipitacion": [{"value": 5, "periodo": "00-24"}],
                    "viento": [{"direccion": "S", "velocidad": 20, "periodo": "00-24"}],
                    "rachaMax": [{"value": "", "periodo": "00-24"}],
                }
            ]
        },
    }
]


def opendata_handler(request: httpx.Request) -> httpx.Response:
    if request.url.host == "opendata.aemet.es":
        if request.url.path.startswith("/opendata/api/"):
            assert request.headers.get("api_key") == "TEST-KEY"
        else:  # la URL `datos` no necesita la clave: no se reenvía
            assert request.headers.get("api_key") is None
        if "/incendios/" in request.url.path:
            return httpx.Response(200, json={"estado": 200, "datos": "https://opendata.aemet.es/sh/mapa.png", "metadatos": "x", "descripcion": "exito"})
        if request.url.path.startswith("/opendata/api/"):
            return httpx.Response(200, json={"estado": 200, "datos": "https://opendata.aemet.es/opendata/sh/datos1", "metadatos": "x", "descripcion": "exito"})
        return httpx.Response(200, content=json.dumps(SYNTHETIC_OD_DAILY).encode("latin-1"))
    raise AssertionError("no debería usar el XML si OpenData responde")


def test_opendata_two_step_with_key():
    c, rec = client_for(opendata_handler)
    ctx = get_weather_context("28079", now=NOW_OK, client=c, api_key="TEST-KEY", cache=TTLCache())
    assert ctx["status"] == "ok" and ctx["provider"] == "aemet_opendata"
    v = {x["indicator_id"]: x for x in ctx["variables"]}
    assert v["weather_temp_max_c"]["value"] == 99 and v["weather_precip_prob_24h_pct"]["value"] == 5
    assert ctx["fire_danger"]["status"] == "official"
    assert ctx["fire_danger"]["value"].endswith("mapa.png")
    assert "no se extrae un valor por municipio" in ctx["fire_danger"]["caveat"].lower()


def test_opendata_quota_falls_back_to_public_xml():
    def handler(request):
        if request.url.host == "opendata.aemet.es":
            return httpx.Response(429, json={"estado": 429, "descripcion": "Too Many Requests"})
        return serve_xml(request)

    c, _ = client_for(handler)
    ctx = get_weather_context("28079", now=NOW_OK, client=c, api_key="TEST-KEY", cache=TTLCache())
    assert ctx["status"] == "ok" and ctx["provider"] == "aemet_xml_public"
    assert any("aemet_opendata" in e for e in ctx["errors"])


# --- Prueba en vivo (opcional) -----------------------------------------------------------

@pytest.mark.network
def test_live_public_xml():
    ctx = get_weather_context("28079", cache=TTLCache())
    assert ctx["status"] in ("ok", "stale", "unavailable")
    if ctx["status"] == "ok":
        assert ctx["variables"]
