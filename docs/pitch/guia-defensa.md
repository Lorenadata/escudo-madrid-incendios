# Guía de defensa de ESCUDO MADRID

Para estudiar antes del 26/11. Está escrita para explicarla con tus palabras, no para recitarla. Las cifras salen del repositorio; si algo cambia, se actualiza aquí.

---

## 1. El proyecto en un minuto

**El problema.** En la Comunidad de Madrid hay muchas urbanizaciones pegadas al monte (la «interfaz urbano-forestal»). El Decreto INFOMA les obliga a tener un **plan de autoprotección** y a hacer trabajos preventivos: desbrozar, podar, mantener franjas sin vegetación, hidrantes, etc. Hoy eso se gestiona con hojas de cálculo, papel y PDF sueltos. El mapa oficial de riesgo existe, pero entre «el mapa dice riesgo alto» y «hemos hecho estos trabajos, con este dinero y aquí están las fotos» no hay ninguna herramienta.

**Lo que hace ESCUDO MADRID.** Es una web abierta que cubre ese hueco en cuatro pasos:

1. **Ver:** fichas de cada municipio con datos oficiales (población, mayores de 65, viviendas, riesgo oficial, incendios históricos, áreas quemadas por satélite y meteorología de AEMET). Cada dato lleva su fuente y su fecha. Además, un **ranking** de los 179 municipios que explica por qué cada uno merece atención, y un **riesgo estimado para hoy** que cruza el mapa oficial con el tiempo previsto por AEMET.
2. **Inspeccionar:** el técnico o el gestor recorre la urbanización con el móvil y anota lo que ve, con fotos, **aunque no haya cobertura**.
3. **Decidir:** con un presupuesto dado, el optimizador propone qué actuaciones hacer primero y lo compara con dos maneras sencillas de elegir.
4. **Ejecutar y comprobar:** se crea el plan con responsables, plazos y evidencias; se prepara el expediente INFOMA con las citas literales del decreto y se genera un informe PDF.

**Lema:** «Del mapa al plan; del plan a la ejecución comprobable».

**Para quién:** ayuntamientos con zonas de alto riesgo, gestores de urbanizaciones y técnicos forestales o de protección civil.

**Lo que NO es:** no es una herramienta de emergencias. No da alertas, ni rutas de evacuación, ni tácticas de extinción, ni aprueba planes. No sustituye a técnicos, a ASEM 112, a AEMET ni al INFOMA.

---

## 2. La web: qué hay en cada pantalla

Demo pública: **https://lorenadata-escudo-madrid.hf.space**. Si lleva 48 h sin visitas, tarda unos 40 s en despertar.

| Pantalla | Qué enseña | Cuenta necesaria |
|---|---|---|
| `/` (inicio) | Mapa de la Comunidad con las capas oficiales de riesgo, peligrosidad y vulnerabilidad, y las áreas quemadas de EFFIS. Al pulsar un municipio se abre su ficha. | No |
| Ficha municipal | Población, densidad, altitud, viviendas (Censo 2021), clases de riesgo oficial, si es Zona de Alto Riesgo, incendios 2015–2024 del Plan Anual, áreas quemadas por satélite y predicción AEMET. Cada bloque tiene «Ver método y fuentes». | No |
| `/analisis` | Filtros sobre valores publicados, por ejemplo municipios con mucha superficie en riesgo alto y poca densidad. | No |
| `/ranking` | **Riesgo estimado hoy** (mapa oficial × tiempo previsto), el cruce con las Zonas de Alto Riesgo y los planes municipales (38 y 28 de 58), y el ranking de los 179 municipios con el porqué de cada puesto y pesos ajustables. | No |
| `/meteo` | Rachas, viento, lluvia, humedad y temperatura hora a hora de AEMET para los 179 municipios, previsión a 7 días y el mapa oficial de peligro de AEMET. | No |
| `/comparar` | Dos o más municipios lado a lado. | No |
| `/demo` | **Caso guiado** con una urbanización ficticia: inspección, 11 actuaciones, presupuesto de 30.000 € y resultado del optimizador. Es lo que se enseña en la defensa. | No |
| `/normativa` | Buscador del Decreto INFOMA y del Plan Anual: devuelve el fragmento literal con la página. | No |
| `/avance` | Portal público del avance por municipio, sin revelar datos de ninguna urbanización concreta. | No |
| `/fuentes` | Las 18 fuentes con URL, licencia, fecha y huella SHA-256, el registro de comprobaciones y la descarga en CSV de los indicadores municipales. | No |
| `/app` | Zona privada: ámbitos, inspecciones, escenarios, plan, calendario, expediente INFOMA, comentarios y decisiones, informe PDF. | Sí |
| `/campo` | Inspección desde el móvil sin conexión; se instala como aplicación. | Sí |

