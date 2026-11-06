---
title: "ESCUDO MADRID | Documento maestro de producto y ejecución"
subtitle: "DATAMAD 2026 — Especificación integral para Claude y equipos de agentes"
version: "1.0 — 06/11/2026"
status: "Especificación de desarrollo; no acredita funcionalidades implementadas"
---

# ESCUDO MADRID
## Documento maestro de producto, datos, ingeniería y competición — DATAMAD 2026

**Versión:** 1.0 · **Fecha de corte:** 6 de noviembre de 2026 · **Propietaria del proyecto:** equipo participante inscrito · **Destino:** Claude Code y agentes de investigación, datos, IA, geoespacial, backend, frontend, calidad y presentación.

> **MISIÓN:** Construir una plataforma regional de inteligencia y gestión de la prevención de incendios forestales para la Comunidad de Madrid. Convertir datos públicos verificables y aportaciones de profesionales en decisiones explicables sobre **qué revisar, qué actuaciones planificar, cómo distribuir un presupuesto y cómo demostrar su ejecución**. El producto debe ser funcional, reproducible, demostrable y útil después de DATAMAD.

**Principio rector:** amplitud de producto, profundidad real y cero funcionalidades simuladas presentadas como operativas. La plataforma aspirará a cubrir la Comunidad de Madrid con datos regionales, diferenciando claramente la precisión municipal de la precisión por zona o parcela. No es una herramienta de dirección de emergencias ni sustituye a ASEM 112, AEMET, INFOMA o personal técnico competente.

---

# 1. BASES DE DATAMAD: CONTRATO OBLIGATORIO PARA TODO AGENTE

**FUENTE PRIMARIA:** documento adjunto del usuario, *Bases de participación DATAMAD 2026* (9 páginas, apartados 1–22), y *DATAMAD Programa 2026 actualizado* (4 páginas). **ACTUALIZACIÓN WEB:** https://eventos.urjc.es/155632/ — consultada el 6/11/2026. Si hay conflicto entre página y bases, registrar discrepancia y consultar a la organización, no asumir una interpretación no confirmada.

## 1.1. Puntuación oficial incluida en las bases (100 puntos)

| Criterio | Puntos | Qué entregará ESCUDO MADRID como prueba evaluable | Responsable |
|---|---:|---|---|
| Uso y aprovechamiento de datos abiertos del Portal de la Comunidad de Madrid | **25** | Descarga, transformación y uso causal/analítico de varios datasets del portal autonómico; catálogo de fuentes, lineage, consultas reproducibles y pantallas que dependen de esos datos | Datos + GIS |
| Originalidad e innovación | **20** | Sistema multiusuario de planificación preventiva con inteligencia territorial + meteorología + optimización + seguimiento verificable; comparativa documentada frente a soluciones ya existentes | Producto + investigación |
| Potencial impacto económico, social, tecnológico o medioambiental | **25** | Problema real, usuarios objetivo, mediciones de planificación, cobertura de medidas, transparencia y métricas sin cifras inventadas | Producto + validación |
| Viabilidad y aplicabilidad de la solución | **15** | Despliegue funcional end-to-end, flujos terminados, costes y arquitectura razonables, datos actuales o modos degradados | Ingeniería + QA |
| Uso de tecnologías abiertas, código abierto y reproducibilidad | **10** | Repositorio público depurado, licencia compatible, contenedores, ETL reproducible, README, tests, trazabilidad de datos y modelo | DevOps + QA |
| Calidad y claridad de la presentación | **5** | 3 diapositivas de contenido + 4.ª captura, demo en 5 minutos, 5 minutos de respuestas y material de respaldo | Pitch + líder |
| **TOTAL** | **100** | | |

**Desempate:** prioridad sucesiva a (1) intensidad del uso de datos de Madrid, (2) impacto, (3) originalidad y (4) viabilidad. Fuente: bases, apartado 10, pp. 4–5. Los agentes deben optimizar *evidencias demostrables*, no características cosméticas.

## 1.2. Requisitos de admisión y legales

