"""Contratos de entrada/salida del optimizador (ver docs/contracts/api-contract.md, `ScenarioResult`)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_SENSITIVITY_STEPS: tuple[float, ...] = (0.5, 0.75, 0.9, 1.1, 1.25, 1.5)
COST_STRESS_MULTIPLIER = 1.2

OBJECTIVE_DEFINITION = (
    "Función objetivo acordada: maximizar Σ (prioridad técnica p_i × peso de cobertura b_i) de las "
    "actuaciones seleccionadas, sujeto a Σ coste_i ≤ presupuesto y a restricciones de elegibilidad, "
    "obligatoriedad, precedencia y exclusión. Desempate: menor coste total y después identificador. "
    "Mide cobertura ponderada de tareas priorizadas por técnicos; no es una estimación científica."
)

DISCLAIMER = (
    "Resultado de planificación administrativa. No cuantifica reducción del riesgo de incendio, "
    "incendios evitados ni daños evitados. Las prioridades y pesos deben ser revisados por personal "
    "técnico competente; el presupuesto puede ser de demostración y no constituye adjudicación."
)


class OptionInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    option_id: str = Field(min_length=1)
    measure_code: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit_cost_eur: float = Field(ge=0)
    technical_priority: int = Field(ge=1, le=5)
    coverage_weight: float = Field(gt=0)
    mandatory: bool = False
    eligible: bool = True
    requires: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)
    manual_rank: int | None = None

    @property
    def cost_eur(self) -> float:
        return self.quantity * self.unit_cost_eur

    @property
    def cost_cents(self) -> int:
        return int(round(self.cost_eur * 100))

    @property
    def weight(self) -> float:
        return self.technical_priority * self.coverage_weight


class SolveRequest(BaseModel):
    budget_eur: float = Field(ge=0)
    options: list[OptionInput]
    is_demo_budget: bool = True
    sensitivity_steps: list[float] = Field(default_factory=lambda: list(DEFAULT_SENSITIVITY_STEPS))
    time_limit_s: float = Field(default=10.0, gt=0)

    @field_validator("sensitivity_steps")
    @classmethod
    def _positive_steps(cls, v: list[float]) -> list[float]:
        if any(s <= 0 for s in v):
            raise ValueError("sensitivity_steps deben ser > 0")
        return v

    @model_validator(mode="after")
    def _check_references(self) -> SolveRequest:
        ids = [o.option_id for o in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("option_id duplicado")
        known = set(ids)
        for o in self.options:
            for ref in (*o.requires, *o.excludes):
                if ref not in known:
                    raise ValueError(f"{o.option_id}: referencia desconocida '{ref}'")
                if ref == o.option_id:
                    raise ValueError(f"{o.option_id}: no puede referenciarse a sí misma")
            if set(o.requires) & set(o.excludes):
                raise ValueError(f"{o.option_id}: una opción no puede requerir y excluir la misma opción")
        return self

    @property
    def budget_cents(self) -> int:
        return int(round(self.budget_eur * 100))


StrategyName = Literal["manual", "cheapest_first", "optimized"]
SolveStatus = Literal["OPTIMAL", "FEASIBLE", "INFEASIBLE"]


class StrategyResult(BaseModel):
    strategy: StrategyName
    feasible: bool
    selected: list[str]  # measure_code de cada opción seleccionada (orden de option_id)
    selected_option_ids: list[str]
    total_cost_eur: float
    objective_value: float
    priority_coverage_share: float


class SensitivityPoint(BaseModel):
    label: str
    budget_eur: float
    cost_multiplier: float
    status: SolveStatus
    objective_value: float
    total_cost_eur: float
    selected_option_ids: list[str]


class ScenarioResult(BaseModel):
    solver: Literal["cp-sat"] = "cp-sat"
    solver_version: str
    status: SolveStatus
    deterministic: bool = True
    budget_eur: float
    is_demo_budget: bool
    strategies: list[StrategyResult]
    sensitivity: list[SensitivityPoint]
    objective_definition: str = OBJECTIVE_DEFINITION
    disclaimer: str = DISCLAIMER
    message: str | None = None