Cuentas ficticias (contraseña `demo-escudo-2026`): `gestor@demo.escudo.local` (urbanización), `municipal@demo.escudo.local` (ayuntamiento), `tecnico@demo.escudo.local` (técnico).

---

## 3. Cómo está hecho, de principio a fin

Imagínalo como una cadena de cinco eslabones:

```
Fuentes oficiales → Programas de descarga y limpieza → Base de datos → API → Web
(CAM, IDEM, AEMET,   (pipelines, en Python)            (PostgreSQL     (FastAPI,  (Next.js,
 Plan Anual, BOCM,                                       + PostGIS)      Python)    React, mapa
 EFFIS)                                                                             MapLibre)
```

### 3.1 Los datos (eslabón 1 y 2)

- **Portal de Datos Abiertos de la Comunidad de Madrid:** 11 conjuntos (población, densidad, altitud, secciones censales, incendios, repoblaciones, usos del suelo, espacios protegidos y tres del Censo 2021 sobre vivienda). Es **requisito de las bases** usar al menos uno.
- **IDEM (cartografía oficial de la Comunidad):** tres mapas de riesgo, peligrosidad y vulnerabilidad por incendios, en píxeles de 5 metros.
- **Plan Anual 2026 (PDF oficial):** de él extraemos qué municipios son **Zona de Alto Riesgo** (Anexo II) y los incendios por municipio 2015–2024 (Anexo I). Comprobamos que la suma de lo extraído coincide con la fila de totales del propio documento.
- **Decreto 59/2017 INFOMA (BOCM):** la norma que dice qué debe tener un plan de autoprotección. Lo usamos para el expediente y el buscador.
- **EFFIS (servicio europeo):** perímetros de áreas quemadas detectadas por satélite.
- **AEMET:** predicción municipal diaria y **horaria** (XML público, sin clave) y mapa oficial de peligro de incendio (OpenData, con clave).

**Cómo se descargan.** Un programa en Python descarga cada fuente y guarda una ficha (`manifest.json`) con la URL, la fecha, la licencia y la **huella SHA-256**. La huella es como la huella dactilar del fichero: si cambia un solo byte, la huella cambia. Así podemos demostrar que el dato que enseñamos es exactamente el oficial, y detectar cuándo la fuente se actualiza (`escudo_pipelines.refresh`).

**Cómo se reparte el riesgo por municipio.** Los mapas del IDEM son imágenes de 5 m por píxel. Para cada municipio contamos cuántos píxeles caen en cada clase («Riesgo alto», «Riesgo muy alto»…). Las clases se muestran **con el nombre literal** de la leyenda oficial; nunca las recalculamos ni las renombramos.

**Regla de oro: cero cifras inventadas.** Todo número viene de un fichero oficial o de un cálculo reproducible sobre él. Si no hay dato, se muestra «no disponible». Cada dato lleva una etiqueta: **oficial**, **derivado**, **escenario**, **aportado por usuario**, **no disponible** o **desactualizado**.

**Escalas separadas.** Un dato municipal (por ejemplo, la población) nunca se reparte ni se atribuye a una urbanización. Sería inventar.

### 3.2 La base de datos (eslabón 3)

**PostgreSQL con PostGIS**, la base de datos libre más usada para información geográfica. Guarda municipios, capas, fuentes y la parte privada de cada organización: ámbitos, inspecciones, fotos, escenarios, planes y comentarios.

**Multi-organización:** cada urbanización o ayuntamiento solo ve lo suyo. Toda consulta privada filtra por la organización de quien pregunta, y hay una prueba automática (T08) que intenta leer datos de otra organización y comprueba que falla.

