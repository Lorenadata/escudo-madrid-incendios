# ROADMAP — Tablero P0/P1, dependencias y gates (A0)

Fechas del PRD §8. Estado a 06/11/2026. ✅ hecho y verificado · 🟡 en curso/parcial · ⬜ pendiente.

## Gates

| Gate | Fecha | Condición | Estado |
|---|---|---|---|
| G0 | 7 nov | Repo, PRD, contratos | ✅ (andamiaje 06/11 declarado en PROVENANCE) |
| G1 | 8–9 nov | ≥1 dataset CAM usado analíticamente; IDEM y AEMET evaluados | ✅ adelantado |
| G2 | 10–11 nov | PostGIS, fuentes versionadas, primer mapa y fichas | 🟡 API ✅ · mapa web A7 en curso |
| G3 | 12–14 nov | Login, zona, inspección, medidas, export E2E | 🟡 backend ✅ · UI pendiente |
| G4 | 15–17 nov | Solver validado, 3 escenarios, baseline, tests | ✅ backend · UI pendiente |
| G5 | 18–20 nov | AEMET, tareas, informes, capas, multiusuario, observabilidad | 🟡 |
| G6 | 21–22 nov | Validación con usuarios/técnico | ⬜ humano |
| G7 | 23 nov | Freeze candidatura + resumen ≤100 palabras | ⬜ |
| G8 | <24 nov | Envío de preselección | ⬜ humano |
| G9 | 24–25 nov | 3+1 slides, ensayo, backup, 0 P0 bloqueantes | ⬜ |
| G10 | 26 nov <14:00 | Entrega | ⬜ humano |

## Issues P0

| # | Módulo | Tarea | Dueño | Depende | Límite | Estado |
|---|---|---|---|---|---|---|
| 1 | M11 | Registro de fuentes, manifests, calidad | A2 | — | 9 nov | ✅ |
| 2 | M03 | Ficha municipal CAM-01/02/03/08 + capas oficiales | A2/A3/A6 | 1 | 11 nov | ✅ API |
| 3 | M02 | Explorador regional MapLibre | A7 | 2 | 11 nov | 🟡 |
| 4 | M04 | Contexto AEMET con caducidad | A4/A6 | — | 11 nov | ✅ API |
| 5 | M01 | Auth JWT, organizaciones, roles, auditoría | A6 | — | 13 nov | ✅ API · ⬜ gestión de usuarios |
| 6 | M05 | Áreas de interés con geometría autorizada | A6/A7 | 5 | 13 nov | ✅ API · 🟡 UI |
| 7 | M06 | Inspecciones, checklist, evidencias | A6/A7 | 6 | 14 nov | ✅ API · 🟡 UI · ⬜ revisión técnica (endpoint) |
| 8 | M07 | Catálogo de medidas | A1 | — | 12 nov | ✅ (revisión técnica humana pendiente) |
| 9 | M08 | Escenarios + optimizador + sensibilidad | A5/A6 | 8 | 17 nov | ✅ API |
| 10 | M09 | Plan de ejecución, historial | A6/A7 | 9 | 18 nov | ✅ API · 🟡 UI |
| 11 | M10 | Informe PDF + export CSV/GeoJSON | A6 | 9 | 18 nov | ✅ PDF · ⬜ CSV/GeoJSON export |
| 12 | M12 | Panel de impacto (KPIs operativos) | A6/A7 | 10 | 19 nov | ✅ API · 🟡 UI |
| 13 | M22 | Observabilidad: logs de latencia, salud de fuentes | A10 | — | 20 nov | 🟡 logs + /health · ⬜ backups |
| 14 | — | Migraciones Alembic formales | A6 | — | 20 nov | ✅ |
| 15 | — | CI en GitHub (requiere repo remoto — decisión humana) | A10 | — | 20 nov | 🟡 workflow escrito |
| 16 | — | e2e Playwright (T10) | A9 | 3 | 22 nov | ⬜ |
| 17 | — | Pitch 3+1, guion, capturas | A11 | 3,9 | 24 nov | ⬜ |

## P1 (tras asegurar P0)

M13 comparador (✅ API `/v1/compare`), M14 histórico (✅ API CAM-05/06/07 + series municipales), M15 PAIF/PAMIF, M16 calendario, M17 colaboración, M18 portal público, M19 asistente documental con citas, M20 API de reutilización (OpenAPI ✅), M21 accesibilidad/PWA.
