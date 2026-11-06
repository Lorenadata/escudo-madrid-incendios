# ADR-0002 — Una tabla para las tres capas oficiales

**Estado:** aceptada. Las capas de riesgo, peligrosidad y vulnerabilidad comparten esquema; se usa `official_layer_polygons(layer, class_code, class_label, geom)` y `official_layer_municipal_shares` en lugar de tres tablas del PRD §6.3. La separación semántica se mantiene por la columna `layer` y en API/UI.
