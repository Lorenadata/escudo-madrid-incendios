"""Predicción horaria AEMET: parseo de captura real, resumen derivado y caídas (nunca datos inventados)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import httpx
import pytest

from escudo_pipelines.aemet import AemetParseError, TTLCache, get_hourly_forecast, parse_hourly_xml
from escudo_pipelines.aemet.fire_weather import KMH_TO_MPH, ffwi
from escudo_pipelines.aemet.hourly import HourPoint, dry_ffwi, summarize
from escudo_pipelines.aemet.parsers import MADRID_TZ

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "aemet"
XML = (FIX / "localidad_h_28131.xml").read_bytes()  # captura real, elaborado 18/11/2026 08:55:09
NOW = datetime(2026, 11, 18, 10, 20, tzinfo=MADRID_TZ)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parsea_horas_rachas_y_lluvia_inapreciable():
    p = parse_hourly_xml(XML, "28131")
    assert p.issued_at.isoformat().startswith("2026-11-18T08:55:09")
    assert len(p.points) >= 40
    h = next(x for x in p.points if x.t.startswith("2026-11-18T09"))
    assert (h.gust_kmh, h.wind_kmh, h.wind_dir) == (44.0, 19.0, "O")
    trace = [x for x in p.points if x.precip_trace]
    assert trace and all(x.precip_mm == 0 for x in trace)  # «Ip» se conserva, no se convierte en lluvia medible
    assert p.precip_prob and p.precip_prob[0]["from_hour"] == 7


def test_rechaza_dtd_y_municipio_ajeno():
    with pytest.raises(AemetParseError):
        parse_hourly_xml(b"<!DOCTYPE x><root/>", "28131")
    with pytest.raises(AemetParseError):
        parse_hourly_xml(XML.replace(b'id="28131"', b'id="28079"'), "28131")


def test_resumen_deriva_solo_de_horas_futuras():
    fc = get_hourly_forecast("28131", now=NOW, client=_client(lambda r: httpx.Response(200, content=XML)),
                             cache=TTLCache(), with_daily=False)
    assert fc["status"] == "ok"
    assert all(p["t"] >= "2026-11-18T10" for p in fc["points"])
    gusts = [p["gust_kmh"] for p in fc["points"] if p["t"] < "2026-11-19T10" and p["gust_kmh"] is not None]
    assert fc["summary"]["gust_max_24h_kmh"] == max(gusts)


def test_fosberg_coincide_con_calculo_manual_y_limites():
    # 90 °F, 20 % y 20 mph: m = 4,0994; η = 0,7534; FFWI = 0,7534 × √401 / 0,3002 = 50,26
    assert ffwi((90 - 32) * 5 / 9, 20, 20 / KMH_TO_MPH) == pytest.approx(50.26, abs=0.06)
    assert ffwi(40, 0, 200) == 100  # el índice está acotado
    assert ffwi(5, 100, 10) < 2  # aire saturado: valor casi nulo
    assert ffwi(None, 20, 10) is None and ffwi(20, None, 10) is None and ffwi(20, 20, None) is None


def _hour(h, rain=0.0, wind=30.0):
    return HourPoint(t=datetime(2026, 11, 18, h, tzinfo=MADRID_TZ).isoformat(), temp_c=20.0, rh_pct=30.0, wind_kmh=wind, precip_mm=rain)


def test_fosberg_solo_cuenta_las_horas_anteriores_a_la_lluvia():
    pts = [_hour(10), _hour(11, rain=0.2), _hour(12, rain=0.3, wind=90.0), _hour(13, wind=90.0)]
    values, rain_from = dry_ffwi(pts)
    assert values[0] is not None and values[1] is not None and values[2:] == [None, None]
    assert rain_from == pts[2].t
    s = summarize(pts, datetime(2026, 11, 18, 10, tzinfo=MADRID_TZ))
    assert s["ffwi_max_24h"] == max(values[:2]) and s["ffwi_rain_from"] == pts[2].t


def test_lluvia_desde_la_primera_hora_deja_el_indice_en_cero():
    s = summarize([_hour(10, rain=2.0), _hour(11)], datetime(2026, 11, 18, 10, tzinfo=MADRID_TZ))
    assert s["ffwi_max_24h"] == 0 and s["ffwi_max_at"] is None and s["ffwi_temp_c"] is None


def test_sin_variables_no_hay_indice_aunque_no_llueva():
    p = HourPoint(t=datetime(2026, 11, 18, 10, tzinfo=MADRID_TZ).isoformat(), temp_c=None, rh_pct=30.0, wind_kmh=10.0)
    assert summarize([p], datetime(2026, 11, 18, 10, tzinfo=MADRID_TZ))["ffwi_max_24h"] is None


def test_aemet_caido_da_unavailable_sin_valores():
    fc = get_hourly_forecast("28131", now=NOW, client=_client(lambda r: httpx.Response(503)), cache=TTLCache())
    assert fc["status"] == "unavailable" and fc["points"] == [] and fc["summary"] is None


def test_prediccion_antigua_es_stale():
    later = datetime(2026, 11, 19, 12, 0, tzinfo=MADRID_TZ)
    fc = get_hourly_forecast("28131", now=later, client=_client(lambda r: httpx.Response(200, content=XML)),
                             cache=TTLCache(), with_daily=False)
    assert fc["status"] == "stale" and fc["message"]
