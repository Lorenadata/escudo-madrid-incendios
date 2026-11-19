"""Puntuación de atención preventiva: fórmula, bandas, motivos y cruce con los planes municipales."""

from __future__ import annotations

from escudo_api.attention import (
    WEIGHTS,
    band_for,
    compute_ranking,
    gap_summary,
    percentile_ranks,
    weighted_score,
)


def _m(code, high, **kw):
    return {"ine_code": code, "name": code, "area_km2": 10.0, "high_share": high, "population_total": 100, "fires_total": 1,
            "burnt_ha": 0, "age_65_plus_share": 0.2, "non_main_share": 0.2, "single_dwelling_building_share": 0.2,
            "zar": False, "plan_required": False, "plan_approved": None, **kw}


def test_percentiles_con_empates_y_nulos():
    assert percentile_ranks({"a": 0, "b": 0, "c": 1, "d": None}) == {"a": 1 / 3, "b": 1 / 3, "c": 5 / 6, "d": None}


def test_bandas_con_cortes_fijos():
    assert [band_for(s)["id"] for s in (80, 79.9, 60, 40, 20, 0)] == ["very_high", "high", "high", "medium", "low", "very_low"]
    assert band_for(None)["id"] == "unavailable"


def test_sin_riesgo_oficial_no_hay_puntuacion_y_un_bloque_nulo_reparte_su_peso():
    assert weighted_score({"territory": None, "history": 1}, WEIGHTS) is None
    s = weighted_score({"territory": 1, "history": None, "residential": 0, "planning": 1}, WEIGHTS)
    assert round(s, 3) == round(100 * 65 / 80, 3)


def test_plan_aprobado_anula_solo_el_bloque_de_planificacion():
    rows = {r["ine_code"]: r for r in compute_ranking([_m("A", 0.9, plan_approved=True), _m("B", 0.9)])}
    assert rows["A"]["components"]["planning"] == 0 and rows["B"]["components"]["planning"] == 0.9
    assert rows["B"]["score"] - rows["A"]["score"] == round(0.9 * WEIGHTS["planning"], 1)
    assert rows["B"]["rank"] == 1


def test_motivos_y_casilla_vacia_no_se_tratan_como_no():
    rows = compute_ranking([_m("A", 0.8, zar=False)])
    text = " ".join(x["text"] for x in rows[0]["reasons"])
    assert "80 % del término" in text and "No figura entre las 59" in text and "sin obligación de plan" in text


def test_cruce_cuenta_literalmente():
    rows = compute_ranking([
        _m("A", 0.8), _m("B", 0.5), _m("C", 0.9, zar=True, plan_required=True, plan_approved=True),
        _m("D", 0.2, zar=True, plan_required=True, plan_approved=False), _m("E", 0.1, zar=True, plan_required=True),
    ])
    g = gap_summary(rows)
    assert (g["high_majority"], g["high_majority_in_zar"], g["high_majority_outside_zar"]) == (2, 1, 1)
    assert g["outside_zar_codes"] == ["A"]
    assert (g["plan_required"], g["plan_required_approved"], g["plan_required_not_approved"], g["plan_required_blank"]) == (3, 1, 1, 1)
