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

## 2 bis. Instalación limpia siguiendo solo el README (T11, 11/11/2026)

Clon nuevo de `github.com/Lorenadata/escudo-madrid-incendios` (commit `203ec34` + corrección de migración), entorno Python nuevo y base de datos vacía (proyecto Docker aparte), en Windows 11 con Git Bash.

| Paso del README | Tiempo | Resultado |
|---|---:|---|
| `git clone` | 3 s | ok |
| `pip install -e ".[dev]"` | 5 min 13 s | ok |
| `docker compose … up -d db` | 9 s | ok |
| `alembic upgrade head` | 18 s | **falló** en la primera prueba: índice espacial duplicado en la migración de EFFIS (GeoAlchemy2 ya lo crea con la tabla). Corregido; tras la corrección, ok y `alembic check` sin diferencias |
| `escudo_api.etl_load` | 30 s | 179 municipios, 73 perímetros EFFIS, 18/18 fuentes |
| `pytest` | 37 s | 128 superados, 1 omitido (necesita el PDF original del BOCM, no incluido en la instalación rápida) |
| `npm ci` + `npm run build` | 1 min 46 s + 25 s | ok |
| API + web + Playwright | 2 min 29 s | **30/30** (flujos, accesibilidad, modo sin conexión) |

Total: unos 9 minutos desde cero hasta la plataforma funcionando y verificada. El fallo encontrado habría impedido arrancar el despliegue público, que siempre parte de una base vacía.

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
