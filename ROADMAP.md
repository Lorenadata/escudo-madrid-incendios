# ROADMAP — Plan para ganar DATAMAD 2026 (A0)

Fuente: `ESCUDO_MADRID_PRD_Maestro.pdf` / `.md` (equivalentes, verificado 06/11/2026). Actualizado: **07/11/2026**.
**Fecha límite de trabajo: 25/11/2026** (el 26/11 es entrega antes de las 14:00 y defensa). El resumen de preselección se envía **antes del 24/11**.
Estado: ✅ hecho y verificado · 🟡 parcial · ⬜ pendiente · 👤 requiere a una persona del equipo.

> Regla para ganar: optimizar **evidencia demostrable** por criterio, no número de pantallas. Cada tarea indica el criterio que mueve: **D25** datos CAM (25) · **D20** originalidad (20) · **I25** impacto (25) · **V15** viabilidad (15) · **R10** código abierto/reproducibilidad (10) · **P5** presentación (5). Desempate: datos de Madrid → impacto → originalidad → viabilidad.

---

## 1. Dónde estamos (07/11)

| Bloque | Estado | Evidencia |
|---|---|---|
| 8 datasets del Portal CAM ingeridos con SHA-256, licencia y calidad | ✅ | `DATA_CATALOG.md`, `pipelines/tests/test_cam.py` |
| Cartografía oficial GEO-01/02/03 (ráster 5 m → reparto exacto por municipio) | ✅ | `pipelines/tests/test_idem.py` |
| AEMET predicción municipal con caducidad y modo degradado | ✅ | `pipelines/tests/test_aemet.py` |
| Optimizador CP-SAT + 2 baselines + sensibilidad | ✅ | `tests/unit/test_optimizer.py` |
| API (39 rutas), multi-organización, auditoría, PDF, CSV, GeoJSON | ✅ | `tests/integration` |
| Web: explorador, ficha, comparador, análisis, fuentes, caso guiado, área privada | ✅ | `apps/web/e2e` (6 tests) |
| Docker (API y web) | ✅ imágenes probadas | `infra/` |
| Presentación 3+1 (borrador) | 🟡 | `artifacts/slides/` |
| Flujo B (responsable municipal) | ✅ | `test_flow_B_municipal_sees_only_authorized_areas`, e2e, captura 07 |
| **Validación con usuarios / experimento de utilidad** | ⬜ 👤 | — |
| **Demo pública y repositorio público** | ⬜ 👤 | — |

**Lo que más puntos puede sumar todavía:** (1) validación real con técnicos y gestores (I25), (2) más uso analítico de datos CAM visible en la demo (D25 + desempate), (3) Flujo B y flujo A pulido de punta a punta (D20/V15), (4) demo pública estable + repositorio público con CI verde (V15/R10).

---

## 2. Decisiones y acciones humanas con fecha límite 👤

Sin estas, el proyecto pierde puntos que ningún agente puede recuperar.

