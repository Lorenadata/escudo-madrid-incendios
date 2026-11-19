"""Puntuación de atención preventiva: orden de revisión municipal, explicado y reproducible.

NO es riesgo de incendio ni una probabilidad, y no usa la meteorología (el cruce con el tiempo previsto está en
`current_risk.py`). Los pesos son una decisión de ESCUDO y se pueden cambiar en la interfaz.
Método completo: docs/attention-index.md.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from itertools import product
from typing import Any

WEIGHTS: dict[str, int] = {"territory": 40, "history": 20, "residential": 15, "planning": 25}
BANDS: tuple[tuple[int, str, str], ...] = (
    (80, "very_high", "Muy alta"),
    (60, "high", "Alta"),
    (40, "medium", "Media"),
    (20, "low", "Baja"),
    (0, "very_low", "Muy baja"),
)
TOP_N = 20
_STEP = 10  # variación de cada peso en la prueba de estabilidad


def band_for(score: float | None) -> dict[str, str]:
    if score is None:
        return {"id": "unavailable", "label": "No disponible"}
    for floor, bid, label in BANDS:
        if score >= floor:
            return {"id": bid, "label": label}
    return {"id": "very_low", "label": "Muy baja"}


def percentile_ranks(values: dict[str, float | None]) -> dict[str, float | None]:
    """Posición relativa 0–1 (rango medio en los empates). Un valor nulo sigue nulo."""
    xs = sorted(v for v in values.values() if v is not None)
    n = len(xs)
    out: dict[str, float | None] = {}
    for k, v in values.items():
        if v is None:
            out[k] = None
        else:
            lo, hi = bisect_left(xs, v), bisect_right(xs, v)
            out[k] = (lo + (hi - lo) / 2) / n
    return out


def _mean(*vals: float | None) -> float | None:
    v = [x for x in vals if x is not None]
    return sum(v) / len(v) if v else None


def weighted_score(components: dict[str, float | None], weights: dict[str, int | float]) -> float | None:
    """Media ponderada 0–100. Sin territorio no hay puntuación; otro bloque sin datos reparte su peso."""
    if components.get("territory") is None:
        return None
    used = {k: w for k, w in weights.items() if components.get(k) is not None}
    total = sum(used.values())
    return 100 * sum(components[k] * w for k, w in used.items()) / total if total else None  # type: ignore[operator]


def _pct(v: float) -> str:
    return f"{v * 100:.0f}".replace(".", ",") + " %"


def _int(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def _reasons(r: dict[str, Any], c: dict[str, float | None], ranks: dict[str, float | None], w: dict[str, int]) -> list[dict]:
    out: list[dict] = []
    high = r.get("high_share")

    def add(block: str, text: str, points: float) -> None:
        out.append({"block": block, "text": text, "points": round(points, 1)})

    if high is not None:
        add("territory", f"{_pct(high)} del término en riesgo alto o muy alto en el mapa oficial", high * w["territory"])
    if r.get("plan_approved") is True:
        add("planning", "Plan municipal aprobado en pleno según el Plan Anual 2026", 0)
    elif high is not None:
        pts = (c.get("planning") or 0) * w["planning"]
        if r.get("plan_required") is True:
            detail = "Obligado a tener plan municipal, sin aprobación que conste"
        elif high >= 0.5:
            detail = "Más de la mitad del término en riesgo alto y sin obligación de plan municipal"
        else:
            detail = "Sin plan municipal aprobado que conste"
        add("planning", detail, pts)
    if r.get("zar") is True:
        add("context", "Declarado Zona de Alto Riesgo", 0)
    elif r.get("zar") is False and high is not None and high >= 0.5:
        add("context", "No figura entre las 59 Zonas de Alto Riesgo", 0)
    hist = (c.get("history") or 0) * w["history"]
    if r.get("fires_total"):
        add("history", f"Siniestros con origen aquí en 2015–2024: {_int(r['fires_total'])}", hist / 2)
    if r.get("burnt_ha"):
        add("history", f"Superficie quemada detectada por satélite desde 2016: {_int(r['burnt_ha'])} ha", hist / 2)
    res = (c.get("residential") or 0) * w["residential"] / 3
    if (ranks.get("non_main") or 0) >= 0.75 and r.get("non_main_share") is not None:
        add("residential", f"{_pct(r['non_main_share'])} de viviendas no principales", res)
    if (ranks.get("age65") or 0) >= 0.75 and r.get("age_65_plus_share") is not None:
        add("residential", f"{_pct(r['age_65_plus_share'])} de la población con 65 años o más", res)
    if (ranks.get("single") or 0) >= 0.75 and r.get("single_dwelling_building_share") is not None:
        add("residential", f"{_pct(r['single_dwelling_building_share'])} de viviendas en edificio unifamiliar", res)
    return sorted(out, key=lambda x: -x["points"])


def _stability(rows: list[dict]) -> dict[str, float]:
    """Parte de las 81 combinaciones de pesos (cada uno ±10) en las que el municipio sigue entre los 20 primeros."""
    scored = [r for r in rows if r["score"] is not None]
    hits = dict.fromkeys((r["ine_code"] for r in scored), 0)
    combos = list(product(*[(w - _STEP, w, w + _STEP) for w in WEIGHTS.values()]))
    for combo in combos:
        w = dict(zip(WEIGHTS, combo, strict=True))
        ranked = sorted(scored, key=lambda r: (-(weighted_score(r["components"], w) or 0), r["ine_code"]))
        for r in ranked[:TOP_N]:
            hits[r["ine_code"]] += 1
    return {k: round(v / len(combos), 3) for k, v in hits.items()}


def compute_ranking(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filas con componentes 0–1, puntuación, banda, puesto, motivos y estabilidad, ordenadas de mayor a menor."""
    by = {r["ine_code"]: r for r in inputs}

    def per_km2(r: dict[str, Any], key: str, factor: float = 1) -> float | None:
        v, a = r.get(key), r.get("area_km2")
        return v / (a * factor) if v is not None and a else None

    rank = {
        "fires": percentile_ranks({c: per_km2(r, "fires_total") for c, r in by.items()}),
        "burnt": percentile_ranks({c: per_km2(r, "burnt_ha", 100) for c, r in by.items()}),
        "age65": percentile_ranks({c: r.get("age_65_plus_share") for c, r in by.items()}),
        "non_main": percentile_ranks({c: r.get("non_main_share") for c, r in by.items()}),
        "single": percentile_ranks({c: r.get("single_dwelling_building_share") for c, r in by.items()}),
    }
    rows = []
    for code, r in by.items():
        high = r.get("high_share")
        own = {k: v[code] for k, v in rank.items()}
        comps: dict[str, float | None] = {
            "territory": high,
            "history": _mean(own["fires"], own["burnt"]),
            "residential": _mean(own["age65"], own["non_main"], own["single"]),
            "planning": None if high is None else (0.0 if r.get("plan_approved") is True else high),
        }
        score = weighted_score(comps, WEIGHTS)
        rows.append({
            **{k: v for k, v in r.items() if k != "area_km2"},
            "components": {k: None if v is None else round(v, 4) for k, v in comps.items()},
            "score": None if score is None else round(score, 1),
            "band": band_for(score),
            "reasons": _reasons(r, comps, own, WEIGHTS),
        })
    rows.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0), x["ine_code"]))
    stable = _stability(rows)
    for i, row in enumerate(rows, 1):
        row["rank"] = i if row["score"] is not None else None
        row["stability_top20"] = stable.get(row["ine_code"])
    return rows


def gap_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Cruce entre riesgo oficial, Zonas de Alto Riesgo y planes municipales (recuentos reproducibles)."""
    high = [r for r in rows if r.get("high_share") is not None and r["high_share"] > 0.5]
    outside = [r for r in high if r.get("zar") is False]
    required = [r for r in rows if r.get("plan_required") is True]
    return {
        "municipalities": len(rows),
        "high_majority": len(high),
        "high_majority_in_zar": sum(r.get("zar") is True for r in high),
        "high_majority_outside_zar": len(outside),
        "outside_zar_required_plan": sum(r.get("plan_required") is True for r in outside),
        "outside_zar_population": sum(r.get("population_total") or 0 for r in outside),
        "outside_zar_codes": [r["ine_code"] for r in sorted(outside, key=lambda x: -x["high_share"])],
        "plan_required": len(required),
        "plan_required_approved": sum(r.get("plan_approved") is True for r in required),
        "plan_required_not_approved": sum(r.get("plan_approved") is False for r in required),
        "plan_required_blank": sum(r.get("plan_approved") is None for r in required),
    }
