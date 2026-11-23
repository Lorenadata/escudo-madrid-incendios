# Recorrido por la web

Demo pública: **https://lorenadata-escudo-madrid.hf.space** · Repositorio: **https://github.com/Lorenadata/escudo-madrid-incendios**

Si nadie la ha abierto en 48 horas, tarda unos 40 segundos en despertar. Ábrela una vez al día hasta el 26/11.

## Las etiquetas que verás en toda la web

Cada dato lleva una etiqueta, y saber leerlas es la mitad de la defensa:

- **Oficial:** el valor tal como lo publica la fuente (Portal CAM, IDEM, Plan Anual, AEMET).
- **Derivado:** un cálculo nuestro, reproducible, sobre datos oficiales (por ejemplo, el % de mayores de 65).
- **Escenario:** un supuesto de demostración, como el presupuesto de 30.000 €.
- **Aportado:** lo que introduce una organización (inspecciones, fotos).
- **Caducado / No disponible:** el dato es viejo o no existe. Nunca se rellena con otro.

**«Ver método y fuentes»** aparece en todo lo importante: abre de dónde sale el número y cómo se calcula.

## Explorador (`/`)

La puerta de entrada: el mapa de los 179 municipios.

- **Buscar municipio** y **filtro de densidad** (mínima y máxima): los que cumplen el filtro llevan borde ocre.
- **Colorear municipios por:** densidad (CAM-02), población de 65 años o más (CAM-01) o altitud (CAM-03). Son datos del Portal.
- **Cartografía oficial de incendios:** riesgo, peligrosidad o vulnerabilidad (IDEM). Las clases se muestran con su nombre oficial, sin recalcular.
- **Histórico por satélite:** perímetros de áreas quemadas de EFFIS (servicio europeo).
- **Al pulsar un municipio se abre su ficha:** población, densidad, mayores de 65, altitud, vivienda del Censo 2021, reparto del término por clase de riesgo oficial, si es Zona de Alto Riesgo, incendios 2015–2024 por causa (Plan Anual), áreas quemadas por satélite y la predicción de AEMET con el mapa oficial de peligro.
- El aviso azul recuerda que los datos son **municipales**: no describen ninguna urbanización concreta.

## Ranking (`/ranking`)

Lo nuevo y lo más vistoso. De arriba abajo:

1. **«Dónde mirar primero»:** cada punto es un municipio, colocado según su puntuación. Al pasar por encima se ve cuál es.
2. **Riesgo estimado hoy:** territorio en riesgo alto del mapa oficial × índice meteorológico de Fosberg con la previsión hora a hora de AEMET. Los diez valores más altos, su mapa y «Por qué hoy». **Es una estimación nuestra, no oficial.**
3. **Lo que aparece al cruzar los datos:** el 38 (fuera de las Zonas de Alto Riesgo y sin obligación de plan municipal) y el 28 de 58 (obligados con plan aprobado). Cada cuadrado es un municipio y se puede pulsar.
4. **El ranking:** buscador, orden (atención, riesgo de hoy, riesgo oficial, siniestros, hectáreas quemadas, racha prevista) y filtros (los 179, Zonas de Alto Riesgo, los 38, obligados sin plan aprobado). La barra de colores de cada fila es el reparto de su puntuación en cuatro bloques.
5. **Panel derecho:** mapa, puntuación de 0 a 100, los cuatro bloques, **«Por qué está aquí»**, reparto oficial del riesgo, previsión de AEMET y en cuántas de 81 combinaciones de pesos sigue entre los 20 primeros.
6. **«Cambiar los pesos de la puntuación»:** mueves los pesos y el ranking se recalcula al momento. **«Ver método y fuentes»** explica la fórmula.

## Meteo (`/meteo`)

La predicción de AEMET para los 179 municipios.

- **Tres cifras:** la racha más fuerte, la lluvia máxima y la humedad más baja de las próximas 24 horas, con el municipio.
- **La región hoy:** mapa por rachas o por lluvia.
- **Las rachas, hora a hora:** cada fila es un municipio y cada casilla una hora; más claro, más viento.
- **Un municipio:** rachas y viento medio, lluvia, humedad y temperatura hora a hora, con la tabla de datos, rosa de los vientos y previsión a 7 días.
- **Mapa oficial de peligro de AEMET:** la imagen tal cual. No se saca ningún valor municipal de ella.

## Comparar (`/comparar`)

Dos o más municipios lado a lado, con el último año disponible de cada fuente.

## Análisis (`/analisis`)

Filtros sobre valores publicados, por ejemplo «más de la mitad del término en riesgo alto y menos de 20 hab/km²», y una matriz que cruza datos del Portal con la capa oficial. Abajo, el contexto regional (incendios, repoblaciones, usos del suelo), que solo existe como total de la Comunidad y así se muestra.

## Caso guiado (`/demo`)

La historia completa con una urbanización **ficticia**, en siete pasos (barra superior):

1. **Municipio real:** la ficha del municipio donde está.
2. **Ámbito ficticio:** la urbanización dibujada y las clases oficiales de riesgo dentro de ella.
3. **Inspección:** lo que anotó el técnico, con fotos.
4. **Medidas y presupuesto:** 11 actuaciones del catálogo ligado al INFOMA, cada una con coste y prioridad; presupuesto de 30.000 €.
5. **Comparación:** priorización manual (84,2 %), lo más barato primero (85,1 %) y optimizado (90,1 %), con sensibilidad al presupuesto y a una subida de costes del 20 %.
6. **Plan y evidencias:** responsables, plazos, historial y fotos de lo hecho.
7. **Informe:** PDF con fuentes, método, supuestos y «validación profesional pendiente».

## Normativa (`/normativa`)

Buscador del Decreto INFOMA y del Plan Anual. Devuelve el **fragmento literal con su página** y un enlace al documento. No usa IA generativa: si no lo encuentra, lo dice. Acierta 18 de 20 preguntas fijadas de antemano.

## Avance (`/avance`)

Cuánto se ha avanzado en cada municipio, sin poder deducir los datos de ninguna urbanización: solo se publica con al menos 3 ámbitos de 3 organizaciones distintas y ninguna por encima del 50 %.

## Fuentes (`/fuentes`)

Las 18 fuentes con URL, licencia, fecha y huella SHA-256; el registro de comprobaciones de actualización; cómo leer las etiquetas; y la descarga en CSV de los indicadores municipales.

## Área de trabajo (`/app`) y Campo (`/campo`)

Requieren entrar con una cuenta ficticia (contraseña `demo-escudo-2026`): `gestor@demo.escudo.local`, `municipal@demo.escudo.local` o `tecnico@demo.escudo.local`.

- **Área de trabajo:** los ámbitos de la organización; se puede dibujar uno en el mapa y ver sus clases oficiales. Secciones: Contexto, Inspecciones, Escenarios y plan, Expediente (15 puntos del INFOMA con cita literal), Comentarios y decisiones, Informe.
- **Campo:** inspección desde el móvil **sin cobertura**. Guarda en el teléfono y envía sola al volver la conexión; borra el GPS de las fotos; se instala como aplicación.
