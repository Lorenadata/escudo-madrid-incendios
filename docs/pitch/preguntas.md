# Banco de preguntas

Respuestas cortas para decirlas con tus palabras. Primero la idea, luego el dato. Si no sabes algo, di «eso no lo hemos medido» antes que improvisar una cifra.

## Datos abiertos: portales, obtención y calidad

Es un datatón de datos abiertos: estas son las preguntas más probables. Fuentes de cada respuesta: `DATA_CATALOG.md`, `docs/spatial-method.md` y `PROVENANCE.md`.

### ¿Qué portales habéis usado?
Cinco de la administración y dos más:
- **Portal de Datos Abiertos de la Comunidad** (datos.comunidad.madrid): los 11 conjuntos.
- **IDEM**, la infraestructura de datos espaciales de la Comunidad: el mapa oficial de riesgo, peligrosidad y vulnerabilidad.
- **Portal de Transparencia de la Comunidad**: el Plan Anual 2026 en PDF.
- **BOCM**: el decreto INFOMA.
- **datos.gob.es**: para localizar las capas de IDEM.
- **AEMET** (la predicción municipal pública) y **EFFIS-Copernicus** (las áreas quemadas por satélite).

En total, 18 fuentes: 11 del Portal, el Plan Anual, el decreto, las 3 capas de IDEM, EFFIS y AEMET.

### ¿Cómo los habéis obtenido? ¿A mano?
No, todo por programa. Los 11 conjuntos se piden a la API del Portal (es un CKAN, con `package_show`), que da la dirección de cada fichero. Las capas de IDEM se localizaron con la API de datos.gob.es y se descargan de IDEM. Cada descarga guarda un `manifest.json` con la URL, la fecha, la licencia y una huella **SHA-256** del fichero. Un comando lo descarga todo de nuevo.

### ¿Para qué sirve la huella SHA-256?
Para demostrar que el dato es el oficial y saber si ha cambiado. Si el fichero cambia en el portal, la huella cambia. Pasó de verdad: el 08/11 cambió la huella de un conjunto (usos del suelo, CAM-07). El comando de actualización lo detectó y comprobó que eran **las mismas 760 filas en otro orden**. Se incorporó con historial y los valores no cambiaron.

### ¿Qué licencias tienen? ¿Podéis reutilizarlos?
- Portal: CC BY, que declara el propio portal.
- IDEM: CC BY 4.0. Ojo: el registro de datos.gob.es **no declara licencia**, así que la tomamos de los metadatos oficiales ISO 19139 de IDEM y los guardamos.
- AEMET: reutilización citando la fuente.
- EFFIS: CC BY 4.0.
- Nuestro código: EUPL-1.2.

Todas permiten reutilizar citando, y la web cita cada fuente.

### ¿Qué problemas de calidad habéis encontrado en los datos?
Muchos, y están documentados. Es de lo mejor que puedes contar:
- **Sin escala municipal.** Incendios (CAM-05) y usos del suelo (CAM-07) solo están como total regional. Por eso no hay «% forestal por municipio»: la web pone «no disponible».
- **Sin geometría.** Espacios protegidos (CAM-04) es una lista de 80 espacios sin mapa, así que no se puede cruzar con el territorio.
- **Secreto estadístico.** En viviendas unifamiliares (CAM-10) solo 151 de 179 municipios tienen dato; el resto viene con «-».
- **Dato provisional.** Consumo eléctrico (CAM-11) es provisional: 135 municipios con dato y un código 28999 sin municipio, que se descarta.
- **Códigos distintos.** El Portal usa códigos de 4 cifras y el INE de 5, así que hay una conversión con su prueba.
- **Erratas en el Plan Anual.** Nombres mal escritos: «Torredolones», «San María de la Alameda»… Se corrigen con una tabla explícita.
- **Totales que no cuadran.** En el propio Plan Anual, la suma de causas de los siniestros no coincide con el total en 95 municipios (2.912 frente a 2.641). Enseñamos los dos valores y lo advertimos; **no corregimos el dato oficial**.

### ¿Cómo comprobáis que los datos están bien procesados?
Con controles automáticos. Algunos ejemplos:
- En el Censo, total = principales + no principales en los 179 municipios.
- La extracción del Plan Anual cuadra con su fila de totales.
- La superficie del mapa de riesgo repartida por municipios cuadra con la total (±2 %).
- Hay una prueba que comprueba que el número que sale en pantalla es el del fichero descargado.

Los controles se guardan en la base de datos y en `quality.json`.

