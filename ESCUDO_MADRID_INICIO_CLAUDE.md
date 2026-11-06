# ESCUDO MADRID — Instrucción inicial para Claude Code / agente orquestador

Lee por completo **`ESCUDO_MADRID_PRD_Maestro.md`** antes de escribir código. El archivo es el contrato principal del producto. Ignora decisiones de arquitectura no justificadas por el PRD; registra divergencias en ADRs.

## Tu misión

Construir un producto funcional y reproducible de prevención y planificación de incendios forestales en la Comunidad de Madrid, con alcance regional, mapa, datos abiertos autonómicos reales, cartografía oficial, integración meteorológica de AEMET, inspecciones, optimizador presupuestario, seguimiento, informes y auditoría. **No crees una demo visual sin backend real ni cifras ficticias disfrazadas de resultados.** El resultado nunca sustituye a Protección Civil o a técnicos competentes.

## Reglas del concurso

La puntuación es **25** puntos por aprovechamiento de datos abiertos del Portal de la Comunidad de Madrid, **20** por originalidad, **25** por impacto, **15** por viabilidad, **10** por software libre/reproducibilidad y **5** por presentación. Fuente: bases adjuntas, sección 10. La entrega final es **26/11/2026 antes de las 14:00**; presentación de **3 diapositivas + 4.ª captura**, defensa **5 min + 5 min preguntas**. La web exige a los equipos inscritos un resumen de máximo 100 palabras **antes del 24/11/2026**.

## Divide el trabajo

Crea issues y ownership de agentes A0–A11, según el capítulo 7 del PRD. Trabaja en paralelo cuando haya contratos claros, integra en `main` diariamente y exige tests y pruebas de procedencia. No permitas que varios agentes cambien migraciones/contratos simultáneamente sin revisión.

## Primera entrega obligatoria de orquestación

1. Árbol del monorepo y Docker Compose ejecutable.
2. Tablero P0/P1 con issues, dependencias, responsables y fecha límite.
3. `COMPLIANCE.md` con cada norma del concurso y su evidencia prevista.
4. `DATA_CATALOG.md` con URL de descarga, fecha, licencia, escala y uso de **datasets del Portal CAM**.
5. Contrato OpenAPI y esquema PostGIS, acordados por backend, frontend, GIS y optimización.
6. Primer recorrido vertical: una ficha real del territorio + inspección + medidas + escenario optimizado + informe.
7. Pipeline CI y tests de integración, GIS, API, privacidad y solver.
8. `EVIDENCE_LOG.md` donde cada equipo registra artefactos verificables que sustentan puntos DATAMAD.

## Condiciones que NO puedes saltarte

- Distinguir **riesgo oficial**, **peligrosidad**, **vulnerabilidad**, **meteorología** y **prioridad administrativa**.
- Jamás atribuir a una urbanización población o riesgos de parcela derivados solo de datos municipales.
- Jamás afirmar «% de incendios evitados» sin modelo y evidencia científica.
- Si AEMET falla, mostrar dato no disponible/caducado, nunca una falsa actualización.
- El producto no puede emitir rutas de evacuación, tácticas de extinción ni certificados PAIF oficiales.
- Todo contenido generado por agentes/IA debe revisarse y su procedencia documentarse.
- El repositorio público debe excluir credenciales, datos privados, datos sin licencia y material inseguro.
- Comprobar los requisitos de asistencia con la organización si hay discrepancias.
- Los participantes del concurso siguen siendo las personas registradas; los agentes son herramientas de trabajo.

## Formato de cada reporte de agente

**Issue / resultado:** …  
**Qué se ha implementado de verdad:** …  
**PR/commits:** …  
**Dataset (fuente, licencia, fecha):** …  
**Tests ejecutados (resultado):** …  
**Prueba visual o URL:** …  
**Puntos DATAMAD respaldados:** …  
**Bloqueadores y limitaciones:** …  
**Siguiente dependencia:** …

**Primera orden:** crea el plan de ejecución y asigna trabajo paralelo. No pidas aprobación para cada pequeña tarea técnica, pero escala de inmediato cambios de alcance, incertidumbres sobre fuentes, seguridad, derecho de uso y afirmaciones públicas.
