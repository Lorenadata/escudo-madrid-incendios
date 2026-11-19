"""Riesgo estimado hoy: fórmula, tramos, orden y ausencia de datos sustitutos."""

from __future__ import annotations

from escudo_api import weather_regional as wr
from escudo_api.current_risk import band_for, compute_current_risk, risk_score


def _w(code, ffwi, status="ok", **kw):
    return {"ine_code": code, "status": status, "ffwi_max_24h": ffwi, "ffwi_max_at": "2026-11-18T15:00:00+01:00",
            "ffwi_temp_c": 18.0, "ffwi_rh_pct": 40.0, "ffwi_wind_kmh": 20.0, "precip_24h_mm": 0.0, "ffwi_hourly": [ffwi], **kw}


def _m(code, high):
    return {"ine_code": code, "name": code, "high_share": high}


def test_producto_y_factor_nulo():
    assert risk_score(0.81, 100) == 81
    assert risk_score(1, 25) == 25
    assert risk_score(0, 100) == 0 and risk_score(1, 0) == 0
    assert risk_score(None, 50) is None and risk_score(0.5, None) is None


def test_tramos_fijos():
    assert [band_for(v)["id"] for v in (80, 79.9, 60, 40, 20, 0)] == ["very_high", "high", "high", "medium", "low", "very_low"]
    assert band_for(None)["id"] == "unavailable"


def test_ordena_explica_y_senala_el_factor_que_limita():
    rain = {"precip_24h_mm": 3.2, "ffwi_rain_from": "2026-11-18T20:00:00+01:00"}
    rows = compute_current_risk([_m("a", 0.9), _m("b", 0.1)], [_w("a", 25), _w("b", 25, **rain)])
    assert [r["ine_code"] for r in rows] == ["a", "b"] and [r["rank"] for r in rows] == [1, 2]
    assert rows[0]["limiting"] == "weather" and rows[1]["limiting"] == "territory"
    assert rows[0]["reasons"][0].startswith("90 % del término")
    assert "18/11 a las 15:00" in rows[0]["reasons"][1] and "18 °C" in rows[0]["reasons"][1]
    assert any("18/11 a las 20:00" in x and "3,2 mm" in x for x in rows[1]["reasons"])


def test_lluvia_desde_la_primera_hora_da_cero_sin_inventar_pico():
    w = _w("a", 0.0, ffwi_max_at=None, ffwi_temp_c=None, ffwi_rh_pct=None, ffwi_wind_kmh=None,
           ffwi_rain_from="2026-11-18T10:00:00+01:00", precip_24h_mm=12.0)
    r = compute_current_risk([_m("a", 0.9)], [w])[0]
    assert r["score"] == 0 and r["band"]["id"] == "very_low" and not any("Fosberg" in x for x in r["reasons"])


def test_regional_reintenta_solo_los_municipios_que_fallaron():
    calls: list[str] = []
    fail = {"b"}

    def fetch(code):
        calls.append(code)
        if code in fail:
            raise RuntimeError("caída")
        return {"status": "ok", "summary": {}, "points": []}

    rw = wr.RegionalWeather(fetch=fetch)
    rw._start = rw._run  # síncrono en la prueba
    munis = [("a", "A"), ("b", "B")]
    rw.ensure(munis)
    assert sorted(calls) == ["a", "b"]
    calls.clear()
    rw.ensure(munis)  # recién terminado: todavía no reintenta
    assert calls == []
    rw._finished_at -= wr.RETRY_SECONDS + 1
    fail.clear()
    rw.ensure(munis)
    assert calls == ["b"] and rw.snapshot()["coverage"] == 2


def test_prediccion_caducada_o_ausente_no_puntua():
    rows = compute_current_risk([_m("a", 0.9), _m("b", 0.9)], [_w("a", 80, status="stale")])
    assert all(r["score"] is None and r["rank"] is None and r["ffwi_max_24h"] is None for r in rows)