### 3.3 La API (eslabón 4)

Es el «camarero» entre la base de datos y la web: la web pide algo («dame la ficha de Torrelodones») y la API lo busca, comprueba permisos y responde en JSON. Está hecha con **FastAPI** (Python) y se documenta sola en `/docs`.

### 3.4 La web (eslabón 5)

**Next.js y React**, con el mapa en **MapLibre** (libre) y el mapa base del IGN. Es accesible: cumple **WCAG 2.1 AA** (la norma de accesibilidad web que exige la administración), comprobado con la herramienta axe con 0 errores, y funciona en un móvil de 390 px de ancho.

### 3.5 Las piezas que destacan

**El optimizador (lo más técnico).**
- Es un problema clásico llamado «problema de la mochila»: tengo un presupuesto (la mochila) y actuaciones con un coste y un valor; ¿qué combinación da más valor sin pasarse?
- El **valor** de cada actuación es **prioridad técnica (1 a 5) × peso de cobertura**, y lo pone el técnico; el sistema no se lo inventa.
- Respeta reglas reales: «esta actuación requiere hacer antes aquella», «estas dos son incompatibles», «esta es obligatoria».
- Lo resuelve **OR-Tools CP-SAT**, un solver libre de Google, configurado para dar siempre el mismo resultado (determinista).
- Lo comparamos con dos formas sencillas de elegir: el orden manual del técnico y «las más baratas primero». En el caso guiado: **90,1 %** de la prioridad cubierta frente a **84,2 %** (manual) y **85,1 %** (más baratas), con los mismos 30.000 €.
- Lo hemos verificado contra la fuerza bruta (probar todas las combinaciones) en **200 casos aleatorios** y coincide siempre.
- **Análisis de sensibilidad:** qué pasa si el presupuesto sube o baja, o si los costes suben un 20 %.
- **Lo que no dice:** cuánto baja el riesgo. Maximiza una prioridad acordada, no el riesgo.

**El expediente INFOMA.** Una lista de **15 puntos** que pide el decreto, cada uno con la **cita literal** del BOCM (comprobada palabra por palabra contra el texto oficial) y enlazado a las actuaciones del plan. La herramienta nunca lo «aprueba»; lo prepara para que lo revise quien corresponda.

**El buscador de normativa.** Busca por palabras (algoritmo **BM25**, el mismo tipo que usan los buscadores clásicos) y devuelve el fragmento literal con su página. **No usa IA generativa**, así que no puede inventarse un artículo. Lo evaluamos con 20 preguntas fijadas **antes** de ajustarlo: acierta **18 de 20** (la cita correcta sale entre los 3 primeros resultados), y los 2 fallos están publicados.

**Inspección sin cobertura (`/campo`).** En el monte no suele haber señal. La página se instala en el móvil, guarda las inspecciones y las fotos en el propio teléfono y las envía solas cuando vuelve la conexión. Cada inspección lleva un identificador único, así que si se envía dos veces no se duplica. A las fotos se les **borra la ubicación GPS y los metadatos** antes de guardarlas.

**Portal público de avance (`/avance`).** Enseña cuánto se ha avanzado en cada municipio sin permitir deducir los datos de ninguna urbanización concreta. Solo se muestra si hay al menos 3 ámbitos de 3 organizaciones distintas y ninguna supera el 50 %, y los valores se redondean.

**El cruce que da el titular.** Cruzamos el mapa oficial de riesgo con dos anexos del Plan Anual 2026: la lista de Zonas de Alto Riesgo (Anexo II) y la tabla de planes municipales (Anexo VI, leída columna a columna porque el texto del PDF pierde las casillas vacías). Resultado: **95** municipios tienen más de la mitad del término en riesgo alto o muy alto; **57** son Zona de Alto Riesgo y **38 no**, y **ninguno de esos 38** está obligado a tener plan municipal (en ellos viven 222.139 personas, padrón 2025). De los **58** municipios obligados, **28** figuran con plan aprobado en pleno, 27 con «No» y 3 con la casilla vacía.

