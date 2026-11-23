# Guion de demostración — 5 minutos + 5 de preguntas (A11)

Formato de las bases (ap. 8–9): exposición de **5 min** y **5 min** de preguntas. Ensayar con cronómetro. Todas las cifras de este guion salen del repositorio; si cambian los datos, regenerarlas (ver «Comprobaciones previas»).

## Preparación (T-30 min)

1. `bash scripts/demo.sh` (≈30 s): BD, migraciones, datos, API :8000, web :3000 y cachés calentadas (incluida AEMET con su fecha real).
2. `bash scripts/demo.sh check`: 10 e2e en verde (T10) y la demo queda restaurada sin ámbitos de prueba. Si falla, usar el **plan B**.
3. Abrir pestañas: `/` (explorador), `/demo`, `/fuentes`, y el PDF `/v1/demo/report.pdf` ya descargado.
4. **Plan B sin red ni servidor:** capturas de la web pública del 22/11 en `artifacts/demo-screenshots/plan-b/` (01 fuentes → 10 meteo, en el orden del guion) y el informe `11-informe-demo.pdf`. AEMET puede estar caído: la ficha mostrará «No disponible» — es el comportamiento correcto y se puede enseñar (pregunta «¿Y si AEMET falla?»).

## Guion

El guion vigente, con lo que se dice y lo que se hace en cada bloque, está en **`docs/pitch/guion-escenario.md`** (abre con el hallazgo 38 / 28 de 58, sigue con `/ranking`, la ficha, el caso guiado y la diapositiva 3). Preguntas: `docs/pitch/preguntas.md`. Recorrido de cada pantalla: `docs/pitch/recorrido-web.md`. Entrega: `docs/pitch/entrega.md`.

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
