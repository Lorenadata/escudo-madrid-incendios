# Contenido de la presentación 3 + 1 (bases DATAMAD, ap. 8)

Estructura **obligatoria**: máximo 3 diapositivas de contenido + 4.ª con una captura del sistema. Este fichero es la fuente del texto; el diseño final se monta a partir de aquí.

## Diapositiva 1 — Nombre, participantes y descripción

- **ESCUDO MADRID**
- *Del mapa al plan; del plan a la ejecución comprobable.*
- Participante: **Lorena Marcos**
- Plataforma abierta de planificación preventiva de incendios forestales para municipios y urbanizaciones de la Comunidad de Madrid: contexto oficial → inspección → actuaciones bajo presupuesto → plan con evidencias → informe trazable.
- Pie: herramienta de apoyo; no sustituye a ASEM 112, AEMET, INFOMA ni a personal técnico.

## Diapositiva 2 — Problema, datasets y enlaces

- **Problema:** la información de prevención existe, pero pasar a actuaciones priorizadas, presupuestadas y documentadas exige coordinación entre ayuntamientos, urbanizaciones y técnicos.
- **Contexto (Plan Anual 2026 de la CAM):** 59 municipios declarados Zona de Alto Riesgo (pág. 16); 68 PAIF en 26 municipios, 21 con informe favorable y 47 en tramitación (pág. 52 del PDF); 5.652,38 ha programadas para trabajos preventivos.
- **Portal de Datos Abiertos de la Comunidad de Madrid (11 conjuntos, CC-BY):**
  - CAM-01 Población censada por edad, nacionalidad y sexo — datos.comunidad.madrid/dataset/poblacion_censada_por_edad_nacionalidad_y_sexo
  - CAM-02 Densidad de población — datos.comunidad.madrid/dataset/1930748
  - CAM-03 Altitud — datos.comunidad.madrid/dataset/101002
  - CAM-08 Secciones censales (geometría de los 179 municipios) — datos.comunidad.madrid/dataset/secciones_censales
  - CAM-04 Espacios protegidos · CAM-05 Incendios y superficie afectada · CAM-06 Repoblaciones · CAM-07 Usos del suelo
  - CAM-09 · CAM-10 · CAM-11 Censo 2021: viviendas no principales, edificios con una vivienda, uso según consumo eléctrico
- **Complementarias:** Plan Anual 2026 (Zonas de Alto Riesgo, siniestros 2015–2024 por municipio) · Decreto INFOMA (BOCM) · cartografía oficial IDEM (CC BY 4.0) · EFFIS, áreas quemadas por satélite (CC BY 4.0) · AEMET OpenData (predicción y mapa de riesgo de incendios).
- Diagrama: Portal CAM / IDEM / AEMET → ETL con SHA-256 → PostGIS → API → mapa, optimizador e informes.

## Diapositiva 3 — Resultados, impacto, viabilidad y enlaces

- **Resultados verificables:** 179 municipios con indicadores trazables · reparto exacto de las clases oficiales de riesgo por municipio · optimizador determinista validado contra la solución exacta en 200 instancias · expediente INFOMA de 15 puntos con cita literal · normativa con citas (18/20) · 159 pruebas automáticas (129 de datos, API y optimizador; 30 de navegador, incluida accesibilidad WCAG 2.1 AA) · instalación limpia en ~9 min.
- **Caso guiado (datos ficticios):** con el mismo presupuesto, la optimización cubre el 90,1 % de la prioridad técnica frente al 84,2 % (priorización manual) y el 85,1 % (menor coste).
- **Impacto que medimos:** cobertura de prioridades bajo presupuesto, actuaciones documentadas con evidencia, plazos vencidos, reproducibilidad. **No** afirmamos incendios evitados ni reducción de riesgo.
- **Viabilidad:** software libre (EUPL-1.2), Docker, datos abiertos, multiusuario aislado, modo degradado si AEMET cae.
- Enlaces: **demo: https://lorenadata-escudo-madrid.hf.space** · **repositorio: https://github.com/Lorenadata/escudo-madrid-incendios** (EUPL-1.2).

## Diapositiva 4 — Captura del sistema

Usar `artifacts/demo-screenshots/02-ficha-riesgo-oficial.png` (mapa + ficha + capa oficial). Alternativa: `04-comparacion-estrategias.png`. Debe ser una pantalla que exista en la versión entregada.
