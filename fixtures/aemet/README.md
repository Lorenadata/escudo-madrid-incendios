# Fixtures AEMET — capturas REALES

Respuestas reales descargadas sin modificación de la predicción municipal pública de AEMET, usadas
para tests deterministas (no son resultados del producto ni se muestran como actuales).

| Fichero | URL de origen | Capturado (UTC) | `elaborado` (hora oficial) | SHA-256 |
|---|---|---|---|---|
| `localidad_28079.xml` (Madrid) | https://www.aemet.es/xml/municipios/localidad_28079.xml | 2026-11-06 18:49 | 2026-11-06T17:15:10 | `2ab724a5ccd5a668162727d98ee2ac4a80f22f56d91df215b1c29552f7d35bff` |
| `localidad_28148.xml` (Torrejón de Ardoz) | https://www.aemet.es/xml/municipios/localidad_28148.xml | 2026-11-06 18:53 | 2026-11-06T17:15:10 | `92541b86fc9c90acd4c8f181a758489ac161a156778f5eb07a255b0bbf3bb245` |
| `localidad_28131.xml` (San Lorenzo de El Escorial) | https://www.aemet.es/xml/municipios/localidad_28131.xml | 2026-11-06 18:48 | 2026-11-06T17:15:10 | `8ffae095270a5e9ee94b1789c3d63f269f1832426fcd0d0f930751c2ad622ebe` |

Codificación ISO-8859-15. Copyright incluido en el propio XML: «© AEMET. Autorizado el uso de la
información y su reproducción citando a AEMET como autora de la misma». Condiciones: https://www.aemet.es/es/nota_legal

**No hay capturas reales de AEMET OpenData** (no se dispone de `AEMET_API_KEY`). Los tests de
OpenData usan una respuesta **sintética** construida en el propio test y marcada como tal.
