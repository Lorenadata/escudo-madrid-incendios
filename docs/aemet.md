# Integración AEMET — ESCUDO MADRID (A4)

Verificado en red el **06/11/2026 (≈18:45–18:55 UTC)**. Módulo: `pipelines/escudo_pipelines/aemet/`.
Uso: `from escudo_pipelines.aemet import get_weather_context` → dict con el tipo `WeatherContext`
de `docs/contracts/api-contract.md`.

## 1. Fuentes comprobadas

| ID | Producto | URL | Auth | Estado verificado |
|---|---|---|---|---|
| AEMET-PRED-MUN (XML) | Predicción municipal diaria, 7 días | `https://www.aemet.es/xml/municipios/localidad_<INE5>.xml` | Ninguna | **200 OK**, ISO-8859-15, `<elaborado>2026-11-06T17:15:10</elaborado>` para 28079, 28131, 28148. Usa el mismo código INE de 5 dígitos. |
| (XML horario) | Predicción municipal horaria | `https://www.aemet.es/xml/municipios_h/localidad_h_<INE5>.xml` | Ninguna | 200 OK (no integrado aún; candidato para M14) |
| AEMET-PRED-MUN (OpenData) | `GET /api/prediccion/especifica/municipio/diaria/{municipio}` (también `/horaria/`) | `https://opendata.aemet.es/opendata` | Cabecera `api_key` | Sin clave responde **200 con cuerpo vacío** (no 401). Implementado, **no probado con clave real**. |
| AEMET-INC-MAPA | `GET /api/incendios/mapasriesgo/estimado/area/{area}` y `/previsto/dia/{dia}/area/{area}`; `area` = `p` (Península y Baleares) o `c` (Canarias) | idem | `api_key` | Documentado en la especificación oficial; sin clave no verificable. Devuelve un **mapa (imagen)**, no valores por municipio. |

Especificación OpenAPI oficial: `https://opendata.aemet.es/AEMET_OpenData_specification.json`
(visor Scalar en `https://opendata.aemet.es/dist/index.html`; `swagger.json` y `/v2/api-docs` dan 404).
Seguridad declarada: `apiKey` en cabecera `api_key`. Respuestas: `200` → `{descripcion, estado, datos, metadatos}`
(patrón de **dos pasos**: `datos` es una URL temporal con el contenido real; ESCUDO **no reenvía la clave** a esa URL),
`401`, `404` (sin datos), `429` (límite del servicio superado). La especificación no publica cifras de cuota;
**pendiente** medirlas cuando exista clave.

**Clave OpenData:** se obtiene gratis en https://opendata.aemet.es/centrodedescargas/altaUsuario con un email.
Requiere acción humana (no solicitada por el agente). Se configura vía `AEMET_API_KEY` en `.env`, nunca en el repo.

## 2. Condiciones de reutilización

- El XML incluye: «© AEMET. Autorizado el uso de la información y su reproducción citando a AEMET como autora de la misma» y enlaza `https://www.aemet.es/es/nota_legal`.
- La nota legal (Ley 37/2007 modificada por Ley 18/2015) autoriza la reutilización **comercial y no comercial**, con condiciones: no desnaturalizar la información; citar «Fuente: AEMET» / «Información elaborada utilizando, entre otras, la obtenida de la Agencia Estatal de Meteorología» en servicios de valor añadido; **mencionar la fecha de última actualización**; **no sugerir que AEMET participa, patrocina o apoya** el uso; conservar metadatos de actualización.
- Implementación: `WeatherContext.attribution` contiene la cita y la declaración de no patrocinio; `issued_at` siempre visible. La UI debe mostrarlos (A7).

## 3. Contrato devuelto