| # | Acción | Por qué | Límite |
|---|---|---|---|
| H1 | ✅ Participante única: **Lorena Marcos**; asistencia presencial el 26/11 (con una persona, bases y web coinciden) | Admisión | hecho 07/11 |
| H2 | Decidir si se consulta a la organización el inicio del repo el 06/11 (declarado en `PROVENANCE.md`) | Cumplimiento | 09/11 |
| H3 | ✅ (10/11, en `.env` local, verificada) Registrar clave gratuita **AEMET OpenData** y ponerla en `.env` (nunca en el repo) | Mapa oficial de peligro de incendios en la ficha (D20/V15) | 10/11 |
| H4 | ✅ Licencia **EUPL-1.2** y repositorio público: https://github.com/Lorenadata/escudo-madrid-incendios (CI verde) | R10 (10 pts) | hecho 07/11 |
| H5 | ✅ (11/11: PRO activado; Space `lorenadata/escudo-madrid` en marcha, 30/30 e2e contra la URL pública) Decidido (08/11): **Hugging Face Spaces** (Docker; exige suscripción PRO, ~9 $/mes, un mes). Lorena activa PRO el **18/11**; A10 publica el Space `lorenadata/escudo-madrid` el 18–19/11 con `infra/docker/space.Dockerfile` (ya preparado) | Enlace de demo en diapositiva 3; T10; URL estable 72 h antes | activar PRO **18/11** |
| H6 | ❌ (11/11: no hay contactos disponibles) → **ensayo interno declarado** con 2 personas ajenas al proyecto antes del 20/11 (👤) — Conseguir **≥1 técnico** (forestal / protección civil) y **≥1 gestor** (urbanización o ayuntamiento) para entrevista de 30 min y sesión de prueba | I25 (25 pts): sin esto el impacto es solo hipótesis | contactos **12/11**, sesiones **14–20/11** |
| H7 | Revisión técnica del catálogo de 16 medidas (o declarar explícitamente que sigue pendiente) | Credibilidad ante jurado | 20/11 |
| H8 | Enviar resumen de preselección (93 palabras, `docs/pitch/resumen-preseleccion.md`) | Preselección | **23/11** (margen sobre el 24) |
| H9 | Ensayo de la defensa con cronómetro: 2 ensayos completos + 1 con preguntas difíciles | P5 | 22–25/11 |

---

## 3. Plan por fases (agentes A0–A11)

### Fase 1 — Demo completa (07–12/11) · gate **G-Demo**

| # | Tarea | Dueño | Criterio | Aceptación |
|---|---|---|---|---|
| 1.1 | ✅ **Flujo B: panel del responsable municipal** — municipio propio, ámbitos de organizaciones que **autorizan** compartir con el ayuntamiento, estado de inspecciones y acciones, cobertura presupuestaria, expediente de solo lectura, informe | A6+A7 | D20, V15, I25 | API + UI + e2e; un ámbito no autorizado nunca aparece (test de privacidad) |
| 1.2 | ✅ Dibujar/importar la geometría de un ámbito en el mapa (M05) y mostrar sus clases oficiales **orientativas** (capa 200 m, `derived`) | A7 | D20 | UI + e2e; aviso de resolución visible |
| 1.3 | ✅ Revisión técnica desde la UI (solo técnico con cualificación verificada; resto ve el motivo del bloqueo) | A7 | V15 | e2e |
| 1.4 | ✅ Recorrido «Flujo A» completo desde cero en la UI (login → ámbito → inspección con foto → medidas → presupuesto → optimizar → comparar → plan → asignar → evidencia → PDF) en < 3 min | A7+A9 | V15, P5 | e2e cronometrado |
| 1.5 | ✅ Modo demo robusto: arranque en un comando (`scripts/demo.sh`), datos precargados, AEMET cacheada con su fecha real, plan B offline | A10 | V15, P5 | ensayo con red cortada |
| 1.6 | 🟡 Investigar el fallo intermitente del primer e2e tras arranque | A9 | V15 | causa documentada o 10 ejecuciones verdes |

### Fase 2 — Intensidad de datos CAM (10–16/11) · gate **G-Datos** (refuerza el desempate)

