# DATA_CATALOG — Fuentes de datos de ESCUDO MADRID

Dueño: A2 (CAM) / A3 (IDEM) / A4 (AEMET). Cada fila procede de un `data/raw/<ID>/manifest.json` generado por el pipeline (no transcrito a mano). Extracción: **06/11/2026**. Reproducir: `python -m escudo_pipelines.fetch` y `python -m escudo_pipelines.idem.fetch`.

## 1. Portal de Datos Abiertos de la Comunidad de Madrid (requisito de admisión DATAMAD)

Todas resueltas vía API CKAN `https://datos.comunidad.madrid/api/3/action/package_show`. Licencia declarada por el portal: `cc-by` (Creative Commons Attribution).

| ID | Dataset (CKAN id) | Formato | SHA-256 (16) | Modificado en portal | Escala real verificada | Uso en producto | Estado |
|---|---|---|---|---|---|---|---|
| CAM-01 | Población censada por edad, nacionalidad y sexo. Municipios (`poblacion_censada_por_edad_nacionalidad_y_sexo`) | CSV 15,6 MB | `9a8087ab86080324` | 2026-11-05 | 179 municipios + 11 zonas estadísticas + CAM; 2021–2025; grupos quinquenales | **Función analítica (a)**: ficha municipal (población total, proporción ≥65) y serie 2021–2025 | Ingerido y usado |
| CAM-02 | Densidad de población. Municipios (`1930748`) | CSV | `89d3248773adfcf2` | 2026-11-05 | 179 municipios; 1985–2025; hab/km² | **Función analítica (b)**: filtro/orden regional por densidad, comparador, coropleta | Ingerido y usado |
| CAM-03 | Altitud. Municipios (`101002`) | CSV | `4d4ebfb93378ba86` | 2026-11-05 | 179 municipios; año ref. 1998; m | Ficha municipal | Ingerido y usado |
| CAM-04 | Espacios protegidos (`espacios_protegidos`) | CSV | `cd93a0984e97842a` | 2026-01-13 | Listado de 80 espacios **sin geometría** | Catálogo `/v1/protected-spaces` (sin cruce espacial) | Ingerido |
| CAM-05 | Incendios y superficie afectada (`101019`) | CSV | `edd4c15627a88470` | 2026-11-05 | **Agregado regional** (sin código territorial); 1985–2025; 9 conceptos | Serie histórica regional `/v1/fire-history` | Ingerido |
| CAM-06 | Repoblaciones forestales (`repoblaciones_forestales`) | CSV (latin-1) | `d77d6f73167932a7` | 2025-11-11 | Regional por grupo vegetal; 2006–2024 | Serie contextual `/v1/regional-series/CAM-06` | Ingerido |
| CAM-07 | Distribución de la superficie por usos (`1101001`) | CSV | `c046c1f3d7abf412` | 2026-11-06 | **Agregado regional**; 1985–2024 | Serie regional; **no** se usa como % forestal municipal | Ingerido |
| CAM-08 | Secciones censales — SHP (`secciones_censales`) | ZIP SHP, EPSG:25830 | `00198d017d032e83` | 2025-02-07 | 4.417 secciones (seccionado 2019) → 179 municipios por disolución | Geometría municipal del mapa y área calculada | Ingerido y usado |
| CAM-09 | Censo 2021. Viviendas familiares convencionales por tipo de vivienda. Municipios (`censo_2021_viviendas_familiares_por_tipo`) | CSV | `a6eb1024d621cfda` | 2026-11-05 | 179 municipios (+ zonas estadísticas y CAM, descartadas); 2021; principales / no principales / total | Ficha «Vivienda y ocupación», filtro y orden en `/analisis`, export CSV | Ingerido y usado (08/11) |
| CAM-10 | Censo 2021. Porcentaje de viviendas familiares por tipo de edificio. Municipios (`censo_2021_porcentaje_viviendas_familiares_por_tipo_edificio`) | CSV | `cd3e2b2e1549539b` | 2026-11-05 | 179 municipios; 151 con «Residencial con una vivienda» publicado (resto «-» por secreto estadístico) | % de viviendas en edificio unifamiliar (ficha, análisis, export) | Ingerido y usado (08/11) |
| CAM-11 | Censo 2021. Viviendas por intensidad de uso según consumo eléctrico. Municipios (`censo_2021_viviendas_por_consumo_electrico`) | CSV | `eb9fc5afa9c40040` | 2026-11-05 | 180 códigos (179 municipios + `28999` sin municipio, descartado); 135 con dato; **provisional** | Viviendas vacías y de uso esporádico / total CAM-09 (ficha, export) | Ingerido y usado (08/11) |

