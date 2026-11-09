# Clave del evaluador — NO entregar a participantes

Calculada con el optimizador CP-SAT de ESCUDO (determinista, 1 worker, semilla 0) y la función objetivo acordada: Σ prioridad técnica × peso de cobertura de las actuaciones seleccionadas / total posible. Es una función objetivo de planificación, **no** una reducción de riesgo.

## Caso A — Urbanización Ejemplo Los Pinos (FICTICIA, validación)

| Estrategia | Actuaciones | Coste | Cobertura de prioridad |
|---|---|---:|---:|
| manual | DELIM-PLANO, FAJA-30, HIDR-REV, PAIF-RED, PODA-GALIBO, RESTOS-TRIT, VIAL-LIMP | 29.900,00 € | 84.2% |
| cheapest_first | CUBIERTAS-LIMP, DELIM-PLANO, FAJA-30, HIDR-REV, INFO-POB, PAIF-RED, RESTOS-QUEMA, SENAL-CALLES, VIAL-LIMP | 28.560,00 € | 85.1% |
| optimized | DELIM-PLANO, FAJA-30, HIDR-REV, INFO-POB, PAIF-RED, PODA-GALIBO, RESTOS-QUEMA, SENAL-CALLES, VIAL-LIMP | 29.260,00 € | 90.1% |

**Elementos obligatorios para contar omisiones** (1 punto cada uno que falte):
- coste dentro de presupuesto;
- ninguna incompatibilidad violada y prerrequisitos incluidos;
- todas las actuaciones de prioridad 5 incluidas o su exclusión justificada;
- cada actuación con responsable;
- cada actuación con fecha límite;
- al menos una fuente oficial citada;
- previsión de evidencia de ejecución.

## Caso B — Urbanización Ejemplo Los Robles (FICTICIA, validación)

| Estrategia | Actuaciones | Coste | Cobertura de prioridad |
|---|---|---:|---:|
| manual | DELIM-PLANO, FAJA-30, HIDR-REV, PAIF-RED, PODA-GALIBO, RESTOS-TRIT, SENAL-CALLES, VIAL-LIMP | 29.870,00 € | 86.5% |
| cheapest_first | CUBIERTAS-LIMP, DELIM-PLANO, FAJA-30, HIDR-REV, INFO-POB, PAIF-RED, RESTOS-QUEMA, SENAL-CALLES, VIAL-LIMP | 28.250,00 € | 82.7% |
| optimized | DELIM-PLANO, FAJA-30, HIDR-REV, INFO-POB, PAIF-RED, PODA-GALIBO, RESTOS-QUEMA, SENAL-CALLES, VIAL-LIMP | 28.850,00 € | 90.4% |

**Elementos obligatorios para contar omisiones** (1 punto cada uno que falte):
- coste dentro de presupuesto;
- ninguna incompatibilidad violada y prerrequisitos incluidos;
- todas las actuaciones de prioridad 5 incluidas o su exclusión justificada;
- cada actuación con responsable;
- cada actuación con fecha límite;
- al menos una fuente oficial citada;
- previsión de evidencia de ejecución.

Puntuar una selección: `python scripts/validation_materials.py score A CÓDIGO1,CÓDIGO2,…`
