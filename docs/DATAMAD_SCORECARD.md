# DATAMAD 2026 — Scorecard de evidencias (uso interno)

> Este documento **no estima la puntuación del jurado**. Registra, por criterio de las bases (apartado 10), qué evidencia verificable existe en el repositorio y qué falta. Estado: ✅ evidencia existente y comprobable · 🟡 parcial · ⬜ pendiente.
> Última actualización: 06/11/2026 (A0).

## Criterio 1 — Uso y aprovechamiento de datos abiertos del Portal CAM (25)

| Requisito | Evidencia | Cómo verificarla | Estado |
|---|---|---|---|
| ≥1 dataset del Portal CAM usado efectivamente (admisión) | 8 datasets CAM ingeridos (CAM-01…08) con manifest y SHA-256 | `DATA_CATALOG.md`; `GET /v1/sources`; `pipelines/tests/test_cam.py::test_T01…` | ✅ |
| Función analítica (a): ficha municipal demográfica con año y unidades | `/v1/municipalities/{ine}/profile` (CAM-01/02/03/08) con `Indicator` trazable | `tests/integration/test_api.py::test_profile_values_trace_to_processed_cam_data` | ✅ API · ✅ UI (`artifacts/demo-screenshots/02-ficha-riesgo-oficial.png`) |
| Función analítica (b): filtro/comparador regional reproducible | `/v1/municipalities?min_density=` y `/v1/compare` (CAM-02) | `test_density_filter_changes_with_cam02` | ✅ API · ✅ UI (filtro de densidad y `/comparar`) |
| Función analítica (c): matriz municipal CAM-01/02 × capa oficial (filtro reproducible, sin índice propio) | `/v1/analysis/municipal-matrix` + página `/analisis` | `test_municipal_matrix_is_reproducible_filter`; e2e `análisis municipal` | ✅ |
| El resultado cambia al actualizar el recurso | Pipeline fetch→transform→load idempotente con versión por SHA-256 (`dataset_versions`) | `test_dataset_version_tracking_on_source_update` | ✅ |
| Lineage por indicador | Tabla `indicator_definitions` + `/v1/indicators` (PRD §4.5) | `GET /v1/indicators` | ✅ |
| Geometría municipal propia del Portal CAM | CAM-08 secciones censales disueltas a 179 municipios | `test_T02_processed_outputs` | ✅ |
| Uso honesto de recursos regionales | CAM-05/06/07 marcados «agregado regional»; `forest_share` municipal = `unavailable` | `test_regional_series_are_labeled_regional` | ✅ |
| Capas IDEM integradas (complemento) | GEO-01/02/03 reparto exacto por municipio | `pipelines/tests/test_idem.py` (15 tests) | ✅ |

## Criterio 2 — Originalidad e innovación (20)

| Requisito | Evidencia | Estado |
|---|---|---|
| Comparativa con soluciones existentes | `COMPETITORS.md` (FIREPRIME, Geoportal/IDEM, INFOMA, SAVER/MINCE, XESBIO2, Technosylva…) | ✅ (hipótesis de demanda sin validar) |
| Cadena integrada mapa → inspección → optimización → plan → evidencia → informe | Test `test_flow_A_end_to_end` | ✅ backend · ✅ UI (capturas 03–05) |
| Optimización transparente con baselines y sensibilidad | `services/optimizer`, `docs/optimizer-method.md`, 13 tests incl. fuerza bruta 200 instancias | ✅ |
| Catálogo de medidas ligado a obligaciones normativas (INFOMA) | `data/reference/measures_catalog.json` (16 medidas) | ✅ (pendiente revisión técnica) |

## Criterio 3 — Impacto económico, social, tecnológico o medioambiental (25)

| Requisito | Evidencia | Estado |
|---|---|---|
| Problema real documentado con cifras citadas | Plan Anual 2026 (5.652,38 ha; 68 PAIF/26 municipios) verificado por A1 | ✅ |
| KPIs operativos permitidos (sin «incendios evitados») | `GET /v1/impact` | ✅ |
| Comparación de cobertura de prioridad vs baselines | Demo: cobertura 0,842 (manual) / 0,851 (menor coste) / 0,901 (optimizada) — **datos ficticios de demo** | 🟡 (válido como demostración de método, no como impacto) |
| Experimento de utilidad con/sin ESCUDO (tiempo, omisiones) | — | ⬜ requiere participantes humanos |
| Entrevista con técnico forestal / gestor | — | ⬜ acción humana |

## Criterio 4 — Viabilidad y aplicabilidad (15)

| Requisito | Evidencia | Estado |
|---|---|---|
| Flujo end-to-end funcional con backend real | API FastAPI + PostGIS; 10 tests de integración | ✅ |
| Modos degradados (AEMET caído) | `test_T05…`, `pipelines/tests/test_aemet.py` | ✅ |
| Multi-tenant (T08) | `test_T08_isolation_between_organizations` | ✅ |
| Despliegue reproducible | `infra/docker-compose.yml` (perfil `full`), Dockerfiles | 🟡 imágenes no construidas aún |
| Costes de operación | — | ⬜ |

## Criterio 5 — Tecnologías abiertas, código abierto y reproducibilidad (10)

| Requisito | Evidencia | Estado |
|---|---|---|
| Licencia abierta | `LICENSE` EUPL-1.2 (pendiente confirmación del equipo) | 🟡 |
| ETL reproducible con checksums | `fetch` + manifests versionados | ✅ |
| Tests y CI | 67 tests pytest + 6 Playwright; `.github/workflows/ci.yml` | ✅ local · ⬜ CI ejecutada en GitHub |
| Contrato OpenAPI | `packages/contracts/openapi.json` (35 rutas) | ✅ |
| Procedencia del trabajo asistido por IA | `PROVENANCE.md` | ✅ |

## Criterio 6 — Calidad y claridad de la presentación (5)

| Requisito | Evidencia | Estado |
|---|---|---|
| 3 diapositivas + 4.ª captura | Capturas reales en `artifacts/demo-screenshots/` | 🟡 faltan las diapositivas (A11) |
| Guion demo 5 min + backup | `docs/demo-script.md` (plan B con capturas y PDF) + `npm run e2e` | ✅ pendiente de ensayo cronometrado |
| Resumen ≤100 palabras antes del 24/11 | `docs/pitch/resumen-preseleccion.md`: 93 palabras (`scripts/count_words.py`), sin promesas inexistentes | ✅ texto · ⬜ envío (humano) |

## Desempate (bases ap. 10)
Prioridad: intensidad de uso de datos de Madrid → impacto → originalidad → viabilidad. Refuerzo previsto: más funciones analíticas sobre CAM (series 2021–2025 en UI, comparador), test de actualización de versión.