### ¿Cómo calculáis el «% del término en riesgo alto»?
El mapa oficial es un ráster con cuadros de 5 m de lado (25.970 × 28.409). Contamos los cuadros de cada clase dentro de cada municipio, a resolución completa y sin simplificar. Los límites municipales salen de las secciones censales del Portal (CAM-08). Las clases se copian literales de la leyenda oficial: si aparece un valor sin etiqueta, el proceso se para.

### ¿Habéis modificado el dato oficial?
No. El riesgo se usa tal como lo publica la Comunidad, sin recalcular ni renombrar clases. Lo que añadimos se marca como «derivado» (porcentajes, ranking) o «estimación» (riesgo de hoy). Cada indicador en pantalla dice si es oficial, derivado, escenario o no disponible.

### Mezcláis años distintos: altitud de 1998, censo de 2021, población de 2025…
Sí, porque es lo que publica cada fuente. Cada dato enseña su año en la ficha y nunca lo hacemos pasar por actual.

### La lista de Zonas de Alto Riesgo, ¿de qué portal sale?
No existe como conjunto en el Portal: solo está en el PDF del Plan Anual 2026 (Anexo II). La extrajimos con su número de página: 59 entradas, todas emparejadas con su código INE. El estado de los planes municipales (Anexo VI) lo leímos columna a columna, porque el texto del PDF pierde las casillas vacías.

### ¿Qué conjuntos mirasteis y descartasteis?
Auditamos más de los que usamos. Superficie forestal por propiedad, montes de utilidad pública por pertenencia y montes por comarca solo existen a escala regional o comarcal, y no aportaban escala municipal. Catastro no se usa porque tiene datos personales.

### ¿Qué le pediríais al Portal para mejorar?
Una respuesta constructiva queda muy bien:
1. **Publicar como conjunto** la lista de Zonas de Alto Riesgo y el estado de los planes municipales, en lugar de solo en PDF.
2. **Incendios por municipio**, no solo el total regional.
3. **Espacios protegidos con su geometría.**
4. **Códigos INE de 5 cifras y UTF-8** en todos los ficheros. Uno venía en latin-1.
5. **Declarar la licencia en datos.gob.es** para las capas de IDEM.

### ¿Cada cuánto se actualiza?
- **Datos oficiales:** cuando el organismo los cambia. Un comando comprueba las huellas y, si algo cambió, lo incorpora con historial. Tarda unos 2 minutos.
- **AEMET:** la predicción se guarda 3 horas. Si caduca o no responde, la web dice «no disponible» y la fecha del último dato válido.

### ¿Es reproducible?
Sí. El código es libre y está en GitHub. Un comando descarga todas las fuentes y comprueba sus huellas, y otro levanta la web. Dos descargas seguidas del mapa de riesgo dieron exactamente la misma huella.

### ¿Usáis datos personales?
No. Todo es municipal y agregado. Nunca atribuimos un dato municipal a una urbanización o a una vivienda. Los datos de la urbanización de la demo son ficticios y están marcados.

### ¿Devolvéis algo como dato abierto?
Sí:
- En `/fuentes` se puede descargar un CSV con los datos de los 179 municipios.
- En esa misma página está el catálogo de fuentes, con la fecha, la licencia y la huella SHA-256 de cada una.
- La API está documentada (OpenAPI).
- El código tiene licencia EUPL-1.2.

## El proyecto y el problema

### ¿Qué aporta si ya existe el mapa oficial de riesgo?
Usamos el mapa oficial tal cual. Lo que falta es el paso siguiente: decidir dónde mirar primero, inspeccionar, priorizar con un presupuesto, ejecutar y demostrar lo hecho. Eso es lo que aportamos.

### ¿Para quién es?
Para ayuntamientos, sobre todo los de riesgo alto; para gestores de urbanizaciones que deben tener un plan de autoprotección; y para técnicos forestales o de protección civil.

### ¿Qué es lo más nuevo del proyecto?
Unir en una sola herramienta el dato oficial, la decisión con presupuesto y la prueba de lo ejecutado, con cada cifra trazable. Y el cruce que nadie había publicado: 38 municipios con más de la mitad del término en riesgo alto, fuera de las Zonas de Alto Riesgo y sin obligación de plan municipal.

### ¿Qué competidores hay?
FIREPRIME es una autoevaluación de viviendas; SAVER y MINCE son plataformas internas de la Comunidad que cita el Plan Anual 2026. No afirmamos más de lo que dice el Plan.

## El hallazgo y el ranking

### El resumen dice que 38 municipios tienen más de la mitad del territorio en riesgo alto. ¿No son más?
Sí, son 95. De ellos, 57 son Zona de Alto Riesgo y 38 no, y ninguno de esos 38 está obligado a tener plan municipal. El resumen tenía 100 palabras y se quedó con los 38, que son el hallazgo. Mejor decirlo tú antes de que lo pregunten.

