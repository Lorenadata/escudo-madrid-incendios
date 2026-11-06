# ADR-0001 — Arquitectura y stack

**Estado:** aceptada (06/11/2026, A0). **Contexto:** PRD §6.1.

**Decisión:** Next.js + TypeScript + Tailwind + MapLibre (web); FastAPI + Pydantic v2 + SQLAlchemy 2 + GeoAlchemy2 (API); PostgreSQL 16 + PostGIS 3.4 en Docker; ETL en Python con httpx, shapely, pyproj, pyshp y rasterio; OR-Tools CP-SAT; ReportLab para PDF; pytest + ruff + ESLint; Docker Compose.

**Divergencias respecto al PRD:**
- Sin GeoPandas: shapely/pyproj/pyshp/rasterio cubren las necesidades y simplifican la instalación en Python 3.14 (entorno del equipo).
- Sin Redis/RQ en esta fase: no hay tareas en segundo plano que lo justifiquen (PRD §6.1 «no añadir servicios sin caso de uso»). La meteo se consulta bajo demanda con caché TTL.
- Evidencias en almacenamiento local privado (`ESCUDO_EVIDENCE_DIR`) con descarga autenticada; S3 compatible queda para despliegue.
- Migraciones Alembic en `infra/migrations` (`alembic upgrade head`); el cargador usa `create_all` para desarrollo rápido. `alembic check` debe quedar sin diferencias. Único dueño de esquema: A0/A6.
- Estructura: paquetes Python `escudo_api` (apps/api), `escudo_pipelines` (pipelines), `escudo_optimizer` (services/optimizer), `escudo_reporting` (services/reporting).
