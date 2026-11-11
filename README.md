# ESCUDO MADRID

Plataforma abierta de **planificación preventiva de incendios forestales** para municipios y urbanizaciones de la Comunidad de Madrid (DATAMAD 2026).

> «Del mapa al plan; del plan a la ejecución comprobable.»
> ESCUDO MADRID es una herramienta de apoyo a la planificación. **No** sustituye a ASEM 112, AEMET, INFOMA ni a personal técnico competente. No emite alertas, rutas de evacuación ni aprobaciones de PAIF.

## Qué hace (estado real en `PROGRESS.md`)

- Ingiere datos del **Portal de Datos Abiertos de la Comunidad de Madrid** (11 datasets: población, densidad, altitud, secciones censales, incendios, repoblaciones, usos del suelo, espacios protegidos y tres del Censo 2021 sobre vivienda y ocupación) con checksum y licencia.
- Integra la **cartografía oficial IDEM** de riesgo, peligrosidad y vulnerabilidad (clases literales, reparto por municipio).
- Consulta la **predicción municipal de AEMET** con caducidad explícita (si falla: «no disponible»).
- Permite a una organización registrar ámbitos, inspecciones y evidencias, construir escenarios de actuaciones con un **optimizador CP-SAT determinista** comparado con dos baselines, convertirlos en un plan con seguimiento y exportar un **informe PDF trazable**.
- Distingue en todo momento dato **oficial**, **derivado**, **escenario**, **aportado por usuario**, **no disponible** y **desactualizado**.

## Arranque rápido

Requisitos: Python ≥ 3.12, Docker, Node ≥ 22 y unos 3 GB de disco. Los **datos procesados vienen incluidos** en el repositorio (con su `manifest.json`, URL y SHA-256), así que no hace falta descargar nada para tener la plataforma funcionando.

```bash
git clone https://github.com/Lorenadata/escudo-madrid-incendios.git && cd escudo-madrid-incendios
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"        # Linux/macOS: .venv/bin/python
docker compose -f infra/docker-compose.yml up -d db     # PostGIS en el puerto 5433
.venv/Scripts/python -m alembic upgrade head            # esquema de la base de datos
.venv/Scripts/python -m escudo_api.etl_load             # carga datos reales + demo FICTICIA etiquetada
.venv/Scripts/python -m uvicorn escudo_api.main:app --port 8000      # API: http://localhost:8000/docs
cd apps/web && npm ci && npm run build && npm run start               # web: http://localhost:3000
```

O todo de una vez: `bash scripts/demo.sh` (si el puerto 8000 está ocupado, el script lo avisa: `API_PORT=8010 bash scripts/demo.sh`).

Opcional: copia `.env.example` a `.env` y añade una clave gratuita de AEMET OpenData (`AEMET_API_KEY`) para la predicción completa y el mapa oficial de riesgo de incendios. Sin ella se usa el XML público de AEMET.

### Reproducir los datos desde el origen (opcional)

Cada paso vuelve a descargar la fuente oficial, comprueba su SHA-256 y regenera `data/processed/`:

```bash
.venv/Scripts/python -m escudo_pipelines.fetch                 # Portal de Datos Abiertos de la CAM (11 datasets)
.venv/Scripts/python -m escudo_pipelines.cam_transform
.venv/Scripts/python -m escudo_pipelines.idem.fetch            # cartografía oficial IDEM (~49 MB)
.venv/Scripts/python -m escudo_pipelines.idem.transform        # ~10 min (o --web-only)
.venv/Scripts/python -m escudo_pipelines.plan_anual fetch      # Plan Anual 2026 (PDF oficial)
.venv/Scripts/python -m escudo_pipelines.plan_anual transform  # Zonas de Alto Riesgo y siniestros municipales
.venv/Scripts/python -m escudo_pipelines.infoma                # Decreto INFOMA (BOCM)
.venv/Scripts/python -m escudo_pipelines.effis fetch           # EFFIS (~262 MB, toda Europa)
.venv/Scripts/python -m escudo_pipelines.effis transform
.venv/Scripts/python -m escudo_pipelines.docsearch build       # índice de normativa
.venv/Scripts/python -m escudo_pipelines.docsearch evaluate    # evaluación (20 preguntas)
.venv/Scripts/python -m escudo_api.etl_load                    # recarga PostGIS
```

**Actualización verificable:** `python -m escudo_pipelines.refresh` vuelve a descargar cada fuente y compara su SHA-256 con el manifest (sin tocar los datos en uso); `--apply --rebuild` incorpora las versiones nuevas, conserva el historial y recarga PostGIS. El resultado se ve en `/fuentes` y en `GET /v1/sources/refresh-log`.

**Demo en un comando:** `bash scripts/demo.sh` (BD, migraciones, datos, API en :8000, web en :3000, cachés calentadas); `bash scripts/demo.sh check` ejecuta las pruebas de navegador (flujos, accesibilidad, modo sin conexión) y restaura la demo; `bash scripts/demo.sh stop` la detiene. Para desarrollo: `bash scripts/dev.sh`. Documentación interactiva de la API: http://localhost:8000/docs.

**Demo local** (datos ficticios): `gestor@demo.escudo.local` / `demo-escudo-2026`. Recorrido público sin credenciales: `GET /v1/demo/guided`.

## Demo pública (Hugging Face Space)

**https://lorenadata-escudo-madrid.hf.space** · cuentas ficticias `gestor@demo.escudo.local`, `tecnico@demo.escudo.local`, `municipal@demo.escudo.local` (contraseña `demo-escudo-2026`) · caso guiado sin cuenta en `/demo` · inspección en campo en `/campo`.

`infra/docker/space.Dockerfile` clona este repositorio en un commit fijo y ejecuta PostGIS, la API (interna, publicada como `/api`) y la web (puerto 7860) en un único contenedor mediante `scripts/space-entrypoint.sh`. La ficha del Space está en `infra/docker/hf-space/README.md`. El disco es efímero: cada reinicio recarga los datos reales y restaura la demo ficticia. `AEMET_API_KEY` y `ESCUDO_JWT_SECRET` se configuran como *secrets* del Space, nunca en el repositorio.

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

Código: EUPL-1.2 (`LICENSE`). Autora: Lorena Marcos. Datos: licencias de origen (CC-BY Portal CAM, CC BY 4.0 IDEM, nota legal AEMET).
