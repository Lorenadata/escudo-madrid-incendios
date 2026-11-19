# ADR-0005 — Riesgo estimado hoy por municipio

**Estado:** aceptada el 18/11/2026 a petición de Lorena Marcos («podemos calcular el riesgo con los datos que tenemos»).

**Contexto:** AEMET publica el peligro de incendios como un mapa peninsular, sin valor por municipio. El PRD §4.3 prohíbe construir una probabilidad sumando arbitrariamente temperatura, viento y vegetación.

**Decisión:** calcular una estimación separada, `parte del término en clases 4 y 5 de GEO-01 × índice de Fosberg`. El índice es una fórmula publicada, la combinación no usa pesos y las horas desde que la lluvia prevista acumula 0,5 mm no cuentan. Se rotula siempre como estimación de ESCUDO, con estado `derived`, y no como probabilidad ni dato oficial. El mapa oficial y la puntuación de atención no cambian. Método: `docs/current-risk.md`.

**Consecuencias:** el proyecto ofrece una respuesta municipal a «dónde es mayor hoy», pero debe explicar que no está calibrada con incendios de Madrid y que no incluye vegetación ni lluvia acumulada.
