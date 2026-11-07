# PROGRESS — Estado real de ESCUDO MADRID

Actualizado: 06/11/2026 (A0). Solo se marca ✅ lo verificado con test o ejecución real.

## Módulos implementados

| Módulo | Estado | Evidencia | Agente |
|---|---|---|---|
| Pipeline Portal CAM (8 datasets, SHA-256, licencia, calidad) | ✅ | `pipelines/tests/test_cam.py` (11 ✔), `quality.json` 8/8 | A2 (A0) |
| Cartografía oficial IDEM GEO-01/02/03 (ráster 5 m → reparto municipal + capa web) | ✅ | `pipelines/tests/test_idem.py` (15 ✔) | A3 |
| Conector AEMET (XML público, OpenData con clave, TTL, stale/unavailable) | ✅ | `pipelines/tests/test_aemet.py` (14 ✔, incl. red) | A4 |
| Optimizador CP-SAT + baselines + sensibilidad | ✅ | `tests/unit/test_optimizer.py` (13 ✔, fuerza bruta 200 instancias) | A5 |
| Esquema PostGIS (28 tablas, PRD §6.3) + migración Alembic verificada (upgrade/check/downgrade) + cargador idempotente + seed ficticio | ✅ | `alembic upgrade head`, `python -m escudo_api.etl_load` | A6 (A0) |
| API FastAPI (37 rutas): fuentes, municipios, comparador, capas, meteo, histórico, auth, áreas, inspecciones, evidencias, revisión técnica, medidas, escenarios, planes, informe PDF, KPIs, auditoría, export CSV, demo guiada | ✅ | `tests/integration/test_api.py` (12 ✔) | A6 (A0) |
| Análisis municipal: matriz CAM-01/02 × GEO-01/02/03 (filtros y orden reproducibles, sin índice propio) | ✅ | `test_municipal_matrix_is_reproducible_filter`, e2e | A0 |
| Flujo B: panel municipal con ámbitos compartidos por autorización expresa, expediente de solo lectura e informe | ✅ | integración + e2e + `artifacts/demo-screenshots/07-panel-municipal.png` | A0 |
| M05: dibujo o pegado GeoJSON del perímetro del ámbito; clases oficiales dentro del ámbito como «derivado» (capa 200 m) | ✅ | e2e «M05» | A0 |
| Revisión técnica desde la UI (bloqueada sin cualificación verificada) | ✅ | e2e «revisión técnica» | A7/A0 |
| Flujo A completo en la UI cronometrado (≈6–12 s automatizado; objetivo < 3 min en vivo) | ✅ | `apps/web/e2e/flujo-a-gestor.spec.ts` | A0 |
| Demo en un comando con calentamiento, cuentas y plan B | ✅ | `scripts/demo.sh` (start/stop/check) | A10 (A0) |
| Informe PDF trazable (T09) | ✅ | `test_T09_report_text` | A6 (A0) |
| Catálogo de 16 medidas con citas INFOMA verificadas (costes `null`/escenario) | ✅ (revisión técnica humana pendiente) | `data/reference/measures_catalog.json` | A1 |
| COMPLIANCE (25 normas), COMPETITORS | ✅ | ficheros raíz | A1 |
| Contrato OpenAPI exportado | ✅ | `packages/contracts/openapi.json` | A0 |
| Docker Compose (db) | ✅ db · 🟡 perfil `full` (api/web) sin construir | `infra/docker-compose.yml` | A10 (A0) |
| CI GitHub Actions | ✅ verde en GitHub (python 1m14s, web 1m03s; run 42368698348) | `.github/workflows/ci.yml` | A10 (A0) |

| Web Next.js 16 + MapLibre: explorador (coropletas CAM-01/02/03, capas oficiales GEO-01/02/03 con leyenda literal, mapa base IGN), ficha municipal con series 2021–2025 y AEMET, comparador, fuentes con SHA-256 y CSV, caso guiado público, login y área de trabajo (áreas, inspecciones, escenarios, plan, KPIs) | ✅ lint + tipos + build; verificado en navegador contra la API real (capturas en `artifacts/demo-screenshots/`) | A7 (verificación A0) |

## En desarrollo

| Módulo | Agente | Nota |
|---|---|---|
| Diseño final de las 3+1 diapositivas | A11 | contenido en `docs/pitch/slides.md`; faltan integrantes y enlaces publicados |

## Pruebas ejecutadas (06/11/2026)

`pytest -m "not network"`: **62 passed** antes de añadir 2 tests nuevos; integración posterior **12/12 passed**; `ruff check` limpio. Pruebas PRD cubiertas: T01, T02, T03, T04, T05, T06, T07, T08, T09. Después: **65 passed** (`pytest -m "not network"`) y **10 passed** Playwright (`npm run e2e`, T10). Pendientes: T11 (instalación limpia en máquina ajena), T12 (entrega).

## Bloqueos y decisiones humanas

1. **Periodo oficial**: el repo se inició el 06/11 (antes del 07/11). Declarado en `PROVENANCE.md`; valorar consulta a la organización.
2. **Asistencia** (bases vs web): escribir a madrid.datamad@urjc.es (C22 en `COMPLIANCE.md`).
3. **Clave AEMET OpenData** (gratuita, registro con email): necesaria para el mapa oficial de peligro de incendios. Sin ella funciona la predicción municipal pública.
4. **Licencia del código**: propuesta EUPL-1.2 (ADR-0004), confirmar.
5. **Repositorio público**: ✅ https://github.com/Lorenadata/escudo-madrid-incendios (EUPL-1.2, 07/11/2026). **Despliegue de la demo**: no realizado (requiere autorización).
6. **Validación profesional y experimento de utilidad**: requieren personas (criterio de impacto).
7. **Costes reales** de medidas: no hay base de precios pública aplicable; hacen falta presupuestos reales o se mantienen como escenario.
8. Web oficial DATAMAD generada con JS: verificar en navegador límite de palabras y preselección.

## Riesgos DATAMAD

| Riesgo | Mitigación |
|---|---|
| UI no terminada a tiempo | A7 en curso; API ya completa; demo pública `/v1/demo/guided` |
| Impacto sin evidencia con usuarios | Planificar ensayo interno cronometrado (G6) y comunicarlo honestamente |
| Inestabilidad de PostGIS en Docker Desktop (reinicios de backend observados) | `shm_size: 512mb` aplicado; sin recurrencia tras el cambio; vigilar |
| Fallo intermitente observado una vez: en el primer test e2e tras arrancar los servidores, el navegador no conectó con la API. Causa **no confirmada**; no se reprodujo en 3 arranques en frío seguidos sin calentamiento (30/30 e2e) | Calentamiento en `scripts/demo.sh` + reintento único de lecturas GET ante fallo de red en la web; vigilar |
| Dependencia de servicios externos en la demo | Datos cargados localmente; AEMET degrada a `unavailable` |

## Próximas tareas

1. Integrar y verificar la web (A7) contra la API; capturas para el pitch.
2. Calendario preventivo (M16, P1) y colaboración (M17, P1).
3. Instalación limpia en otra máquina (T11). Imágenes Docker de API y web ya construidas y probadas.
4. A11: ensayo cronometrado del guion y diseño de las diapositivas (contenido, guion y resumen de 93 palabras ya listos).
5. P1: calendario preventivo, colaboración, asistente documental con citas.