**Ranking de atención preventiva (`/ranking`).** Ordena los 179 municipios de 0 a 100 con cuatro bloques: territorio en riesgo oficial alto (peso 40), historial de incendios (20), contexto residencial (15) y falta de plan aprobado (25). Cada municipio enseña sus motivos. Los pesos son una decisión nuestra: se ven, se pueden mover en pantalla y publicamos su **estabilidad** (en cuántas de 81 combinaciones de pesos sigue entre los 20 primeros). No usa meteorología.

**Riesgo estimado hoy (`/ranking`).** Parte del término en riesgo alto o muy alto (mapa oficial) **×** índice de Fosberg, un índice meteorológico de incendios publicado en 1978 que combina temperatura, humedad y viento. Lo calculamos con la predicción hora a hora de AEMET para las próximas 24 horas. Las horas desde que empieza a llover (0,5 mm) no cuentan, porque el índice no tiene en cuenta la lluvia. Es una **estimación nuestra, no un dato oficial**, y no está validada con incendios reales de Madrid (decisión en ADR-0005).

**Calendario.** Las tareas del plan se exportan a Google Calendar o a Outlook (fichero `.ics`).

### 3.6 Seguridad y privacidad (en una frase cada una)

- Contraseñas cifradas con bcrypt; nunca se guardan en claro.
- Bloqueo tras demasiados intentos de acceso, para evitar que alguien pruebe contraseñas a lo bruto.
- Cabeceras de seguridad que impiden incrustar la web en páginas ajenas o cargar código de terceros.
- Las fotos pierden su GPS; las claves (AEMET) nunca están en el código, solo como secreto del servidor.
- Se ha pasado una revisión de seguridad automática y se corrigieron todos los hallazgos.

### 3.7 Pruebas y calidad

- **196 pruebas automáticas:** 159 de datos, API y optimizador, y 37 de navegador, que hacen clic como una persona, incluidas accesibilidad y modo sin conexión.
- Cada vez que se sube código, GitHub ejecuta las pruebas solo («integración continua»).
- Instalación desde cero comprobada: unos 9 minutos siguiendo el README.

### 3.8 Despliegue y coste

- La web está en **Hugging Face Spaces**: un único contenedor con la base de datos, la API y la web, construido desde el repositorio público en una versión fija. Lo que ve el jurado es exactamente el código abierto.
- Coste: **6,50 €** de la suscripción PRO de Hugging Face. Todo lo demás es software libre y datos abiertos.
- Licencia del código: **EUPL-1.2**, la licencia de software libre de la Unión Europea, pensada para administraciones.

---

## 4. Preguntas que pueden hacerte

**¿Qué aporta si ya existe el mapa oficial de riesgo?**
Usamos el mapa oficial tal cual. Lo que falta es el paso siguiente: inspeccionar, decidir con un presupuesto, ejecutar y demostrar lo hecho. Eso es lo que aportamos.

**¿Dónde usáis los datos del Portal de la Comunidad de Madrid?**
Once conjuntos en la ficha municipal, el análisis y el comparador. Hay una prueba automática que comprueba que el número en pantalla es exactamente el del fichero descargado. En `/fuentes` se ve cada uno con su huella.

**¿Reduce el riesgo de incendio?**
No lo afirmamos. Medimos gestión: qué parte de las prioridades se cubre con el presupuesto, qué actuaciones están documentadas y si se cumplen los plazos. Decir «reduce el riesgo un X %» sería inventar.

**¿Cómo decide el optimizador?**
Es el problema de la mochila: maximiza la prioridad técnica cubierta sin pasarse del presupuesto y respetando qué actuaciones dependen de otras o son incompatibles. Las prioridades las pone el técnico. Lo comprobamos contra la fuerza bruta en 200 casos.

**¿Por qué no usáis inteligencia artificial generativa (tipo ChatGPT) en el buscador?**
Porque en normativa no se puede inventar. El buscador devuelve el texto literal con la página; si no lo encuentra, lo dice. Acierta 18 de 20 y publicamos los 2 fallos.

