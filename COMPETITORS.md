# COMPETITORS.md — Alternativas existentes y diferenciación honesta

Dueño: **A1 — Bases/Research**. Todas las consultas: **06/11/2026**. Las descripciones se limitan a lo que dicen las fuentes citadas; donde no se pudo comprobar algo, se indica.

## Resumen

Hay herramientas sólidas para **autoevaluar una vivienda** (FIREPRIME), **consultar cartografía oficial** (IDEM / visor de Protección Civil), **gestionar inspecciones de franjas en Galicia** (XESBIO2) y **simular el comportamiento del fuego** (Technosylva). En la Comunidad de Madrid, la propia administración tiene plataformas internas (SAVER, MINCE) para elementos vulnerables y para guardar la última versión de PAMIF/PAIF. **No hemos encontrado** una herramienta pública que una, para urbanizaciones y ayuntamientos de Madrid, el contexto oficial, las inspecciones, un catálogo de medidas ligado al Decreto INFOMA, la priorización bajo presupuesto con optimización transparente y el seguimiento con evidencias. Esto es una **hipótesis por validar** con usuarios (PRD §2.3), no una afirmación de vacío de mercado: la búsqueda no fue exhaustiva y no incluye software comercial no indexado ni licitaciones.

## Fichas

### 1. FIREPRIME App (UPC – CERTEC / GESSI, proyecto UE)
- **URL:** https://www.upc.edu/en/press-room/news/an-app-to-assess-wildfire-risk-to-homes · https://apps.apple.com/es/app/fireprime/id6740866195 · https://gessi.upc.edu/en/projects/fireprime · entregable D3.2: https://civil-protection-knowledge-network.europa.eu/system/files/2026-06/d3.2_fireprime_the-fireprime-app.pdf
- **Qué hace:** app gratuita (inglés, español, catalán, alemán, sueco) para que **residentes** autoevalúen el riesgo de su vivienda frente a incendios forestales: peligro de la zona y vulnerabilidad de la casa, con un análisis cuantitativo basado en árboles de fallos (materiales, mantenimiento del jardín…) y recomendaciones. Cofinanciada por la UE (UCPM-2023-KAPP), coordinada por CERTEC-UPC.
- **Qué no hace (según las fuentes consultadas):** no consta gestión colectiva de una urbanización, multiusuario con roles, presupuestos ni optimización, planes de ejecución con responsables y evidencias, ni integración de datasets autonómicos de Madrid.
- **Relación con ESCUDO:** complementaria. ESCUDO no evalúa viviendas individuales ni calcula probabilidades de ignición; podría enlazar FIREPRIME como recurso para residentes.

### 2. Geoportal / IDEM de la Comunidad de Madrid — Visor de Protección Civil
- **URL:** https://www.comunidad.madrid/geoportal · visor: https://idem.comunidad.madrid/visor/?v=pcivil&ZONE=430000%2C4485000%2C7 · catálogo: https://idem.comunidad.madrid/catalogocartografia/srv/spa/catalog.search#/home
- **Qué hace:** visores oficiales de cartografía; el de Protección Civil incluye el catálogo de riesgos potenciales con **peligrosidad, vulnerabilidad y riesgo**. Existe además un visor de la delimitación aproximada del incendio de julio de 2026.
- **Qué no hace:** consulta cartográfica; no gestiona inspecciones, medidas, presupuestos ni seguimiento de la ejecución.
- **Relación con ESCUDO:** **fuente** (GEO-01..03), no competidor. ESCUDO muestra sus clases literalmente y enlaza al visor oficial.

### 3. INFOMA 2026 (ASEM 112, Comunidad de Madrid)
- **URL:** https://www.comunidad.madrid/seguridad-emergencias-asem-112/infoma26 · Decreto 59/2017: https://www.bocm.es/boletin/CM_Orden_BOCM/2017/06/09/BOCM-20170609-1.PDF · ficha de transparencia: https://www.comunidad.madrid/transparencia/node/1470
- **Qué es:** el Plan Especial de Protección Civil de Emergencia por Incendios Forestales (Decreto 59/2017) y su campaña 2026 (época de peligro alto del 15/06 al 30/09/2026). La página de la campaña no describe herramientas digitales para que urbanizaciones o ayuntamientos planifiquen o sigan medidas; menciona proyectos piloto de sensibilización y participación comunitaria (programa PIMA Eventos Adversos) y la obligación de PAMIF.
- **Relación con ESCUDO:** **marco normativo** que ESCUDO operacionaliza (Anexos 5, 6 y 7 → catálogo de medidas). ESCUDO no interviene en la dirección de emergencias.

### 4. SAVER y MINCE (plataformas online de la Comunidad de Madrid)
- **Fuente:** *Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales 2026*, https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf — «Gestión de la Interfaz Urbano Forestal, mediante generación de dos plataformas online: SAVER (elementos vulnerables, hidrantes, zonas de acceso restringido) y MINCE (disponibilidad de última versión de PAMIF/PAIF para uso en planificación y emergencia)». El Plan menciona también aplicaciones online compartidas con entidades locales en el SITREM.
- **Qué no sabemos:** no hemos encontrado URL pública ni documentación de funciones; parecen herramientas de la administración. **No afirmar en el pitch qué hacen o no hacen más allá de esa frase.**
- **Relación con ESCUDO:** riesgo de solapamiento percibido. Mensaje honesto: ESCUDO trabaja **antes** del documento oficial —inventario, inspección, medidas, presupuesto y evidencias de ejecución por parte del titular obligado— y podría exportar información útil para el PAIF, sin sustituir ni conectarse a sistemas oficiales sin autorización.

