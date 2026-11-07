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
