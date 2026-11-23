# Banco de preguntas

Respuestas cortas para decirlas con tus palabras. Primero la idea, luego el dato. Si no sabes algo, di «eso no lo hemos medido» antes que improvisar una cifra.

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
