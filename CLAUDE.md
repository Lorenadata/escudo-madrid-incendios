# CLAUDE.md — Reglas permanentes de ESCUDO MADRID

Plataforma de planificación preventiva de incendios forestales para la Comunidad de Madrid (DATAMAD 2026).
Contrato de producto: `ESCUDO_MADRID_PRD_Maestro.md` (el PDF es copia equivalente, verificado 06/11/2026).
Instrucciones de orquestación: `ESCUDO_MADRID_INICIO_CLAUDE.md`. Divergencias del PRD → `docs/adr/`.

## Reglas inviolables (PRD §1.2, §4, §5, §6.5 e INICIO)

1. **Cero cifras inventadas.** Todo número en pantalla, informe o pitch procede de un fichero en `data/raw/` con `manifest.json` (URL, SHA-256, fecha, licencia) o de un cálculo reproducible sobre él. Si no existe, se muestra `no disponible`.
2. **Cada indicador lleva `status`**: `official` · `derived` · `scenario` · `user_reported` · `unavailable` (y `stale` para meteo caducada). La UI los distingue visualmente.
3. **Separar** riesgo oficial (GEO-01), peligrosidad (GEO-02), vulnerabilidad (GEO-03), meteorología AEMET y prioridad de revisión ESCUDO. Las clases oficiales se muestran literales, nunca recalculadas ni renombradas.
4. **Separación de escalas**: datos municipales (CAM-01, CAM-02…) jamás se reparten ni se atribuyen a una urbanización/zona. La API no expone población por área.
5. **AEMET caído o sin clave** → `status: unavailable` con fecha del último dato válido. Nunca reutilizar silenciosamente datos antiguos.
6. **Prohibido**: rutas de evacuación, tácticas de extinción, certificados/aprobaciones PAIF, «% incendios evitados», «vidas salvadas», «reducción de riesgo X %», «ahorro real».
7. El optimizador maximiza una **función objetivo acordada** (prioridad técnica × cobertura), no reducción de riesgo. Presupuestos de demo se marcan `is_demo_budget: true`.
8. Datos de demo (organización, urbanización, inspección, presupuestos) son **ficticios y etiquetados** (`fixtures/synthetic/`, `record_status='synthetic'`).
9. Multi-tenant: toda consulta de datos privados filtra por `organization_id` de la pertenencia del usuario. Test T08 obligatorio.
10. Nada de credenciales en el repo (`.env` ignorado; `.env.example` sí). Sin despliegues públicos ni gastos sin autorización humana.
11. Lenguaje: «revisión preventiva prioritaria», no «vivienda segura/insegura». Toda salida sensible: botón «Ver método y fuentes».

## Arquitectura (ADR-0001)

```
Portal CAM (CKAN) / IDEM / AEMET
   → pipelines/escudo_pipelines (fetch → data/raw/<SRC>/ + manifest.json → transform → data/processed/)
   → loader (escudo_api.etl_load) → PostGIS (infra/docker-compose.yml, puerto 5433)
   → FastAPI apps/api/escudo_api (OpenAPI en /openapi.json, contrato exportado a packages/contracts/openapi.json)
   → Next.js apps/web (MapLibre GL) → informes PDF (services/reporting) / optimizador (services/optimizer)
```

| Capa | Tecnología |
|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind + MapLibre GL JS |
| API | FastAPI + Pydantic v2 + SQLAlchemy 2 + GeoAlchemy2 |
| BD | PostgreSQL 16 + PostGIS 3.4 (Docker) |
| ETL | Python (httpx, shapely, pyproj, pyshp) — sin GeoPandas para mantener instalación ligera en Py3.14 |
| Optimizador | OR-Tools CP-SAT (determinista: 1 worker, semilla fija) |
| Informes | ReportLab (PDF) |
| Tests | pytest (unit, integración PostGIS, pipelines), Playwright (e2e web), ruff, ESLint |

## Comandos

