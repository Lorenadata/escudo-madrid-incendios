# Seguridad y privacidad de ESCUDO MADRID (ROADMAP 5.1)

Revisión del 11/11/2026. Alcance: API (FastAPI), web (Next.js), pipelines de datos, despliegue previsto en Hugging Face Spaces. Cada control remite a la prueba automática que lo verifica.

## 1. Qué protegemos

| Activo | Riesgo principal | Quién lo ve |
|---|---|---|
| Ámbitos, inspecciones, fotos, planes, decisiones y expedientes de cada organización | Que otra organización los lea o los modifique | Solo los miembros de esa organización (T08) |
| Ámbitos autorizados por su organización | Que el ayuntamiento vea más de lo autorizado | Ayuntamiento del término, solo lectura |
| Agregados del portal público | Re-identificar una organización a partir de los totales | Cualquiera, con umbral y redondeo |
| Fotos de campo | Ubicación GPS y datos del móvil en los metadatos | Solo la organización, y sin metadatos |
| Cuentas | Robo de sesión, fuerza bruta, falsificación de tokens | — |

ESCUDO no trata categorías especiales de datos ni datos de residentes: las cuentas son de gestores y técnicos, y la población solo aparece agregada por municipio (Portal CAM).

## 2. Controles

| Control | Implementación | Prueba |
|---|---|---|
| Aislamiento entre organizaciones | Toda ruta privada comprueba `organization_id` del recurso; responde 404 (no 403) para no revelar existencia. Revisadas todas las búsquedas por identificador (11/11) | `test_T08_isolation_between_organizations`, tests de M15, M16, M17 |
| Autorización expresa al ayuntamiento | `shared_with_municipality`, revocable; la vista municipal es de solo lectura | `test_flow_B_municipal_sees_only_authorized_areas` |
| Contraseñas | bcrypt (coste 10) | — |
| Tokens de sesión | JWT HS256 con caducidad (8 h). **Nunca** con el secreto de ejemplo del repositorio: si falta o tiene menos de 32 bytes, la API genera uno aleatorio al arrancar | `test_published_example_secret_is_never_used`, `test_51_security_headers_…` |
| Fuerza bruta | 10 intentos fallidos por par (email, IP) o 50 por IP en 15 min → 429 con `Retry-After`. Ligado a la IP para que nadie pueda bloquear la cuenta de otra persona; el intento se reserva de forma atómica (cerrojo) antes de verificar la contraseña | `tests/unit/test_security_unit.py` (incl. 100 peticiones simultáneas), `test_51_security_headers_login_throttle_and_strong_jwt_secret` |
| Enumeración de usuarios | Mismo mensaje y mismo coste (bcrypt de relleno) exista o no el email | revisión de código |
| Cabeceras de la web | CSP (`default-src 'self'`, solo IGN y AEMET como orígenes externos, `frame-ancestors 'none'`, `object-src 'none'`), `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` | e2e del explorador falla si la CSP bloquea algo |
| Cabeceras de la API | `nosniff`, `DENY`, `no-referrer`; `Cache-Control: private, no-store` en respuestas con sesión | `test_51_security_headers_…` |
| Subida de ficheros | Máx. 10 MB; solo JPEG, PNG o PDF con firma válida; **las imágenes se decodifican y se recodifican sin metadatos** (EXIF con GPS, fabricante, fecha), con un máximo de 40 megapíxeles comprobado antes de decodificar (contra bombas de descompresión); almacenamiento por SHA-256, sin nombres de usuario en rutas | `test_51_photo_metadata_gps_is_stripped_on_upload` |
| Descarga de evidencias | Solo la organización; `Cache-Control: private, no-store`; `Content-Disposition: attachment` | tests de evidencias |
| Textos libres | Control de caracteres eliminado en comentarios; escapado RFC 5545 en el calendario (sin inyección de líneas) | `test_m17_…`, `tests/unit/test_calendar_ics.py` |
| Redirecciones | `?next=` del login solo acepta rutas internas | revisión de código |
| Ficheros descargados de fuentes | Nombres saneados y confinados a `data/raw/<fuente>` | `test_remote_filenames_cannot_escape_raw_dir` |
| Portal público | Solo ámbitos autorizados; ≥3 ámbitos de ≥3 organizaciones; ninguna aporta >50 % de las actuaciones; porcentajes en tramos de 10 puntos y totales a múltiplos de 5; sin nombres, costes ni ubicaciones | `test_m18_…`, `tests/unit/test_portal_privacy.py` |
| Modo sin conexión | El service worker solo guarda la página `/campo` y los estáticos; **nunca** respuestas de la API. La cola local guarda borradores hasta enviarlos | e2e `campo-offline.spec.ts` |
| Secretos | `.env` ignorado por git; sin claves en el repositorio ni en su historial (comprobado 10/11 y 11/11) | revisión |
| Auditoría | Inicio de sesión, cambios de plan, evidencias, decisiones, expediente y autorizaciones quedan en `audit_events` | tests de M15 y M17 |

