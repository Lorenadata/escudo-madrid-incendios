# Protocolo del experimento de utilidad (ROADMAP 3.1 · PRD §5.5)

**Estado:** protocolo cerrado el 09/11/2026, **antes** de cualquier sesión. Los resultados se registran en `docs/validation-report.md`. Si no se consiguen participantes externos, se hará un **ensayo interno** y se declarará como tal.

## 1. Pregunta

¿Ayuda ESCUDO MADRID a preparar un plan de actuaciones preventivas **más completo, mejor documentado y en menos tiempo** que el método habitual (hoja de cálculo, papel, buscador), con la misma información y el mismo presupuesto?

No se pregunta, ni se concluirá, nada sobre reducción del riesgo, incendios evitados o ahorro real (PRD §5.5, KPIs no permitidos).

## 2. Participantes

| Perfil | Objetivo mínimo | Cómo |
|---|---|---|
| Técnico forestal o de protección civil | 1 | Contacto de la participante (👤 H6) |
| Gestor de urbanización o técnico municipal | 1 | Contacto de la participante (👤 H6) |
| Ensayo interno (si faltan externos) | declarado | Personas sin relación con el desarrollo, identificadas como «ensayo interno» |

Con n tan pequeño, los resultados son **exploratorios**: se informan caso a caso, con n explícito, sin medias que aparenten precisión ni contrastes estadísticos.

## 3. Diseño: intra-sujeto y contrabalanceado

Cada participante resuelve **dos casos ficticios equivalentes**, uno con su método habitual y otro con ESCUDO. Para que el aprendizaje no favorezca a una condición, se alterna el orden:

| Participante | Primera tarea | Segunda tarea |
|---|---|---|
| Impar (1, 3…) | Caso A **sin** ESCUDO | Caso B **con** ESCUDO |
| Par (2, 4…) | Caso B **sin** ESCUDO | Caso A **con** ESCUDO |

**Equivalencia de los casos** (`fixtures/synthetic/demo_seed.json`, organización «Sesiones de validación»):

| | Caso A (Los Pinos) | Caso B (Los Robles) |
|---|---|---|
| Hallazgos de inspección | 7 | 7 |
| Actuaciones posibles | 11 (mismos códigos) | 11 (mismos códigos) |
| Coste total / presupuesto | 38.560 € / 30.000 € (78 %) | 38.350 € / 30.000 € (78 %) |
| Cobertura óptima vs. orden manual | 90,1 % vs. 84,2 % | 90,4 % vs. 86,5 % |

Todo es inventado; solo los municipios de referencia son reales.

## 4. Materiales

- Hojas de participante: `docs/validation/materiales/caso-A-participante.md` y `caso-B-participante.md`. Contienen **la misma información** que ve quien usa ESCUDO.
- Clave del evaluador: `docs/validation/materiales/clave-evaluador.md` (no se entrega).
- ESCUDO: cuentas `validacion1@demo.escudo.local` / `validacion2@demo.escudo.local` (contraseña de demo). Cada caso tiene la inspección cargada y un **escenario en borrador** sin resolver.
- Consentimiento: `docs/validation/consentimiento.md`. Guion de entrevista: `docs/validation/guion-entrevista.md`.
- Registro: `docs/validation/registro-sesiones.csv`.
- Regenerar materiales: `python scripts/validation_materials.py`. Restaurar la demo entre sesiones: `python -m escudo_api.etl_load --skip-idem`.

## 5. Desarrollo de la sesión (≈ 60 min)

1. Consentimiento firmado o verbal grabado (5 min).
2. Explicación común: datos ficticios, objetivo de la tarea, que se mide la herramienta y no a la persona (3 min).
3. Tarea 1 (máx. 20 min) con la condición asignada. Cronómetro desde que se entrega la hoja hasta que el participante dice «terminado».
4. Formación mínima en ESCUDO **antes** de la tarea con ESCUDO, la misma para todos: 3 min con el caso guiado `/demo`.
5. Tarea 2 (máx. 20 min) con la otra condición.
6. Cuestionario breve y entrevista (10 min, `guion-entrevista.md`).

La persona que conduce no ayuda durante las tareas salvo dudas de manejo, que se anotan.

## 6. Medidas (solo KPIs permitidos, PRD §5.5)

| Medida | Cómo se obtiene | Unidad |
|---|---|---|
| Tiempo de planificación | Cronómetro | minutos |
| Omisiones | 7 elementos obligatorios de la clave del evaluador | nº de 0 a 7 |
| Cobertura de prioridades bajo presupuesto | `python scripts/validation_materials.py score <caso> <códigos>` (misma función objetivo que el optimizador) | % |
| Dentro de presupuesto | mismo comando | sí / no |
| Calidad documental | Actuaciones con responsable, fecha y evidencia prevista / total de actuaciones | % |
| Fuentes citadas | Recuento | nº |
| Finalización | Termina en 20 min | sí / no |
| Percepción de utilidad | 5 ítems Likert 1–5 del guion | 1–5 por ítem |
| Valoración de las recomendaciones | útil / inviable / redundante / requiere revisión (PRD §5.5) | categorías |

## 7. Análisis y comunicación

- Tabla por participante y condición, con n y perfil anonimizado («técnico 1», «gestor 1»).
- Diferencias con/sin **por participante**; sin extrapolar a otros municipios ni a la población.
- Se publican también los resultados desfavorables y las dificultades de manejo.
- Los comentarios cualitativos se resumen fielmente; las citas literales solo con permiso explícito.
- El panel de impacto (3.4) mostrará **solo** cifras medidas aquí.

## 8. Ética y datos

Participación voluntaria; se puede abandonar en cualquier momento. No se recogen datos personales más allá del perfil profesional genérico. Los registros se guardan anonimizados en el repositorio; las notas con nombres, si las hubiera, se quedan fuera del repositorio y se destruyen tras el concurso.
