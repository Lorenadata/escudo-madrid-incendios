# ESCUDO MADRID

Plataforma abierta de **planificación preventiva de incendios forestales** para municipios y urbanizaciones de la Comunidad de Madrid (DATAMAD 2026).

> «Del mapa al plan; del plan a la ejecución comprobable.»
> ESCUDO MADRID es una herramienta de apoyo a la planificación. **No** sustituye a ASEM 112, AEMET, INFOMA ni a personal técnico competente. No emite alertas, rutas de evacuación ni aprobaciones de PAIF.

## Qué hace (estado real en `PROGRESS.md`)

- Ingiere datos del **Portal de Datos Abiertos de la Comunidad de Madrid** (8 datasets: población, densidad, altitud, secciones censales, incendios, repoblaciones, usos del suelo, espacios protegidos) con checksum y licencia.
- Integra la **cartografía oficial IDEM** de riesgo, peligrosidad y vulnerabilidad (clases literales, reparto por municipio).
- Consulta la **predicción municipal de AEMET** con caducidad explícita (si falla: «no disponible»).
- Permite a una organización registrar ámbitos, inspecciones y evidencias, construir escenarios de actuaciones con un **optimizador CP-SAT determinista** comparado con dos baselines, convertirlos en un plan con seguimiento y exportar un **informe PDF trazable**.
- Distingue en todo momento dato **oficial**, **derivado**, **escenario**, **aportado por usuario**, **no disponible** y **desactualizado**.

## Arranque rápido

Requisitos: Python ≥3.12, Docker, Node ≥22.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"        # Linux/macOS: .venv/bin/python
docker compose -f infra/docker-compose.yml up -d db
.venv/Scripts/python -m escudo_pipelines.fetch          # descarga real del Portal CAM (SHA-256)
.venv/Scripts/python -m escudo_pipelines.cam_transform
.venv/Scripts/python -m escudo_pipelines.idem.fetch     # ~49 MB, cartografía oficial
.venv/Scripts/python -m escudo_pipelines.idem.transform # ~10 min (o --web-only)
.venv/Scripts/python -m escudo_api.etl_load             # carga PostGIS + demo FICTICIA etiquetada
.venv/Scripts/python -m uvicorn escudo_api.main:app --port 8000
cd apps/web && npm install && npm run dev               # http://localhost:3000
```

**Demo en un comando:** `bash scripts/demo.sh` (BD, migraciones, datos, API en :8000, web en :3000, cachés calentadas); `bash scripts/demo.sh check` ejecuta los 10 e2e y restaura la demo; `bash scripts/demo.sh stop` la detiene. Para desarrollo: `bash scripts/dev.sh`. Documentación interactiva de la API: http://localhost:8000/docs.

**Demo local** (datos ficticios): `gestor@demo.escudo.local` / `demo-escudo-2026`. Recorrido público sin credenciales: `GET /v1/demo/guided`.

## Tests

```bash
.venv/Scripts/python -m pytest            # unit + pipelines + integración PostGIS (BD escudo_test)
.venv/Scripts/python -m pytest -m network # incluye llamadas reales a AEMET
.venv/Scripts/python -m ruff check apps/api pipelines services tests
```

## Documentación

| Documento | Contenido |
|---|---|
| `ESCUDO_MADRID_PRD_Maestro.md` | Especificación de producto (contrato) |
| `CLAUDE.md` | Reglas permanentes, arquitectura, propiedad por agente |
| `PROGRESS.md` · `ROADMAP.md` | Estado real · tablero P0/P1 y gates |
| `DATA_CATALOG.md` | Fuentes, licencias, checksums, escalas |
| `COMPLIANCE.md` · `docs/DATAMAD_SCORECARD.md` | Bases del concurso · evidencias por criterio |
| `docs/spatial-method.md` · `docs/optimizer-method.md` · `docs/model-card.md` · `docs/aemet.md` | Métodos |
| `docs/contracts/api-contract.md` · `packages/contracts/openapi.json` | Contrato API |
| `PROVENANCE.md` · `EVIDENCE_LOG.md` | Autoría, IA, terceros · evidencias |

## Licencia

Código: EUPL-1.2 (`LICENSE`, pendiente de confirmación del equipo). Datos: licencias de origen (CC-BY Portal CAM, CC BY 4.0 IDEM, nota legal AEMET).
