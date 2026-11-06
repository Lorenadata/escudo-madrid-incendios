# Método espacial — capas oficiales de incendios forestales (A3 GIS)

Responsable: A3 GIS · Código: `pipelines/escudo_pipelines/idem/` · Tests: `pipelines/tests/test_idem.py` (T02, T03).

## 1. Fuentes verificadas (06/11/2026)

| ID | Capa | Descarga | Formato real | Licencia | Fechas ISO 19139 |
|---|---|---|---|---|---|
| GEO-01 | Riesgo por incendios forestales (`riesgo_3_1`) | `https://idem.comunidad.madrid/recursos_cat_geo/Catalogo/recursos/ZonasRiesgo/PCivil/riesgo_3_1.zip` | GeoTIFF uint8 5 m + TFW | CC BY 4.0 Comunidad de Madrid | creación 2018-12-12 · revisión 2025-12-01 · metadatos 2026-07-07 |
| GEO-02 | Peligrosidad por incendios forestales (`peligrosid_3_1`) | `…/PCivil/peligrosid_3_1.zip` | GeoTIFF uint8 5 m + TFW | CC BY 4.0 Comunidad de Madrid | ídem |
| GEO-03 | Vulnerabilidad por incendios forestales (`vulnera_3_1`) | `…/PCivil/vulnera_3_1.zip` | GeoTIFF uint8 5 m + TFW | CC BY 4.0 Comunidad de Madrid | ídem |

- Descubrimiento: API de datos.gob.es (`/apidata/catalog/dataset/a13002908-<capa>-por-incendios-forestales.json`, publicador A13002908). El registro de datos.gob.es **no declara licencia**; la licencia se toma de los metadatos ISO 19139 del catálogo GeoNetwork del IDEM (`spacm_riesgoiiff`, `spacm_peligroiiff`, `spacm_vulneraiiff`), que se guardan en `data/raw/GEO-0X/*.iso19139.xml` con su SHA-256.
- **Discrepancia con el PRD:** el PRD esperaba polígonos; la distribución oficial descargable es **ráster** (5 m, LZW, nodata = 255, 25 970 × 28 409 px, EPSG:25830). Se procesa como ráster y se vectoriza solo para la vista web.
- Productor del dato de peligrosidad según la memoria metodológica del Catálogo de Riesgos Potenciales (CRP-CAM, nov. 2025): *Servicio de Incendios Forestales (CM)*. Memoria: `…/PCivil/CRP-CAM_MEMORIA_METODOLOGICA_NOV.2025.pdf`. ESCUDO no reproduce ni modifica la combinación peligrosidad/vulnerabilidad → riesgo; usa el resultado publicado.
- Reproducibilidad: dos descargas consecutivas (06/11/2026) dieron SHA-256 idénticos (`9388b85f…`, `1e31036a…`, `c42cb86c…`).

## 2. Clases (literales de la fuente)

Las etiquetas y colores proceden de la leyenda oficial del WMS IDEM (`GetLegendGraphic&format=application/json`), guardada en `data/raw/GEO-0X/legend.json`. Ningún valor se renombra ni se recalcula; un valor del ráster sin etiqueta en la leyenda hace fallar el pipeline.

| Código | GEO-01 Riesgo | GEO-02 Peligrosidad | GEO-03 Vulnerabilidad |
|---|---|---|---|
| 0 | Sin Riesgo | Sin peligro | Sin Vulnerabilidad |
| 1 | Riesgo muy bajo | Peligrosidad muy baja | Vulnerabilidad muy baja |
| 2 | Riesgo bajo | Peligrosidad baja | Vulnerabilidad baja |
| 3 | Riesgo moderado | Peligrosidad moderada | Vulnerabilidad moderada |
| 4 | Riesgo alto | Peligrosidad alta | Vulnerabilidad alta |
| 5 | Riesgo muy alto | Peligrosidad muy alta | Vulnerabilidad muy alta |
| 99 | Riesgo no calculado | Peligrosidad no calculada | Vulnerabilidad no calculada |
| 255 | nodata (fuera de la CAM) | nodata | nodata |

Valores presentes en cada ráster y superficie regional por clase: `data/processed/idem/layers_meta.json` (`present_in_raster`, `regional_area_ha`). Observación: la superficie de «Riesgo no calculado» (99) en GEO-01 coincide en nº de píxeles con «Sin Vulnerabilidad» (0) en GEO-03; se informa tal cual, sin interpretarlo.

## 3. Procesamiento