### ¿Entonces la Comunidad se ha equivocado con las Zonas de Alto Riesgo?
No lo decimos. Las Zonas de Alto Riesgo son el tercio de municipios con mayor valor en otro índice oficial (peligrosidad potencial e importancia de protección, Plan Anual pág. 15), y la lista es de 2017. Enseñamos una pregunta que merece revisión, no un error.

### ¿Las urbanizaciones solo necesitan plan si están en Zona de Alto Riesgo?
No. El plan de autoprotección depende de estar en terreno forestal o a menos de 400 m de él (Plan Anual pág. 51 y Anexo 5 del INFOMA). Lo que obliga ser Zona de Alto Riesgo es el plan **municipal**.

### ¿De dónde sale el 28 de 58?
Del Anexo VI del Plan Anual 2026: 58 municipios obligados, 28 con aprobación en pleno, 27 con «No» y 3 con la casilla vacía. Lo leímos columna a columna porque el texto del PDF pierde las casillas vacías, y comprobamos que la lista coincide con la del Anexo II. Un plan aprobado después puede no figurar.

### ¿Cómo se calcula la puntuación del ranking?
Cuatro bloques de 0 a 1: territorio en riesgo alto o muy alto (peso 40), historial de incendios y hectáreas quemadas por km² (20), contexto residencial (15) y falta de plan aprobado (25). No es riesgo de incendio ni una probabilidad: es un orden de revisión.

### ¿Los pesos no son arbitrarios?
Son una decisión, y por eso se ven, se pueden mover en pantalla y publicamos cuánto cambia el resultado: probamos 81 combinaciones de pesos y decimos en cuántas sigue cada municipio entre los 20 primeros. Robregordo sigue en todas.

### ¿Por qué Robregordo es el primero?
Porque lo dice su ficha: el 95 % del término en riesgo alto o muy alto, Zona de Alto Riesgo, obligado a plan municipal sin aprobación que conste, y el 80 % de sus viviendas no son vivienda habitual.

### ¿Dónde entran los datos del Portal de la Comunidad?
En todo lo que describe a la población y la vivienda: población y mayores de 65 (CAM-01), densidad (CAM-02), altitud (CAM-03), la geometría de los 179 municipios (CAM-08) y tres conjuntos del Censo 2021 de vivienda (CAM-09, 10 y 11). El bloque residencial del ranking usa CAM-01, CAM-09 y CAM-10. Hay una prueba automática que comprueba que el número en pantalla es el del fichero descargado.

## El riesgo estimado hoy

### ¿Cómo calculáis el «riesgo estimado hoy»? ¿Es oficial?
No es oficial, y la página lo dice. Es la parte del término en riesgo alto o muy alto del mapa oficial multiplicada por el índice de Fosberg, calculado con la temperatura, la humedad y el viento que prevé AEMET hora a hora. Las horas desde que empieza a llover no cuentan. No usamos pesos inventados.

### ¿Por qué Fosberg y no el FWI, que es el que usa AEMET?
El FWI canadiense acumula días: necesita observaciones diarias continuas y la lluvia caída en días anteriores, y AEMET además le añade vegetación y humedad del suelo. Nosotros solo tenemos la previsión de las próximas horas, y Fosberg es un índice publicado que funciona con eso. Por eso enseñamos el mapa oficial de AEMET al lado.

### ¿Lo habéis validado?
No con incendios reales de Madrid, y lo decimos. Es una estimación para orientar la mirada, no para tomar decisiones operativas.

### Hoy sale todo bajo. ¿Funciona?
Es noviembre y ha llovido: el mapa oficial de AEMET también marca peligro bajo o muy bajo. En un día de verano con calor, humedad baja y viento, el índice sube mucho.

## El optimizador y el caso guiado

### ¿Cómo decide el optimizador?
Es el problema de la mochila: con un presupuesto, elige la combinación de actuaciones que cubre más prioridad técnica, respetando que unas dependen de otras, que otras son incompatibles y que algunas son obligatorias. Lo resuelve OR-Tools CP-SAT, un programa libre, y siempre da el mismo resultado.

### ¿Quién pone las prioridades?
El técnico. El sistema no se inventa el valor de cada actuación: prioridad técnica de 1 a 5 por el peso de cobertura.

### ¿Cómo sabéis que acierta?
Lo comparamos con probar todas las combinaciones posibles en 200 casos aleatorios y coincide siempre.

