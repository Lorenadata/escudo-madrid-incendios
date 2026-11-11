# COMPLIANCE.md — Matriz de cumplimiento de las bases DATAMAD 2026

Dueño: **A1 — Bases/Research**. Última revisión: **06/11/2026**.

**Fuentes de las normas**
- *Bases de participación DATAMAD 2026* (9 pp., apartados 1–22) y *Programa 2026 actualizado* (4 pp.): documentos aportados por la participante. **No están en el repositorio**; esta matriz se apoya en su transcripción en `ESCUDO_MADRID_PRD_Maestro.md` §1 (en adelante «PRD»). **Acción humana:** añadir los PDF originales de las bases a `docs/reference/` (si su difusión está permitida) o, como mínimo, contrastar esta matriz frase a frase con ellos.
- Web oficial https://eventos.urjc.es/155632/ — **consultada el 06/11/2026 por A1: la página se sirve renderizada en JavaScript y la herramienta de lectura solo obtuvo el título «DATAMAD 2026»; no se pudo extraer contenido.** Los datos que el PRD atribuye a la web (resumen ≤100 palabras antes del 24/11, preselección de hasta 50 proyectos y 12 finalistas, ≥1 persona presencial) siguen **sin verificación independiente**. Acción humana: abrirla en un navegador y guardar captura fechada en `docs/reference/`.

Estados: `pendiente` · `en curso` · `cumplido`. Solo se marca `cumplido` cuando la evidencia existe y es verificable en el repositorio o en un registro externo.

## 1. Admisión y uso de datos

| # | Norma | Fuente | Evidencia prevista en el repo | Estado | Responsable |
|---|---|---|---|---|---|
| C01 | Usar de forma **efectiva al menos un dataset del Portal de Datos Abiertos de la Comunidad de Madrid** (datos.comunidad.madrid). IDEM, AEMET y Copernicus son complementarios y **no** sustituyen esta condición. | Bases vía PRD §1.2.1 (apartado exacto: verificar en el PDF) | `data/raw/CAM-*/manifest.json` (URL, SHA-256, fecha), conector `pipelines/escudo_pipelines/fetch.py`, transformación, endpoints `/v1/municipalities/*` y pantalla de ficha municipal cuyo resultado cambia al actualizar el recurso | ✅ cumple (11 datasets CAM, 11/11/2026) | A2 |
| C02 | **Dos funciones analíticas** cuyo resultado cambie al actualizar CAM-01/CAM-02 (ficha demográfica municipal con año y unidades; filtro o comparador regional reproducible). Que los datos del portal no sean decoración. | PRD §4.1 (objetivo interno para el criterio de 25 pts) | Tests que modifican el CSV de entrada y comprueban cambio de salida; `/v1/compare`, filtro por densidad | ✅ cumple (ficha, filtro/comparador y matriz con tests) | A2 + A6 |
| C03 | Identificar **todos** los datasets: URL, productor, fecha de extracción, licencia, fecha de actualización, ámbito, unidades, cobertura, transformaciones. | Bases vía PRD §1.2.2 y §4.5 | `DATA_CATALOG.md`, tabla `data_sources`, endpoint `/v1/sources`, ficha de procedencia por indicador | ✅ cumple (DATA_CATALOG.md, /fuentes, /v1/sources) | A2 |
| C04 | Separar evidencia de uso del **Portal CAM (CKAN)** frente a capas IDEM/datos.gob.es (riesgo, peligrosidad, vulnerabilidad), que no son necesariamente datasets CKAN. | PRD §4.2 | Columna `portal` en catálogo (`CAM`/`IDEM`/`AEMET`); slide 2 muestra explícitamente el dataset CAM | ✅ cumple (campo `portal`: CAM, CAM-DOC, IDEM, EFFIS, AEMET) | A1 + A2 |
| C05 | Respetar licencias de datos, mapas, fotos, modelos, código, librerías, APIs y contenidos; **sin scraping ilícito ni datos privados no autorizados**. | Bases vía PRD §1.2.3 | Licencia por fuente en `DATA_CATALOG.md` (CC-BY 4.0 para los datasets CAM verificados); `THIRD_PARTY_LICENSES` de dependencias; términos de AEMET OpenData revisados antes de redistribuir mapas | ✅ cumple (licencias en DATA_CATALOG y PROVENANCE) | A1 + A2 + A4 |
| C06 | Atribución de las licencias CC-BY (citar productor y fuente en la interfaz y en informes). | Licencia CC-BY de los datasets CAM (CKAN `license_id: cc-by`) | Pie «Fuente: … (CC-BY)» en ficha, mapa e informe PDF | ✅ cumple (atribución en ficha, mapa, fuentes e informes) | A7 + A6 |

## 2. Honestidad, autoría e IA