**¿Habéis usado IA para desarrollarlo?**
Sí, y está declarado en `PROVENANCE.md`: las bases lo permiten. Usé Claude Code como asistente de programación siguiendo un documento de especialidades que redacté yo. Las decisiones, los criterios (cero cifras inventadas, separar oficial de escenario, no hacer herramienta de emergencias) y la validación son míos. *(Responde con sinceridad; es mejor decirlo con naturalidad que dar la sensación de esconderlo.)*

**¿Lo ha probado alguien real?**
Todavía no con técnicos ni gestores; es el siguiente paso y el protocolo está listo y cerrado de antemano. *(Si haces el ensayo interno: «Lo probaron 2 personas ajenas al proyecto en un ensayo interno; con 2 personas no sacamos conclusiones, solo detectamos problemas de uso».)*

**¿Qué pasa si AEMET no responde?**
Si el servicio con clave tarda más de 6 segundos, se usa la predicción pública de AEMET y no se vuelve a probar en 5 minutos. Si tampoco hay predicción pública, se muestra «no disponible» con la fecha del último dato válido. Nunca se enseña un dato viejo como si fuera actual. El resto sigue funcionando.

**El resumen dice que 38 municipios tienen más de la mitad del territorio en riesgo alto. ¿No son más?**
Sí: son 95. De ellos, 57 son Zona de Alto Riesgo y 38 no, y ninguno de esos 38 está obligado a tener plan municipal. El resumen tenía 100 palabras y se quedó con los 38, que son el hallazgo. *(Dilo tú antes de que lo pregunten si sale el tema: da credibilidad.)*

**¿Entonces la Comunidad se ha equivocado con las Zonas de Alto Riesgo?**
No lo decimos. Las Zonas de Alto Riesgo son el tercio de municipios con mayor valor en otro índice oficial (peligrosidad potencial e importancia de protección, Plan Anual pág. 15), y la lista es de 2017. Lo que enseñamos es una pregunta que merece revisión, no un error.

**¿Las urbanizaciones solo tienen que tener plan si están en Zona de Alto Riesgo?**
No. El plan de autoprotección depende de estar en terreno forestal o a menos de 400 m de él (Plan Anual pág. 51 y Anexo 5 del INFOMA), no de ser Zona de Alto Riesgo. La obligación de las Zonas de Alto Riesgo es el plan **municipal**.

**¿Cómo calculáis el «riesgo estimado hoy»? ¿Es oficial?**
No es oficial y la página lo dice. Es la parte del término en riesgo alto o muy alto del mapa oficial multiplicada por el índice de Fosberg, calculado con temperatura, humedad y viento previstos por AEMET; las horas con lluvia no cuentan. No usamos pesos inventados. Límites: no conoce el estado de la vegetación ni la lluvia ya caída, y no está validado con incendios de Madrid.

**Hoy sale todo bajo. ¿Funciona?**
Es noviembre y llueve: el mapa oficial de peligro de AEMET, que se ve en `/meteo`, también marca peligro bajo o muy bajo en Madrid. En un día de verano con 38 °C, 15 % de humedad y viento fuerte, el índice sube mucho.

**¿Por qué Robregordo es el primero del ranking?**
Pulsa en él y lo dice: el 95 % del término está en riesgo alto o muy alto, es Zona de Alto Riesgo y está obligado a plan municipal sin aprobación que conste, y el 80 % de sus viviendas no son principales. Cada puesto se explica así.

**¿Los pesos del ranking no son arbitrarios?**
Son una decisión, y por eso se ven, se pueden cambiar en pantalla y publicamos cuánto cambia el resultado al moverlos. Robregordo sigue entre los 20 primeros en todas las combinaciones probadas.

**¿Y si cambian los datos oficiales?**
Un comando vuelve a descargar todas las fuentes, compara las huellas y, si algo cambió, lo incorpora y guarda el historial. Se ve en `/fuentes`.

**¿Quién lo mantendría y cuánto costaría?**
Un ayuntamiento, una mancomunidad o la propia Comunidad. El software es libre; el coste real sería el servidor, las copias de seguridad y el almacenamiento de fotos, que no hemos medido y no inventamos. Lo medido: actualizar datos tarda unos 2 minutos y redesplegar de 2 a 4.