| # | Tarea | Dueño | Criterio | Aceptación |
|---|---|---|---|---|
| 2.1 | ✅ (08/11) Auditar el Portal CAM buscando datasets **municipales** con relación directa: viviendas / segundas residencias / hogares (exposición en interfaz urbano-forestal a escala municipal), montes de utilidad pública, superficie forestal por propiedad, equipamientos de emergencia por municipio | A2 | D25 | `DATA_CATALOG.md` ampliado con verificación real (no se integra lo que no sirve) |
| 2.2 | ✅ (08/11: CAM-09, CAM-10, CAM-11 — Censo 2021; e2e local 10/10 ✔ 09/11) Integrar 2–4 datasets nuevos que superen la auditoría, con ficha, filtro y comparador | A2+A6+A7 | D25 | tests T01/T02 + visibles en la demo |
| 2.3 | ✅ (09/11, DOC-01: 59 ZAR + siniestros municipales 2015–2024 por causa, Anexo I) Lista oficial de **municipios en Zonas de Alto Riesgo (ZAR)** del Plan Anual 2026 / INFOMA como capa de contexto (documento oficial, citado con página) | A1+A2 | D25, D20 | fuente y página citadas; test de que coincide con el documento |
| 2.4 | ✅ (09/11: `escudo_pipelines.refresh`; prueba real: CAM-07 cambió de SHA-256 con las mismas 760 filas reordenadas) Actualización automática verificable: comando `refresh` que vuelve a descargar, compara SHA-256 y registra versión; panel «última actualización» por fuente | A2+A10 | D25, R10 | test existente + demostración en vivo |
| 2.5 | ✅ (08/11; e2e local 10/10 ✔ 09/11) Histórico regional en la ficha y en el análisis: CAM-05 incendios 1985–2025, CAM-06 repoblaciones (M14), siempre etiquetado «regional» | A7 | D25 | UI + e2e |
| 2.6 | ✅ (09/11: integrado como EFF-01, CC BY 4.0; 73 perímetros 2016–2026, capa en mapa y ficha) Copernicus EFFIS: evaluar licencia y utilidad (áreas quemadas históricas) — integrar solo si aporta y la licencia lo permite | A3 | D20 | decisión documentada |

### Fase 3 — Impacto con evidencia (12–21/11) · gate **G-Impacto** 👤

| # | Tarea | Dueño | Criterio | Aceptación |
|---|---|---|---|---|
| 3.1 | ✅ (09/11: `docs/validation/protocolo-experimento.md`, diseño intra-sujeto contrabalanceado con casos A/B ficticios equivalentes, materiales y clave generados por script) Protocolo del **experimento de utilidad** (PRD §5.5): misma tarea con y sin ESCUDO; medir tiempo, omisiones, cobertura de prioridades, calidad documental; consentimiento | A8 | I25 | `docs/validation-report.md` con protocolo antes de las sesiones |
| 3.2 | ✅ plantillas (09/11: guion, consentimiento, registro CSV); faltan respuestas reales (👤 H6) — Guion de entrevista (técnico y gestor) y registro de respuestas: útil / inviable / redundante / requiere revisión | A8 | I25, D20 | plantilla + respuestas reales anonimizadas |
| 3.3 | Ejecutar sesiones (👤 H6) y, si no se logra, **ensayo interno** declarado como tal con tamaño de muestra | A8+👤 | I25 | resultados con n y límites; nunca extrapolar |
| 3.4 | Panel de impacto «antes / después» del flujo (M12) con las métricas medidas en 3.3 | A7 | I25 | solo cifras medidas |
| 3.5 | Modelo de implantación y costes reales: coste mensual medido del despliegue, horas de mantenimiento, quién lo opera (ayuntamiento, mancomunidad, CAM) | A0+A10 | V15, I25 | tabla con costes medidos, no estimados a ojo |

### Fase 4 — Producto P1 que suma originalidad (13–20/11)

Solo tras G-Demo. Orden por valor ante el jurado:

