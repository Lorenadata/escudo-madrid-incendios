"""ROADMAP 3.1: los materiales del experimento puntúan igual que el optimizador y los casos A/B son equivalentes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("validation_materials", ROOT / "scripts" / "validation_materials.py")
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)


@pytest.mark.parametrize("case", ["A", "B"])
def test_score_matches_optimizer_for_every_strategy(case):
    _, _, scen, catalog = vm.load_case(case)
    res = vm.solve_case(scen, catalog)
    for s in res["strategies"]:
        sc = vm.score(case, s["selected"])
        assert sc["priority_coverage_share"] == pytest.approx(s["priority_coverage_share"], abs=1e-4)
        assert sc["within_budget"] and not sc["constraint_violations"]


def test_cases_are_structurally_equivalent():
    a = vm.load_case("A")[2]
    b = vm.load_case("B")[2]
    assert sorted(o["measure_code"] for o in a["options"]) == sorted(o["measure_code"] for o in b["options"])
    ratio = [s["budget_eur"] / sum(o["quantity"] * o["unit_cost_eur"] for o in s["options"]) for s in (a, b)]
    assert abs(ratio[0] - ratio[1]) < 0.02
    assert a.get("solve") is False and b.get("solve") is False  # borradores: los resuelve el participante


def test_score_flags_budget_and_constraints():
    allc = [o["measure_code"] for o in vm.load_case("A")[2]["options"]]
    sc = vm.score("A", allc + ["NO-EXISTE"])
    assert not sc["within_budget"] and sc["unknown_codes"] == ["NO-EXISTE"]


def test_participant_sheet_has_no_solution_and_is_labeled_fictitious():
    for case in ("A", "B"):
        sheet = vm.participant_sheet(case)
        assert "FICTICIOS" in sheet and "optimized" not in sheet and "Cobertura" not in sheet