## 3. Dependencias

| Fecha | Herramienta | Resultado |
|---|---|---|
| 11/11/2026 | `pip-audit` | Sin vulnerabilidades conocidas |
| 11/11/2026 | `npm audit` (incluye desarrollo) | 8 avisos moderados en herramientas de lint (`minimatch` vía `eslint-config-next`); no se publican con la aplicación; su arreglo exige bajar de versión mayor. Aceptado |
| 11/11/2026 | `npm audit --omit=dev` | 1 crítica en `maplibre-gl` 5.6.0 (GHSA-jrc7-96c5-q579, saneado de HTML de popups). ESCUDO usaba `setText`, no `setHTML`, pero se actualizó a 6.16.0 (publicada hace más de dos semanas). Tras la actualización: 0 vulnerabilidades; 13/13 e2e |

## 4. Hallazgos corregidos

| Fecha | Hallazgo | Corrección |
|---|---|---|
| 09/11 | Ruta de fichero tomada de una URL remota (path traversal) | `safe_filename` + `inside` |
| 09/11 | Inyección de líneas en el `.ics` desde textos de usuario | escapado RFC 5545 completo |
| 10/11 | Re-identificación por diferencias en el portal público | umbral de 3 organizaciones, dominancia, redondeo |
| 11/11 | Secreto JWT de ejemplo publicado utilizable | secreto aleatorio si es débil o de ejemplo |
| 11/11 | Sin límite de intentos de login; tiempo distinto si el email no existe | límite 429 y bcrypt de relleno |
| 11/11 | Sin cabeceras de seguridad (CSP, marcos, sniffing) | cabeceras en web y API |
| 11/11 | Fotos con ubicación GPS en EXIF | recodificación sin metadatos |
| 11/11 | `maplibre-gl` vulnerable | actualizado a 6.16.0 |
| 11/11 | Revisión automática: bloqueo dirigido de cuentas, carrera en el límite de intentos, bomba de descompresión en imágenes | límite por (email, IP) con reserva atómica; tope de 40 MP antes de decodificar |

## 5. Riesgos que quedan (aceptados o pendientes)

- **CSP con `'unsafe-inline'` en scripts y estilos**: lo exige el arranque de Next.js sin *nonces*. Se mitiga con `default-src 'self'` y sin `eval`. Mejora posible: CSP con *nonce* por petición.
- **Token en `sessionStorage`**: un XSS podría leerlo; mitigado por la CSP y porque React escapa todo el texto. Alternativa futura: cookie `HttpOnly`.
- **Límite de intentos en memoria del proceso**: válido para una sola instancia (el despliegue previsto); con varias réplicas haría falta un almacén compartido (p. ej. Redis con `INCR` y caducidad).
- **Fuerza bruta distribuida**: un atacante con muchas IP puede probar 10 contraseñas por IP contra una cuenta. Es el precio de no permitir bloqueos dirigidos; mitigación futura: retardos progresivos o segundo factor.
- **Demo pública con cuentas de ejemplo conocidas**: cualquiera puede crear datos en las organizaciones ficticias. Son datos ficticios, el disco del Space es efímero y cada reinicio restaura la demo; los avisos piden no subir datos ni fotos reales.
- **Sin cifrado de las fotos en reposo** en el disco del servidor: aceptable para la demo (datos ficticios); en una implantación real, almacenamiento cifrado.
- **Sin validación de malware en PDF**: se valida la firma y el tamaño, no el contenido.

## 6. Datos personales (resumen RGPD)

Datos tratados: email, nombre y rol de los usuarios; nombre de la persona que inspecciona; textos y fotos que aporta la organización. Finalidad: planificación preventiva de la propia organización. Base: interés legítimo o relación con la organización usuaria. Minimización: sin datos de residentes, población solo agregada por municipio, fotos sin metadatos, portal público sin datos identificables. En la demo, todas las personas y organizaciones son ficticias. Antes de un uso real haría falta un registro de actividades de tratamiento, un encargo de tratamiento con quien aloje el servicio y un procedimiento de ejercicio de derechos.