| # | Módulo | Dueño | Criterio | Nota |
|---|---|---|---|---|
| 4.1 | ✅ (09/11: `GET /v1/calendar` y `.ics`; épocas de peligro oficiales DOC-01 pág. 18) M16 Calendario preventivo: vencimientos de acciones, revisión anual del PAIF, inspecciones programadas; export iCal | A6+A7 | D20, V15 | recordatorios no críticos |
| 4.2 | ✅ (09/11: 15 puntos con cita literal verificada contra el BOCM, DOC-02; enlazado al plan; nunca aprueba) M15 Expediente PAIF/PAMIF: checklist de información pendiente según INFOMA, adjuntos, estado; **nunca aprobación** | A6+A7 | D20, I25 | texto legal revisado por A1 |
| 4.3 | ✅ (10/11: comentarios y decisiones inmutables por actuación, inspección y ámbito; pestaña «Decisiones»; aislado y auditado) M17 Colaboración: comentarios por acción/inspección, registro de decisiones con autor y fecha | A6+A7 | D20 | auditado |
| 4.4 | ✅ (10/11: búsqueda EXTRACTIVA sin IA generativa sobre DOC-01 y DOC-02; acierto@3 = 18/20 en conjunto fijado antes de ajustar; Ley 43/2003 no indexada) M19 Asistente documental con citas sobre el Plan 2026, INFOMA y Ley 43/2003 (RAG local; responde solo con cita; nunca decisiones operativas) | A5+A6 | D20 | evaluación con 20 preguntas y respuestas verificadas |
| 4.5 | ✅ (10/11: `/avance` y `GET /v1/public/progress`; solo ámbitos autorizados, umbral ≥3 ámbitos de ≥2 organizaciones, sin nombres ni costes; 3 ámbitos ficticios en Collado Villalba para la demo) M18 Portal público: avance agregado por municipio sin datos privados | A7 | I25 | test de privacidad |
| 4.6 | ✅ (10/11: `/campo` instalable, abre sin conexión vía service worker que nunca guarda la API, cola IndexedDB, envío idempotente por `client_uuid` y deduplicación de fotos; probado en e2e con red cortada; falta prueba en móvil físico) M21 PWA para inspección en campo (formulario offline y sincronización) | A7 | V15 | probado en móvil |

### Fase 5 — Calidad, seguridad y publicación (17–23/11) · gates **G7/G9**

