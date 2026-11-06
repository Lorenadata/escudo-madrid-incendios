# ADR-0003 — GEO-01/02/03 son ráster, no polígonos

**Estado:** aceptada (A3). La distribución oficial descargable es GeoTIFF uint8 de 5 m (EPSG:25830). El reparto por municipio se calcula sobre el ráster completo (exacto a 5 m); para el mapa web se generaliza a celdas de 200 m y se vectoriza (solo visualización, no consulta por parcela). Ver `docs/spatial-method.md`.