**¿Y la privacidad de las urbanizaciones?**
Cada organización solo ve lo suyo, y hay una prueba automática que lo comprueba. A las fotos se les borra el GPS. El portal público solo agrega cuando hay suficientes participantes para que no se pueda identificar a nadie.

**¿Cómo sabéis que la extracción del PDF del Plan Anual está bien?**
La suma de lo que extraemos coincide con la fila de totales del propio documento, y cada dato guarda su página.

**¿Los datos de la demo son reales?**
Los datos territoriales sí (municipios, riesgo, incendios, AEMET). La urbanización, las inspecciones y el presupuesto son **ficticios** y están etiquetados como tales.

**¿Qué competidores hay?**
FIREPRIME, que es una autoevaluación de viviendas, y SAVER y MINCE, plataformas internas de la Comunidad citadas en el Plan 2026. No afirmamos más de lo que dice el Plan (`COMPETITORS.md`).

**¿Qué hicisteis dentro del periodo del concurso?**
Todo el historial de cambios está fechado en GitHub. `PROVENANCE.md` declara la preparación previa del 06/11.

---

## 5. Frases que nunca hay que decir

- «Reduce el riesgo un X %», «evita incendios», «salva vidas», «ahorra X €».
- «Vivienda segura / insegura». Se dice «revisión preventiva prioritaria».
- «Aprueba el plan de autoprotección» o «certifica». Se dice que **prepara** el expediente.
- «La IA decide». El optimizador sigue reglas explícitas y las prioridades las pone un técnico.
- «Este municipio tiene hoy riesgo alto» sin más. Se dice «nuestra estimación de hoy» y se recuerda que no es oficial.
- «La Comunidad se ha equivocado con las Zonas de Alto Riesgo». Se dice que el cruce plantea una pregunta que merece revisión.

---

## 6. Vocabulario rápido

| Término | En una frase |
|---|---|
| Interfaz urbano-forestal | Zona donde las casas se juntan con el monte. |
| INFOMA | Plan de la Comunidad de Madrid contra incendios forestales (Decreto 59/2017). |
| Plan de autoprotección | Documento que el INFOMA exige a urbanizaciones, campings o núcleos en terreno forestal o a menos de 400 m de él. |
| ZAR | Zona de Alto Riesgo: 59 municipios, el tercio con mayor valor en un índice oficial de peligrosidad e importancia de protección. Obliga a tener plan **municipal**. |
| Índice de Fosberg | Índice meteorológico de incendios (1978) que combina temperatura, humedad y viento; de 0 a 100. |
| Puntuación de atención | Nuestro orden de revisión de los 179 municipios; no es riesgo de incendio. |
| Riesgo / peligrosidad / vulnerabilidad | Peligrosidad: probabilidad de que el fuego se produzca y se propague. Vulnerabilidad: lo que se puede perder. Riesgo: la combinación de ambas, que publica la Comunidad. |
| SHA-256 | Huella digital de un fichero; demuestra que no ha cambiado. |
| API | Intermediario entre la base de datos y la web. |
| PostGIS | Base de datos con funciones geográficas. |
| Optimizador CP-SAT | Programa que busca la mejor combinación cumpliendo restricciones. |
| BM25 | Método clásico de búsqueda por palabras; no inventa texto. |
| PWA | Web que se instala en el móvil y funciona sin conexión. |
| WCAG 2.1 AA | Norma de accesibilidad web. |
| EUPL | Licencia de software libre de la Unión Europea. |
| Integración continua | Las pruebas se ejecutan solas cada vez que se cambia el código. |

---

## 7. Plan de estudio sugerido

| Día | Qué hacer |
|---|---|
| 1 | Leer las secciones 1 y 2 y recorrer la web pantalla por pantalla con esta guía al lado. |
| 2 | Sección 3. Explicar en voz alta la cadena de cinco eslabones sin mirar. |
| 3 | Hacer el caso guiado `/demo` tres veces y contar en voz alta qué hace el optimizador. |
| 4 | Sección 4: que alguien te haga las preguntas en orden aleatorio. |
| 22–25/11 | Ensayos completos con cronómetro: 5 min de exposición siguiendo `docs/demo-script.md` y 5 min de preguntas. |
