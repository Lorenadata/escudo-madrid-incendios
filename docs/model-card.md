# Model card — Optimizador presupuestario ESCUDO MADRID

| Campo | Valor |
|---|---|
| Nombre | `escudo_optimizer` (M08) |
| Tipo | Programación entera binaria (knapsack con restricciones lógicas), OR-Tools CP-SAT. **No es un modelo de aprendizaje automático** ni usa datos de entrenamiento. |
| Versión | 0.1.0 (06/11/2026) |
| Dueño | Agente A5; validación humana pendiente (líder de producto + técnico competente) |
| Método | `docs/optimizer-method.md` |

## Uso previsto
Apoyar a gestores de urbanización, técnicos y responsables municipales a **comparar alternativas de selección de actuaciones preventivas** bajo un presupuesto, con criterios transparentes y editables, y documentar la decisión.

## Usos fuera de alcance
- Dirección de emergencias, tácticas de extinción o evacuación.
- Aprobación de PAIF/PAMIF o certificación de cumplimiento normativo.
- Estimar probabilidad de incendio, daños o reducción del riesgo.
- Adjudicar contratos o presentar presupuestos de demostración como reales.

## Entradas
Opciones con coste, prioridad técnica (1–5), peso de cobertura, elegibilidad, obligatoriedad, precedencias y exclusiones; presupuesto; marca `is_demo_budget`. Las prioridades/pesos son juicios técnicos, no datos oficiales.

## Salidas
Selección por estrategia (`manual`, `cheapest_first`, `optimized`), coste total, valor objetivo, `priority_coverage_share`, análisis de sensibilidad, estado (`OPTIMAL`/`FEASIBLE`/`INFEASIBLE`), definición del objetivo y advertencia.

## Propiedades garantizadas (verificadas por tests)
Presupuesto nunca excedido; restricciones inviolables; determinismo (1 worker, semilla 0, desempate lexicográfico); óptimo exacto en instancias pequeñas frente a fuerza bruta; optimized ≥ baselines.

## Limitaciones
- La calidad del resultado depende enteramente de prioridades, pesos y costes introducidos.
- Sin plazos, recursos ni efectos acumulativos entre actuaciones (P1).
- Para instancias grandes con límite de tiempo puede devolver `FEASIBLE` (no óptimo probado), lo cual se indica.

## KPIs permitidos
Coste total vs. presupuesto; nº y % de actuaciones priorizadas cubiertas; `priority_coverage_share` frente a baselines; diferencia de cobertura ponderada entre estrategias; reproducibilidad de escenarios; tiempo de cálculo.

## KPIs NO permitidos
«Incendios evitados», «vidas salvadas», «reducción del riesgo X %», «hectáreas protegidas efectivamente», «ahorro público real». El incremento de `priority_coverage_share` **no** equivale a reducción del riesgo.

## Consideraciones éticas
Las salidas son recomendaciones de planificación sujetas a revisión técnica; se muestran siempre con fuentes de coste, estado del presupuesto y advertencia.