1. **Descarga** (`python -m escudo_pipelines.idem.fetch`): ZIP, XML ISO 19139 y leyenda JSON → `data/raw/GEO-0X/` + `manifest.json` (SHA-256, URL, fechas, licencia, clases).
2. **Lectura** directa del ZIP vía GDAL (`zip://…!riesgo_3_1.tif`), por bandas de 2 048 filas (memoria acotada).
3. **Municipios**: `data/processed/cam/municipalities.geojson` (A0/A2, derivado de CAM-08 secciones censales) reproyectado EPSG:4326 → EPSG:25830 con pyproj (`always_xy`). Geometrías inválidas → `shapely.make_valid` y se cuentan (`n_invalid_fixed`).
4. **Reparto municipal (resolución nativa 5 m)**: se rasteriza cada municipio sobre la malla exacta del ráster (criterio *centro de píxel*, `all_touched=False`) y se cuentan píxeles municipio × clase con `bincount`. Las tres capas comparten malla (se comprueba transform, forma y CRS; si no, error).
   - `area_ha = nº píxeles × 25 m² / 10 000`.
   - `area_share = área de la clase / área del polígono municipal en EPSG:25830` (status `derived`).
   - Se excluye nodata (255). Las clases 0 y 99 se conservan con su etiqueta literal.
5. **Capa web** (solo visualización): remuestreo por **moda** a celdas de 200 m, vectorización (`rasterio.features.shapes`, conectividad 4), simplificación Douglas-Peucker 40 m con preservación de topología, `make_valid`, reproyección a EPSG:4326 y redondeo a 4 decimales (~10 m). Props: `class_code`, `class_label`. Se probaron 100 m (18,7–23,6 MB) y 150 m (hasta 10,1 MB); 200 m es el primer valor que deja las tres capas por debajo de 8 MB. Regenerar solo esta parte: `python -m escudo_pipelines.idem.transform --web-only`.
6. **Controles automáticos** (tests): clases de salida = leyenda fuente; geometrías válidas y en lon/lat dentro de la CAM; `0 ≤ share ≤ 1,01` y suma por municipio y capa ≤ 1,01; los 179 municipios con cobertura; superficie con dato del ráster ≈ suma de superficies municipales (±2 %).

## 4. Casos frontera

- Píxeles atravesados por un límite municipal se asignan al municipio que contiene su centro: cada píxel cuenta una sola vez (sin doble conteo). Error máximo por municipio ≈ perímetro × 2,5 m; despreciable a escala municipal.
- Píxeles con dato fuera de todos los polígonos municipales (diferencias entre el límite estadístico de secciones censales y la extensión del ráster) se contabilizan en `pixels_with_data_outside_municipalities` y no se asignan.
- La suma de `area_share` puede superar 1 de forma marginal por la discretización a 5 m; se tolera ε = 0,01 y se verifica en test.

## 5. Limitaciones de escala (obligatorio mostrar en UI)

- Escala de referencia de los metadatos: 1:5 000. La capa web generalizada a 200 m **no** sirve para consultas de parcela o vivienda; para un ámbito concreto se debe calcular el cruce sobre el ráster nativo.
- `area_share` describe la composición del territorio municipal según la capa oficial; **no** es una probabilidad de incendio ni una medida de población o viviendas expuestas.
- Riesgo, peligrosidad y vulnerabilidad son capas distintas y se muestran por separado; ESCUDO no las combina.
- Fecha de la capa: la de los metadatos oficiales (revisión 2025-12-01). No refleja cambios posteriores del territorio.

## 6. Resultado de la ejecución (06/11/2026)

| Salida | Polígonos | Tamaño | Geometrías corregidas | Superficie regional por clase (ráster nativo 5 m) |
|---|---|---|---|---|
| GEO-01 `risk.geojson` | 15149 | 5.0 MB | 0 | 1: 134.853 ha · 2: 85.791 ha · 3: 142.693 ha · 4: 155.418 ha · 5: 267.019 ha · 99: 16.774 ha |
| GEO-02 `hazard.geojson` | 17696 | 5.9 MB | 0 | 1: 158.542 ha · 2: 122.319 ha · 3: 206.678 ha · 4: 175.485 ha · 5: 139.525 ha |
| GEO-03 `vulnerability.geojson` | 6541 | 2.6 MB | 0 | 0: 16.774 ha · 1: 6.819 ha · 2: 226.317 ha · 3: 99.774 ha · 4: 11.339 ha · 5: 441.525 ha |

- `municipal_class_shares.csv`: 2 939 filas. 179 municipios × 3 capas. todos con cobertura. Municipios: 179. 0 geometrías corregidas.
- Píxeles con dato fuera de los polígonos municipales: 150.065 (≈ 375.2 ha). idénticos en las tres capas (misma malla); no se asignan.
- Tiempo: reparto municipal + vectorización ≈ 10 min en portátil; `--web-only` ≈ 1.5 min.
- Tests: `pytest pipelines/tests/test_idem.py` → 15 pasados (6 unitarios sintéticos + 9 sobre salidas reales).
