# Puntuación de atención preventiva

**Qué es:** un orden de revisión de los 179 municipios, de 0 a 100, derivado de datos oficiales. Responde a «por dónde conviene empezar a mirar».

**Qué no es:** no es riesgo de incendio, ni una probabilidad, ni una alerta. No sustituye al mapa oficial GEO-01 ni a personal técnico. **No usa meteorología:** cambia solo cuando cambian las fuentes. El cruce con el tiempo previsto es un cálculo separado, el «riesgo estimado hoy» (`docs/current-risk.md`).

## Fórmula

`puntuación = 100 × Σ(peso × bloque) / Σ(pesos)`. Cada bloque va de 0 a 1.

| Bloque | Peso | Cálculo | Fuentes |
|---|---:|---|---|
| Territorio | 40 | Parte del término en clases 4 y 5 («alto» y «muy alto»), suma literal | GEO-01 |
| Historial | 20 | Media de dos posiciones entre municipios: siniestros 2015–2024 por km² y superficie quemada por km² | DOC-01, EFF-01, CAM-01 |
| Contexto residencial | 15 | Media de tres posiciones: % de 65 años o más, % de viviendas no principales y % en edificio unifamiliar | CAM-01, CAM-09, CAM-10 |
| Planificación | 25 | Igual a Territorio si no consta plan municipal aprobado; 0 si consta | GEO-01, DOC-01 |

- **Posición:** rango medio entre los municipios con dato (los empates comparten posición).
- **Sin dato:** sin capa oficial no hay puntuación. Si falta otro bloque, se excluye y su peso se reparte. Una casilla vacía del Anexo VI significa «no consta», nunca «No».
- **Tramos fijos:** muy alta ≥ 80, alta ≥ 60, media ≥ 40, baja ≥ 20, muy baja < 20.

## Decisiones y límites

Los pesos son una decisión de ESCUDO, no un dato. Por eso son visibles, se pueden cambiar en `/ranking` y se publica la **estabilidad**: la parte de las 81 combinaciones (cada peso ±10) en las que el municipio sigue entre los 20 primeros.

El dato de planes refleja el Plan Anual 2026: un plan aprobado después puede no figurar. Las variables residenciales son contexto municipal; no describen a ninguna urbanización. Las Zonas de Alto Riesgo se declararon con otro método (tercio de municipios con mayor valor de peligrosidad potencial e importancia de protección, Plan Anual pág. 15), así que quedar fuera de la lista no es un error de la lista.
