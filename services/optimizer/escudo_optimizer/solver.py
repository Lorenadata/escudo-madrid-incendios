"""Optimizador presupuestario determinista (PRD §5.3) con OR-Tools CP-SAT.

max Σ w_i x_i   con w_i = p_i · b_i
s.a. Σ c_i x_i ≤ B                     (c_i, B en céntimos enteros)
     x_i ≤ x_j       ∀ j ∈ requires(i)  (precedencia)
     x_i + x_j ≤ 1   ∀ j ∈ excludes(i)  (exclusión, simétrica)
     x_i = 0         si no elegible
     x_i = 1         si obligatoria
Desempate lexicográfico: (1) máximo objetivo, (2) mínimo coste, (3) mínimo Σ índice(option_id).
"""

from __future__ import annotations

import ortools
from ortools.sat.python import cp_model

from .models import (
    COST_STRESS_MULTIPLIER,
    OptionInput,
    ScenarioResult,
    SensitivityPoint,
    SolveRequest,
    SolveStatus,
    StrategyResult,
)

WEIGHT_SCALE = 1000  # w_i se escala a entero: round(p_i · b_i · 1000)


def _scaled_weight(o: OptionInput) -> int:
    return int(round(o.weight * WEIGHT_SCALE))


def _sorted(options: list[OptionInput]) -> list[OptionInput]:
    return sorted(options, key=lambda o: o.option_id)


def _exclusion_pairs(options: list[OptionInput]) -> set[frozenset[str]]:
    pairs: set[frozenset[str]] = set()
    for o in options:
        for e in o.excludes:
            pairs.add(frozenset((o.option_id, e)))
    return pairs


def _summarize(
    strategy: str, chosen: set[str], options: list[OptionInput], feasible: bool
) -> StrategyResult:
    opts = _sorted(options)
    sel = [o for o in opts if o.option_id in chosen]
    eligible_weight = sum(o.weight for o in opts if o.eligible)
    obj = sum(o.weight for o in sel)
    return StrategyResult(
        strategy=strategy,  # type: ignore[arg-type]
        feasible=feasible,
        selected=[o.measure_code for o in sel],
        selected_option_ids=[o.option_id for o in sel],
        total_cost_eur=round(sum(o.cost_cents for o in sel) / 100, 2),
        objective_value=round(obj, 6),
        priority_coverage_share=round(obj / eligible_weight, 6) if eligible_weight > 0 else 0.0,
    )


# ---------------------------------------------------------------- CP-SAT

def _cp_sat(
    options: list[OptionInput], budget_cents: int, time_limit_s: float
) -> tuple[SolveStatus, set[str]]:
    opts = _sorted(options)
    by_id = {o.option_id: o for o in opts}

    def build() -> tuple[cp_model.CpModel, dict[str, cp_model.IntVar]]:
        m = cp_model.CpModel()
        x = {o.option_id: m.NewBoolVar(f"x_{k}") for k, o in enumerate(opts)}
        m.Add(sum(o.cost_cents * x[o.option_id] for o in opts) <= budget_cents)
        for o in opts:
            if not o.eligible:
                m.Add(x[o.option_id] == 0)
            if o.mandatory:
                m.Add(x[o.option_id] == 1)
            for r in o.requires:
                m.AddImplication(x[o.option_id], x[r])
        for pair in _exclusion_pairs(opts):
            a, b = sorted(pair)
            m.AddBoolOr([x[a].Not(), x[b].Not()])
        return m, x

    def run(m: cp_model.CpModel) -> tuple[int, cp_model.CpSolver]:
        s = cp_model.CpSolver()
        s.parameters.num_workers = 1
        s.parameters.random_seed = 0
        s.parameters.max_time_in_seconds = time_limit_s
        return s.Solve(m), s

    weight = {o.option_id: _scaled_weight(o) for o in opts}

    # Fase 1: máximo objetivo
    m, x = build()
    obj_expr = sum(weight[i] * x[i] for i in x)
    m.Maximize(obj_expr)
    st, s = run(m)
    if st == cp_model.INFEASIBLE or st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return "INFEASIBLE", set()
    proven = st == cp_model.OPTIMAL
    best_obj = int(round(s.ObjectiveValue()))

    # Fase 2 (lexicográfica exacta): con el objetivo fijado, minimizar coste·M + Σ índice(option_id),
    # donde M > Σ índices posibles, de modo que el coste domina y el índice solo desempata.
    m, x = build()
    m.Add(sum(weight[i] * x[i] for i in x) >= best_obj)
    big_m = len(opts) * (len(opts) + 1) // 2 + 1
    m.Minimize(
        sum(by_id[o.option_id].cost_cents * big_m * x[o.option_id] for o in opts)
        + sum((k + 1) * x[o.option_id] for k, o in enumerate(opts))
    )
    st2, s2 = run(m)
    proven = proven and st2 == cp_model.OPTIMAL
    chosen = {i for i in x if s2.Value(x[i])}
    return ("OPTIMAL" if proven else "FEASIBLE"), chosen


