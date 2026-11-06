# ESCUDO MADRID — aplicación web (A7)

Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 + MapLibre GL JS 5. Consume la API FastAPI definida en
`docs/contracts/api-contract.md`. Sin datos simulados en el código: si la API falla, cada pantalla muestra su estado de error.

## Uso

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000 (por defecto ya apunta a :8000)
npm run lint && npm run typecheck && npm run build
```

Requiere la API levantada (ver `CLAUDE.md` en la raíz) y su CORS abierto a `http://localhost:3000`.

## Pantallas

| Ruta | Módulo PRD | Qué muestra |
|---|---|---|
| `/` | M02, M03, M04 | Mapa regional (coropleta CAM-01/02/03), capas oficiales GEO-01..03 con leyenda literal, buscador y filtro por densidad, ficha municipal con series anuales, cartografía oficial y contexto AEMET. Admite enlace directo `/#28079`. |
| `/comparar` | M13 | Dos municipios lado a lado con los mismos indicadores. |
| `/fuentes` | M11, M14, M20 | Registro de fuentes (licencia, fechas, SHA-256, estado), exportación CSV, serie regional CAM-05. |
| `/demo` | Flujo C | Caso guiado público: datos oficiales reales + ámbito, inspección, escenario y plan FICTICIOS etiquetados; PDF. |
| `/login`, `/app` | M01, M05–M10, M12 | Flujo A: ámbitos, inspecciones con checklist y evidencias, revisión técnica, escenarios, solver, plan de ejecución, informe PDF, KPIs de gestión y auditoría. |

## Convenciones

- `StatusBadge` distingue `official`, `derived`, `scenario`, `user_reported`, `unavailable` y `stale` por **forma** (relleno, contorno, discontinuo, doble, rayado, punteado) además de por color.
- `IndicatorValue` pinta cualquier `Indicator` con unidad, escala, año y «Ver método y fuentes».
- Capas oficiales: colores `color_suggestion` de la fuente; si faltan, rampa ordinal (muy bajo → muy alto). Nunca orden alfabético.
- Mapa base: IGN España WMTS `IGNBaseTodo` (CC BY 4.0, atribución visible). Sin claves.
- El token JWT se guarda en `sessionStorage` (se pierde al cerrar la pestaña).
- No se muestran credenciales en la interfaz; las cuentas ficticias locales están en `fixtures/synthetic/demo_seed.json`.
