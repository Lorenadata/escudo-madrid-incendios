# Método del optimizador presupuestario (M08) — PRD §5.3

Dueño: A5. Código: `services/optimizer/escudo_optimizer/`. Tests: `tests/unit/test_optimizer.py` (T06, T07).

## 1. Qué resuelve

Dada una lista de actuaciones preventivas candidatas para un ámbito (propuestas y revisadas por personal técnico) y un presupuesto `B`, selecciona el subconjunto que maximiza una **función objetivo acordada** respetando todas las restricciones. **No estima reducción del riesgo de incendio, incendios evitados ni daños evitados.**

## 2. Formulación

Para cada opción `i`: coste `c_i = quantity_i × unit_cost_eur_i` (en céntimos enteros), prioridad técnica `p_i ∈ {1..5}`, peso de cobertura `b_i > 0`, `x_i ∈ {0,1}`.

```
max   Σ_i (p_i · b_i) · x_i
s.a.  Σ_i c_i · x_i ≤ B
      x_i ≤ x_j            ∀ j ∈ requires(i)        (precedencia, transitiva por encadenamiento)
      x_i + x_j ≤ 1        ∀ j ∈ excludes(i)        (incompatibilidad; simétrica)
      x_i = 0              si eligible_i = false
      x_i = 1              si mandatory_i = true
```

- Pesos escalados a enteros: `w_i = round(p_i · b_i · 1000)` (CP-SAT trabaja con enteros). Costes en céntimos.
- **Desempate lexicográfico determinista**: (1) máximo `Σ w_i x_i`; (2) con ese objetivo fijado, mínimo `coste·M + Σ índice(option_id)` con `M > n(n+1)/2`, de modo que domina el coste y el orden alfabético de `option_id` solo rompe empates exactos.
- Solver: OR-Tools CP-SAT, `num_workers=1`, `random_seed=0`, `max_time_in_seconds` configurable (10 s por defecto). Si no prueba optimalidad en ese tiempo, devuelve `FEASIBLE` (nunca se presenta como óptimo).
- `INFEASIBLE` cuando las obligatorias (con sus precedencias) no caben en `B`, son incompatibles entre sí o no son elegibles; se devuelve mensaje explicativo y ninguna selección.

## 3. Estrategias comparadas (T07)

| Estrategia | Regla |
|---|---|
| `manual` | Voraz en orden `manual_rank` asc (si no hay, prioridad técnica desc; desempate `option_id`). Representa la priorización base del técnico. |
| `cheapest_first` | Voraz por coste ascendente. |
| `optimized` | CP-SAT según §2. |

Los voraces primero incluyen las obligatorias; al considerar una opción añaden también sus precedencias pendientes como bloque, solo si el bloque completo cabe, es elegible y no viola exclusiones.

Métrica común `priority_coverage_share = Σ w_i seleccionadas / Σ w_i elegibles` ∈ [0,1]: cobertura de la prioridad técnica ponderada, **no** cobertura de riesgo.

## 4. Sensibilidad

Se re-optimiza con presupuesto × {0,5; 0,75; 0,9; 1,1; 1,25; 1,5} (configurable con `sensitivity_steps`) y con todos los costes × 1,2 al presupuesto base. Cada punto devuelve estado, objetivo, coste y selección.

## 5. Supuestos y límites

- `p_i` y `b_i` los asigna personal técnico; el sistema no los infiere. Si `b_i` carece de fundamento se usa `b_i = 1` (optimiza cobertura de tareas prioritarias).
- Costes: de referencia, presupuesto del usuario o escenario; el estado del coste (`cost_status`) lo gestiona A6/M07 y debe mostrarse junto al resultado.
- `is_demo_budget` se propaga al resultado para que UI e informe lo etiqueten.
- No modela plazos ni recursos humanos todavía (P1): se añadirían como restricciones lineales adicionales.

## 6. Validación ejecutada

`tests/unit/test_optimizer.py` (13 tests):
- Casos pequeños resueltos a mano (knapsack, desempate, precedencia, exclusión, obligatorias, no elegibles).
- 200 instancias aleatorias (semilla 20261126, n ≤ 12, con precedencias, exclusiones, obligatorias y no elegibles) comparadas con fuerza bruta exhaustiva aplicando el mismo orden lexicográfico: la selección óptima coincide exactamente; todas las estrategias factibles respetan presupuesto y restricciones; `optimized ≥ manual, cheapest_first` en objetivo; infactibilidad detectada correctamente.
- Reproducibilidad: dos ejecuciones idénticas byte a byte (`model_dump`).
- Presupuesto 0, lista vacía, referencias inválidas, sensibilidad monótona y textos de advertencia.