1. **Obligatorio:** utilizar de forma efectiva **al menos un conjunto de datos del Portal de Datos Abiertos de la Comunidad de Madrid** (https://datos.comunidad.madrid/). Las capas de IDEM, AEMET, Copernicus y otras fuentes son complementarias; por sí solas no sustituyen esta condición.
2. Identificar todos los datasets utilizados y preservar URL, productor, fecha de extracción, licencia, fecha de actualización, ámbito, unidades, cobertura y transformaciones.
3. Respetar licencias de datos, mapas, fotografías, modelos, código, librerías, APIs y contenidos; sin scraping ilícito ni datos privados no autorizados.
4. Presentar en plazo, explicar funcionamiento, metodología y utilidad; sin plagio, resultados falsos ni fuentes inventadas.
5. El uso de IA generativa y asistentes de programación **está expresamente permitido**; cada resultado sigue siendo responsabilidad del equipo.
6. Se permite reutilizar recursos preexistentes si se identifican correctamente, pero el trabajo presentado debe desarrollarse o evolucionar **sustancialmente entre el 7 y el 26 de noviembre de 2026**. Mantener `PROVENANCE.md` y changelog de commits con fecha.
7. Derechos del proyecto corresponden a sus autores, sin perjuicio de licencias de terceros. Se valora positivamente publicar desarrollo bajo licencia abierta.
8. No publicar información personal, vulnerabilidades de infraestructuras ni detalles operativos sensibles sin autorización. No presentarse como producto homologado por Protección Civil.
9. La participación es de personas físicas; equipo identificado antes del cierre. Cambios de integrantes: bases indican límite 7/11/2026 y autorización excepcional para incorporaciones posteriores.
10. Los premios son **3.000 €, 2.000 € y 1.000 € brutos**, sujetos a obligaciones fiscales; se reparten por igual entre miembros del equipo. No afirmar que el premio íntegro corresponde a una persona si hay varios inscritos.

## 1.3. Fechas y entregables oficiales

| Hito | Requisito | Estado / acción |
|---|---|---|
| **5/11/2026** | Cierre de inscripción de proyectos | **CERRADO a la fecha de este documento.** Confirmar que los integrantes figuran inscritos. |
| 5–6/11/2026 | Formación | Comprobar asistencia/condiciones si se buscan ECTS. |
| **7–26/11/2026** | Periodo oficial de desarrollo | Registrar aquí la creación/evolución sustancial del trabajo. |
| **Antes del 24/11/2026** | Según la web oficial: resumen de **máximo 100 palabras**, título, integrantes y confirmación de presencia | Preparar y remitir a través del procedimiento que comunique la organización. La web indica preselección de hasta 50 y presentación de 12 ante el jurado. |
| **26/11/2026 antes de las 14:00** | Entrega oficial por plataforma habilitada | Subir presentación y enlaces funcionales; no depender de última hora. |
| **26/11/2026** | Defensa presencial | **5 minutos** de exposición + **5 minutos** de preguntas. |

**Formato de presentación según las bases, apartado 8:** **máximo 3 diapositivas de contenido**: (1) nombre, participantes, descripción; (2) problema, datasets y enlaces; (3) resultados, impacto, viabilidad y enlace de demo/repositorio. **4.ª diapositiva** con una captura del sistema. Esta distribución es obligatoria aunque el equipo disponga de muchas pantallas y análisis.

**Discrepancia de asistencia:** las bases (apartado 9) exigen presencia de todos los componentes salvo causa justificada; la página actualizada señala al menos una persona presencial por equipo. Escalar al contacto oficial **madrid.datamad@urjc.es** para resolverlo. El programa sitúa la jornada final en el campus de Vicálvaro de la URJC.

**Uso interno de puntuación:** cada pull request debe indicar a qué criterio contribuye, con evidencia verificable (captura, test, métrica o fuente). No convertir la puntuación en estimaciones falsas de la calificación del jurado.

---

# 2. VISIÓN ESTRATÉGICA Y DIFERENCIACIÓN

## 2.1. Problema real

La Comunidad de Madrid ya dispone de cartografía oficial de riesgo/peligrosidad/vulnerabilidad, un Plan anual de prevención, información meteorológica y personal especializado. El problema que abordamos es la **fragmentación entre conocimiento territorial y ejecución verificable de medidas preventivas** por parte de ayuntamientos, gestores de urbanizaciones e inspecciones técnicas. Debe confirmarse mediante entrevistas que sus sistemas actuales no lo resuelven suficientemente.

El *Plan Anual 2026* documenta **5.652,38 ha programadas para trabajos preventivos**; además identifica **68 PAIF realizados** de distintas tipologías en 26 municipios, de los cuales 21 cuentan con informe favorable y 47 están en tramitación a la fecha del plan. Estos números contextualizan el trabajo administrativo y preventivo; **no equivalen** a un déficit demostrado ni a todas las urbanizaciones afectadas. Fuente: Plan anual 2026, apartado 9.2 y tabla de indicadores de prevención.

## 2.2. Propuesta única de valor

**«Del mapa al plan; del plan a la ejecución comprobable».** Un sistema común que:

1. Integra varias fuentes geográficas, estadísticas y meteorológicas **sin confundir escalas ni significados**.
2. Identifica áreas y activos para **revisión preventiva prioritaria**, no «viviendas seguras/inseguras».
3. Organiza inspecciones y registro de evidencias.
4. Convierte acciones revisadas por personal competente en escenarios de presupuesto con optimización transparente.
5. Mantiene seguimiento, responsables, revisiones y exportación de expedientes.
6. Expone métricas de resultado **operativo** (cobertura de tareas, tiempo de planificación, auditabilidad), no supuestos de incendios evitados.

## 2.3. Comparativa con alternativas existentes

- **Geoportal/IDEM, Protección Civil, INFOMA:** proporcionan cartografía, planes y gestión pública. ESCUDO no pretende sustituirlos; añade flujo de trabajo y optimización de actuaciones propuestas por técnicos.
- **AEMET:** proporciona meteorología e índices oficiales. ESCUDO los consume y comunica con sus límites, no emite alertas propias de emergencia.
- **FIREPRIME (UPC):** autoevaluación de vulnerabilidad de viviendas y recomendaciones. ESCUDO se diferencia por **planificación colectiva, multiusuario, presupuesto, seguimiento y documentación**. Verificar adicionalmente durante la investigación si existen otras herramientas municipales o comerciales con estas funciones.

**Hipótesis de demanda por validar:** una urbanización/municipio mejorará tiempo, cobertura y trazabilidad frente a su proceso actual. No afirmar uso institucional, aval o interés del Gobierno regional sin autorización escrita.

## 2.4. Usuarios y permisos

| Rol | Objetivo | Permisos generales |
|---|---|---|
| Visitante público | Consultar información territorial agregada y aprender | Mapas generales, fuentes, información pública; sin datos privados |
| Gestor de urbanización | Mantener inventario, tareas y presupuestos | Solo su organización; crear borradores, adjuntar evidencias, exportar |
| Técnico competente | Validar inspecciones y medidas | Revisar, firmar/atestiguar revisión **solo si su función y cualificación están verificadas**; firma digital no equivale a aprobación administrativa |
| Responsable municipal | Consultar áreas y planes de su ámbito | Panel municipal, expedientes de su competencia, comparativas |
| Analista/investigador | Auditar métricas y metodología | Acceso a datasets autorizados y resultados reproducibles |
| Administrador del sistema | Gestionar fuentes, usuarios y calidad | Permisos mínimos, auditoría completa y acceso restringido |

---

# 3. ALCANCE DEL PRODUCTO COMPLETO

El objetivo es un **producto integrado y real** para municipios y urbanizaciones de la Comunidad de Madrid, no una maqueta. Construir muchos módulos solo aporta valor si comparten datos y funcionan conjuntamente. Prioridad de ejecución: primero la columna vertebral completa; después amplitud, siempre manteniendo una versión desplegable.

## 3.1. Módulos funcionales

| ID | Módulo | Funcionalidad terminada esperada | Prioridad para DATAMAD |
|---|---|---|---|
| M01 | Acceso y organizaciones | Autenticación, pertenencia a organización, roles, permisos, auditoría | P0 |
| M02 | Explorador regional | Mapa CAM con municipios, filtros, leyenda, capas y fuentes | P0 |
| M03 | Fichas territoriales | Riesgo/peligrosidad/vulnerabilidad **oficiales**, indicadores municipales y explicación de escalas | P0 |
| M04 | AEMET y contexto diario | Pronóstico, variables y mapa/índice oficial disponible; fecha, validez, caducidad | P0 |
| M05 | Inventario de ámbitos | Urbanizaciones/zonas, geometría autorizada, activos sin exposición de datos privados | P0 |
| M06 | Inspecciones | Checklists configurables, observaciones, fotografías, evidencias y revisión técnica | P0 |
| M07 | Catálogo de medidas | Actuaciones preventivas parametrizadas, costo, unidad, referencias normativas, prerequisitos | P0 |
| M08 | Escenarios y optimizador | Selección de medidas bajo presupuesto y restricciones; comparación con baseline | P0 |
| M09 | Plan de ejecución | Responsable, vencimiento, estado, costes reales, evidencia, historial y control de cambios | P0 |
| M10 | Informes y exportaciones | PDF de escenario, fuentes, limitaciones, export CSV/GeoJSON cuando proceda | P0 |
| M11 | Calidad y procedencia | Ficha por fuente, licencia, última actualización, cobertura, fallo del conector | P0 |
| M12 | Panel de impacto | KPIs operativos y comparación antes/después del flujo | P0 |
| M13 | Comparador geográfico | Dos municipios o áreas lado a lado, misma escala y fecha | P1 |
| M14 | Histórico y estacionalidad | Series AEMET/incendios disponibles y escenarios históricos documentados | P1 |
| M15 | Revisión de PAIF/PAMIF | Referencias, expedientes y lista de información pendiente, sin generar aprobación jurídica | P1 |
| M16 | Calendario preventivo | Programación de inspecciones, recordatorios no críticos, revisión anual | P1 |
| M17 | Colaboración | Comentarios, asignación, adjuntos, registro de decisiones | P1 |
| M18 | Portal público | Información pedagógica y avances agregados sin divulgar vulnerabilidades privadas | P1 |
| M19 | Asistente de consulta documental | Búsqueda con citas sobre fuentes oficiales y normativa; nunca toma decisiones operativas | P1 |
| M20 | API de reutilización | Endpoints documentados, exportación reproducible, OpenAPI | P1 |
| M21 | Accesibilidad y móvil | UI responsive, teclado, contraste, estados vacíos, PWA para inspecciones | P1 |
| M22 | Observabilidad | Logs, métricas de latencia, fallos de ETL, estado de AEMET, backups | P0 |

**P0:** bloqueo de competición si no funciona. **P1:** ampliar en paralelo solo después de asegurar arquitectura e integración. **P2 futuro:** visión artificial sobre parcelas con consentimiento y revisión experta, nuevos algoritmos validados, integración administrativa, trabajo de campo sin conexión y seguimiento remoto de vegetación. Nunca presentarlos como disponibles si no están implementados.

## 3.2. Viajes de usuario que deben funcionar end-to-end

**Flujo A — Gestor de urbanización:** iniciar sesión → seleccionar urbanización → visualizar contexto oficial y meteorológico → crear inspección → registrar medidas propuestas → introducir precios o presupuestos → optimizar → comparar alternativas → confirmar plan → asignar tareas → adjuntar evidencia → exportar informe.

**Flujo B — Responsable municipal:** seleccionar municipio → comprobar estado de fuentes y de las actuaciones registradas → comparar zonas con datos a escala correcta → abrir expediente autorizado → revisar prioridades y cobertura presupuestaria → descargar informe con trazabilidad.

**Flujo C — Evaluador DATAMAD:** abrir demo pública sin credenciales → ver mapa regional real → seleccionar caso guiado con datos reconocibles → consultar procedencia de cada indicador → observar escenario de presupuesto y comparación automática → ver una tarea con evidencia de ejemplo **etiquetada como ficticia** → descargar un informe reproducible.

**Flujo D — Investigador/a:** clonar repositorio → ejecutar scripts de ingestión sobre recursos abiertos → obtener métricas y capas versionadas → ejecutar tests y un escenario determinista → reproducir cifras de la presentación.

## 3.3. Diseño del producto

- Identidad sobria, institucional y contemporánea; no emular logotipos de la Comunidad de Madrid ni insinuar colaboración oficial.
- Mapa como elemento central; panel lateral de filtros, ficha contextual con fuente y fecha; leyenda visible y accesible.
- Distinguir visualmente: **dato oficial**, **dato aportado por usuario**, **estimación**, **simulación**, **no disponible** y **desactualizado**.
- Incluir una vista de incertidumbre / límites de resolución; no mostrar mapas de precisión de vivienda cuando el dato solo es municipal.
- Todos los resultados sensibles deben tener explicación y botón «Ver método y fuentes».

---

# 4. CATÁLOGO DE DATOS: FUENTES COMPROBADAS Y BRECHAS

**REGLA:** el agente de datos comprobará URL exacta de descarga, esquema, granularidad, cobertura, licencia y vigencia antes de integrar. Un catálogo publicado no demuestra que todos sus campos estén disponibles o sirvan a escala urbanización. Todas las fechas de ingestión deben registrarse.

## 4.1. Datos autonómicos del Portal de Datos Abiertos — OBLIGATORIOS

| Código | Dataset verificado | URL de catálogo | Uso de verdad en el producto | Advertencia |
|---|---|---|---|---|
| CAM-01 | Población censada por edad, nacionalidad y sexo. Censo anual. Municipios | https://datos.comunidad.madrid/dataset/poblacion_censada_por_edad_nacionalidad_y_sexo | Contexto demográfico, distribución por edades y perfiles **municipales** | No inferir personas o viviendas expuestas sin desagregación adecuada |
| CAM-02 | Densidad de población. Municipios | https://datos.comunidad.madrid/dataset/1930748 | Caracterización comparativa de municipios y normalización territorial | Municipios, no parcela |
| CAM-03 | Altitud. Municipios | https://datos.comunidad.madrid/dataset/101002 | Contexto de elevación administrativa; solo a escala municipal | No sustituye un modelo digital de elevaciones para pendientes |
| CAM-04 | Espacios protegidos | https://datos.comunidad.madrid/dataset/espacios_protegidos | Catálogo y enlace a zonas de interés ambiental; integrar espacialmente **solo si** geometría disponible y consistente | Verificar si el recurso es listado sin geometría |
| CAM-05 | Incendios y superficie afectada | https://datos.comunidad.madrid/dataset/101019 | Serie contextual histórica, escala/alcance real según fichero | Metadatos indican ámbito nacional; no atribuir granularidad municipal |
| CAM-06 | Repoblaciones forestales | https://datos.comunidad.madrid/dataset/repoblaciones_forestales | Contexto histórico de trabajos de restauración | Puede ser solo serie agregada regional |

**Obligación adicional para obtener los 25 puntos:** construir por lo menos **dos funciones analíticas** cuyo resultado cambie al actualizar CAM-01 / CAM-02 u otro recurso autonómico: (a) ficha municipal de contexto demográfico con año y unidades; (b) filtro o comparador regional documentado y reproducible. Si los datos del portal solo aparecen como decoración en una tabla, no está cumplido el objetivo de aprovechamiento.

## 4.2. Cartografía regional IDEM y Geoportal — complemento esencial

| Código | Recurso | Fuente | Uso |
|---|---|---|---|
| GEO-01 | Riesgo por incendios forestales | https://datos.gob.es/es/catalogo/a13002908-riesgo-por-incendios-forestales | Capa de **riesgo oficial** (sin recalcular ni renombrar categorías) |
| GEO-02 | Peligrosidad por incendios forestales | https://datos.gob.es/es/catalogo/a13002908-peligrosidad-por-incendios-forestales | Capa **peligrosidad** (distinta del riesgo) |
| GEO-03 | Vulnerabilidad por incendios forestales | https://datos.gob.es/es/catalogo/a13002908-vulnerabilidad-por-incendios-forestales | Capa **vulnerabilidad** (distinta de peligrosidad) |
| GEO-04 | Geoportal CAM / visor Protección Civil | https://www.comunidad.madrid/geoportal | Descubrimiento de servicios y metadatos, WMS/descarga cuando esté permitida |
| GEO-05 | Plan anual y anexos 2026 | https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf | Reglas, contexto territorial, municipios ZAR, trabajos previstos, PAIF/PAMIF |

**Importante:** el Geoportal y los datasets de protección civil están publicados por la Comunidad, pero varios aparecen distribuidos mediante IDEM/datos.gob.es, **no necesariamente como datasets de CKAN**. El agente de compliance deberá conservar pruebas de uso separado del Portal de Datos Abiertos.

## 4.3. Meteorología AEMET — contexto temporal

- **API oficial:** https://www.aemet.es/es/datos_abiertos/AEMET_OpenData
- **Documentación de endpoints:** https://opendata.aemet.es/dist/
- **Interpretación oficial de peligro:** https://www.aemet.es/es/eltiempo/prediccion/incendios/ayuda
- **Mapa público:** https://www.aemet.es/es/eltiempo/prediccion/incendios

**Fuentes a implementar:** predicción municipal cuando haya cobertura útil, observaciones disponibles y mapas oficiales de peligro de incendios. La documentación publica endpoints `api/incendios/mapasriesgo/estimado/area/{area}` y `.../previsto/dia/{dia}/area/{area}`. Verificar autenticación, cuotas, formato, permisos de redistribución y uso de mapas antes de codificar. No dar por hecho que un mapa-ráster equivale a un valor exacto por urbanización.

**Variables explicativas:** temperatura, humedad relativa, viento, precipitación; el producto oficial de peligro integra otras variables. NO construir una probabilidad de incendio sumando arbitrariamente temperatura + viento + vegetación. Mostrar la fecha de emisión, horizonte de validez, localización de referencia y la advertencia de que es un índice de peligro, no pronóstico de ignición o evacuación.

**Política de caducidad:** cada tipo de recurso declarará su TTL según vigencia oficial. Si AEMET falla o no hay observación válida, mostrar `Datos meteorológicos no disponibles` con fecha de último dato y no reutilizar silenciosamente información antigua.

## 4.4. Otras fuentes opcionales, no sustitutivas

- **Copernicus EMS/EFFIS:** https://forest-fire.emergency.copernicus.eu/ — contexto de incendios históricos/áreas quemadas y capas satelitales si licencias y resolución lo permiten; no mezclar perímetros provisionales con daños certificados.
- **CNIG/IGN:** modelos digitales de elevación y límites administrativos, si se necesita pendiente o relieve real.
- **MITECO / EGIF:** https://www.miteco.gob.es/es/ministerio/servicios/estadisticas/estadisticas-forestales/incendios-forestales.html — series históricas con límites de actualización y accesibilidad.
- **Catastro:** solo datos abiertos autorizados; no difundir datos personales ni inferir propietarios.
- **Documentos PAIF/PAMIF aportados voluntariamente:** acceso controlado, no publicación automática, autorización expresa, revisión legal.

## 4.5. Tabla de trazabilidad por indicador (obligatoria)

Cada indicador que aparece en pantalla debe tener: `indicator_id`, etiqueta, definición, unidad, ámbito espacial, ámbito temporal, `source_id`, fecha fuente, versión, frecuencia de actualización, tratamiento de nulos, transformación SQL/Python, advertencias y `status` (`official`, `derived`, `scenario`, `user_reported`, `unavailable`).

**Ejemplos:**
- `official_fire_risk_class`: clase literal de GEO-01 para un polígono válido. No transformar en una probabilidad anual.
- `municipality_age_65_plus_share`: proporción de población municipal por edad de CAM-01; **no** número de personas mayores en la urbanización.
- `review_priority_index`: puntuación de cola para solicitar revisión, definida por el equipo, **no** índice oficial de peligro; fórmula, pesos, incertidumbre y aprobación técnica documentadas.
- `budget_allocation_result`: selección de actuaciones del catálogo conforme a restricciones, **no** reducción cuantificada del riesgo real.

---

# 5. MOTOR ANALÍTICO, CIENCIA DE DATOS Y VALIDACIÓN

## 5.1. Pipeline geoespacial

1. Descarga con metadatos y checksum SHA-256.
2. Validación de formato, geometrías, CRS/SRID, unidad, fechas, licencias y duplicados.
3. Normalización de códigos de municipio (INE) y nombres; resolver manualmente inconsistencias.
4. Reproyección a CRS métrico apropiado para medición local; conservar geometría original y registrar transformación.
5. Cruces espaciales con `intersection`, `within` o área de solapamiento según definición; registrar casos frontera y geometrías inválidas.
6. Agregación territorial manteniendo separadas las escalas municipal, zona y urbanización autorizada.
7. Materialización de tablas y vectores para API, y caché/teselas para mapa.
8. Validaciones automáticas de conteos, rangos, topología, nulidad y regresión sobre ejemplos conocidos.

**Nunca:** distribuir la población municipal de forma uniforme por urbanización o contar viviendas expuestas sin parcelario y método válido.

## 5.2. Estructura del conocimiento de riesgo

- **Peligrosidad oficial (GEO-02):** mostrar clase publicada.
- **Vulnerabilidad oficial (GEO-03):** mostrar clase publicada.
- **Riesgo oficial (GEO-01):** mostrar resultado publicado; no duplicar un modelo implícito.
- **Contexto AEMET:** temporal, con periodo válido y limitaciones.
- **Prioridad de revisión ESCUDO:** cola administrativa/operativa basada en estado de tareas, fechas vencidas, inspecciones pendientes y prioridades **asignadas por técnicos**. No denominarla «riesgo de incendio».

Si se propone un modelo propio de ML, debe explicar variable objetivo, disponibilidad de etiquetas, separación temporal/espacial, fuga de datos, calibración, comparación con baseline y coste de errores. **No introducir Random Forest/XGBoost/LLM por marketing** cuando un enfoque determinista sea más fiable.

## 5.3. Optimizador presupuestario

Para cada actuación `i`: coste `c_i`, prioridad técnica `p_i`, beneficio operativo o cobertura verificable `b_i`, plazo, dependencia, exclusión y elegibilidad. Variables binarias `x_i ∈ {0,1}`. Modelo base:

`max Σ (p_i × b_i) × x_i`, sujeto a `Σ c_i × x_i ≤ B` y restricciones de precedencia, compatibilidad, recursos, plazos y elegibilidad.

**Advertencia:** `p_i × b_i` es una **función objetivo acordada**, no una estimación científica de incendios evitados. Los pesos deben ser transparentes, editables para técnicos y comparables bajo análisis de sensibilidad. Si `b_i` carece de fundamento, optimizar cobertura de tareas prioritarias, no «reducción de riesgo».

Comparar al menos tres escenarios: (a) priorización manual/base, (b) menor coste primero y (c) modelo optimizado; idealmente explorar alternativas Pareto coste/cobertura. Mostrar sensibilidad a variación de presupuestos y costes. No usar presupuesto ficticio como si fuera adjudicación real.

## 5.4. Meteorología e histórico

- Panel diario informativo: condición emitida por AEMET + sello horario + «no es una alerta operativa».
- Escenarios retrospectivos: seleccionar fecha histórica realmente disponible, congelar la fecha de corte y evitar fuga de información posterior.
- No entrenar un predictor de ignición a escala urbanización con etiquetas agregadas regionales.
- Diferenciar **observación**, **pronóstico**, **simulación** y **dato faltante**. Si la API no provee histórico suficiente, mostrar un caso histórico solo con datos que sí sean recuperables y verificables.

## 5.5. Validación científica y de producto

**Validación de datos:** cobertura por fuente, actualidad, geometrías válidas, errores de unión, valores fuera de rango y anomalías documentadas.

**Validación del optimizador:** casos pequeños resueltos manualmente, restricciones inviolables, presupuestos nunca excedidos, reproducibilidad con semilla/versión y comparación con baseline.

**Validación con profesionales:** entrevistas con un técnico forestal/protección civil y, cuando sea posible, un gestor de urbanización o municipio. Registrar si las recomendaciones se consideran útiles, inviables, redundantes o necesitadas de revisión.

**Experimento de utilidad:** tarea realista con/ sin ESCUDO, misma información y presupuesto; medir tiempo de planificación, omisiones, cobertura de tareas prioritarias, calidad de documentación y percepción de utilidad. Identificar si es ensayo interno y tamaño de muestra; no extrapolar causalmente a toda Madrid.

**KPIs permitidos:** tiempo medido, porcentaje de actuaciones documentadas, tareas priorizadas dentro de presupuesto, número de fuentes utilizadas, porcentaje de escenarios reproducibles, éxito de tareas de usuario, disponibilidad de datos.

**KPIs NO permitidos sin investigación rigurosa:** «incendios evitados», «vidas salvadas», «reducción del riesgo en 37 %», «hectáreas protegidas efectivamente» o «ahorro público real» sin evidencia.

---

# 6. ARQUITECTURA TÉCNICA RECOMENDADA

## 6.1. Stack

| Capa | Elección | Motivo |
|---|---|---|
| Frontend | Next.js + TypeScript + Tailwind + MapLibre GL JS | Plataforma web ágil, mapas interactivos, buen DX |
| Backend | FastAPI + Pydantic + SQLAlchemy | API tipada, ecosistema científico Python |
| Datos | PostgreSQL + PostGIS | Geometrías, consultas espaciales, índices |
| ETL | Python + GeoPandas + pandas/Polars + rasterio según datos | Integración de fuentes y tests |
| Optimizador | OR-Tools CP-SAT o PuLP | Restricciones reproducibles y transparentes |
| Procesos en background | Redis + RQ/Celery o tareas programadas simples | Actualización de datos y generación de informes |
| Almacenamiento | S3 compatible para evidencias; almacenamiento local seguro en desarrollo | Archivos con controles de acceso |
| Testing | pytest, Playwright, mypy/ruff, ESLint | Calidad e2e, tipado, seguridad de regresión |
| Despliegue | Docker Compose + hosting europeo adecuado | Reproducibilidad y control |
| Observabilidad | OpenTelemetry opcional + logs estructurados + error tracking | Diagnóstico de incidencias |
| Asistente IA | RAG opcional sobre fuentes verificadas | Explicación documental con citas; nunca decisiones de emergencia |

**No añadir servicios nuevos sin justificar un caso de uso y coste.** Primero se exige un recorrido completo operable, luego se habilitan prestaciones adicionales.

## 6.2. Flujos de información

`Portal CAM / IDEM / AEMET / fuentes autorizadas → conectores ETL → capa raw versionada → validación y normalización → PostGIS + tablas analíticas → servicios FastAPI → Next.js/MapLibre → informes, planificador y auditoría`.

Ramas separadas para **datos públicos** y **datos privados de cada organización**. El sistema nunca mezcla registros internos de terceros ni devuelve datos de una organización a otra.

## 6.3. Modelo de datos mínimo

- `data_sources`, `dataset_versions`, `ingestion_runs`, `data_quality_checks`.
- `municipalities`, `official_risk_polygons`, `official_hazard_polygons`, `official_vulnerability_polygons`, `protected_areas`.
- `weather_snapshots`, `weather_forecasts`, `fire_history_series`.
- `organizations`, `users`, `memberships`, `areas_of_interest`, `assets`.
- `inspections`, `inspection_items`, `evidence_files`, `professional_reviews`.
- `measures_catalog`, `measure_dependencies`, `quotes`, `scenarios`, `scenario_options`, `scenario_results`.
- `action_plans`, `plan_actions`, `assignments`, `audit_events`, `reports`.

Reglas: `source_id` en analítica, `organization_id` y autorización en datos privados, `created_at/updated_at`, `record_status`, idempotencia de ETL y claves estables.

## 6.4. API mínima

- `GET /v1/sources` y `/v1/sources/{id}`: procedencia y salud.
- `GET /v1/municipalities`, `/v1/municipalities/{code}/profile`.
- `GET /v1/layers`, `/v1/layers/{name}/tiles-or-geojson`.
- `GET /v1/weather/context?municipality_code=...`.
- `POST /v1/areas`, `GET /v1/areas/{id}` con autorización.
- `POST /v1/inspections`, `POST /v1/inspections/{id}/evidence`.
- `GET /v1/measures`, `POST /v1/scenarios`, `POST /v1/scenarios/{id}/solve`.
- `POST /v1/action-plans`, `PATCH /v1/action-plans/{id}/actions/{action_id}`.
- `GET /v1/reports/{id}` y `GET /health`.

API OpenAPI generada y contratos de ejemplo. Endpoint `solve` **determinista** en casos de prueba y con indicador claro cuando se usan presupuestos de demostración.

## 6.5. Seguridad y privacidad

- Principio de mínimo privilegio, aislamiento multi-tenant y controles por cada consulta.
- Datos personales minimizados; consentimiento/contrato aplicable; evitar publicar direcciones exactas o detalles de seguridad de hogares sin base legal.
- Evidencias con almacenamiento privado, cifrado de secretos y URLs firmadas de corta duración.
- Auditoría de cambios sobre prioridad, presupuestos, informes y aprobación técnica.
- Limitar/validar archivos, sanear inputs, throttling, protección de API keys AEMET y restauración de backups.
- Asistente IA con recuperación de fuentes y filtrado; no exponer datos de otros usuarios ni permitirle crear certificados oficiales.
- No generar instrucciones tácticas de extinción ni evacuaciones individualizadas; remitirse siempre a avisos y servicios oficiales.

---

# 7. PLAN DE AGENTES: TRABAJO EN PARALELO SIN ROMPER INTEGRACIONES

**Líder de producto humano:** valida prioridades, datos usados, metodologías y afirmaciones públicas. Los agentes no pueden dar por aprobado un análisis por sí mismos.

| Agente | Responsabilidad | Entregable principal | Depende de |
|---|---|---|---|
| A0 — Orquestación / PM | Alcance, ADR, integración, PR review, seguimiento de scoring | `ROADMAP.md`, tablero, release checklist | Ninguno |
| A1 — Bases / Research | Matriz de compliance, competencia FIREPRIME/IDEM, fuentes normativas | `COMPLIANCE.md`, `COMPETITORS.md` | Ninguno |
| A2 — Open Data | Verificar CKAN, licencias, extracción, ETL y catálogo | Scripts ETL + `DATA_CATALOG.md` | Ninguno |
| A3 — GIS | Importar IDEM, CRS, PostGIS, tiles, controles topológicos | Mapas y `SPATIAL_METHOD.md` | A2 contratos |
| A4 — AEMET | Consumir API, caché, calidad temporal, fallback | Weather service + tests | A2 contratos |
| A5 — Data Science / OR | Modelo y solver verificables, sensibilidad, baselines | Optimizer + notebook y `MODEL_CARD.md` | A2 + A3 contratos |
| A6 — Backend | APIs, auth, multiempresa, informes, integraciones | FastAPI + OpenAPI | A2/A3/A4/A5 |
| A7 — Frontend | Dashboard, mapa, flujos de usuario, accesibilidad | Next.js + Playwright | Contrato OpenAPI |
| A8 — UX / Product | Flujos, roles, validación y lenguaje seguro | Wireframes, copys, tests con usuarios | A0/A1 |
| A9 — Seguridad / QA | Test suite, revisión privacidad, logging, backup | Informe QA y release gates | Todas |
| A10 — DevOps | Infra, CI/CD, staging, snapshots, despliegue | Docker, workflows, runbook | A6/A7 |
| A11 — Pitch / Evidence | Evidencia puntuada, presentación 3+1, 5 min, demo backup | Slides, script, capturas y métricas | A0 + equipos |

**No multiplicar agentes sin asignación clara:** cada tarea tiene un propietario, una interfaz/contrato y un test de aceptación. No permitir a varios agentes editar simultáneamente el mismo archivo crítico.

## 7.1. Políticas de colaboración

- Ramas `feature/<modulo>-<issue>`, PR pequeño con review, un solo dueño de esquemas/migraciones.
- `main` siempre desplegable; CI obligatoria para fusionar.
- API-first: frontend trabaja con contratos tipados y mocks explícitos solo en desarrollo; demo final con backend real.
- Datos reales públicos versionados por checksum; fixtures de test señalados, nunca vendidos como resultados.
- Cada ticket debe tener: **qué problema**, fuente y licencia, criterios DATAMAD, contrato, pruebas, demo y estado.
- Todo agente añade una entrada en `EVIDENCE_LOG.md` y en `PROVENANCE.md` sobre trabajo generado y asistido por IA.
- Bloqueos de fuentes, alcance o seguridad se escalan a A0 y al responsable humano, no se disimulan con mocks en producción.

## 7.2. Dependencias / orden de integración

**Fase 1 (paralela):** A1 compliance + A2 CKAN + A3 IDEM + A4 AEMET + A8 producto + A10 scaffolding.

**Fase 2:** A3 publica modelos espaciales validados; A5 solver con medidas y costes de prueba; A6 APIs; A7 dashboard apoyado en contratos.

**Fase 3:** A6 conecta orígenes reales; A7 completa flujos; A9 verifica seguridad y errores; A11 captura evidencia reproducible.

**Fase 4:** Freeze de features; limpieza de repo; despliegue alternativo y ensayo con fallo de red/APIs externas.

## 7.3. Estructura de repositorio

```text
escudo-madrid/
  README.md
  LICENSE
  PROVENANCE.md
  EVIDENCE_LOG.md
  DATA_CATALOG.md
  COMPLIANCE.md
  docs/
    prd.md
    source-register.md
    spatial-method.md
    optimizer-method.md
    model-card.md
    privacy-security.md
    validation-report.md
    demo-script.md
    pitch/
  apps/
    web/                     # Next.js
    api/                     # FastAPI
  packages/
    contracts/               # OpenAPI/types
    ui/
  pipelines/
    cam_open_data/
    idem/
    aemet/
    history/
    tests/
  services/
    optimizer/
    reporting/
  infra/
    docker-compose.yml
    migrations/
    ci/
  fixtures/
    synthetic/               # marcados como sintéticos
  notebooks/
  tests/
    unit/
    integration/
    e2e/
  artifacts/
    slides/
    demo-screenshots/
    reproducibility/
```

---

# 8. HOJA DE RUTA CON FECHAS DURAS (7–26 NOVIEMBRE)

**Regla de gestión:** «el tiempo de los agentes» no elimina las fechas de inscripción, preselección, integración, QA o entrega. No sacrificar la oportunidad de competir por construir prestaciones secundarias.

| Fecha | Hito | Entrega verificable | Gate |
|---|---|---|---|
| 7 nov. | Inicio oficial / repositorio | Código nuevo etiquetado desde la fase competitiva, PRD y contratos | G0 |
| 8–9 nov. | Auditoría de datos y compliance | ≥1 dataset CAM descargado y usado analíticamente; IDEM y AEMET evaluados | G1 |
| 10–11 nov. | Modelo de datos + backend base + mapa | PostGIS, fuentes versionadas, primer mapa y fichas municipales | G2 |
| 12–14 nov. | Vertical slice real | Login, zona, inspección, medidas y exportación básica end-to-end | G3 |
| 15–17 nov. | Motor de optimización | Restricciones validadas, tres escenarios, comparación baseline y tests | G4 |
| 18–20 nov. | Integración completa | AEMET, tareas, informes, capas, multiusuario, observabilidad | G5 |
| 21–22 nov. | Validación | Revisión por usuarios/técnico si se consigue; informe de calidad y límites | G6 |
| **23 nov.** | Freeze de candidatura y resumen | Versión candidata, texto ≤100 palabras, evidencias y capturas | G7 |
| **Antes 24 nov.** | Preselección | Resumen, integrantes y confirmación a la organización | G8 |
| 24–25 nov. | Hardening y ensayo | 3+1 slides, 5-min pitch, 5-min Q&A, backup y cero P0 bloqueantes | G9 |
| **26 nov. antes 14:00** | Entrega | Presentación, enlace app, repositorio y captura verificados | G10 |

**Gates de bloqueo:** G1 sin dato CAM de uso efectivo = replantear producto; G4 solver sin pruebas = mostrar solo modo de planificación auditable; G7 sin evidencia cuantitativa = no prometer impacto; G9 con fuga de datos o error grave = detener release. Las funciones P1 pueden seguir en ramas sin fusionar, pero la versión de concurso queda estable.

---

# 9. CRITERIOS DE ACEPTACIÓN Y DEMOSTRACIÓN

## 9.1. Definition of Done global

Una función está **DONE** solo si: usa datos reales o datos privados autorizados, su fuente es visible, tiene API/UX real, hay prueba automatizada, maneja nulos/errores, cumple privacidad, queda documentada y puede reproducirse. Un mock aislado no es DONE.

## 9.2. Pruebas obligatorias

| ID | Prueba | Criterio de aceptación |
|---|---|---|
| T01 | Portal CAM real | Conector ingiere dataset verificable, checksum, fecha y transformación documentados |
| T02 | Cruce territorial | Municipios con códigos/CRS válidos; detección de geometrías inválidas |
| T03 | Riesgo oficial | Las clases mostradas equivalen a capa fuente; leyenda y versión disponibles |
| T04 | Separación de escalas | El sistema no devuelve población de urbanización a partir de censo municipal |
| T05 | Meteo offline | Caída AEMET muestra estado de error/antigüedad, sin dato actual falso |
| T06 | Solver | Para escenarios de prueba, coste ≤ presupuesto, restricciones respetadas y resultado reproducible |
| T07 | Comparación baseline | Tabla y gráfico reflejan valores calculados, sin «% riesgo evitado» |
| T08 | Roles | Usuarios no acceden a datos/evidencias de otra organización |
| T09 | Informe | Incluye fuente, fecha, método, supuestos, distinción real/simulado y validación profesional pendiente |
| T10 | Demo | Flujo de 5 minutos sin servicios externos frágiles y con enlace de respaldo |
| T11 | Reproducibilidad | Instalación limpia con instrucciones, datos accesibles y tests verdes |
| T12 | Entrega | Diapositivas 1–3 + captura 4, antes del límite oficial |

## 9.3. Métricas de evaluación con usuarios

- Tiempo medio para preparar un escenario preventivo (cronómetro y tamaño de muestra).
- Cobertura de medidas prioritarias bajo presupuesto, comparada con baseline.
- Número de omisiones/errores administrativos en una tarea definida.
- Calidad de documentación: fuentes, responsables y evidencias completas.
- Tasa de finalización del flujo y satisfacción mediante cuestionario simple.

**Diseño mínimo:** pruebas exploratorias con al menos un perfil técnico y un gestor; si no se logra contacto, realizar ensayo interno y comunicar honestamente su alcance. Registrar consentimiento para entrevistas y uso de datos.

---

# 10. ESTRATEGIA DE PITCH Y DEMO PARA GANAR PUNTOS

## 10.1. Narrativa de 5 minutos

- **0:00–0:40 — Problema:** «La información de prevención existe; pasar a actuaciones documentadas y priorizadas exige coordinación». Citar el Plan 2026 con cifras etiquetadas.
- **0:40–1:30 — Datos:** portal de datos de Madrid (obligatorio), mapas IDEM y AEMET; distinguir quién aporta qué.
- **1:30–3:30 — Demostración:** una ubicación real con datos reales → inspección y medidas → presupuesto → comparación solver/baseline → plan e informe.
- **3:30–4:20 — Resultados:** métricas verificadas, restricciones y valor para usuario.
- **4:20–5:00 — Implantación:** perfiles, despliegue, repositorio, escalabilidad y visión de producto.

## 10.2. Distribución exacta de la entrega 3+1

1. **Título y propuesta:** ESCUDO MADRID, integrantes oficiales, problema y beneficio en una frase.
2. **Problema y datasets:** evidencia del Plan 2026, fuentes con enlaces y un diagrama de integración; hacer visible el dataset CAM.
3. **Resultados, impacto, viabilidad:** números de pruebas reales, comparación de escenarios, enlace demo y GitHub; metodología/reproducibilidad.
4. **Captura del sistema:** mapa + ficha + escenario/plan en una pantalla que exista realmente.

## 10.3. Preguntas difíciles del jurado y respuestas esperadas

- **«¿No existe ya un mapa oficial?»** Sí, y lo respetamos. Lo diferencial es el flujo de planificación, presupuestos y ejecución reproducible.
- **«¿No hace esto FIREPRIME?»** FIREPRIME aborda autoevaluación residencial; nuestro foco es la gestión colectiva multiusuario, optimización y evidencias.
- **«¿Dónde entra el dato del Portal de Madrid?»** Mostrar CAM-01/CAM-02, transformación y función analítica; no solo IDEM/AEMET.
- **«¿Podéis garantizar reducción de riesgo?»** No; medimos decisiones/gestión y derivamos planificación. Las consecuencias físicas exigirían validación técnica específica.
- **«¿Qué pasa si AEMET está caído?»** Se invalida/etiqueta el contexto meteorológico; permanece disponible la información no temporal.
- **«¿Qué aportan 20 días?»** Evidencia de commits, pruebas, funcionalidad desarrollada/evolucionada desde el periodo oficial.
- **«¿Quién aprueba las medidas?»** Un técnico competente y autoridades conforme a procedimientos; nuestra herramienta no aprueba PAIF ni sustituye legislación.
- **«¿Cómo se sostiene?»** Infraestructura estándar, datos abiertos, servicios escalables; costes reales todavía por medir.

## 10.4. Resumen provisional de preselección (máximo 100 palabras)

**ESCUDO MADRID** integra datos abiertos de la Comunidad de Madrid, cartografía oficial de incendios y meteorología de AEMET en una plataforma de prevención para municipios y urbanizaciones. Permite consultar información territorial, registrar inspecciones, planificar actuaciones, comparar presupuestos mediante optimización matemática y documentar su ejecución. Sus resultados distinguen datos oficiales, estimaciones y escenarios, con fuentes y métodos reproducibles. La solución busca mejorar la coordinación, transparencia y seguimiento de la prevención, sin sustituir a los técnicos ni a los sistemas de emergencias. Presentaremos una demostración funcional y una evaluación verificable de su utilidad.

**Nota:** contar palabras y comprobar el texto final antes de enviarlo; no asegurar prestaciones todavía inexistentes.

---

# 11. RIESGOS, SUPUESTOS Y DECISIONES ABIERTAS

| Riesgo | Consecuencia | Mitigación |
|---|---|---|
| Riesgo de no cumplir Portal CAM | Exclusión o pérdida total de criterio de 25 puntos | Gate G1 y uso analítico demostrable de CAM-01/CAM-02 |
| Geometrías sin calidad o muy generales | Conclusiones a escala errónea | QA GIS, escalas visibles, desactivar resultados finos |
| Datos AEMET inaccesibles/cuotas | Meteo incompleta | Caché etiquetada y estado no disponible; sin resultados inventados |
| Costes de medidas poco documentados | Optimización aparente | Cotizaciones reales o escenarios claramente simulados |
| Falta de validación profesional | Recomendaciones inseguras o no aplicables | Estado «pendiente de revisión técnica», entrevistas, referencias verificables |
| Desarrollo disperso en agentes | App inconexa, fallos de integración | APIs primero, merges centralizados, integración diaria |
| Problemas de autoría/IA/preexistencia | Incumplimiento de bases | PROVENANCE.md, trazabilidad de commits, licencias y fuentes |
| Seguridad y privacidad | Exposición de datos privados | Threat model, multi-tenancy, storage privado, QA |
| Presentación 3+1 y 5 min | Pérdida de claridad/puntos | Ensayo, demo guiada, slides exactas y backup |
| Resumen 24/11 y entrega 26/11 14h | Exclusión | Freeze temprano, entregables preparados con margen |

**Decisiones que debe aprobar la líder:** alcance público de coordenadas sensibles; primer conjunto de ámbitos/municipios; catálogo de medidas y autoridad técnica; almacenamiento de adjuntos y términos legales; licencias de datasets; qué resultados se muestran como simulación; nombre/identidad visual definitiva; qué P1 pasa a P0 si se valida con usuarios.

---

# 12. PRIMERAS ÓRDENES PARA CLAUDE Y LOS AGENTES

**Instrucción de inicio para A0:** «Actúa como tech lead y director de ejecución de ESCUDO MADRID. Lee íntegramente este PRD. Desglosa P0/P1 en issues con definición de hecho y criterios DATAMAD. Abre contratos OpenAPI y esquema PostGIS antes de implementar pantallas. Programa integración diaria. No aceptes cifras, mapas ni simulaciones sin fuente o señalización. Prioriza gates G1, G3, G4 y G9».

**Primer sprint, tareas delegables inmediatamente:**

1. **A1 — Compliance:** `COMPLIANCE.md` cláusula a cláusula; confirmación escrita de inscripción, asistencia y resumen 24/11; estudio competencia.
2. **A2 — Datos:** ingestar CAM-01 y CAM-02, guardar snapshots/versiones; crear al menos dos salidas analíticas de producto. Auditar CAM-03..06.
3. **A3 — GIS:** descargar/inspeccionar GEO-01..03, validar CRS, preparar visualización mapa y cruces solo a escalas legítimas.
4. **A4 — AEMET:** probar endpoint real, registrar autenticación/límites, parsear metadatos y fallback, crear tests con fixtures claramente marcadas.
5. **A5 — OR:** solver knapsack con dependencias; pruebas de presupuesto, elegibilidad y sensibilidad; `MODEL_CARD.md`.
6. **A6/A7 — Producto:** auth básica, proyecto de áreas, mapa y ficha municipal, flujo de inspección/medida/escenario/plan según API.
7. **A9/A10 — Calidad/infra:** CI, Docker, secretos, backup, monitorización, políticas de PR.
8. **A11 — Presentación:** plantilla de 3+1 slides, matriz de evidencia y temporización exacta de demo.

**Mensaje estándar de cierre para cada agente:** indicar (a) funcionalidad real completada, (b) commits y archivos, (c) datasets y licencias, (d) pruebas ejecutadas y resultados, (e) discrepancias/bloqueos, (f) puntos DATAMAD que respalda, (g) capturas o métricas reproducibles. Nunca responder solo «terminado».

---

# 13. REFERENCIAS Y DOCUMENTOS DE CONTROL

## Documentos oficiales del concurso aportados por la participante

- *Bases de participación DATAMAD 2026*, 9 pp. Apartados: objeto, fechas, registro, requisitos, tecnología/IA, entrega, defensa, criterios, premios, propiedad intelectual y exclusión.
- *DATAMAD Programa 2026 actualizado*, 4 pp. Jornada final, ubicación y formación.
- Web organizadora actualizada: https://eventos.urjc.es/155632/ (consultada el 6/11/2026).

## Fuentes oficiales de contexto y datos verificadas

1. Comunidad de Madrid — Plan Anual 2026: https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf
2. Comunidad de Madrid — Portal de Datos Abiertos: https://datos.comunidad.madrid/
3. Población censada por edad: https://datos.comunidad.madrid/dataset/poblacion_censada_por_edad_nacionalidad_y_sexo
4. Densidad poblacional: https://datos.comunidad.madrid/dataset/1930748
5. Espacios protegidos: https://datos.comunidad.madrid/dataset/espacios_protegidos
6. Incendios y superficie afectada: https://datos.comunidad.madrid/dataset/101019
7. Geoportal: https://www.comunidad.madrid/geoportal
8. Cartografía de riesgo: https://datos.gob.es/es/catalogo/a13002908-riesgo-por-incendios-forestales
9. Cartografía de peligrosidad: https://datos.gob.es/es/catalogo/a13002908-peligrosidad-por-incendios-forestales
10. Cartografía de vulnerabilidad: https://datos.gob.es/es/catalogo/a13002908-vulnerabilidad-por-incendios-forestales
11. AEMET OpenData: https://www.aemet.es/es/datos_abiertos/AEMET_OpenData
12. AEMET — peligro e interpretación: https://www.aemet.es/es/eltiempo/prediccion/incendios/ayuda
13. INFOMA 2026: https://www.comunidad.madrid/seguridad-emergencias-asem-112/infoma26
14. FIREPRIME / UPC (comparativa): https://www.upc.edu/es/sala-de-prensa/noticias/app-conocer-riesgo-viviendas-incendios-forestales
15. Copernicus EMS / EFFIS: https://forest-fire.emergency.copernicus.eu/

**Advertencia de procedencia:** los enlaces y descripciones de catálogo se verificaron por consulta pública; **no se ha descargado, examinado ni integrado todavía cada fichero, capa o API en una aplicación**. Las tareas del PRD son requisitos a implementar, no funcionalidades ya existentes. Donde el catálogo no confirma granularidad o licencia de un recurso específico, comprobarla antes de su uso.

---

# 14. DEFINICIÓN DE ÉXITO

**Para el concurso:** un producto público de demostración que funcione, use sustancialmente datos abiertos CAM, integre cartografía oficial y contexto meteorológico, cierre un flujo de prevención multiusuario, optimice escenarios con pruebas, exporte evidencia y demuestre utilidad con datos honestos; repositorio abierto, presentación exacta y entrega puntual.

**Para el futuro:** un software que gestores y técnicos puedan evaluar en entornos reales y, sujeto a validación profesional, licencias, seguridad y adopción, emplear regularmente para organizar la prevención. La cobertura regional es la ambición del producto, no una afirmación de que cada vivienda está evaluada.

**CRITERIO FINAL DE ACEPTACIÓN:** el jurado debe poder señalar un dato autonómico, seguir su transformación, comprobar una decisión resultante, abrir su evidencia y reproducirla. Todo lo que no ayude a eso es secundario.
