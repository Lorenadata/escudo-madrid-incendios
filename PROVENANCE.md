# PROVENANCE — Autoría, recursos reutilizados y uso de IA

Bases DATAMAD §1.2.5–1.2.6 (PRD): el uso de IA generativa está permitido; el trabajo debe desarrollarse o evolucionar sustancialmente entre el **7 y el 26 de noviembre de 2026**; los recursos preexistentes deben identificarse.

## Cronología declarada

| Fecha | Hecho | Comentario |
|---|---|---|
| 06/11/2026 (tarde) | Inicialización del repositorio, andamiaje, primeros pipelines, API y tests | **Anterior al periodo oficial** (empieza el 07/11). Se declara expresamente como andamiaje inicial. Todo el trabajo posterior queda registrado por commits fechados. |
| 07–26/11/2026 | Periodo oficial de desarrollo | Ver `git log --date=iso`. |

## Trabajo asistido por IA

- Código, documentación y análisis generados con **Claude Code** (Anthropic) actuando como orquestador (A0) y como agentes especializados (A1 bases/research, A3 GIS, A4 AEMET, A5 optimización, A7 frontend), bajo instrucciones del PRD maestro redactado por el equipo.
- La participante inscrita, **Lorena Marcos** (única integrante), es la autora y responsable del proyecto; los agentes son herramientas.
- **Revisión humana pendiente** de: metodología del optimizador, catálogo de medidas (todas `pending_technical_review`), textos públicos y pitch.

## Recursos de terceros

| Recurso | Licencia | Uso |
|---|---|---|
| Datasets Portal CAM (CAM-01…08) | CC-BY | Datos (ver `DATA_CATALOG.md`) |
| Cartografía IDEM GEO-01…03 | CC BY 4.0 Comunidad de Madrid | Capas oficiales |
| AEMET predicción municipal | Nota legal AEMET (cita obligatoria) | Contexto meteorológico |
| FastAPI, SQLAlchemy, GeoAlchemy2, Shapely, pyproj, pyshp, rasterio, OR-Tools, ReportLab, Next.js, MapLibre GL JS | Licencias abiertas (MIT/BSD/Apache-2.0/LGPL según paquete) | Dependencias |
| Texto `LICENSE` EUPL-1.2 | Obtenido de `api.github.com/licenses/eupl-1.2` | Licencia del proyecto (confirmada por Lorena Marcos el 07/11/2026) |

## Datos ficticios

`fixtures/synthetic/demo_seed.json`: organización, usuarios, ámbito, inspección, costes y presupuesto **inventados y etiquetados** para la demostración (Flujo C). Nunca se presentan como resultados.