### ¿El 90,1 % es un resultado real?
Es un caso de demostración con una urbanización ficticia. Muestra el método: con los mismos 30.000 €, optimizar cubre más prioridad que elegir a mano (84,2 %) o empezar por lo más barato (85,1 %). No es una medida de impacto real.

### ¿Reduce el riesgo de incendio?
No lo afirmamos. Medimos gestión: qué parte de las prioridades se cubre con el presupuesto, qué actuaciones están documentadas y si se cumplen los plazos. Decir «reduce el riesgo un X %» sería inventar.

## Impacto y validación

### ¿Lo ha probado alguien real?
Todavía no con técnicos ni gestores; es el siguiente paso y el protocolo está preparado. *(Si hablas con alguien antes del jueves, cuéntalo aquí con su permiso.)*

### ¿Qué ayuntamiento lo usaría el lunes?
Uno de los 38: tienen el término en riesgo alto y ninguna obligación que les empuje a planificar. ESCUDO les da por dónde empezar, qué hacer con su presupuesto y cómo documentarlo, sin coste de licencia.

### ¿Quién lo mantendría y cuánto costaría?
Un ayuntamiento, una mancomunidad o la propia Comunidad. El software es libre; el coste real sería el servidor, las copias de seguridad y el almacenamiento de fotos, que no hemos medido y no inventamos. Medido: actualizar los datos tarda unos 2 minutos y volver a publicar, de 2 a 4.

### ¿Y si cambian los datos oficiales?
Un comando vuelve a descargar todas las fuentes, compara las huellas y, si algo cambió, lo incorpora y deja historial. Se ve en `/fuentes`.

## Técnica y seguridad

### ¿Con qué está hecho?
Python para descargar y limpiar los datos, PostgreSQL con PostGIS como base de datos geográfica, FastAPI para la API y Next.js con React y MapLibre para la web. Todo libre.

### ¿Qué pasa si AEMET no responde?
Si el servicio con clave tarda más de 6 segundos, se usa la predicción pública de AEMET y no se vuelve a intentar en 5 minutos. Si tampoco hay predicción pública, pone «no disponible» con la fecha del último dato válido. Nunca enseña un dato viejo como actual.

### ¿Cómo protegéis los datos de las urbanizaciones?
Cada organización solo ve lo suyo, y una prueba automática intenta leer datos de otra y comprueba que falla. A las fotos se les borra el GPS. El portal público solo agrega cuando no se puede identificar a nadie. Contraseñas cifradas y bloqueo tras varios intentos fallidos.

### ¿Cómo sabéis que la extracción del PDF del Plan Anual está bien?
La suma de lo extraído coincide con la fila de totales del propio documento, cada dato guarda su página, y la lista de Zonas de Alto Riesgo de un anexo coincide con la del otro.

### ¿Por qué no usáis inteligencia artificial generativa en el buscador de normativa?
Porque en normativa no se puede inventar. El buscador devuelve el texto literal con su página; si no lo encuentra, lo dice. Acierta 18 de 20 preguntas fijadas antes de ajustarlo, y publicamos los 2 fallos.

### ¿Es accesible?
Cumple WCAG 2.1 AA, la norma que exige la administración, comprobado con la herramienta axe en las pantallas públicas, y funciona en un móvil de 390 px de ancho.

## Autoría y concurso

### ¿Habéis usado IA para desarrollarlo?
Sí, y está declarado en `PROVENANCE.md`; las bases lo permiten. Usé Claude Code como asistente de programación. Las decisiones, los criterios (cero cifras inventadas, separar lo oficial de lo estimado, no hacer una herramienta de emergencias) y la validación son míos. Dilo con naturalidad.

### ¿Qué hicisteis dentro del periodo del concurso?
Todo el historial está fechado en GitHub. `PROVENANCE.md` declara la preparación previa del 06/11.

### ¿Los datos de la demo son reales?
Los territoriales sí: municipios, riesgo, incendios, AEMET. La urbanización, las inspecciones y el presupuesto son ficticios y están marcados como tales.

## Frases que nunca hay que decir

- «Reduce el riesgo un X %», «evita incendios», «salva vidas», «ahorra X €».
- «Vivienda segura / insegura». Se dice «revisión preventiva prioritaria».
- «Aprueba el plan» o «certifica». Se dice que **prepara** el expediente.
- «La IA decide». El optimizador sigue reglas explícitas y las prioridades las pone un técnico.
- «Este municipio tiene hoy riesgo alto» sin más. Se dice «nuestra estimación de hoy, que no es oficial».
- «La Comunidad se ha equivocado». Se dice que el cruce plantea una pregunta que merece revisión.
