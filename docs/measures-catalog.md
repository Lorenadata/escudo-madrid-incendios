# Catálogo de medidas preventivas (M07)

Dueño: **A1**. Fichero máquina: `data/reference/measures_catalog.json` (v0.1.0, 06/11/2026). Esquema por medida = tipo `Measure` de `docs/contracts/api-contract.md` más cuatro campos informativos: `obligation_level`, `obligated_party`, `review_status` y, a nivel de catálogo, `references`/`disclaimer`/`cost_policy`. Las medidas están bajo la clave `measures`.

> **Estado: `pending_technical_review`.** Lo ha redactado un agente de IA a partir del texto publicado del Decreto 59/2017 (INFOMA) y del Plan Anual 2026. Ninguna medida está validada por un técnico competente. ESCUDO no redacta, aprueba ni certifica PAIF.

## Fuentes verificadas (06/11/2026)

| Clave | Documento | URL | SHA-256 |
|---|---|---|---|
| INFOMA | Decreto 59/2017 (BOCM núm. 136, 09/06/2017), Anexos 2, 5, 6 y 7 | https://www.bocm.es/boletin/CM_Orden_BOCM/2017/06/09/BOCM-20170609-1.PDF | `d9524a09…909271c` |
| PLAN_ANUAL_2026 | Plan Anual de Prevención, Vigilancia y Extinción de Incendios Forestales 2026, ap. 9.2 | https://www.comunidad.madrid/transparencia/sites/default/files/plan_anual_iiff_2026.pdf | `22d08b64…16c6efc` |
| LEY_43_2003 | Ley de Montes, art. 48.6 (solo citada a través del INFOMA) | https://www.boe.es/buscar/act.php?id=BOE-A-2003-21339 | — |

Las citas se han comprobado sobre el texto extraído del PDF del BOCM. **Pendiente:** contrastar con la versión consolidada vigente (corrección de errores de 28/07/2017 y posibles modificaciones posteriores).

**No se cita el RD 893/2013 como vigente:** la Directriz Básica de 2026 (BOE-A-2026-9159) recoge que fue derogado por el RD 524/2023, aunque el INFOMA (Anexo 5, ap. 2.8) y el Plan Anual 2026 todavía lo mencionan.

## Medidas

| Código | Medida | Unidad | Base normativa | Requiere técnico | Prerrequisitos / exclusiones |
|---|---|---|---|---|---|
| DELIM-PLANO | Consulta del plano municipal de delimitación | ud | INFOMA An. 6 ap. 1.1.1 | no | — |
| FAJA-30 | Faja perimetral de protección de 30 m | m² | INFOMA An. 6 ap. 1.2.1.b; An. 7 a | sí | requiere DELIM-PLANO |
| PARC-NOED | Mantenimiento de parcelas no edificadas | m² | INFOMA An. 6 ap. 1.2.1.c | sí | requiere DELIM-PLANO |
| VIAL-LIMP | Limpieza de viales privados y cunetas | m | INFOMA An. 6 ap. 1.2.1.e; An. 5 ap. 1 | no | — |
| PODA-GALIBO | Poda para gálibo de 5 m | m | INFOMA An. 7 c | sí | — |
| ACCESO-VIAL | Adecuación de accesos para servicios de extinción | m | INFOMA An. 7 c; Ley 43/2003 art. 48.6 | sí | — |
| HIDR-REV | Verificación del estado de hidrantes | ud | INFOMA An. 5 ap. 1 | sí | — |
| HIDR-RED | Red de hidrantes homologados (CTE) | ud | INFOMA An. 6 ap. 1.2.1.d; An. 7 d–e | sí | — |
| PAIF-RED | Redacción del PAIF por técnico competente | ud | INFOMA An. 6 ap. 1.2.1.a; An. 5 ap. 2; Plan 2026 ap. 9.2 | sí | requiere DELIM-PLANO |
| PAIF-MANT | Programa anual de mantenimiento y actuaciones | ud/año | INFOMA An. 5 ap. 2.7 | sí | requiere PAIF-RED |
| PAIF-AVISOS | Directorio de comunicación y plan de avisos al 112 | ud/año | INFOMA An. 5 ap. 2.4–2.5.a | no | requiere PAIF-RED |
| SENAL-CALLES | Señalización de calles sin salida | ud | INFOMA An. 6 ap. 1.1.2 | no | — |
| RESTOS-TRIT | Restos: triturado/astillado y retirada | m² | — (buena práctica) | no | requiere FAJA-30; excluye RESTOS-QUEMA |
| RESTOS-QUEMA | Restos: quema con autorización | m² | INFOMA An. 2 ap. 2.3.1 | sí | requiere FAJA-30; excluye RESTOS-TRIT |
| CUBIERTAS-LIMP | Limpieza de cubiertas, canalones y hojarasca | ud | — (buena práctica, sin norma verificada) | no | — |
| INFO-POB | Sesión informativa a residentes | sesión | INFOMA An. 5 ap. 1 | no | — |

`obligation_level` distingue: `obligacion_infoma` (Anexo 6, urbanizaciones sin continuidad con la trama urbana y supuestos asimilados), `obligacion_infoma_nuevas_o_buena_practica` (Anexo 7, exigible a nuevas edificaciones/instalaciones; en existentes es una buena práctica a validar), `contenido_paif` (Anexo 5), `actividad_sujeta_a_autorizacion`, `prerequisito_administrativo` y `buena_practica_sin_norma_verificada`.

## Costes

**Todos los `reference_unit_cost_eur` son `null` y `cost_status = "scenario"`.** No se encontró una base de precios pública y verificable para estas partidas aplicables a urbanizaciones:
- *Tarifas TRAGSA 2026*: el BOE-A-2026-9265 (28/04/2026) publica solo el acuerdo de aprobación y la revisión de coeficientes, no los precios unitarios (que se consultan en tragsa.es), y solo aplican a encargos de entidades del sector público. Podrían servir de **referencia orientativa** para ayuntamientos si alguien extrae las partidas concretas (código, año, unidad) y las revisa.
- En la demo, los costes deben entrar como `user_quote` (presupuesto real aportado) o como `scenario` claramente etiquetado, con `is_demo_budget: true`.

## Reglas de uso en el producto
1. Mostrar siempre la base normativa y el `review_status`; las medidas sin norma verificada aparecen como «buena práctica».
2. La responsabilidad (`obligated_party`) se muestra como información, no como imputación a personas concretas; ESCUDO no identifica propietarios.
3. Las prioridades técnicas (`p_i`) las asigna un técnico en cada escenario; el catálogo no las fija.
4. Las medidas que tocan emergencias (PAIF-AVISOS) solo registran la existencia y fecha del documento.