# ---------------------------------------------------------------- Baselines voraces

def _closure(oid: str, by_id: dict[str, OptionInput]) -> set[str]:
    """Opción + todas sus precedencias (transitivas)."""
    out: set[str] = set()
    stack = [oid]
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(by_id[cur].requires)
    return out


def _try_add(
    group: set[str], chosen: set[str], by_id: dict[str, OptionInput],
    excl: set[frozenset[str]], budget_cents: int,
) -> bool:
    new = group - chosen
    if not new:
        return True
    if any(not by_id[i].eligible for i in new):
        return False
    union = chosen | new
    for i in new:
        for j in union:
            if i != j and frozenset((i, j)) in excl:
                return False
    if sum(by_id[i].cost_cents for i in union) > budget_cents:
        return False
    chosen |= new
    return True


def _greedy(
    options: list[OptionInput], budget_cents: int, order: list[OptionInput]
) -> tuple[bool, set[str]]:
    by_id = {o.option_id: o for o in options}
    excl = _exclusion_pairs(options)
    chosen: set[str] = set()
    for o in _sorted(options):
        if o.mandatory and not _try_add(_closure(o.option_id, by_id), chosen, by_id, excl, budget_cents):
            return False, set()
    for o in order:
        if o.option_id in chosen or not o.eligible:
            continue
        _try_add(_closure(o.option_id, by_id), chosen, by_id, excl, budget_cents)
    return True, chosen


def manual_order(options: list[OptionInput]) -> list[OptionInput]:
    """Orden manual: manual_rank asc si existe; si no, prioridad técnica desc; desempate option_id."""
    big = 10**9
    return sorted(
        options,
        key=lambda o: (o.manual_rank if o.manual_rank is not None else big, -o.technical_priority, o.option_id),
    )


def cheapest_order(options: list[OptionInput]) -> list[OptionInput]:
    return sorted(options, key=lambda o: (o.cost_cents, o.option_id))


# ---------------------------------------------------------------- API pública

def _with_cost_multiplier(options: list[OptionInput], mult: float) -> list[OptionInput]:
    return [o.model_copy(update={"unit_cost_eur": o.unit_cost_eur * mult}) for o in options]


def solve(request: SolveRequest) -> ScenarioResult:
    options = list(request.options)
    budget_cents = request.budget_cents
    version = ortools.__version__

    status, chosen = _cp_sat(options, budget_cents, request.time_limit_s)
    if status == "INFEASIBLE":
        mandatory = [o.option_id for o in _sorted(options) if o.mandatory]
        return ScenarioResult(
            solver_version=version,
            status="INFEASIBLE",
            budget_eur=request.budget_eur,
            is_demo_budget=request.is_demo_budget,
            strategies=[],
            sensitivity=[],
            message=(
                "No existe selección que cumpla las restricciones: las actuaciones obligatorias "
                f"{mandatory} (con sus precedencias) no caben en el presupuesto o son incompatibles/no elegibles."
            ),
        )

    m_ok, m_sel = _greedy(options, budget_cents, manual_order(options))
    c_ok, c_sel = _greedy(options, budget_cents, cheapest_order(options))
    strategies = [
        _summarize("manual", m_sel, options, m_ok),
        _summarize("cheapest_first", c_sel, options, c_ok),
        _summarize("optimized", chosen, options, True),
    ]

    sensitivity: list[SensitivityPoint] = []
    scenarios = [(f"presupuesto ×{f:g}", request.budget_eur * f, 1.0) for f in request.sensitivity_steps]
    scenarios.append((f"costes ×{COST_STRESS_MULTIPLIER:g}", request.budget_eur, COST_STRESS_MULTIPLIER))
    for label, budget, mult in scenarios:
        opts = _with_cost_multiplier(options, mult) if mult != 1.0 else options
        st, sel = _cp_sat(opts, int(round(budget * 100)), request.time_limit_s)
        summ = _summarize("optimized", sel, opts, st != "INFEASIBLE")
        sensitivity.append(
            SensitivityPoint(
                label=label,
                budget_eur=round(budget, 2),
                cost_multiplier=mult,
                status=st,
                objective_value=summ.objective_value,
                total_cost_eur=summ.total_cost_eur,
                selected_option_ids=summ.selected_option_ids,
            )
        )

    return ScenarioResult(
        solver_version=version,
        status=status,
        budget_eur=request.budget_eur,
        is_demo_budget=request.is_demo_budget,
        strategies=strategies,
        sensitivity=sensitivity,
        message=None if m_ok and c_ok else "Alguna estrategia base no pudo incluir las obligatorias.",
    )