| # | Tarea | Dueño | Criterio | Aceptación |
|---|---|---|---|---|
| 5.1 | ✅ (11/11: `docs/privacy-security.md`; 8 hallazgos corregidos, 0 vulnerabilidades en dependencias) Revisión de seguridad y privacidad: aislamiento multi-tenant, subida de ficheros, cabeceras, secretos, dependencias (`docs/privacy-security.md`) | A9 | V15, R10 | sin hallazgos P0 |
| 5.2 | ✅ (11/11: 0 incidencias WCAG 2.1 AA con axe en 9 páginas y el área privada; sin desbordamiento a 390 px; `docs/accessibility.md`; falta móvil físico) Accesibilidad (teclado, contraste, lector de pantalla) y responsive | A9 | V15, P5 | informe + correcciones |
| 5.3 | ✅ Repositorio público depurado (👤 H4): sin credenciales, datos con licencia, README, CI verde en GitHub (07/11) | A10 | R10 | CI verde en el repo público |
| 5.4 | ✅ (11/11: https://lorenadata-escudo-madrid.hf.space; construcción 3 min; secretos AEMET y JWT en el Space; 30/30 e2e en la URL pública; falta móvil físico) Despliegue público en HF Spaces 18–19/11 (👤 H5; contenedor único listo, sin probar en remoto) + copia local de respaldo + capturas y vídeo de 60 s como plan C | A10 | V15, P5 | URL estable 72 h antes del 26 |
| 5.5 | ✅ (11/11: clon nuevo + README, ~9 min, 128 pytest + 30/30 e2e; encontrado y corregido índice duplicado en migración) T11: instalación limpia en otra máquina siguiendo solo el README | A9 | R10 | cronometrada y documentada |
| 5.6 | Freeze de funcionalidades **23/11**; solo correcciones después | A0 | todos | etiqueta `v1.0-datamad` |

### Fase 6 — Presentación y defensa (21–25/11)

| # | Tarea | Dueño | Criterio | Aceptación |
|---|---|---|---|---|
| 6.1 | Actualizar las 3+1 diapositivas con resultados de validación, enlaces y equipo | A11 | P5 | formato exacto de las bases |
| 6.2 | Guion de 5 min afinado + respuestas a 15 preguntas difíciles (`docs/demo-script.md`) | A11 | P5 | ensayado |
| 6.3 | Kit de respaldo: PDF de las diapositivas, vídeo, capturas, informe PDF, demo local | A11 | P5, V15 | probado sin red |
| 6.4 | Verificación final de cifras: cada número del pitch con su comando de comprobación | A0 | todos | checklist firmada 25/11 |

---

## 4. Calendario día a día

| Día | Foco | Salida |
|---|---|---|
| Vie 07/11 | Roadmap · Flujo B (API + datos) | Flujo B en API con tests |
| Sáb 08/11 | Flujo B (UI) · geometría de ámbitos | Flujo B navegable |
| Dom 09/11 | Revisión técnica UI · Flujo A completo · 👤 H1, H2 | e2e Flujo A |
| Lun 10/11 | Auditoría de datasets CAM municipales · 👤 H3 | lista verificada |
| Mar 11/11 | Integración datasets CAM nuevos · ZAR | fichas ampliadas |
| Mié 12/11 | Refresh automático · histórico regional · 👤 H4, contactos H6 | **G-Demo + G-Datos** |
| Jue 13/11 | Calendario preventivo (M16) · protocolo experimento | |
| Vie 14/11 | Expediente PAIF (M15) · 👤 H5 · primeras sesiones | |
| Sáb–Dom 15–16/11 | Colaboración (M17) · sesiones de validación | |
| Lun 17/11 | Asistente documental con citas (M19) | |
| Mar 18/11 | Portal público (M18) · panel antes/después | |
| Mié 19/11 | PWA de inspección (M21) · costes medidos | |
| Jue 20/11 | Seguridad, privacidad, accesibilidad · 👤 H7 | **G-Impacto** |
| Vie 21/11 | Repo público + CI + despliegue | |
| Sáb 22/11 | T11 instalación limpia · informe de validación · ensayo 1 | |
| Dom 23/11 | **Freeze** · 👤 H8 envío del resumen | `v1.0-datamad` |
| Lun 24/11 | Diapositivas finales · kit de respaldo · ensayo 2 | |
| Mar 25/11 | Verificación final de cifras · ensayo con preguntas | **listo** |
| Mié 26/11 | Entrega antes de las 14:00 · defensa | |

---

## 5. Riesgos que pueden costar el premio

| Riesgo | Impacto | Mitigación |
|---|---|---|
| No hay validación con usuarios | Impacto (25) se queda en hipótesis | H6 desde ya; ensayo interno declarado como plan B |
| Demo falla en directo | Viabilidad y presentación | Demo local + vídeo + capturas; e2e antes de salir |
| Datos CAM percibidos como decorativos | Criterio de 25 y desempate | Funciones analíticas visibles en la demo (ficha, filtro, comparador, análisis) y más datasets municipales |
| Repo no público a tiempo | Código abierto (10) | H4 antes del 12/11 |
| Afirmaciones de impacto no sostenidas | Credibilidad y posible penalización | Regla de cero cifras inventadas; verificación 6.4 |
| Dispersión en P1 | Producto inconexo | Freeze 23/11; P1 solo tras G-Demo |
| Memoria limitada en el equipo de desarrollo | Servidores cortados | Parar contenedores ajenos durante la sesión |

---

## 6. Histórico de gates del PRD

| Gate | Estado |
|---|---|
| G0–G4 | ✅ (backend, mapa, vertical, solver) |
| G5 integración completa | 🟡 falta Flujo B, observabilidad ampliada |
| G6 validación | ⬜ 👤 |
| G7 freeze + resumen | ⬜ 23/11 |
| G8 preselección | ⬜ 👤 antes del 24/11 |
| G9 ensayo y backup | ⬜ 24–25/11 |
| G10 entrega | ⬜ 26/11 |
