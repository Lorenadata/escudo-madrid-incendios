# Operación y costes de ESCUDO MADRID (ROADMAP 3.5)

Medido el 11/11/2026 sobre el despliegue real: **https://lorenadata-escudo-madrid.hf.space** (Hugging Face Space `lorenadata/escudo-madrid`). Solo se anotan cifras medidas o facturadas; lo no medido se indica como tal.

## 1. Despliegue actual

| Elemento | Valor | Origen |
|---|---|---|
| Plataforma | Hugging Face Spaces, Docker, hardware `cpu-basic` | API del Space (`runtime.hardware`) |
| Coste | **6,50 €** cobrados por la suscripción PRO de Hugging Face (noviembre de 2026); se cancelará tras la entrega | factura de la participante (12/11) |
| Arquitectura | Un contenedor: PostGIS + API + web, construido desde el repositorio público en un commit fijo | `infra/docker/space.Dockerfile` |
| Construcción completa | 2–4 min (dos construcciones el 11/11) | estado del Space |
| Arranque en frío (reinicio) | 40 s hasta que responde el caso guiado | medición del 11/11 |
| Suspensión por inactividad | Tras 48 h sin visitas (`gcTimeout` = 172 800 s); no modificable en `cpu-basic` | API del Space |
| Persistencia | Ninguna: cada reinicio recarga los datos reales y restaura la demo ficticia | diseño |
| Secretos | `AEMET_API_KEY` y `ESCUDO_JWT_SECRET` como *secrets* del Space | configuración |
| Verificación | 30/30 pruebas de navegador ejecutadas contra la URL pública | 11/11 |

**Antes de la entrega y de la defensa:** abrir la demo unos minutos antes para despertarla si lleva 48 h sin visitas.

## 2. Tareas de mantenimiento medidas

| Tarea | Frecuencia sugerida | Tiempo medido | Comando |
|---|---|---|---|
| Comprobar si las fuentes han cambiado | mensual (y antes de la campaña) | ~1 min (12 fuentes) | `python -m escudo_pipelines.refresh` |
| Incorporar versiones nuevas y recargar | cuando haya cambios | ~2 min (CAM-07, 09/11) | `python -m escudo_pipelines.refresh --apply --rebuild` |
| Pruebas completas | en cada cambio | ~1,5 min Python + ~2,5 min navegador | `pytest` · `bash scripts/demo.sh check` |
| Redesplegar | en cada versión | 2–4 min de construcción | commit del Space con el nuevo `REPO_REF` |
| Instalación desde cero | puntual | ~9 min | README (T11, `docs/validation-report.md`) |

## 3. Quién lo operaría en una implantación real

| Opción | Quién mantiene | Datos propios | Comentario |
|---|---|---|---|
| Ayuntamiento ZAR | servicio municipal de protección civil o medio ambiente | sí, de su término | el panel municipal y el expediente ya están pensados para este rol |
| Mancomunidad o conjunto de municipios | técnico compartido | sí | reparte el coste entre municipios pequeños |
| Comunidad de Madrid | ASEM 112 o Medio Ambiente | sí, regional | encaja con el Plan Anual y el INFOMA, que ya se usan como fuentes |

En cualquier caso haría falta una base de datos persistente con copias de seguridad, almacenamiento cifrado de fotos y un encargo de tratamiento de datos (ver `docs/privacy-security.md` §6). Esos costes **no** están medidos y no se presentan como tales.