### 5. XESBIO2 (Xunta de Galicia)
- **URL:** https://www.xunta.gal/es/notas-de-prensa/-/nova/025204/medio-rural-refuerza-formacion-sobre-uso-aplicacion-informatica-xesbio2-empleada (nota del 03/06/2026) · visor de franjas: https://www.xunta.gal/es/hemeroteca/-/nova/112350/instituto-estudios-del-territorio-digitalizo-red-franjas-gestion-biomasa-millon
- **Qué hace:** aplicación de la administración gallega para **inspecciones** de la gestión de biomasa en las franjas secundarias (registro de actuaciones sobre el terreno con información geográfica y fotográfica, identificación de parcelas) y **seguimiento de expedientes** de requerimiento. Usuarios: técnicos y agentes forestales, Seaga y ayuntamientos adheridos al convenio. El IET digitalizó la red de franjas a nivel de parcela catastral en un visor público.
- **Qué no hace / límites:** es específica del régimen gallego de franjas secundarias (franjas de 50 m según la Xunta; norma gallega no verificada por A1) y de uso administrativo; según las fuentes, no ofrece planificación presupuestaria con optimización ni está orientada a gestores de urbanización.
- **Relación con ESCUDO:** **el referente más próximo** al flujo inspección → expediente → seguimiento. Demuestra que el problema es real y que la administración lo digitaliza; la diferencia de ESCUDO es el ámbito (Madrid, INFOMA), los usuarios (titulares obligados + ayuntamiento + técnico) y la capa de priorización presupuestaria transparente.

### 6. Technosylva (Wildfire Analyst, fiResponse, Tactical Analyst)
- **URL:** https://www.esri.com/partners/technosylva-sl-a2T70000000TNfzEAG
- **Qué hace:** empresa con sedes en León y San Diego; soluciones GIS de simulación del comportamiento del fuego, planificación de la protección y respuesta operativa para agencias de extinción y compañías eléctricas.
- **Qué no hace / límites:** orientada a simulación y operaciones de grandes organizaciones; no hemos encontrado evidencia de uso por urbanizaciones o ayuntamientos madrileños para gestionar medidas preventivas.
- **Relación con ESCUDO:** no compite: ESCUDO **no simula propagación** ni hace análisis táctico (prohibido por el PRD).

### 7. Guías y plantillas oficiales (no son software)
- Guía para elaborar un PAMIF (MITECO/CENEAM): https://www.miteco.gob.es/content/dam/miteco/es/ceneam/recursos/materiales/13%20GUIA%20PARA%20ELABORAR%20UN%20PLAN%20DE%20ACTUACI%C3%93N%20MUNICIPAL%20ANTE%20EMERGENCIAS%20POR%20INCENDIOS%20FORESTALES%20(PAMIF).pdf
- Guía PAMIF de la Comunidad de Madrid (2022): https://comunidad.madrid/sites/default/files/2022_guia_pamif.pdf
- Guía de elaboración de PAIF (Protección Civil de Málaga): https://proteccioncivil.malaga.eu/export/sites/proteccioncivil/.galleries/Documentos-General/Guia-de-elaboracion-PAIF.pdf
- **Relación con ESCUDO:** contenido de referencia para los checklists de inspección (M06) y la lista de información pendiente (M15). No se reproducen textos sin verificar su licencia.

## Diferenciación (para el pitch, sin exagerar)

| Capacidad | FIREPRIME | IDEM/visor PC | XESBIO2 | Technosylva | ESCUDO MADRID (objetivo) |
|---|---|---|---|---|---|
| Datos abiertos del Portal CAM integrados | no consta | n/a (fuente) | no (Galicia) | no consta | **sí** (requisito) |
| Cartografía oficial de riesgo/peligrosidad/vulnerabilidad de Madrid | no consta | **sí** | no | no consta | **sí**, mostrada literal |
| Autoevaluación de vivienda | **sí** | no | no | no | no (fuera de alcance) |
| Inspecciones con evidencias | parcial (autoevaluación) | no | **sí** | no consta | **sí** |
| Catálogo de medidas ligado a INFOMA | no | no | no (norma gallega) | no | **sí** |
| Presupuesto + optimización transparente + baseline | no | no | no consta | no consta | **sí** |
| Plan de ejecución y seguimiento multiusuario | no | no | expedientes (administración) | no consta | **sí** |
| Simulación de propagación | no | no | no | **sí** | **no** (prohibido) |

«no consta» = las fuentes consultadas no lo mencionan; no equivale a «no lo hace».

## Pendiente
- Buscar en la Plataforma de Contratación del Sector Público licitaciones de software PAIF/IUF de ayuntamientos madrileños.
- Revisar herramientas de Cataluña (plans d'autoprotecció d'urbanitzacions) y Comunitat Valenciana; esta búsqueda no devolvió resultados.
- Confirmar con un técnico (entrevista PRD §5.5) si SAVER/MINCE cubren parte de este flujo.
