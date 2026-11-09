# Informe de validación de ESCUDO MADRID

**Estado (09/11/2026): protocolo cerrado, sesiones pendientes. n = 0.** No hay todavía resultados de usuarios; no se publica ninguna cifra de impacto hasta que existan.

## 1. Validación de datos (hecha, automatizada)

| Fuente | Controles | Evidencia |
|---|---|---|
| Portal CAM (CAM-01…11) | 12/12 | `data/processed/cam/quality.json`, `pipelines/tests/test_cam.py` |
| Plan Anual 2026 (DOC-01) | 8/8; extracción cuadrada con la fila TOTALES | `data/processed/plan/quality.json`, `pipelines/tests/test_plan_anual.py` |
| EFFIS (EFF-01) | 4/4; área calculada vs publicada 0,1 % | `data/processed/effis/quality.json`, `pipelines/tests/test_effis.py` |
| IDEM (GEO-01…03) | ver `data/processed/idem/quality.json` | `pipelines/tests/test_idem*.py` |
| Actualización | 12 fuentes comprobadas contra el origen | `data/processed/refresh_log.json` |

## 2. Validación del optimizador (hecha, automatizada)

Coincide con la solución exacta (fuerza bruta) en 200 instancias aleatorias; nunca supera el presupuesto; determinista. Ver `docs/optimizer-method.md` y `tests/unit/test_optimizer.py`.

## 3. Validación con profesionales y experimento de utilidad (pendiente)

- Protocolo: `docs/validation/protocolo-experimento.md` (cerrado antes de las sesiones).
- Guion: `docs/validation/guion-entrevista.md` · Consentimiento: `docs/validation/consentimiento.md`.
- Materiales: `docs/validation/materiales/` · Registro: `docs/validation/registro-sesiones.csv`.

| Participante | Perfil | Tipo | Resultado |
|---|---|---|---|
| — | — | — | pendiente |

Si no se consiguen participantes externos antes del 20/11, se realizará un ensayo interno, declarado como tal, con su tamaño de muestra.

## 4. Límites

Los casos son ficticios y pequeños; el experimento mide planificación y documentación, no efectos sobre el riesgo de incendio. Con n muy pequeño, los resultados son exploratorios.
