# Accesibilidad y uso en móvil (ROADMAP 5.2)

Revisión del 11/11/2026. Objetivo: WCAG 2.1 nivel AA en todas las páginas, y uso cómodo en móvil.

## Auditoría automática (axe-core 4.14, reglas WCAG 2.0/2.1 A y AA)

| Página | Incidencias (cualquier gravedad) |
|---|---|
| Explorador `/` (lienzo del mapa excluido: su alternativa textual es la lista y la ficha de municipios) | 0 |
| Análisis `/analisis` | 0 |
| Comparar `/comparar` | 0 |
| Caso guiado `/demo` | 0 |
| Normativa `/normativa` | 0 |
| Avance `/avance` | 0 |
| Fuentes `/fuentes` | 0 |
| Acceso `/login` | 0 |
| Inspección en campo `/campo` | 0 |
| Área de trabajo con sesión: Contexto, Inspecciones, Escenarios y plan, Expediente, Decisiones | 0 |

Se ejecuta en cada `bash scripts/demo.sh check` (`apps/web/e2e/a11y.spec.ts`): una incidencia grave o crítica hace fallar la batería.

## Móvil

- Ninguna página principal se desborda en horizontal a 390 px (prueba automática en `a11y.spec.ts`).
- `/campo` está pensada para el pulgar: botones de respuesta grandes, envío en una sola pantalla y funcionamiento sin cobertura.
- Pendiente: probar en un móvil físico cuando haya enlace público (18–19/11 o antes si se activa el despliegue).

## Comprobaciones manuales

- Foco de teclado visible en todos los controles (`:focus-visible`, contorno de 2 px).
- Enlace «Saltar al contenido» al principio de cada página.
- Idioma declarado (`lang="es"`).
- Los estados de los datos (oficial, derivado, escenario…) se distinguen por forma y texto, no solo por color.
- Las gráficas tienen tabla de datos equivalente («Ver tabla de datos»).

## Límites conocidos

- El mapa (MapLibre) es un lienzo: no es navegable con lector de pantalla. Toda su información está disponible también como lista, ficha y tablas.
- La auditoría automática no sustituye una prueba con personas usuarias de tecnologías de apoyo.
