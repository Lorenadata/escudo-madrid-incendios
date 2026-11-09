# EVIDENCE_LOG — Artefactos verificables por criterio DATAMAD

Formato: fecha · agente · artefacto · cómo verificar · criterio(s). Solo hechos comprobables.

| Fecha | Agente | Artefacto | Verificación | Criterio |
|---|---|---|---|---|
| 06/11/2026 | A0/A2 | 8 datasets del Portal CAM descargados vía CKAN con SHA-256 y licencia | `data/raw/CAM-*/manifest.json`; `pytest pipelines/tests/test_cam.py` | D25, D10 |
| 06/11/2026 | A0/A2 | Transformación CAM: 179 municipios, 8 controles de calidad superados | `python -m escudo_pipelines.cam_transform` → `quality.json` | D25, D15 |
| 06/11/2026 | A3 | GEO-01/02/03: ráster oficial 5 m, reparto por municipio (2.939 filas, 179 municipios), capas web | `pytest pipelines/tests/test_idem.py` (15 ✔) | D25, D15, D10 |
| 06/11/2026 | A4 | Conector AEMET: XML público real, caché TTL, `stale`/`unavailable` | `pytest pipelines/tests/test_aemet.py` (14 ✔ incl. red) | D15, D20 |
| 06/11/2026 | A5 | Optimizador CP-SAT determinista + 2 baselines + sensibilidad; validado contra fuerza bruta (200 instancias) | `pytest tests/unit/test_optimizer.py` (13 ✔) | D20, D15, D10 |
| 06/11/2026 | A1 | `COMPLIANCE.md` (25 normas), `COMPETITORS.md`, catálogo de 16 medidas con citas INFOMA verificadas | Lectura + JSON validado | Admisión, D20, D15 |
| 06/11/2026 | A0/A6 | API FastAPI + PostGIS: 35 rutas, multi-tenant, auditoría, informe PDF | `pytest tests/integration` (10 ✔: T01, T04, T05, T06, T07, T08, T09, Flujo A) | D15, D25, D10 |
| 06/11/2026 | A0 | Recorrido vertical: dato CAM → PostGIS → API → escenario optimizado → plan → PDF | `GET /v1/demo/guided`, `GET /v1/demo/report.pdf` | D15, D20, D25 |
| 06/11/2026 | A7 (+A0) | Web Next.js + MapLibre verificada contra la API real: explorador, ficha con capas oficiales y AEMET, caso guiado, área privada, fuentes | `npm run lint && npm run build`; capturas `artifacts/demo-screenshots/01…06` | D15, D25, D5 |
| 06/11/2026 | A9 (A0) | e2e Playwright del Flujo C: 5 tests contra web + API reales, incluida comprobación de lenguaje prohibido | `cd apps/web && npm run e2e` | D15, D10 |
| 06/11/2026 | A0 | Versionado: un nuevo SHA-256 de un recurso CAM crea versión nueva, recarga idempotente | `test_dataset_version_tracking_on_source_update` | D25 |
| 06/11/2026 | A11 (A0) | Guion de demo 5 min con plan B, contenido 3+1 y resumen de 93 palabras | `docs/demo-script.md`, `docs/pitch/`, `scripts/count_words.py` | D5 |
| 07/11/2026 | A0 | Matriz municipal CAM-01/02 × capa oficial (95 municipios con ≥50 % en riesgo alto/muy alto según GEO-01) | `GET /v1/analysis/municipal-matrix?min_high_share=0.5`; test de integración | D25 |
| 07/11/2026 | A0 | Bug corregido: crear áreas con geometría fallaba; reparto por ámbito marcado «derived» (capa 200 m) | `test_area_geojson_export_is_private` | D15 |
| 07/11/2026 | A10 (A0) | Imagen Docker de la API verificada dentro de la red de Compose | `docker compose --profile full build api` + humo `/health` | D10 |
| 07/11/2026 | A0 | Flujo B (PRD §3.2): panel municipal; solo ámbitos con autorización expresa; revocación inmediata; expediente e informe | `test_flow_B_municipal_sees_only_authorized_areas`, e2e «Flujo B», captura 07 | D20, V15, I25 |
| 07/11/2026 | A0 | ROADMAP completo hasta el 25/11 con acciones humanas, fases, calendario y riesgos | `ROADMAP.md` | P5 |
| 07/11/2026 | A0 | M05 dibujo del ámbito en el mapa + clases oficiales orientativas marcadas «derivado»; revisión técnica cubierta por e2e | `npm run e2e` (9 ✔) | D20, V15 |
| 07/11/2026 | A0 | Flujo A completo en UI (login → ámbito → inspección con foto → medidas → optimizar → plan → evidencia → PDF) en 6–12 s automatizado | `apps/web/e2e/flujo-a-gestor.spec.ts` | V15, D20 |
| 07/11/2026 | A10 (A0) | Demo en un comando (31 s) y 3 arranques en frío consecutivos con 10/10 e2e cada uno | `bash scripts/demo.sh` · `bash scripts/demo.sh check` | V15, R10, P5 |
| 07/11/2026 | A10 (A0) | Código abierto publicado en GitHub (cuenta de la participante, EUPL-1.2 detectada) con revisión previa de secretos y CI verde | https://github.com/Lorenadata/escudo-madrid-incendios · run 42368698348 | D5, R10, P5 |
| 08/11/2026 | A2+A6+A7 (A0) | Fase 2: auditoría del Portal CAM (24 búsquedas) e integración de 3 datasets municipales del Censo 2021 (viviendas no principales, edificio unifamiliar, uso según consumo eléctrico) con controles de coherencia entre fuentes | `quality.json` (12/12 PASS), `test_build_housing_fixture`, `test_housing_indicators_trace_to_processed_census`, `test_matrix_filters_by_non_main_share_and_export_has_census` | D25, D20 |
| 09/11/2026 | A1+A2+A6+A7 (A0) | 2.3: Zonas de Alto Riesgo (59 municipios, Anexo II pág. 59) y siniestros 2015–2024 por municipio y causa (Anexo I, págs. 54–58) extraídos literalmente del Plan Anual 2026 oficial; extracción cuadrada con la fila TOTALES del documento | `data/processed/plan/quality.json` (8/8), `pipelines/tests/test_plan_anual.py`, `test_fire_plan_zar_and_municipal_fires_are_literal` | D25, D20 |
| 09/11/2026 | A2+A10 (A0) | 2.4: actualización verificable (`escudo_pipelines.refresh`): descarga, SHA-256, comparación con el manifest, historial de versiones, detección de «mismas filas reordenadas»; panel en `/fuentes` y `GET /v1/sources/refresh-log`. Prueba real: 12 fuentes, CAM-07 con versión nueva sin cambios de contenido | `pipelines/tests/test_refresh.py` (6), `test_sources_expose_refresh_check_and_log`, `data/processed/refresh_log.json` | D25, R10 |
| 09/11/2026 | A3+A6+A7 (A0) | 2.6: EFFIS integrado (EFF-01, CC BY 4.0): 73 perímetros 2016–2026 que tocan la región, capa activable en el mapa, ficha con superficie por término (intersección EPSG:25830) y avisos del productor; tablas nuevas con migración Alembic `3e96224da392` | `data/processed/effis/quality.json` (4/4), `pipelines/tests/test_effis.py`, `test_satellite_burnt_areas_profile_and_layer` | D20, D25 |
| 09/11/2026 | A9 (A0) | Revisión automática de seguridad: nombres de fichero remotos saneados y confinados (path traversal) en fetch/refresh | `test_remote_filenames_cannot_escape_raw_dir` | R10 |
| 09/11/2026 | A8+A9 (A0) | 3.1–3.2: protocolo del experimento de utilidad cerrado antes de las sesiones (intra-sujeto, contrabalanceado), casos A/B ficticios equivalentes en la app (escenarios en borrador) y en papel, clave del evaluador con el mismo optimizador, guion, consentimiento y registro | `docs/validation/`, `tests/unit/test_validation_materials.py`, `test_validation_accounts_see_both_cases_with_draft_scenarios` | I25, D20 |
