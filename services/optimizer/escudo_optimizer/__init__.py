"""ESCUDO MADRID — optimizador presupuestario determinista (CP-SAT)."""

from .models import (
    DISCLAIMER,
    OBJECTIVE_DEFINITION,
    OptionInput,
    ScenarioResult,
    SensitivityPoint,
    SolveRequest,
    StrategyResult,
)
from .solver import solve

__all__ = [
    "DISCLAIMER",
    "OBJECTIVE_DEFINITION",
    "OptionInput",
    "ScenarioResult",
    "SensitivityPoint",
    "SolveRequest",
    "StrategyResult",
    "solve",
]