```bash
# Entorno Python
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"   # Windows (Linux: .venv/bin/python)
# Base de datos
docker compose -f infra/docker-compose.yml up -d db
# Datos (descarga real + transformación + carga)
.venv/Scripts/python -m escudo_pipelines.fetch            # descarga CAM con checksum
.venv/Scripts/python -m escudo_pipelines.cam_transform    # normaliza a data/processed/cam
.venv/Scripts/python -m escudo_pipelines.plan_anual fetch && .venv/Scripts/python -m escudo_pipelines.plan_anual transform  # DOC-01: ZAR y siniestros municipales
.venv/Scripts/python -m escudo_api.etl_load               # carga en PostGIS + seed demo ficticio
.venv/Scripts/python -m escudo_pipelines.effis fetch && .venv/Scripts/python -m escudo_pipelines.effis transform  # EFF-01 (262 MB): áreas quemadas EFFIS
.venv/Scripts/python -m escudo_pipelines.refresh          # comprueba SHA-256 contra el origen (--apply --rebuild para incorporar)
# API
.venv/Scripts/python -m uvicorn escudo_api.main:app --reload --port 8000
# Web
cd apps/web && npm install && npm run dev                  # http://localhost:3000
# Demo completa en un comando
bash scripts/demo.sh            # start | stop | check (e2e + restaurar demo); si :8000 está ocupado → API_PORT=8010 bash scripts/demo.sh
# Tests
.venv/Scripts/python -m pytest                             # unit + integración (requiere db) + pipelines
cd apps/web && npm run lint && npm run build
cd apps/web && E2E_BASE_URL=http://localhost:3000 npm run e2e   # T10 Playwright (API + web levantadas)
```

Variables: ver `.env.example`. `DATABASE_URL`, `DATABASE_URL_TEST`, `AEMET_API_KEY` (opcional, sin ella la meteo es `unavailable`), `ESCUDO_JWT_SECRET`.

## Propiedad de archivos (agentes A0–A11, PRD §7)

Un único dueño por zona. Para tocar una zona ajena, pedirlo a A0. **Esquema BD y contratos API: solo A0/A6.**

| Agente | Zona en exclusiva |
|---|---|
| A0 Orquestación | `CLAUDE.md`, `PROGRESS.md`, `ROADMAP.md`, `docs/DATAMAD_SCORECARD.md`, `docs/adr/`, `EVIDENCE_LOG.md`, `PROVENANCE.md` |
| A1 Bases/Research | `COMPLIANCE.md`, `COMPETITORS.md`, `docs/measures-catalog.md`, `data/reference/measures_catalog.json` |
| A2 Open Data | `pipelines/escudo_pipelines/{sources,fetch,cam_transform}.py`, `DATA_CATALOG.md`, `data/raw/CAM-*`, `data/processed/cam/` |
| A3 GIS | `pipelines/escudo_pipelines/idem/`, `data/processed/idem/`, `docs/spatial-method.md`, `pipelines/tests/test_idem*.py` |
| A4 AEMET | `pipelines/escudo_pipelines/aemet/`, `fixtures/aemet/`, `docs/aemet.md`, `pipelines/tests/test_aemet*.py` |
| A5 OR | `services/optimizer/`, `docs/optimizer-method.md`, `docs/model-card.md`, `tests/unit/test_optimizer*.py` |
| A6 Backend | `apps/api/`, `infra/migrations/`, `packages/contracts/`, `tests/integration/` |
| A7 Frontend | `apps/web/` |
| A8 UX/Product | `docs/ux/`, copys revisados vía PR a A7 |
| A9 Seguridad/QA | `docs/privacy-security.md`, `docs/validation-report.md`, `apps/web/e2e/` (Playwright vive junto a la web para resolver `@playwright/test`) |
| A10 DevOps | `infra/docker/`, `.github/workflows/`, `scripts/` |
| A11 Pitch | `docs/pitch/`, `docs/demo-script.md`, `artifacts/` |

## Metodología

- API-first: el contrato vive en `docs/contracts/api-contract.md` y `packages/contracts/openapi.json` (generado). Cambios de contrato → A0.
- Rama `main` siempre verde. Commits pequeños, mensaje con criterio DATAMAD afectado (`[D25]`, `[D20]`, `[D25i]`, `[D15]`, `[D10]`, `[D5]`).
- Definition of Done (PRD §9.1): datos reales o autorizados, fuente visible, API+UI reales, test automático, nulos/errores gestionados, privacidad, documentado y reproducible.
- Cada agente cierra con el formato de reporte de `ESCUDO_MADRID_INICIO_CLAUDE.md` y añade entrada en `EVIDENCE_LOG.md` (vía A0).
- Tras `npm run build`, reiniciar `next start`: un servidor ya arrancado sirve HTML que apunta a chunks borrados (500) y la página no hidrata.
- Red: en Windows `curl` necesita `--ssl-no-revoke` contra datos.comunidad.madrid (schannel). Python/httpx funciona sin cambios.
- Fechas: periodo oficial de desarrollo 07–26/11/2026. Resumen ≤100 palabras antes del 24/11. Entrega antes de las 14:00 del 26/11.