`status` (`ok`|`stale`|`unavailable`), `provider` (`aemet_opendata`|`aemet_xml_public`|null), `source_id`, `source_url`,
`issued_at` (`<elaborado>`, hora oficial peninsular), `valid_from`/`valid_to` (día natural previsto, Europe/Madrid),
`reference_location` (`ine_code`, `name`, tipo «municipio (predicción AEMET para el término municipal)», `aemet_url`),
`variables` (`Indicator[]`), `fire_danger` (`Indicator` o `null`), `disclaimer`, `attribution`, `last_valid_at`, `message`, `errors`.
Campos añadidos al contrato base: `source_id`, `provider`, `source_url`, `attribution` (obligatorio por licencia), `message`, `errors` — **A0/A6 deben reflejarlos en el modelo Pydantic**.

Variables (día actual):

| indicator_id | Status si vigente | Método |
|---|---|---|
| `weather_temp_max_c`, `weather_temp_min_c` | official | valor publicado |
| `weather_rh_min_pct`, `weather_rh_max_pct` | official | valor publicado |
| `weather_precip_prob_24h_pct` | official | periodo 00-24 publicado (a menudo vacío para el día en curso → `unavailable`) |
| `weather_precip_prob_max_pct` | derived | máximo de subperiodos publicados |
| `weather_wind_max_kmh`, `weather_wind_dir_at_max` | derived | máximo de velocidad media entre periodos |
| `weather_gust_max_kmh` | derived | máximo de rachas publicadas (vacío → `unavailable`) |

Valores vacíos en origen se devuelven `null` con `status: unavailable`; **nunca se interpolan**.
`fire_danger`: sin clave → `null`. Con clave → URL del último mapa oficial (`status: official`) con la advertencia
de que es un ráster peninsular del que **no se extrae un valor por municipio ni por urbanización**. No se calcula
ningún índice propio (PRD §4.3: prohibido sumar temperatura + viento + vegetación).

## 4. Política de caducidad (T05)

| Situación | Resultado |
|---|---|
| Red caída, HTTP ≠ 200, cuerpo vacío/HTML, XML con DTD, municipio distinto | `unavailable`, `variables: []`, `message: "Datos meteorológicos no disponibles"`, `last_valid_at` = último `issued_at` vigente conocido o `null` |
| `issued_at` con más de 24 h, o la predicción no cubre el día actual | `stale`; variables con `status: stale` y su fecha real en `temporal_scope`; `message: "Predicción desactualizada…"` |
| Resto | `ok` |

Caché (`TTLCache`, memoria + disco opcional en `ESCUDO_AEMET_CACHE_DIR`): TTL de red `forecast_municipal` 3 h,
`fire_danger_map` 6 h. La caché solo evita peticiones repetidas; la vigencia se evalúa siempre contra `issued_at`.
Orden de proveedores: OpenData si hay `AEMET_API_KEY` (401/403/429/vacío → se registra en `errors` y se usa el XML); sin clave **no se hace ninguna petición a opendata.aemet.es**.

Seguridad: se rechazan documentos con `<!DOCTYPE>`/`<!ENTITY>` antes de parsear (mitiga XXE/billion laughs con el parser stdlib).

## 5. Tests

`pipelines/tests/test_aemet.py` (14 tests, `httpx.MockTransport`): parseo de captura real, rechazo de municipio
erróneo/DTD/XML roto, contexto OK, caché, red caída sin y con histórico, HTTP 503 y basura, dato caducado → stale,
predicción que no cubre hoy → stale, INE inválido, sin clave no llama a OpenData, OpenData dos pasos (respuesta
**sintética** etiquetada), 429 → fallback a XML, y un test `@pytest.mark.network` en vivo.

## 6. Limitaciones y pendientes

- OpenData y mapas de incendios **no verificados con clave real**: parser OpenData basado en la especificación + estructura conocida; validar con una captura real en cuanto haya clave.
- Sin observaciones (estaciones) ni histórico: M14 requiere `valores/climatologicos` (con clave; retardo de 4 días según metadatos públicos de AEMET).
- La predicción es para el término municipal; no representa una urbanización concreta.