**Hallazgos de calidad (registrados en `data/processed/cam/quality.json` y tabla `data_quality_checks`):**
- Códigos territoriales CAM de 4 dígitos = 3 de municipio + dígito de control → INE `28` + 3 primeros (test `test_cam_code_to_ine`).
- 1 sección censal inválida corregida con `make_valid`.
- Densidad publicada vs población/área de secciones: desviación mediana 0,07 %; máxima 18,6 % en Navacerrada (28093) — atribuible a que el seccionado no es deslinde jurídico. Control informativo.
- CAM-09: Total = Principales + No principales en los 179 municipios (control `cam09_total_igual_suma`).
- CAM-11: la suma de sus categorías (sin el subtotal «Uso esporádico») coincide **exactamente** con el total de CAM-09 en todos los municipios con dato (control `cam11_mismo_universo_que_cam09`); por eso las proporciones usan el total de CAM-09 como denominador. Si no coincidiera, la proporción sería `null`.
- CAM-05 y CAM-07 **no** tienen desagregación municipal: el PRD lo anticipaba; el producto lo indica y marca `forest_share` municipal como `unavailable`.

## 2. Cartografía oficial IDEM (complementaria)

| ID | Recurso | Formato real | SHA-256 (16) | Fecha metadatos | Licencia (verificada en ISO 19139) | Uso |
|---|---|---|---|---|---|---|
| GEO-01 | Riesgo por incendios forestales | GeoTIFF uint8 5 m, EPSG:25830 | `9388b85fddec144c` | revisión 2025-12-01; sello 2026-07-07 | CC BY 4.0 Comunidad de Madrid | Reparto exacto por municipio (ráster completo) + capa web 200 m |
| GEO-02 | Peligrosidad por incendios forestales | ídem | `1e31036a4f9a9fd9` | ídem | ídem | ídem |
| GEO-03 | Vulnerabilidad por incendios forestales | ídem | `c42cb86c80bf23d0` | ídem | ídem | ídem |

Clases literales tomadas de la leyenda oficial del WMS (`legend.json`). Método: `docs/spatial-method.md`. Divergencia con PRD: el PRD esperaba polígonos; la distribución oficial es ráster (ADR-0003).

## 3. AEMET (complementaria)

| ID | Recurso | Acceso | Licencia | Uso |
|---|---|---|---|---|
| AEMET | Predicción municipal XML `https://www.aemet.es/xml/municipios/localidad_<INE>.xml` | Público, sin clave | Nota legal AEMET: reutilización citando «Fuente: AEMET» y fecha | Contexto diario con `issued_at`, TTL 3 h, `stale`/`unavailable` |
| AEMET | AEMET OpenData (predicción, mapas de peligro de incendio) | Requiere `AEMET_API_KEY` (registro humano pendiente) | ídem | Mapa oficial de peligro (ráster) cuando haya clave |

Detalle y pruebas: `docs/aemet.md`, `fixtures/aemet/README.md`.

## 4. Candidatos no integrados todavía

| Fuente | Motivo |
|---|---|
| Copernicus EMS/EFFIS | P1: verificar licencia y resolución de perímetros; no mezclar provisionales con certificados |
| CNIG MDT | P1: pendientes reales (CAM-03 no lo permite) |
| MITECO EGIF | P1: series municipales históricas si son accesibles |
| Catastro | Fuera de alcance sin base legal (datos personales) |
| Superficie de terreno forestal por tipo de propiedad (`1913040`) | Auditado 08/11: solo agregado **regional** (14 conceptos, sin código territorial); no aporta escala municipal |
| Montes de Utilidad Pública por pertenencia administrativa (`1919480`) y por comarca (`montes_por_comarca`) | Auditado 08/11: regional / comarcal; no municipal. Posible contexto regional futuro |
| Lista de municipios en Zonas de Alto Riesgo (ZAR) | No existe como dataset en el Portal CAM (búsqueda 08/11); requiere el documento oficial del plan (tarea 2.3) |
