"""T06 (solver) y T07 (comparación con baselines) — PRD §9.2.

Todos los datos de este fichero son instancias sintéticas de prueba, no presupuestos reales.
"""

from __future__ import annotations

import itertools
import random

import pytest
from pydantic import ValidationError

from escudo_optimizer import OptionInput, SolveRequest, solve
from escudo_optimizer.solver import WEIGHT_SCALE


def opt(oid, cost, p=3, b=1.0, **kw) -> OptionInput:
    return OptionInput(
        option_id=oid, measure_code=f"M-{oid}", quantity=1, unit_cost_eur=cost,
        technical_priority=p, coverage_weight=b, **kw,
    )


def strat(res, name):
    return next(s for s in res.strategies if s.strategy == name)


def check_constraints(sel: set[str], options: list[OptionInput], budget: float) -> None:
    by_id = {o.option_id: o for o in options}
    assert sum(by_id[i].cost_cents for i in sel) <= round(budget * 100)
    for o in options:
        if o.mandatory:
            assert o.option_id in sel
        if not o.eligible:
            assert o.option_id not in sel
        if o.option_id in sel:
            assert set(o.requires) <= sel
            assert not (set(o.excludes) & sel)


# ---------------------------------------------------------- casos resueltos a mano

def test_hand_solved_knapsack():
    # A: 600 €, w=5·1=5 ; B: 500 €, w=4·1=4 ; C: 500 €, w=3·1=3 ; budget 1000
    # Factibles con 2 elementos: {B,C} w=7 (1000 €). {A,B} cuesta 1100 > 1000. Óptimo = {B,C}.
    options = [opt("A", 600, p=5), opt("B", 500, p=4), opt("C", 500, p=3)]
    res = solve(SolveRequest(budget_eur=1000, options=options))
    o = strat(res, "optimized")
    assert res.status == "OPTIMAL"
    assert o.selected_option_ids == ["B", "C"]
    assert o.total_cost_eur == 1000
    assert o.objective_value == pytest.approx(7)
    # manual (prioridad desc): A primero (600), luego B no cabe, C no cabe → {A} w=5
    assert strat(res, "manual").selected_option_ids == ["A"]
    # cheapest_first: B (500), C (500) → {B,C}
    assert strat(res, "cheapest_first").selected_option_ids == ["B", "C"]
    assert o.priority_coverage_share == pytest.approx(7 / 12)


def test_tie_break_prefers_lower_cost_then_id():
    # A y B misma ponderación; B más barata → se elige B
    res = solve(SolveRequest(budget_eur=100, options=[opt("A", 90, p=3), opt("B", 80, p=3)]))
    assert strat(res, "optimized").selected_option_ids == ["B"]
    # Mismo coste y ponderación → menor option_id
    res = solve(SolveRequest(budget_eur=100, options=[opt("Z", 80), opt("Y", 80)]))
    assert strat(res, "optimized").selected_option_ids == ["Y"]


def test_precedence_respected():
    # C requiere A. C es muy valiosa pero solo junto con A.
    options = [opt("A", 400, p=1), opt("B", 500, p=3), opt("C", 500, p=5, requires=["A"])]
    res = solve(SolveRequest(budget_eur=900, options=options))
    o = strat(res, "optimized")
    # {A,C} w=6 cost 900 ; {B} w=3 ; {A,B} w=4 → óptimo {A,C}
    assert o.selected_option_ids == ["A", "C"]
    for s in res.strategies:
        check_constraints(set(s.selected_option_ids), options, 900)


def test_exclusion_respected():
    options = [opt("A", 100, p=5, excludes=["B"]), opt("B", 100, p=4), opt("C", 100, p=1)]
    res = solve(SolveRequest(budget_eur=1000, options=options))
    o = strat(res, "optimized")
    assert o.selected_option_ids == ["A", "C"]
    for s in res.strategies:
        check_constraints(set(s.selected_option_ids), options, 1000)


def test_mandatory_and_ineligible():
    options = [opt("A", 300, p=1, mandatory=True), opt("B", 300, p=5, eligible=False), opt("C", 300, p=4)]
    res = solve(SolveRequest(budget_eur=600, options=options))
    for s in res.strategies:
        assert s.feasible
        assert s.selected_option_ids == ["A", "C"]
    # La cobertura se mide sobre las elegibles (A, C)
    assert strat(res, "optimized").priority_coverage_share == pytest.approx(1.0)


def test_infeasible_when_mandatory_does_not_fit():
    options = [opt("A", 700, mandatory=True), opt("B", 500, mandatory=True)]
    res = solve(SolveRequest(budget_eur=1000, options=options))
    assert res.status == "INFEASIBLE"
    assert res.strategies == []
    assert "obligatorias" in (res.message or "")


def test_infeasible_when_mandatory_ineligible():
    res = solve(SolveRequest(budget_eur=1000, options=[opt("A", 10, mandatory=True, eligible=False)]))
    assert res.status == "INFEASIBLE"


def test_zero_budget():
    res = solve(SolveRequest(budget_eur=0, options=[opt("A", 10), opt("B", 0.0, p=2)]))
    assert res.status == "OPTIMAL"
    for s in res.strategies:
        assert s.total_cost_eur == 0
        assert s.selected_option_ids == ["B"]  # coste 0 sí cabe


