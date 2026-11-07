# Guion de demostración — 5 minutos + 5 de preguntas (A11)

Formato de las bases (ap. 8–9): exposición de **5 min** y **5 min** de preguntas. Ensayar con cronómetro. Todas las cifras de este guion salen del repositorio; si cambian los datos, regenerarlas (ver «Comprobaciones previas»).

## Preparación (T-30 min)

1. `bash scripts/demo.sh` (≈30 s): BD, migraciones, datos, API :8000, web :3000 y cachés calentadas (incluida AEMET con su fecha real).
2. `bash scripts/demo.sh check`: 10 e2e en verde (T10) y la demo queda restaurada sin ámbitos de prueba. Si falla, usar el **plan B**.
3. Abrir pestañas: `/` (explorador), `/demo`, `/fuentes`, y el PDF `/v1/demo/report.pdf` ya descargado.
4. **Plan B sin red ni servidor:** capturas `artifacts/demo-screenshots/01…06` y el PDF descargado. AEMET puede estar caído: la ficha mostrará «No disponible» — es el comportamiento correcto y se puede enseñar (pregunta «¿Y si AEMET falla?»).

## Guion

| Tiempo | Pantalla | Qué decir (idea, no literal) |
|---|---|---|
| 0:00–0:40 | Diapositiva 1–2 | La información de prevención existe; convertirla en actuaciones priorizadas y documentadas exige coordinación. El *Plan Anual 2026* programa **5.652,38 ha** de trabajos preventivos y recoge **68 PAIF** en **26 municipios** (21 con informe favorable, 47 en tramitación). Estas cifras dan contexto: no prueban un déficit. |
| 0:40–1:30 | `/fuentes` | Ocho conjuntos del **Portal de Datos Abiertos de la CAM**, cada uno con licencia, fecha y huella SHA-256; cartografía oficial del IDEM y AEMET como complemento. Descargar el CSV: cualquiera reproduce las cifras. |
| 1:30–2:15 | `/` explorador | Coropleta de densidad (CAM-02) sobre los 179 municipios. Buscar **San Lorenzo de El Escorial**: población 18.942 (CAM-01, 2025), 20,8 % ≥65, serie 2021–2025. Aviso de escala municipal. «Superficie forestal municipal: no disponible» — el portal solo la publica a escala regional y no la inventamos. |
| 2:15–2:45 | capa de riesgo | Activar **Riesgo oficial (GEO-01)**: clases literales; 53,9 % de la superficie municipal en «Riesgo muy alto». Peligrosidad y vulnerabilidad son capas distintas y no se mezclan. AEMET con fecha de emisión. |
| (opcional, si sobra tiempo) | `/analisis` | Con un clic: municipios con ≥50 % de superficie en riesgo alto o muy alto (GEO-01) y densidad < 20 hab/km² (CAM-02). Es un filtro sobre valores publicados, no un índice nuestro. |
| 2:45–3:45 | `/demo` | Caso guiado con urbanización **ficticia** etiquetada: inspección → 11 medidas del catálogo ligado al INFOMA → presupuesto de demo 30.000 €. El optimizador CP-SAT cubre el **90,1 %** de la prioridad técnica frente a **84,2 %** (manual) y **85,1 %** (menor coste), sin superar el presupuesto. Mostrar sensibilidad. Insistir: es una función objetivo acordada, **no reducción de riesgo**. |
| 3:45–4:20 | plan + PDF | Plan con responsables, vencimientos, historial y evidencias; informe PDF con fuentes, método, supuestos y «validación profesional pendiente». |
| 4:20–5:00 | Diapositiva 3 | 67 tests automáticos + 6 de navegador, código abierto, ETL reproducible, multiusuario aislado. Siguiente paso: validar con técnicos y una urbanización real. |

## Preguntas previsibles (PRD §10.3)

- **¿No existe ya un mapa oficial?** Sí y lo usamos tal cual; aportamos el flujo de planificación, presupuesto y seguimiento.
- **¿Y FIREPRIME / SAVER / MINCE?** FIREPRIME autoevalúa viviendas; SAVER y MINCE son plataformas internas de la CAM citadas en el Plan 2026. No afirmamos más de lo que dice el Plan (`COMPETITORS.md`).
- **¿Dónde está el dato del Portal de Madrid?** CAM-01/02/03/08 en la ficha, el filtro y el comparador; el test `test_profile_values_trace_to_processed_cam_data` comprueba que el valor mostrado es el del fichero.
- **¿Garantizáis reducción de riesgo?** No. Medimos gestión: cobertura de prioridades, actuaciones documentadas, plazos.
- **¿Si AEMET cae?** «No disponible» con la fecha del último dato válido; el resto sigue funcionando.
- **¿Quién aprueba las medidas?** Personal técnico competente y la administración. La herramienta no aprueba PAIF; la revisión técnica exige cualificación verificada.
- **¿Qué habéis hecho en el periodo?** Historial de commits fechado; `PROVENANCE.md` declara el andamiaje del 06/11.

## Comprobaciones previas de cifras

`GET /v1/municipalities/28131/profile` (población, ≥65, clases GEO-01) · `GET /v1/demo/guided` (coberturas) · `pytest -q` y `npm run e2e` (número de tests).