| # | Norma | Fuente | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|
| C07 | Presentar en plazo y explicar funcionamiento, metodología y utilidad; **sin plagio, resultados falsos ni fuentes inventadas**. | Bases vía PRD §1.2.4 | `docs/spatial-method.md`, `docs/optimizer-method.md`, `docs/model-card.md`, `EVIDENCE_LOG.md`; regla CLAUDE.md nº 1 («cero cifras inventadas») | 🟡 en curso (presentación pendiente de actualizar) | Todos (A0 vigila) |
| C08 | Uso de IA generativa y asistentes **permitido**; cada resultado es responsabilidad del equipo. | Bases vía PRD §1.2.5 (apartado exacto: verificar en el PDF) | `PROVENANCE.md` con trabajo asistido por IA y revisión humana; los agentes son herramientas, los participantes son las personas inscritas | ✅ cumple (PROVENANCE.md) | A0 |
| C09 | Reutilizar recursos preexistentes solo si se identifican; el trabajo debe desarrollarse o evolucionar **sustancialmente entre el 7 y el 26/11/2026**. | Bases vía PRD §1.2.6 | Historial git con fechas; `PROVENANCE.md` + changelog. **El repositorio se inició el 06/11/2026 por la tarde (andamiaje inicial: estructura, contratos, primeras descargas). Debe declararse como andamiaje previo al periodo oficial en `PROVENANCE.md`**, con el hash del último commit de ese día para que la evolución posterior sea comprobable. | 🟡 declarado; 👤 H2 decidir consulta a la organización | A0 |
| C10 | Derechos del proyecto para sus autores, sin perjuicio de licencias de terceros; se valora publicar bajo licencia abierta. | Bases vía PRD §1.2.7 | `LICENSE` (el `pyproject.toml` declara AGPL-3.0-or-later: falta el fichero `LICENSE` y confirmar la elección con la líder humana) | ✅ cumple (repositorio público EUPL-1.2) | A0 + líder |
| C11 | No publicar información personal, vulnerabilidades de infraestructuras ni detalles operativos sensibles sin autorización. | Bases vía PRD §1.2.8 | `docs/privacy-security.md`; datos de demo ficticios (`fixtures/synthetic/`); sin coordenadas de hidrantes ni elementos vulnerables reales; test T08 de aislamiento multi-tenant | ✅ cumple (datos de demo ficticios; portal con umbral de privacidad) | A9 |
| C12 | **No presentarse como producto homologado por Protección Civil** ni insinuar colaboración oficial; no emitir rutas de evacuación, tácticas de extinción ni certificados PAIF. | Bases vía PRD §1.2.8 y §3.3; INICIO | Aviso permanente en UI e informes; revisión de copys (A8); sin logotipos institucionales | ✅ cumple («no oficial» en cabecera y avisos) | A8 + A11 |
| C13 | No afirmar uso institucional, aval o interés del Gobierno regional sin autorización escrita. | PRD §2.3 | Revisión de pitch y README | ✅ cumple | A11 |

## 3. Participantes y premios

| # | Norma | Fuente | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|
| C14 | Participación de **personas físicas**; equipo identificado antes del cierre. Inscripción de proyectos cerrada el **05/11/2026**. | Bases vía PRD §1.2.9 y §1.3 | **Acción humana:** conservar justificante de inscripción con los nombres de los integrantes en `docs/reference/` (sin datos personales innecesarios en el repo público) | 🟡 👤 confirmar que la inscripción quedó registrada | Líder humana |
| C15 | Cambios de integrantes: límite **07/11/2026**; incorporaciones posteriores solo con autorización excepcional. | Bases vía PRD §1.2.9 | Si hay cambios, solicitud escrita a la organización antes del 07/11 | ✅ no aplica (participante única desde el inicio) | Líder humana |
| C16 | Premios **3.000 / 2.000 / 1.000 € brutos**, sujetos a fiscalidad y repartidos **a partes iguales** entre los miembros. No afirmar que el premio corresponde a una sola persona. | Bases vía PRD §1.2.10 | Revisión de textos de pitch/README | — informativo | A11 |

## 4. Plazos y entregables