def test_empty_options():
    res = solve(SolveRequest(budget_eur=100, options=[]))
    assert res.status == "OPTIMAL"
    assert strat(res, "optimized").selected_option_ids == []
    assert strat(res, "optimized").priority_coverage_share == 0.0


def test_invalid_references_rejected():
    with pytest.raises(ValidationError):
        SolveRequest(budget_eur=10, options=[opt("A", 1, requires=["X"])])
    with pytest.raises(ValidationError):
        SolveRequest(budget_eur=10, options=[opt("A", 1), opt("A", 2)])
    with pytest.raises(ValidationError):
        opt("A", 1, p=6)


def test_reproducible():
    rng = random.Random(7)
    options = [opt(f"O{i:02d}", rng.randint(50, 900), p=rng.randint(1, 5), b=rng.choice([0.5, 1, 2]))
               for i in range(25)]
    req = SolveRequest(budget_eur=4000, options=options)
    a, b = solve(req), solve(req)
    assert a.model_dump() == b.model_dump()
    assert a.deterministic is True


def test_sensitivity_and_disclaimers():
    options = [opt("A", 600, p=5), opt("B", 500, p=4), opt("C", 500, p=3)]
    res = solve(SolveRequest(budget_eur=1000, options=options, is_demo_budget=True))
    labels = [p.label for p in res.sensitivity]
    assert len(res.sensitivity) == 7
    assert labels[-1].startswith("costes ×1.2")
    for p in res.sensitivity:
        assert p.total_cost_eur <= p.budget_eur + 1e-9
    # Monotonía: más presupuesto nunca reduce el objetivo
    budget_pts = sorted((p for p in res.sensitivity if p.cost_multiplier == 1.0), key=lambda p: p.budget_eur)
    vals = [p.objective_value for p in budget_pts]
    assert vals == sorted(vals)
    assert res.is_demo_budget is True
    text = (res.objective_definition + res.disclaimer).lower()
    assert "no cuantifica reducción del riesgo" in text
    assert "incendios evitados" in text  # mencionado solo como negación


# ---------------------------------------------------------- fuerza bruta aleatoria

def brute_force(options: list[OptionInput], budget: float) -> tuple[int, int, set[str]]:
    opts = sorted(options, key=lambda o: o.option_id)
    best: tuple[int, int, int] | None = None
    best_sel: set[str] = set()
    for mask in itertools.product((0, 1), repeat=len(opts)):
        sel = {o.option_id for o, v in zip(opts, mask, strict=True) if v}
        try:
            check_constraints(sel, options, budget)
        except AssertionError:
            continue
        w = sum(int(round(o.weight * WEIGHT_SCALE)) for o in opts if o.option_id in sel)
        c = sum(o.cost_cents for o in opts if o.option_id in sel)
        idx = sum(k + 1 for k, o in enumerate(opts) if o.option_id in sel)
        key = (-w, c, idx)
        if best is None or key < best:
            best, best_sel = key, sel
    if best is None:
        return -1, -1, set()
    return -best[0], best[1], best_sel


def random_instance(rng: random.Random) -> tuple[list[OptionInput], float]:
    n = rng.randint(1, 12)
    ids = [f"O{i:02d}" for i in range(n)]
    options = []
    for i, oid in enumerate(ids):
        others = [x for x in ids if x != oid]
        req = rng.sample(others, k=min(len(others), rng.choice([0, 0, 0, 1]))) if others else []
        exc_pool = [x for x in others if x not in req]
        exc = rng.sample(exc_pool, k=min(len(exc_pool), rng.choice([0, 0, 0, 1]))) if exc_pool else []
        options.append(OptionInput(
            option_id=oid, measure_code=f"M{i}", quantity=rng.choice([1, 2, 3.5]),
            unit_cost_eur=round(rng.uniform(10, 500), 2), technical_priority=rng.randint(1, 5),
            coverage_weight=rng.choice([0.5, 1.0, 1.5, 2.0]), mandatory=rng.random() < 0.08,
            eligible=rng.random() > 0.1, requires=req, excludes=exc,
        ))
    total = sum(o.cost_eur for o in options)
    budget = round(rng.uniform(0, total), 2)
    return options, budget


def test_random_vs_brute_force():
    rng = random.Random(20261126)
    n_feasible = 0
    for _ in range(200):
        options, budget = random_instance(rng)
        req = SolveRequest(budget_eur=budget, options=options, sensitivity_steps=[1.0])
        res = solve(req)
        bw, bc, bsel = brute_force(options, budget)
        if bw < 0:
            assert res.status == "INFEASIBLE"
            continue
        n_feasible += 1
        assert res.status == "OPTIMAL"
        o = strat(res, "optimized")
        assert set(o.selected_option_ids) == bsel
        for s in res.strategies:
            sel = set(s.selected_option_ids)
            if s.feasible:
                check_constraints(sel, options, budget)
                assert s.total_cost_eur <= budget + 1e-9
                assert o.objective_value >= s.objective_value - 1e-9
    assert n_feasible > 100