| # | Norma | Fuente | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|
| C17 | **Resumen de máximo 100 palabras**, título, integrantes y confirmación de presencia **antes del 24/11/2026**, por el procedimiento que comunique la organización. | Web oficial según PRD §1.3 (no verificada por A1, ver cabecera) | `docs/pitch/resumen-preseleccion.md` con recuento automático de palabras y justificante de envío. **Borrador del PRD §10.4: 91 palabras** (recuento por espacios, contando «ESCUDO MADRID» como 2). Cabe en el límite, pero su última frase («evaluación verificable de su utilidad») promete una evaluación que aún no existe: mantenerla solo si el ensayo de utilidad (PRD §5.5) se realiza antes del 23/11. | 🟡 texto listo (93 palabras); 👤 enviar el 23/11 | A11 + líder |
| C18 | Preselección: hasta 50 proyectos; 12 se presentan ante el jurado. | Web oficial según PRD §1.3 (no verificada) | — (informativo) | — informativo | A1 |
| C19 | **Entrega oficial el 26/11/2026 antes de las 14:00** por la plataforma habilitada: presentación + enlaces funcionales (demo y repositorio). | Bases vía PRD §1.3 | Checklist de entrega en `docs/pitch/`; objetivo interno: subir el 25/11; verificación de enlaces (T12) | 🟡 repositorio listo; falta demo pública (despliegue) | A11 + A10 |
| C20 | Formato obligatorio: **máximo 3 diapositivas de contenido** — (1) nombre, participantes, descripción; (2) problema, datasets y enlaces; (3) resultados, impacto, viabilidad y enlace de demo/repositorio — **+ 4.ª diapositiva con una captura del sistema**. | Bases ap. 8 vía PRD §1.3 y §10.2 | `artifacts/slides/` con exactamente 3+1; la captura corresponde a una pantalla que exista realmente | 🟡 formato 3+1 hecho; actualizar contenido | A11 |
| C21 | Defensa presencial el **26/11/2026: 5 min de exposición + 5 min de preguntas**. Jornada final en el campus de Vicálvaro (URJC) según el programa. | Bases vía PRD §1.3 | `docs/demo-script.md` cronometrado; demo sin servicios externos frágiles + vídeo/capturas de respaldo (T10) | 🟡 👤 ensayos 22–25/11 | A11 |
| C22 | **Discrepancia de asistencia:** las bases (ap. 9) exigen presencia de **todos** los componentes salvo causa justificada; la web actualizada indica **al menos una persona** por equipo. | PRD §1.3 | **Resuelta por composición del equipo (07/11/2026):** la participante única es **Lorena Marcos**; con una sola persona ambas lecturas coinciden: debe asistir presencialmente el 26/11. Consultar a madrid.datamad@urjc.es solo si surge una causa justificada de ausencia. | resuelta | Lorena Marcos |
| C23 | ECTS / formación 5–6/11: comprobar condiciones de asistencia si se buscan créditos. | PRD §1.3 | Acción humana | — no aplica | Líder humana |

## 5. Evaluación (para orientar evidencias, no para autopuntuarse)

| # | Norma | Fuente | Evidencia prevista | Estado | Responsable |
|---|---|---|---|---|---|
| C24 | Criterios: datos CAM 25 · originalidad 20 · impacto 25 · viabilidad 15 · tecnologías abiertas/reproducibilidad 10 · presentación 5. | Bases ap. 10, pp. 4–5 vía PRD §1.1 | `docs/DATAMAD_SCORECARD.md` (A0) con evidencias por criterio; **sin estimar la nota del jurado** | 🟡 en curso (impacto sin validación externa: ensayo interno) | A0 |
| C25 | Desempate: (1) intensidad del uso de datos de Madrid, (2) impacto, (3) originalidad, (4) viabilidad. | Bases ap. 10 vía PRD §1.1 | Priorizar profundidad de uso de datasets CAM (más de un dataset, con lineage y funciones que dependan de ellos) | ✅ intensidad de datos CAM como primer desempate | A0 + A2 |

## 6. Verificaciones factuales hechas por A1 (06/11/2026)

- Las cifras del PRD §2.1 están **literalmente** en el *Plan Anual 2026* (https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf, 100 pp., SHA-256 `22d08b64bab311bff65327338f2599a4392931f02c00244e7d0e3f48416c6efc`, descargado 06/11/2026): «Superficie de la Comunidad Autónoma destinada a trabajos preventivos (ha) … Programado 2026 **5.652,38**» (tabla de indicadores de prevención) y, en el ap. 9.2.1, «**68 PAIF** realizados … repartidos en **26 municipios**, de los cuales **21** tienen el informe favorable de la Subdirección General de Protección Civil y **47** están en tramitación». ✔
- **Marco normativo con matiz:** el Plan Anual 2026 cita aún el RD 893/2013 (Directriz Básica de incendios forestales), pero la nueva *Directriz Básica de Planificación de Protección Civil ante el riesgo de incendios forestales* (BOE-A-2026-9159, 27/04/2026) recoge en su preámbulo que el RD 893/2013 fue **derogado por el RD 524/2023** (Norma Básica de Protección Civil). El propio Plan 2026 (ap. 9.2) reconoce que el RD 393/2007 (Norma Básica de Autoprotección) está derogado por el RD 524/2023. **Regla para todo el equipo:** no citar el RD 893/2013 como norma vigente; citar el Decreto 59/2017 (INFOMA) y la Directriz de 2026.
- La plataforma no debe presentarse como sustituto de herramientas oficiales: el Plan 2026 menciona plataformas online de la propia CAM (SAVER, MINCE; ver `COMPETITORS.md`).
