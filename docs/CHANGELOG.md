# Changelog

Historial de cambios significativos del proyecto. Basado en [Keep a Changelog](https://keepachangelog.com/).

## 2026-10-02 — El asistente sabe qué columna agrupa y qué pregunta se mide

- **Qué pidió el usuario.** Que el asistente deje de adivinar por el nombre de la columna: el índice debe anunciar
  los dos papeles (las columnas por las que se agrupa y las preguntas que se miden, con su escala) y el contexto
  debe dejar de enumerar pregunta por pregunta lo que el dato ya dice.
- **`construirMenu()`** (`zoho-survey/shared/js/portal/portal-preguntas.js`) arma el menú con el bloque `preguntas`
  que publica cada `respuestas.json` (Fase 1): las columnas de tipo `agrupacion` van en su grupo y las de tipo
  `medida` en el grupo de su escala (CSAT, NPS). Un JSON sin el bloque se sigue anunciando como siempre (lista plana).
- **`asistente_contexto.json`**: se retiró la sección *Cómo se preguntó cada cosa* (la enumeración larga por
  secciones del formulario). Queda `cierre_de_la_encuesta`, sólo con lo que el dato no puede decir: que las dos
  últimas medidas de satisfacción son los **dos ítems de una sola** pregunta global («De manera global, ¿cuál es
  tu nivel de satisfacción con…?»), cuyo sujeto cambia por público, y la nota de cómo leerlo (la carrera, la
  universidad, recomendación). El portal actualiza la lista de secciones que arma `textoDeContexto()`.
- **Pruebas:** asistente 1.9 en jsdom **24** (dos pruebas nuevas: el menú distingue los dos papeles y se arma con el
  bloque `preguntas` en vez de nombres fijos; y el contexto del cierre).
- **Marcador del asistente** (`portal-preguntas.js?v=`) sube a `2026093403` para que el sitio publicado sirva el JS nuevo.

## 2026-10-01 — El contexto trae el texto real de las preguntas (de los cuestionarios) y su sección

- **Qué pidió el usuario.** Que las cabeceras con peculiaridades lleven su contexto correcto (La carrera, La
  Universidad de Lima, el NPS, las fechas, el ID) y que a las preguntas que sí están en el cuestionario se les
  agregue su dimensión. Mandó los dos PDF.
- **Qué se reescribió en `asistente_contexto.json`** (sección *Cómo se preguntó cada cosa*): ahora, por sección
  del formulario (DATOS PERSONALES, SERVICIOS ACADÉMICOS, SERVICIOS AL ESTUDIANTE, RECURSOS E INFRAESTRUCTURA,
  TECNOLOGÍAS DE INFORMACIÓN, PLANA DOCENTE, DESARROLLO PROFESIONAL, SATISFACCIÓN GLOBAL), va el texto real de
  cada pregunta que **no** coincide con el nombre publicado, con su columna. Lo verificado de los cuestionarios:
  - **La carrera** y **La Universidad de Lima** son los dos ítems de **una sola** pregunta: *«De manera global,
    ¿cuál es tu nivel de satisfacción con…?»*. Está escrito con esa frase, tomada del PDF.
  - **Recomiendas la Universidad de Lima** es la pregunta del 0 al 10: *«En una escala del 0 al 10, … ¿Qué tan
    probable es que recomiendes la Universidad de Lima a un familiar o amigo…?»*.
  - Graduados pregunta *«¿Qué carrera profesional estudiaste?»*, *«¿Cuál es tu situación laboral actual?»* y
    *«¿Cuál es el tiempo dedicado a tu trabajo?»*.
  - Se agregó cómo leerlo: "la carrera" = satisfacción global con tu carrera; "la universidad" = con la
    Universidad de Lima; "recomendarías" = la pregunta del 0 al 10.
- **Las dimensiones** ahora dicen que cada una corresponde a una sección del formulario.
- **El contexto creció** a 18 612 bytes, así que el tope pasó de 16 000 a 24 000 caracteres en los dos lados.
- **Pendiente:** la encuesta de estudiantes adjunta es la de **2026-2**, un período que todavía no está
  publicado (hoy hay 2025-2 y 2026-1); cuando se publique habrá que revisar que el texto de las preguntas siga
  coincidiendo.

## 2026-10-01 — El contexto explica cómo se preguntó cada cosa, qué columnas no son preguntas y las dimensiones

- **Qué pidió el usuario.** Que "La carrera" y "La Universidad de Lima" (que son ítems, no preguntas) lleven su
  contexto correcto; que las columnas que no son preguntas (ID, Inicio, Fin) queden explicadas; y que a cada
  pregunta se le agregue **su dimensión**, para mejorar el contexto.
- **Qué se agregó a `asistente_contexto.json`** (tres secciones nuevas):
  - *Cómo se preguntó cada cosa*: el texto real de las cabeceras peculiares, tomado de la tabla de renombrado
    del ETL («¿Qué carrera profesional estudias?», «Net Promoter Score (de un total de 10)», «¿Cuál es tu
    situación laboral actual?», …). Incluye la explicación de que **La carrera** y **La Universidad de Lima**
    son los dos ítems de una misma pregunta del formulario sobre satisfacción global: el texto completo de esa
    pregunta **no está en los datos**, porque la encuesta la parte en ítems (queda pendiente si se quiere el
    texto exacto del PDF).
  - *Columnas que no son preguntas*: ID, Inicio, Fin y el uso de Carrera, Ciclo y Facultad para agrupar.
  - *Dimensiones*: las cuatro de Pregrado (Académico 11, Administrativo y Bienestar 10, Infraestructura 7,
    Tecnología 5) y las seis de Graduados (las mismas más Docencia 8 y Desarrollo Profesional 4), con las
    preguntas de cada una. Sale del mapa del ETL (`CATEGORIA_DIMENSION_*`), no se escribe a mano.
- **El contexto creció:** 7 378 → 13 052 bytes, así que el tope subió de 8 000 a 16 000 caracteres en los dos
  lados (portal y función).
- **Pruebas:** asistente 1.9 en jsdom 20 → **20** (cinco comprobaciones nuevas dentro de la prueba del contexto).

## 2026-10-01 — El contexto del asistente deja de tener equivalencias y corrige sus reglas viejas

- **Qué se corrigió (dos reglas que viajaban en cada pregunta y ya eran falsas).** Decían "las cifras las
  calcula la página, nunca el modelo" y "cada respuesta cita el archivo del que salió". Hoy el modelo **sí**
  calcula (sumar, restar, multiplicar, dividir y contar) y la cita es **la encuesta**, no el archivo. Se
  reescribieron las dos, y se agregó que lo que no está en los datos (la hora, la fecha, el clima) no se
  responde.
- **Qué se retiró.** La llave `equivalencias`: eran tres entradas que le decían a la IA, pregunta por
  pregunta, cómo interpretar ("cuando habla de *trabajan*…"). Decisión del usuario: la IA lo debe deducir,
  no se le dan instrucciones por pregunta; solo restricciones. Se conservó lo útil como dos reglas nuevas:
  interpretar sinónimos del habla común sin que se los enumeren, y copiar los valores del índice tal cual
  (sin inventar categorías).
- **Qué se arregla de paso.** El aviso "Tratamiento especial equivalencias" que apareció una vez en las
  respuestas era el modelo nombrando la sección `Equivalencias`: al retirarse la llave, desaparece el motivo.
- **Pruebas:** la del contexto sigue verde (comprueba las secciones y las palabras coloquiales).

## 2026-09-30 — La IA calcula (sumar, restar, multiplicar, dividir, contar) y escribe los números como el proyecto

- **Decisión del usuario.** "Calcular no es inventar". La comprobación de la pantalla ya no exige que cada
  cifra esté escrita tal cual: acepta el resultado de una cuenta entre cifras publicadas (suma, resta,
  multiplicación, división, cambio porcentual, proporción), con el resultado escrito a dos decimales como el
  resto del proyecto. Sigue rechazando cualquier cifra que no salga de los datos de ninguna de esas formas.
- **Corrección (misma fecha).** Una versión intermedia de esta comprobación aceptaba además una cifra
  *parecida* a una publicada (73 en lugar de 72,61). El usuario lo detuvo: en el proyecto no existe ese
  redondeo, y dejar pasar 73 cuando el dato dice 72,61 es mostrar un número que no está. Se retiró esa
  tolerancia y hay una prueba que exige su rechazo.
- **Instrucciones del intérprete.** Puede hacer esas cuentas con las cifras que recibe, y nunca negarse por
  ser la pregunta amplia, general o conversacional.
- **Formato de los números (regla del proyecto).** La pantalla normaliza lo que escriba el modelo: enteros
  sin separador de miles (4239, no 4.239), decimales con coma (72,61), porcentajes con coma y espacio antes
  del signo (97,85 %). Se probó con `formatearNumeros`.
- **Pruebas:** asistente 1.9 en jsdom 18 → **20** (una de ellas exige que 73 por 72,61 se rechace).

## 2026-09-30 — La IA ya responde cuando la pregunta es amplia, y puede hacer cuentas simples

- **Qué pasaba.** A "Compara las carreras del 2025 y 2026" el asistente contestaba "la comparación global es
  demasiado amplia para una sola consulta": el primer paso (el que decide qué leer) se negaba **antes de leer**,
  inventando reglas que nadie le dio —alcance, tipo de consulta, "es conversacional"—. Medido: devolvía
  `se_puede: false` y al modelo no le llegaba **ni un carácter** de datos, aunque la comparación sí se puede
  armar (dos períodos, catorce carreras cada uno, con sus respuestas, su NPS y su satisfacción).
- **Qué cambió (el texto, no los datos).** En las instrucciones de los dos pasos: que **nunca** se niegue por
  ser la pregunta amplia, general, larga o conversacional; que los únicos dos motivos para negarse son que el
  tema no esté en las encuestas o que la pregunta no sea sobre ellas; y que en la redacción no hable de
  alcance, tipos de consulta ni reglas internas.
- **Calcular no es inventar (corrección del usuario).** La pantalla dejó de exigir que cada cifra estuviera
  escrita letra por letra: ahora acepta también las **cuentas simples entre dos cifras publicadas** (resta,
  suma, cambio porcentual), así "el NPS subió 11,3 puntos (de 61,31 a 72,61)" es válido. Lo que sigue
  prohibido es una cifra que no venga de los datos de ninguna de las dos formas: si no está publicada ni sale
  de una cuenta entre dos publicadas, la respuesta no se muestra.
- **Pruebas:** asistente 1.9 en jsdom 17 → **18**.
- **Pendiente:** las "dimensiones" (`dimensiones.json`) todavía no se le pueden pedir: eso es agregar un tipo
  de datos nuevo, no texto.

## 2026-09-30 — Se retira la función `/api/preguntas`

- **Qué era.** La función del backend de `survey-tracker` que guardaba sin datos personales las preguntas
  que hacía la gente y contaba las más frecuentes: alimentaba la lista "las más preguntadas" del portal.
- **Por qué se retira.** El portal dejó de registrar preguntas el 2026-09-30 (decisión del usuario: esa
  lista no debía existir), así que la función quedó publicada y sin ningún consumidor.
- **Qué se hizo** (en `survey-tracker`): se borraron `apps/backend/api/preguntas.js` y su prueba, y su
  ruta en `apps/backend/vercel.json`. La documentación de endpoints de ese repositorio no la mencionaba.
- **Verificación.** CI del otro repositorio en verde y, contra el servicio publicado, `/api/preguntas`
  responde **404** (tres veces, tras el despliegue); el control `/api/interpretar` sigue vivo (400 sin
  pregunta, como corresponde).

## 2026-09-30 — La guardiana del CSS evita tokens fuera de su bloque

- **Qué pasó.** Al pasar los colores sueltos a `tokens.css`, los 13 tokens nuevos quedaron escritos
  después del cierre de `:root`: la hoja era CSS válido, las pruebas seguían verdes, y el navegador
  descartaba cada declaración sin avisar. En pantalla: la barra de desplazamiento del portal y los
  anillos "próximamente" del Dashboard quedaron sin color.
- **Qué se corrigió.** Los tokens volvieron dentro de `:root` (verificado en la página publicada: el
  navegador resuelve los seis que se comprobaron y los anillos vuelven a pintarse).
- **Qué se agregó.** Una cuarta regla a la guardiana del CSS (`test_css_limpio.py`): falla si un token
  queda declarado fuera de un bloque. Es la prueba que habría detenido este error, y sus cuatro reglas
  quedan documentadas en `ARCHITECTURE.md`.

## 2026-09-30 — Los colores sueltos del CSS tienen nombre

- **Qué pasaba.** 14 colores estaban escritos a mano dentro de las hojas (un verde, un celeste, un violeta,
  un ámbar, un rosa, varios grises y tres blancos), sin nombre y fuera de la paleta.
- **Qué cambió.** Viven en `shared/css/tokens.css` con su nombre (`--mark-ei`, `--mark-inf`, `--mark-hip`,
  `--mark-inc`, `--postcondition`, `--line-soft`, `--line-strong`, `--ink-dark`, `--btn-zip-hover`,
  `--scrollbar-thumb`, `--scrollbar-thumb-hover`, `--ring-pendiente`, `--ring-vacio`) y los blancos usan
  `--white`. **Los valores son idénticos**: no cambia ni un pixel.
- **Lo que se deja a propósito.** Las cuatro definiciones propias del portal (`--foreground`, `--muted`,
  `--border`, `--sidebar`) y los respaldos `var(--token, #valor)` de `generated.css` y `components.css`:
  esas hojas también las cargan las fichas, donde esos tokens del portal no existen, así que el respaldo
  hace trabajo real.
- **Verificación:** ningún color queda suelto fuera de `tokens.css` salvo esos casos explicados, y los 13
  tokens nuevos tienen uso (la guardiana de CSS falla por token declarado y sin usar).

## 2026-09-30 — Las reglas de negocio de las pantallas, en un solo sitio

- **Qué pasaba.** Cada pantalla llevaba su copia de las metas del proyecto: 14 respaldos escritos a mano
  (`?? 93`, `?? 80`, `?? 50`, `?? 70`, `?? 85`) en 6 archivos, el umbral intermedio (80) suelto en 3 sitios
  más, la meta del NPS medio (20) solo en `portal-dashboard.js` —su comentario admitía que no estaba en la
  configuración—, los cortes del NPS (9 y 7) repetidos en 2 archivos, y los niveles de la escala
  re-declarados en `portal-radar.js` y `utils/metrics.js`. Si cambiaba una meta, hasta 6 archivos seguían
  juzgando con el número viejo y nada avisaba.
- **Qué cambió.** Todo eso vive ahora en `config/constants.js`, que además expone un único acceso
  (`window.SURVEY_META('CSAT')`): las pantallas ya no escriben ningún número ni su propio respaldo, y si la
  configuración no cargara no juzgan (mejor no juzgar que juzgar con un número viejo). Se agregaron a la
  configuración `META_NPS_MEDIO: 20`, `META_NPS_PROMOTOR: 9` y `META_NPS_PASIVO: 7`.
- **Alcance.** 9 módulos: `dashboard.js`, `utils/metrics.js`, `components/sentiment-view.js`,
  `components/radar-chart.js` y los cinco `portal/*.js`. El orden de carga no cambia: `constants.js` va
  primero en las tres familias de páginas (portal, fichas y plantilla).
- **Pruebas:** las del proyecto siguen verdes (métricas, sentimiento, portal y asistente); los marcadores
  `?v=` de las tres fichas y del portal quedaron actualizados.
- **Pendiente de la misma propuesta:** la leyenda de niveles (hoy escrita en 4 fichas y en
  `portal-survey.js`) y los 22 colores sueltos del CSS.

## 2026-09-30 — El asistente entrega las dos lecturas de "trabajan"

- **Qué pasaba.** A "¿Qué porcentaje de graduados de la carrera de economía trabajan?" el asistente
  contestaba que no podía: recibía el reparto de la situación laboral (57,14 % dependiente y 42,86 %
  prácticas profesionales, sobre 14 respuestas) y tenía prohibido sumar o decidir si una práctica es
  trabajo.
- **Qué cambió.** Los datos que el portal le manda ahora traen ya las dos lecturas, calculadas por la
  página con los grupos de `constants.js` (`VALORES_TRABAJO` / `VALORES_PRACTICA`): "Trabajan (trabajo
  formal): 8 de 14 (57,14 %)" y "Si se cuentan también las prácticas: 14 de 14 (100 %)", más el tiempo
  laboral de esos 8 (completo 8 · parcial 0). Es la misma decisión de negocio que el usuario ya había
  fijado: las prácticas no son trabajo, y por eso las dos cifras van juntas.
- **Pruebas:** asistente 1.9 en jsdom 16 → **17**.

## 2026-09-30 — El asistente busca los datos y el modelo redacta (sin catálogo de operaciones)

- **Qué pasaba.** El asistente elegía entre una lista cerrada de operaciones (`contar`, `porcentaje`,
  `cruce`, `listar`…) y no veía ninguna cifra: cada forma nueva de preguntar exigía una regla nueva, y
  preguntas como "compara la satisfacción de Psicología entre 2025-2 y 2026-1" terminaban en los totales de
  la universidad.
- **Qué cambió.** El servicio ahora atiende **dos pasos**: primero el modelo dice **qué datos hay que leer**
  (períodos, preguntas y filtros, copiados del menú); después el portal **busca esos datos** en los JSON
  publicados (bloques de pocos KB) y el modelo **redacta** la respuesta. El portal **comprueba que cada
  cifra escrita esté en los datos** antes de mostrarla; si no, no la muestra.
- **Lo que se retiró.** El catálogo de operaciones del portal (863 líneas del módulo), el registro anónimo
  de preguntas y la lista de "las más preguntadas": la pantalla ya no registra nada.
- **Verificación en la página publicada.** "Compara la satisfacción de Psicología entre 2025-2 y 2026-1"
  devuelve 96,84 % → 97,22 % (los tres mejores niveles de Psicología en cada período) citando las dos
  encuestas, en ~23 s; para eso el modelo pidió dos períodos, dos preguntas y el filtro `Carrera =
  Psicología`, y el portal le mandó **1 175 caracteres** de datos.
- **Pruebas:** asistente 1.9 en jsdom 40 → **16** (la suite se reescribió para el flujo nuevo, que tiene
  menos piezas); `interpretar` (vitest) 14 → **17** (el plan, la redacción y el recorte del plan).

## 2026-09-30 — El conteo se lee de un vistazo: recuadros y una línea con colores

- **Qué cambió.** En un conteo: la línea de la respuesta va en un **recuadro, igual que la pregunta**; el título ("Cruce: …") ya no se repite arriba (vive en la fuente); los datos iniciales son **dos tarjetas** (los encuestados del período y el grupo contado: 598 y 14) hechas con la tarjeta del portal; y el gráfico es la **barra de distribución del proyecto** (una línea con un tramo de color por valor, con su leyenda y sus conteos) en vez de una barra por renglón, que no se entendía. Los ceros siguen nombrados en la leyenda y no llevan tramo.
- **Por qué.** Se pidió algo legible de un vistazo y sin datos que confundan.
- **Nota.** No hay gráfico circular en el proyecto: se reusa la barra de distribución (`csat-bar-row` / `csat-segment`) y los colores de los tokens (`COLORES_DISTRIBUCION` en `constants.js`).
- **Ajuste de estilo (mismo día).** Las líneas de la respuesta van **sin negrita** y la barra usa **escala de grises** (`COLORES_DISTRIBUCION` en `constants.js`), con el color del texto de cada tramo para que el porcentaje se lea en cualquier tono.

## 2026-09-30 — "¿Qué carreras se encuestaron en el 2025?" lista las carreras (lo resuelve la IA)

- **Qué fallaba.** La regla de "cuántos se encuestaron" atajaba la pregunta por la palabra *encuestaron* y respondía el **total del período** (3998), sin ver que se pedían las **carreras**.
- **Cómo se arregló.** No con otra regla escrita a mano: se le dio al intérprete una operación nueva, **`listar`** —"qué valores hay de una pregunta"— y la regla del conteo ya no ataja las preguntas de lista ("qué carreras/facultades/ciclos"). El modelo elige la pregunta objetivo (por ejemplo `Carrera`) y la página cuenta **todos sus valores publicados** y responde la lista, de mayor a menor, con el total. Si la pregunta nombra valores concretos, se cuentan esos.
- **Comprobado en la página.** La pregunta devuelve: *En total: 3998 respuestas* + **Derecho 512 · Administración 497 · Ingeniería Industrial 459 · …**, y las doce carreras suman **3998** exacto.
- **Alcance.** Sirve para cualquier pregunta del menú y cualquier período (carreras, ciclos, facultades, dimensiones...), sin reglas nuevas por cada forma de preguntar.
- **Pruebas:** asistente 1.9 en jsdom **39 → 40**.

## 2026-09-30 — El asistente entiende las preguntas de seguimiento ("y del 2025?")

- **Qué fallaba.** Un seguimiento como "y del 2025?" no se podía responder: el mensaje al modelo llevaba el menú de **un solo período** (el detectado, casi siempre el más nuevo) y **nada de lo anterior**, así que no sabía a qué se refería ni qué había publicado el 2025.
- **Qué cambió.** El portal manda ahora el **menú de todos los períodos publicados** (un bloque `## Menú — …` por cada uno) y agrega al contexto una sección **Conversación reciente** con los dos últimos turnos (pregunta y respuesta). El formulario que devuelve el modelo puede apuntar a **otro período** distinto del detectado, y la página cuenta sobre el suyo. En la función (`survey-tracker`), el tope del menú sube de 16 000 a 40 000 caracteres y una regla nueva le dice que complete los seguimientos con lo anterior.
- **Medido antes del arreglo:** el segundo envío llevaba 6 586 caracteres de menú con **un solo bloque** (`## Menú — Estudiantes Pregrado 2026-1`) y sin conversación; el modelo respondía honestamente "no hay datos del período 2025 en el menú actual".
- **Pruebas:** asistente 1.9 en jsdom **38 → 39** (una nueva: la segunda pregunta lleva la conversación anterior).

## 2026-09-30 — El bloque de respuesta se lee como una conversación (formato D)

- **Qué cambió.** La pregunta va en una **burbuja a la derecha** y la respuesta en un bloque al costado, con el gráfico dentro; se retiraron los rótulos «Pregunta:» y «Respuesta:» que quedaban fuera. Es el formato elegido entre cuatro ejemplos (buscador que responde, rótulo dentro, tarjetas y conversación).
- **Y más respuestas grafican.** El cuadro ahora es genérico —`cuadro(tarjetas, graficos)`— así que además del conteo, el **NPS** (general y por carrera) dibuja su reparto (promotores, pasivos, detractores) con tarjetas de encuestados y NPS. Las demás respuestas siguen con sus líneas hasta el paso siguiente: que **el intérprete indique qué gráfico** le toca a cada respuesta (número, reparto, ranking o comparación).
- **Pruebas:** asistente 1.9 en jsdom **38** (una renombrada y ajustada al formato nuevo).
- **Pruebas:** asistente 1.9 en jsdom **38** (actualizadas al dibujo nuevo).

## 2026-09-30 — La respuesta de un conteo: dos lecturas, barras y fuente sin archivo

- **Qué cambió.** Cuando la respuesta es un conteo (por ejemplo, las 14 respuestas de Economía), el bloque muestra ahora: las **lecturas del porcentaje** ("100 % considerando <los cuatro valores>." y, si el grupo mezcla trabajo con prácticas, "57,14 % considerando <solo trabajo formal>."), un **cuadro con barras** —Encuestados, el grupo, la dimensión con un renglón por valor y, si se cuenta la situación laboral, el reparto por tiempo de trabajo de quienes trabajan— y la **fuente sin el nombre del archivo**: `Fuente: Graduados Pregrado 2026 — Cruce: Situación laboral — Filtro: Carrera = Economía`.
- **Por qué.** El número resalta, se ve de dónde sale y las barras ya son las del proyecto (`.survey-bar-row`).
- **Cómo se calcula.** Las dos lecturas son una **regla de la página** (`constants.js`: `VALORES_TRABAJO` / `VALORES_PRACTICA`), no del modelo: el modelo sigue sin contar nada.
- **Regla reescrita.** "Toda respuesta cita su archivo" pasa a "**toda respuesta cita su fuente**" (la encuesta o encuestas a las que pertenece).
- **Pruebas:** asistente 1.9 en jsdom 37 → **38**.

## 2026-09-30 — Los cuestionarios quedan documentados y el asistente recibe su estructura

- **Qué cambió.** `CONTRACTS.md` tiene una sección nueva, **Cuestionarios (preguntas del formulario)**: las secciones de cada encuesta, la pregunta del formulario con su columna publicada y sus opciones, los saltos y las preguntas anidadas. Además, el contexto que el portal manda al modelo (ítem 1.9) incluye ahora la sección **Cómo está organizado el cuestionario**.
- **De dónde salió.** De los cuestionarios exportados de Zoho Survey (Pregrado 2025-2 y 2026-1; Graduados 2026). Los PDF no se versionan: el texto vive en `CONTRACTS.md` y las cabeceras siguen en `zoho_a_csv.py` / `lib/config.py`.
- **Lo que se comprobó en los datos.** El "tiempo dedicado al trabajo" solo se les pregunta a quienes trabajan (598 respuestas: 322 trabajan y 276 quedaron en blanco); el texto del perfil de egreso cambia según la carrera, pero es una sola pregunta; `Facultad` (y `Ciclo` en Graduados) no son preguntas del formulario: las deriva el ETL.
- **Costo.** El texto que se manda al modelo pasa de 1 621 a 2 444 caracteres (el límite es 6 000).

## 2026-09-30 — La respuesta del asistente muestra la pregunta

- **Qué cambió.** Cada bloque de respuesta empieza ahora con la **pregunta** tal como se escribió, sigue la etiqueta «Respuesta:», el dato y —cuando la respuesta es un cruce o una sola línea— el **resultado aparte y en negrita**. La fuente citaba el archivo (`Fuente: Graduados Pregrado 2026 — respuestas.json`); más tarde el mismo día se quitó el nombre del archivo (ver la entrada de abajo).
- **Por qué.** Antes los bloques se apilaban sin decir qué se había preguntado; ahora cada uno se explica solo, y el número (que es lo que se viene a buscar) resalta.
- **Detalle.** Las respuestas que son listas (varios períodos, rankings) siguen mostrándose como lista: solo se destaca el resultado cuando hay un número único.
- **Estilo de la pregunta.** Va dentro de un recuadro redondeado, con el mismo aspecto que las sugerencias del bloque (elegido entre cinco variantes).
- **Pruebas:** asistente 1.9 en jsdom 34 → **37**.

## 2026-09-30 — El contador de cupo se retira (no coincidía con AI Studio)

- **Qué se probó.** Se agregó un contador propio de las preguntas que se envían a Google (15 por minuto y 500 por día, con corte en hora del Pacífico), un endpoint `/api/cuota` para consultarlo y una fila con el cupo dentro del aviso de espera del ítem 1.9.
- **Por qué se retira.** El número propio **no coincide con el de AI Studio** — Google cuenta además reintentos y cualquier otro uso del proyecto —, así que en vez de informar confundía. Se quitaron la fila del aviso, el contador, el endpoint y sus pruebas.
- **Cómo se consulta el cupo ahora.** Directamente en **AI Studio → Límites de frecuencia**, que es la fuente real (15 solicitudes por minuto y 500 por día para `gemini-3.5-flash-lite`).
- **El aviso de espera** queda con su texto de siempre: «Consultando… / Buscando en los datos publicados. Puede tardar unos minutos.»

## 2026-09-30 — El intérprete del asistente arranca con Gemini 3.5 Flash Lite

- **Qué pasaba.** La función `/api/interpretar` (Vercel) usaba solo modelos gratuitos de NVIDIA: medido con la pregunta real del portal, tardaba **90 962 ms** — el primer modelo se cortaba a los 90 segundos y recién el siguiente contestaba. Ese paso era el **99,7 %** del tiempo total de la consulta.
- **Qué se hizo.** La cadena ahora empieza por **Google `gemini-3.5-flash-lite`** (llave `GOOGLE_API_KEY` en Vercel; medido: 983 / 1 644 / 1 808 ms y 3 de 3 formularios correctos) y conserva los modelos de NVIDIA como respaldo (`nvidia/nemotron-3.5-lightning-30b-a3b` → `z-ai/glm-5.3-flash` → `poolside/laguna-xs-2.1`). El primer intento corta a los 20 s (`INTERPRETAR_TIMEOUT_GOOGLE_MS`) y los de NVIDIA a los 90 s (`INTERPRETAR_TIMEOUT_MS`); si falta una llave, ese proveedor se salta en vez de fallar.
- **Comparación medida antes de decidir** (misma pregunta y mismo menú): `Gemini 3.8/3.7/3.5 Flash` fallan por saturación (503) en todas las rondas; `Gemini 3.1 Flash Lite` (2,1-2,7 s) y `Mistral codestral-latest` (1,96 s) devuelven formularios equivocados (ponen la cuenta como filtro); `Gemma 4` responde 500; los modelos gratis de **OpenCode Zen** están bloqueados por el proveedor («el plan gratuito solo se puede usar desde dentro de OpenCode»), así que quedan fuera.
- **Cupos del plan gratuito de Google** (proyecto `gen-lang-client-0581927016`, leído en AI Studio): 15 solicitudes/minuto, 250 000 tokens/minuto y 500 solicitudes/día para el 3.5 Flash Lite — **por proyecto**, no por llave.
- **Documentación:** `CONTRACTS.md` (cadena de la función), `ARCHITECTURE.md` (ítem 1.9) y el `README.md` del proyecto survey-tracker (variables de entorno del asistente).
- **Ajuste medido después de desplegar.** Con Google en la cadena el formulario llega en ~1,2 s, pero en **3 de 5 pruebas seguidas** el modelo escribió un rótulo inventado («Tratamiento especial equivalencias») en `valores_objetivo` en lugar de las cuatro opciones del menú: estaba nombrando la sección «Equivalencias» del contexto. Se precisó esa sección (`asistente_contexto.json`: el valor es la opción del menú, no la etiqueta de la equivalencia) y se añadió una regla explícita a las instrucciones de la función. La página ya impedía el número falso: valida cada nombre contra los datos publicados y avisa si no existe.
- **Pruebas:** `interpretar` (vitest) 11 → **14** (Google primero, respaldo NVIDIA, corte por proveedor y lectura de la respuesta de cada uno).

## 2026-09-29 — El asistente del portal entiende con contexto y menú

- **Qué pasaba.** El portal mandaba la pregunta sola a `/api/interpretar` y esa función devolvía cuatro campos (`dato`, `periodo`, `entidad`, `orden`) sin saber qué preguntas existen; el portal volvía a adivinar con reglas. Preguntas como «¿qué porcentaje de graduados de la carrera de economía trabajan?» terminaban respondiendo sobre la satisfacción de «La carrera».
- **Qué se hizo.** La función ahora recibe `{pregunta, contexto, menu}` y devuelve un formulario con nombres exactos del menú; el portal valida cada nombre contra los datos publicados y cuenta sobre `respuestas.json`. Nuevo `zoho-survey/shared/config/asistente_contexto.json` (qué es el proyecto, cómo están los datos y las reglas; editable sin tocar código). Además se corrigió la causa raíz del caso reportado: el cruce de reglas ya no toma un nombre pegado a un «de» («la carrera de Economía») como objetivo. El modelo sigue sin calcular ni redactar cifras. La pantalla ahora avisa «Consultando…» mientras espera, la respuesta se pinta siempre en la caja que está en pantalla (aunque se navegue mientras se espera) y, si el intérprete no responde, se reintenta una vez y el aviso final es propio del servicio («No pude consultar al intérprete…»), distinto del aviso de «eso no está en las encuestas». La cadena de modelos corta a los 90 segundos por modelo (configurable) para no quedarse colgada, y el contexto trae las equivalencias de negocio (por ejemplo que "trabajan" incluye dependiente, independiente y practicas).
- **Pruebas.** Asistente 1.9 en jsdom 23 → 34; `interpretar` (vitest) 9 → 11. Conteos de `tests/README.md` y `AGENTS.md` corregidos y verificados contra el run (113 TestFramework, 66 jsdom —32+34—, 313 Python).

## 2026-09-29 — `respuestas.json` deja de ser un contrato obligatorio (el proceso nunca lo generaba)

- **Qué pasaba.** El validador exigía `respuestas.json` en los tres períodos, pero `build_json.py` importaba el generador y **no lo llamaba nunca**. El archivo solo existía en el repositorio porque se había confirmado a mano, así que cualquier corrida del ETL terminaba en rojo, y el atajo de idempotencia (que lo contaba entre los archivos a revisar) no podía cumplirse nunca.
- **Qué se hizo.** Se quitó de los archivos obligatorios del validador y de la lista del atajo. Si el archivo aparece, se sigue validando contra su schema.
- **Qué sigue pendiente.** El módulo `lib/tabla_respuestas.py` y sus pruebas se quedan (están verdes). Su futuro depende del ítem 1.9: si el asistente se retira, se retiran con él.

## 2026-09-29 — El proceso publica la tabla de respuestas del asistente (ítem 1.9)

- **Qué faltaba.** El módulo `lib/tabla_respuestas.py` estaba escrito y probado, pero `build_json.py` importaba `construir_tabla` y **no la llamaba**: la tabla solo existía si alguien la confirmaba a mano, así que cada corrida del ETL terminaba en rojo y el asistente no tenía con qué responder cruces.
- **Qué se hizo.** El ETL la genera y publica como `respuestas.json` en cada período, y el atajo de idempotencia la revisa como a los demás. Quedó además como archivo **obligatorio** del validador, después de comprobar que existe en los tres períodos.
- **Qué trae.** Una fila por respuesta (3998 / 4239 / 598, iguales al dashboard), 33 preguntas en Pregrado y 48 en Graduados, con las opciones declaradas una sola vez, el identificador de cada respuesta y su fecha. Fuera quedan el comentario abierto (viaja en `sentimiento.json`), el estado del webhook y lo que supere 50 valores distintos (texto libre). Sin datos personales.
- **Para qué.** Es lo que permite contestar cruces del tipo «de los que trabajan a tiempo completo, cuántos están satisfechos», que no se pueden precalcular.

## 2026-09-29 — Fase 5: se midió qué puede salir del navegador (y se revirtió un intento)

- **Lo que se intentó.** Publicar en `resumenes.json` un agregado por dimensión (la suma de todas las facultades, carreras y ciclos) para que el radar y las tablas dejaran de sumarlo. El proceso lo generó correcto: **0 filas descuadradas y desvío 0,00** frente a las filas de `dimensiones.json`, en los tres períodos.
- **Por qué se revirtió.** El radar y las tablas agrupan filas **ya filtradas** por la persona (facultad, carrera, ciclo). El agregado solo sirve a la vista sin filtros y usarlo obligaba a un camino extra en el código para mostrar exactamente los mismos números: la sobreingeniería que el usuario rechaza, y dejaba en los JSON un dato sin consumidor.
- **Lo que queda medido.** De las 96 líneas que hoy calculan algo en `shared/js/`: 40 son formato, 4 son geometría de los dibujos (el ángulo del radar, el ancho de una barra) y 52 son agregaciones sobre los filtros elegidos. Las dos primeras se quedan; la tercera **no se puede precalcular** por definición.
- **Conclusión.** La regla «el HTML no calcula» se cumple para todo lo que no depende de un filtro; lo que depende de él es inherente a una pantalla que reacciona a lo que la persona elige. No se movió ningún número visible.

## 2026-09-29 — Auditoría de documentación tras las tres reducciones

- **Qué se revisó.** Que ningún documento mencione archivos que ya no existen, que los cinco archivos publicados por período estén en `CONTRACTS.md` y que los conteos de pruebas sean los reales.
- **Lo que se corrigió.** `ARCHITECTURE.md` tenía cuatro menciones a `nps_carrera.json` y `csat_carrera.json` (ahora apuntan a las partes de `resumenes.json`). `tests/README.md` y `AGENTS.md` no contaban las 19 pruebas del asistente del ítem 1.9: ahora dicen 32 pruebas de DOM (el dato real, no 33) + 19 del asistente, y 312 de Python.
- **Lo que quedó bien sin tocar.** `CONTRACTS.md` documenta los cinco archivos publicados; los archivos retirados solo se mencionan en este registro, donde se explica su retiro.
- **Hallazgo y arreglo.** `CONTRACTS.md` contenía el documento **dos veces** (44 658 caracteres) y las dos copias no eran iguales: la segunda era una versión vieja, con la nota equivocada de `dimensiones.json` y sin las secciones de `resumenes.json` y `respuestas.json`. Se comparó sección por sección (son 25, once idénticas y tres distintas) y se conservó la copia vigente: el documento quedó en 23 701 caracteres y 25 secciones, sin perder nada (la copia vieja no tenía ninguna sección propia). De paso se separaron diez encabezados que estaban pegados al párrafo anterior y se movió `respuestas.json` junto a los demás archivos.

## 2026-09-29 — Los cinco resúmenes del período pasan a un solo archivo (`resumenes.json`)

- **Qué cambia.** `ids.json`, `nps_carrera.json`, `csat_carrera.json`, `nps_ciclo_carrera.json` y `csat_ciclo_carrera.json` se unifican en `resumenes.json`, con la misma información bajo las claves `ids`, `nps_carrera`, `csat_carrera`, `nps_ciclo_carrera` y `csat_ciclo_carrera`. Cada período pasa de 9 archivos a 5.
- **Qué NO cambia.** Ni un número ni un dibujo: cada parte se valida contra su schema de siempre (los cinco schemas se mantienen) y los tres cargadores reparten el contenido en memoria con los mismos nombres internos, así que el resto del dashboard y del portal no se toca.
- **Verificación.** La comparación del aspecto dio 100,0 % de elementos y figuras idénticas en las cuatro páginas reales (portal 595/145, Alumnos 2026-1 1825/203, Alumnos 2025-2 1165/161, Graduados 1978/294) y los números publicados siguen iguales.
- **Por qué se hizo.** Los cinco archivos se usaban siempre juntos y sumaban seis peticiones por período.

## 2026-09-29 — Se retiran tres campos de `sentimiento.json` (la barra de visibilidad estuvo a punto de caer)

- **Lo que se buscaba.** Dejar de publicar campos que ningún módulo parecía leer: candidatos `b2b`, `no_utilizo` y `no_conozco` en `dimensiones.json`, y `por_carrera`, `por_ciclo` y `distribucion_intensidad` en `sentimiento.json`.
- **Lo que apareció al probarlo.** La comparación del aspecto (elemento por elemento, antes y después, en las cinco páginas) mostró que se perdían 15 filas de las barras de visibilidad —los segmentos «conocido», «no-utilizo» y «no-conozco»— y que cada página se acortaba 545 píxeles. Esos tres campos **sí se usan**: el frontend arma los nombres de los segmentos en tiempo de ejecución, por eso una búsqueda por nombre no los encuentra.
- **Lo que quedó.** De `dimensiones.json` no se retiró nada; los tres campos siguen publicados y el ETL ahora lleva un comentario que explica por qué. De `sentimiento.json` se retiraron los tres: la comparación confirmó que no se mueve ningún elemento ni una figura.
- **Verificación.** 312 pruebas en verde, contratos válidos, los números publicados idénticos (3998/61,31/96,97 · 4239/72,61/97,85 · 598/85,62/99,00) y el peso por período de 5,8 MB a 4,2 MB.

## 2026-09-29 — Se retira `conteos.json` (ningún visual lo leía)

- **Qué era.** Un archivo por período con los conteos de las preguntas de perfil, la empleabilidad por carrera y un catálogo de preguntas. Se agregó el 2026-09-28.
- **Por qué se retira.** Ninguna página ni módulo lo leía. Su catálogo de preguntas está en las cabeceras de `respuestas.json`, sus conteos de perfil salen de esa misma tabla, y su empleabilidad ya estaba en `dashboard_data.json` (`resumen.empleabilidad`). Mantenerlo era un dato de más y un contrato más que cuidar.
- **Qué se borró.** El archivo en los tres períodos, el módulo `zoho-survey/scripts/lib/conteos.py`, sus 7 pruebas, su schema, sus entradas en el validador y su escritura en el ETL (incluida su mención en el atajo de idempotencia).
- **Verificación.** Los números publicados quedaron idénticos (3998/61,31/96,97 · 4239/72,61/97,85 · 598/85,62/99,00) y la foto del aspecto de las cinco páginas dio 100,0 % de elementos idénticos, con las mismas figuras (portal 595/145, Alumnos 2026-1 1825/203, Alumnos 2025-2 1165/161, Graduados 1978/294).

## 2026-09-29 — La tabla de respuestas del período (base del asistente 1.9)

- **Qué se agrega.** Un archivo nuevo por período, `respuestas.json`: **una fila por respuesta**, con un número por pregunta que apunta a su opción (así el texto va una sola vez y el archivo pesa poco), más el `id` y la `fecha` de cada respuesta. Es la "hoja" con la que el asistente del ítem 1.9 podrá responder filtrando y contando, incluidos los cruces entre preguntas que hoy no se pueden ("de los que trabajan a tiempo completo, cuántos están satisfechos con su perfil de egreso").
- **Qué no lleva.** El texto libre de la pregunta abierta no entra: sigue en `sentimiento.json`, ya analizado y con los datos personales enmascarados. Tampoco entran `Estado de respuesta` (solo filtra las completas) ni las columnas que no son preguntas.
- **Tamaño real publicado.** 3 998 respuestas y 33 preguntas (367 KB, 80 KB comprimido) en Alumnos 2025-2; 4 239 y 33 (389 KB, 86 KB) en Alumnos 2026-1; 598 y 48 (79 KB, 15 KB) en Graduados 2026. El navegador lo baja una sola vez por período y solo cuando la pregunta lo necesita.
- **Sin cambios en lo demás.** Los nueve archivos de siempre quedaron con los **mismos números** (NPS, satisfacción y cantidad de respuestas idénticos en los tres períodos): lo único distinto es la fecha de generación del dashboard. Los comentarios ya analizados se reutilizaron: aparecieron 24 fragmentos nuevos en Graduados y 150 en Alumnos 2026-1, por las respuestas que siguen entrando.
- **Un detalle que se vio en la corrida.** En Alumnos 2025-2 los 3 998 "comentarios" vuelven a descartarse como inválidos (el análisis los revisa y no encuentra texto aprovechable). Queda anotado para revisar ese período, porque no es normal que todas las respuestas traigan algo escrito.
- **Contrato y pruebas.** Schema propio (`scripts/schemas/respuestas.schema.json`), invariantes en el validador (cada fila con un número por pregunta y dentro de sus opciones; `ids` y `fechas` con el mismo largo que las filas) y 7 pruebas unitarias nuevas, que corren en cada push.

## 2026-09-28 — Los conteos de todas las preguntas quedan publicados (`conteos.json`)

- **Qué se agrega.** Un archivo nuevo por período, `conteos.json`, con los conteos que hasta ahora no publicaba ningún otro: las preguntas de perfil (situación laboral, tiempo laboral y las que traiga cada encuesta), contadas por opción, y **cada opción partida por carrera, facultad y ciclo**. Trae además el **catálogo**: la lista de todas las preguntas de la encuesta y en qué archivo vive el conteo de cada una. Con eso el asistente del ítem 1.9 puede responder «¿qué porcentaje de graduados de Economía trabaja?» sin escribir código por pregunta.
- **Nada se duplica.** Las preguntas de escala siguen en `dimensiones.json` (con sus siete niveles), la de recomendación en `nps_*.json`, la de satisfacción general en `csat_*.json`, las respuestas por carrera y ciclo en `ids.json` y los comentarios en `sentimiento.json`. El archivo es **aditivo**: no cambia ninguna clave de los nueve que ya existían.
- **La empleabilidad, ahora por carrera.** Se publica con las mismas reglas que el total global, así que el 87,29 % de Graduados no cambia: se le agrega el corte por carrera (Economía: 14 de 14 = 100,00 %) y por facultad.
- **Cuántos no respondieron.** Cada pregunta dice cuántas respuestas vinieron en blanco (`sin_respuesta`): en Graduados, 276 de 598 en «Tiempo laboral».
- **El ETL dejó de saltarse el período.** `conteos.json` entró en la lista de archivos que revisa el atajo de idempotencia; antes, un período con el CSV sin cambios se saltaba y nunca habría generado el archivo nuevo.
- **Contrato y pruebas.** Schema Draft-07 propio (`scripts/schemas/conteos.schema.json`), invariantes en el validador (el catálogo no puede estar vacío; los cortes deben sumar el total de su opción; toda pregunta contada figura en el catálogo) y 8 pruebas unitarias nuevas que se ejecutan en cada push.
- **Verificación.** Los nueve archivos de siempre quedaron **idénticos**: mismos NPS (61,31 / 72,61 / 85,62), mismos CSAT (96,97 % / 97,85 % / 99,00 %) y mismas respuestas (3998 / 4239 / 598); lo único que cambió en `dashboard_data.json` es la fecha de generación. Los comentarios ya analizados se reutilizaron **al 100 %** (0 de 1827 y 0 de 427 cambiaron): solo se analizaron los nuevos (6 y 2). Y el catálogo quedó con 46 preguntas en Graduados y 31 en cada período de Pregrado.

## 2026-09-28 — El asistente 1.9 ahora entiende la pregunta (y sigue sin inventar)

- **Capa nueva de traducción.** Cuando las palabras clave del motor no alcanzan, el portal manda la pregunta a una función en Vercel (`/api/interpretar`) que la traduce a una consulta ordenada: `{dato, periodo, entidad, orden}`. El motor de datos toma esa consulta y responde con el número real y su archivo de origen.
- **La IA no responde ni calcula:** solo dice *qué* se pregunta. Ningún número sale del modelo, así que no puede inventar cifras. Si la consulta nombra algo que no existe en los datos publicados, el portal lo dice ("No encontré … entre las carreras, facultades o ciclos publicados").
- **Fuera de tema sigue fuera:** si la pregunta no es de las encuestas (la hora, el clima, noticias), el traductor devuelve `ninguna` y el portal contesta el mismo aviso de siempre.
- **Modelo:** cadena de modelos gratuitos de NVIDIA, con la misma llave que ya usa el proceso del ETL (`NVIDIA_API_KEY` en Vercel). Si un modelo falla, se prueba el siguiente.
- **Más formas de preguntar:** «cuántos alumnos se encuestaron en el 2026» (todos los períodos de ese año), «cuántos respondieron de Psicología» (total por carrera, de `ids.json`), «cuántos se encuestaron en total», y «¿cuál es el NPS del 2026?».
- **Pruebas:** 19 del asistente en el portal (3 nuevas para la capa de traducción) y 9 del endpoint en el backend.

## 2026-09-26 — Item 1.9: asistente de preguntas (solo datos de las encuestas)

- **Qué hace:** la barra lateral ya tiene el item **1.9 "Preguntas"** funcionando. Se escribe una pregunta y responde con los números que están en los JSON publicados de cada período: NPS, satisfacción, respuestas, carreras, ciclos, dimensiones (Top 3 Box), comentarios, temas y comparaciones entre períodos.
- **La regla:** todo sale de los JSON; **nada se inventa**. Cada respuesta dice de qué archivo salió (por ejemplo `Fuente: Estudiantes Pregrado 2026-1 — nps_carrera.json`). Si la pregunta no se puede responder con esos datos (hora, clima, noticias, cualquier tema ajeno a las encuestas), contesta que solo responde sobre las encuestas y no improvisa.
- **Sin modelo de lenguaje y sin servidor:** es un motor de consulta sobre los datos. No usa ninguna IA externa, no gasta dinero ni necesita llaves: por eso tampoco puede "alucinar".
- **Módulos nuevos:** `shared/js/portal/portal-preguntas.js` (motor + pantalla) y `tests/unit/test-preguntas.js` (9 pruebas con jsdom, que leen los JSON del repositorio y comprueban que las respuestas salgan de ahí y que lo que no está en los datos no se responda).
- **Los archivos grandes se leen solo si hacen falta:** `dimensiones.json` y `sentimiento.json` se piden únicamente cuando la pregunta los necesita; el resto (dashboard, NPS y CSAT por carrera y por ciclo, filtros) se carga una vez.
- **Verificación:** 20 preguntas probadas contra los datos reales (incluidas "¿qué hora es?", "¿cómo estará el clima?" y "¿quién ganó el partido?", que quedan fuera de alcance), y la pantalla probada de punta a punta en el navegador: clic en el item, escribir, enviar, y respuesta en pantalla con su fuente.

## 2026-09-26 — Limpieza y reordenamiento de las hojas de estilo

- **Reglas repetidas:** 53 reglas estaban escritas igual en dos hojas (el portal y las fichas por período mantenían cada una su copia). Ahora viven una sola vez en `shared/css/common.css`, que se carga después de `tokens.css` y antes de las hojas propias de cada familia.
- **Código muerto:** se borraron 43 clases que ninguna página ni módulo usaba (familias `.flow-*`, `.metric-*`, `.verdict-*`, `.vars-*`, `.brand-*`, `.splash`, `.fade-out`, `.software-italic`), 1 identificador (`#tabla-sentimiento-carrera`) y 20 tokens sin uso.
- **Colores:** 23 colores escritos a mano que ya existían como token pasaron a `var(--token)`; 65 variables que `portal-base.css` volvía a declarar igual que `tokens.css` se retiraron (quedan solo las 11 propias del portal y las 2 que difieren a propósito: `--muted` y `--surface`).
- **`!important`:** se quitaron los 8 que quedaban. La comparación del aspecto demostró que no hacían falta.
- **Carpetas y nombres:** las hojas quedaron ordenadas por familia — lo compartido en la raíz (`tokens.css`, `reset.css`, `common.css`, `generated.css`), las fichas en `dashboard/` y el portal en `portal/` con nombres sin prefijo repetido (`portal/base.css` en vez de `portal/portal-base.css`).
- **Una prueba guardiana nueva:** `zoho-survey/scripts/tests/test_css_limpio.py` falla si vuelve a aparecer una clase muerta, una regla repetida igual en dos hojas o un token sin uso. Se subió primero en rojo (con los 43 hallazgos) y quedó verde al terminar la limpieza.
- **48 selectores que se quedan distintos a propósito** (el portal usa su paleta y su tamaño de texto; las fichas el semáforo verde/ámbar/rojo) quedaron documentados en `shared/css/DIVERGENCIAS.md` para que nadie los una por error.
- **Verificación:** la misma foto del aspecto de cada elemento, a 1400×1000, contra el estado anterior, en las cinco páginas: **100,0% idéntico en las cuatro páginas reales y las mismas figuras en cada una**, después de cada una de las cinco etapas del trabajo.

## 2026-09-26 — Estilos y programas separados: todo el estilo vive en CSS

- **Los estilos en línea de los módulos JavaScript pasaron a clases.** Se migraron los 8 módulos y las 5 páginas (1 145 declaraciones en 597 usos, 172 combinaciones distintas): `sentiment-view.js`, `portal-survey.js`, `dashboard.js`, `radar-chart.js`, `portal.js`, `portal-dashboard.js`, `portal-filters.js`, la plantilla, las tres fichas por período, `index.html` y `health.html`.
- **Una sola excepción, el dato:** la medida de una barra, su color y el color de las tarjetas viajan como variable CSS (`--w`, `--c`, `--delay`, `--kpi-color`, `--cat-h`, `--cat-pct`). No son reglas de estilo: son el valor de esa fila.
- **`generated.css` se carga al final**, después de `components.css` y `sections.css` (y de `portal-*.css` en el portal): sus reglas están pensadas para ajustar las de las capas anteriores cuando coinciden en fuerza.
- **Tres diferencias que solo aparecieron al comparar las dos versiones**, ya corregidas: (1) el ancho fijo de 80px de la etiqueta de barra se había aplicado a todas las listas y las de aspectos no lo llevaban (los nombres se partían en dos líneas y la página crecía 220px); (2) las reglas de celda perdían ante `.survey-table td` y 182 celdas quedaban sin negrita (se recuperó con reglas dentro de la tabla); (3) las reglas de barra, al ser ahora más fuertes, borraban el color de las barras que lo toman de sus clases `high`/`medium`/`low`.
- **Estilos que se ponen propiedad por propiedad** (`el.style.width = ...`): 82 en total. Casi todos son dato (la medida de una barra) o colocación que solo se sabe al ejecutar (la posición de los globos según el mouse, el mostrar/ocultar de la navegación), y esos se quedan en el JavaScript. Los estáticos se movieron: el envoltorio de los filtros y el `select` oculto para lectores de pantalla ahora usan las clases que ya existían.
- **Los dibujos también.** Los colores, grosores y tamaños que iban dentro del dibujo (94 atributos de `fill`, `stroke`, `font-size`, `font-weight` y `stroke-width` en seis archivos) pasaron a clases (`radar-anillo`, `radar-eje`, `radar-guia`, `radar-rotulo`, `radar-area`, `seg-nombre`, `seg-valor`, `etiqueta-corta`, `etiqueta-conteo`, `icono-svg`). La paleta de los anillos de satisfacción, que era una lista de hexadecimales dentro del programa, son ahora cinco clases (`seg-csat-0` a `seg-csat-4`) y los dos colores de las tarjetas de KPI que no venían de la paleta quedaron como tokens (`--kpi-neutro`, `--kpi-azul`). También se retiraron los 11 estilos sueltos que quedaban (el globo del radar, un `cursor:pointer`, un rótulo en versalitas y la animación del icono de refresco, que ahora es la clase `girando`) y los colores de dato viajan como variable (`--c`) en las clases `ring-nps` y `ring-satisf-texto`.
- **Verificación:** la misma foto del aspecto de cada elemento, a 1400×1000, contra el commit anterior: **100% idéntico en las cuatro páginas reales**, y las **796 figuras** de los gráficos idénticas elemento por elemento.
- **La prueba de `renderInsightsIA`** contaba los bloques por su estilo en línea (`border-left`), que es justo lo que el refactor retira; ahora los cuenta por su clase (`.insight-cat`). El reporte de pruebas del proyecto también pasó sus estilos a una hoja interna.
- **Cómo se verificó:** foto del aspecto de cada elemento visible (familia, tamaños, colores, márgenes y medidas) de la versión anterior y de la nueva, a la misma ventana de 1400×1000, en las cinco páginas. Queda idéntico el 97-98% de los elementos; el portal no cambia de alto y las fichas varían 26px sobre más de 9 000px (0,3%), efecto de los altos de línea enteros.

## 2026-09-26 — Auditoría tipográfica completa: todo desde tokens, sin valores sueltos

- **Fuentes:** la familia se declara ahora en `:root`, no solo en `body` (la raíz del documento resolvía a Times New Roman). No queda ninguna familia fuera de Roboto/Lusitania.
- **Controles:** `select`, `input`, `textarea` y `button` heredan también el tamaño, no solo la familia (los botones sin tamaño propio quedaban en 13,3333px, el valor que pone el navegador).
- **Todos los tamaños, grosores y familias salen de tokens:** los valores escritos a mano (13px, 12px, 11px, ...) se reemplazaron por `var(--text-*)`, `var(--font-*)` y `var(--font-family-primary)`.
- **Tokens nuevos:** grosor 600 (`--font-semibold`) y escala de cifras destacadas (`--display-md/lg/xl` = 28/32/36px), declarados en `tokens.css`.
- **Valores fuera de escala corregidos:** 9→10px, 15→14px, 20→18px, 30→28px, 35→36px; en `health.html`, 22→24px y 16→18px.
- **Altos de línea enteros:** las 68 reglas de texto de 8, 10, 11 y 13px llevaban línea fraccionaria (12, 15, 16,5 y 19,5px) por heredar el multiplicador 1,5; ahora cada una declara su alto entero (12, 15, 17 y 20px). También el contador del panel de sentimiento, que se escribía desde JavaScript.
- **`health.html`:** la página no declaraba tamaño base, así que el navegador ponía 16px; ahora usa 14px con línea de 21px.
- **Fuera `!important`** de las reglas de tipografía de los radares: era innecesario, porque el CSS ya gana a los atributos del SVG.
- **Documentado** el estándar completo (fuente, escalas, niveles de título, reglas y forma de verificación) en `ARCHITECTURE.md`.
- Verificado sobre el sitio publicado con el navegador en modo sin ventana: la revisión recorre el documento elemento por elemento y busca familia distinta, valores fraccionarios y valores fuera de escala.

## 2026-09-26 — Escala única de títulos y subtítulos

- Los títulos y subtítulos usan una sola escala: 24px (bloques grandes, título del visor y h1 del
  texto largo), 18px (secciones, "próximamente" y h2/h3 del texto largo), 14px (h4 y sección en
  pantalla angosta), 13px (subtítulo y título de tarjeta), 12px (hallazgo) y 11px (rótulo de
  indicador). Antes había 9px, 15px, 16px y 20px sueltos, fuera de la escala del proyecto.
- Todos los títulos llevan su alto de línea en píxeles enteros (antes ocho lo heredaban y quedaban en
  medias unidades: 19,5 / 13,5 / 16,5px).
- Se igualan dos diferencias entre el portal y las páginas de detalle: el título de tarjeta del portal
  pasa de grosor 600 a 700, y el rótulo chico de los indicadores de 9px a 11px (el mismo que en las
  páginas de detalle).
- Al angostar la ventana, el título de sección baja a 14px en las dos familias (antes solo en las
  páginas de detalle, y a un 15px fuera de escala).
- Se retira la regla `.section-title` de `portal-components.css`: no la usa ninguna página del portal
  (las de detalle usan la de `layout.css`).

## 2026-09-26 — Alturas de línea en píxeles enteros

- Trece alturas de línea que daban fracciones de píxel (1,1 × 15px = 16,5; 1,7 × 13px = 22,1;
  1,35 × 12px = 16,2, etc.) pasan a su píxel más cercano, para que la línea completa caiga en la
  cuadrícula y no solo las palabras.
- El número grande de los indicadores crece por ancho de pantalla (24 / 28 / 32 px), así que cada
  tamaño tiene su propia altura entera (26 / 31 / 35 px) en lugar de un solo valor fijo.
- El texto largo (historial y transcripciones) recibe un alto entero por tamaño: 26px el párrafo
  (15px), y 53 / 35 / 32 / 28 / 25px para los cuatro títulos y las tablas, que tienen su propio
  tamaño. Así ningún texto queda con la línea entre dos píxeles ni apretado.
- El texto general de las páginas de detalle pasa de 1,6 a 1,5 de alto de línea (21px exactos para
  la letra de 14px). El resto de valores sin unidad se quedan porque ya dan píxeles enteros en sus
  tamaños (1,5 × 12px = 18; 1,6 × 15px = 24; 1,1 × 10px = 11).

## 2026-09-26 — Texto nítido: sin suavizado artificial y medidas enteras

- Se quita el suavizado global (`-webkit-font-smoothing: antialiased` y su equivalente de Firefox) de
  las dos hojas base: en Windows apagaba el dibujado nítido del sistema y hacía ver la letra más
  delgada y emborronada.
- Todos los tamaños y espaciados entre letras pasan a valores enteros en píxeles. Los que no caían en
  un píxel exacto (0,72rem = 11,52px; 0,8em; 0,85em; 13,5px; y espaciados de 0,5px / 0,05em) hacían
  que unas letras encajaran y otras no: unas salían nítidas y otras más gruesas dentro de la misma
  palabra. Regla: si el valor real queda por debajo de medio píxel se lleva a 0; si no, al entero más
  cercano.
- El título de la barra lateral usa grosor 900 (pedía 800, que no se carga, y el navegador lo
  engrosaba a mano).

## 2026-09-26 — Tipografía única: Roboto con Lusitania de respaldo

- Todo el proyecto declara una sola familia: `'Roboto', 'Lusitania'`. Se quitó la cadena anterior
  (`-apple-system`, `Segoe UI`, `sans-serif`) de las hojas de estilo, del reporte de pruebas y del
  chequeo técnico. Si ninguna de las dos existe en el equipo, el navegador usa su letra por defecto.
- Los controles de formulario (desplegables, campos de texto y botones) ahora heredan la tipografía:
  el navegador les ponía la suya, así que los doce filtros de cada página de detalle salían con otra
  letra. Regla agregada en `portal-base.css` y en `reset.css`.
- El enlace de Google Fonts carga además el grosor 600, que usaban 29 reglas y se dibujaba con el 700.

## 2026-09-25 — El Dashboard abre con la última encuesta de cada grupo

- La vista **Dashboard** empieza con una fila de **anillos**: uno por encuesta (los nueve niveles
  del catálogo), mostrando solo su medición más reciente. Estudiante Pregrado aparece una sola vez,
  con 2026-1; el 2025-2 solo se usa para la flecha de tendencia.
- El anillo se llena sobre la escala real del índice de promotores netos (−100 a +100: medio anillo
  es cero) y el color sigue las metas, en lugar de dibujarlo como un porcentaje de 0 a 100.
- Las encuestas que todavía no tienen datos ocupan su lugar en gris ("próximamente"). Las nueve van
  agrupadas en Estudiantes · Graduados y egresados · Colaboradores y empleadores.
- Datos: `portal-data.js` suma `medicionDeFase()` y `loadMedicionesDeEncuestas()`, que piden solo el
  `dashboard_data.json` de cada periodo (no el juego completo de JSON). Con pruebas.

## 2026-09-25 — Los mensajes del portal usan el naranja institucional

- Los avisos salen centrados en la pantalla (antes pegados al borde inferior), con el naranja de la
  marca (`--brand`, `#FF5117`) y letras blancas, según el Manual de Marca Ulima.
- El botón de refrescar ignora clics repetidos: uno mientras hay una solicitud en curso y quince
  segundos de espera después, para no pedir corridas de más.
- El pie de la página dice "ítems" en lugar de "fases", y los botones avisan "Actualizar" y "Dashboard".

## 2026-09-25 — El análisis reutilizado ya no pierde fragmentos

- Al reusar el `sentimiento.json` previo se guardaba una sola fila por comentario, así que cada
  corrida incremental dejaba menos fragmentos y menos tópicos (2026-1 cayó de 1847 a 856 filas).
- La reconstrucción del dataset se extrae a `_dataset_desde_sentimiento()`, que conserva una fila por
  fragmento, y se restauraron los dashboards de 2026-1 (1852 filas) y Graduados (434).

## 2026-09-25 — El proceso no arranca si no hay respuestas nuevas

- El servicio que dispara la corrida (función de Vercel) compara la fecha del último cambio en las
  bandejas de `data/zoho_pendientes/` con la de los datos generados en `zoho-survey/students/`:
  si no llegó nada nuevo responde "Sin cambios" y no gasta una corrida del ETL (de 2 a 25 minutos).
- Si el historial de commits no se puede leer, dispara igual que antes.

## 2026-09-24 — La cadena de motores se queda con OpenCode y NVIDIA

- Google (`gemini-3.8-flash`) sale de la cadena por defecto: en las corridas respondía 503
  (Service Unavailable) y obligaba a saltar al motor siguiente.
- `nvidia:deepseek-ai/deepseek-v4-pro-0813` sale porque NVIDIA lo retiró el 14 de setiembre (responde 410 Gone).
  La cadena por defecto queda: `opencode:deepseek-v4.1-flash` -> NVIDIA con 7 modelos
  (`moonshotai/kimi-k3`, `meta/muse-glimmer-30b`, `z-ai/glm-5.3`, `nvidia/nemotron-3.5-lightning-30b-a3b`,
  `deepseek-ai/deepseek-v4.1-flash`, `z-ai/glm-5.3-flash`, `poolside/laguna-xs-2.1`), todos verificados
  como activos contra `https://integrate.api.nvidia.com/v1/models` el 2026-09-24.` `nvidia/nemotron-3-ultra-550b-a55b`
  sale de la cadena: sigue activo pero ya no figuraba entre los modelos vigentes.
- La extracción del JSON deja de usar un patrón codicioso (`{.*}`) y toma el primer objeto **balanceado**,
  así que tolera prosa alrededor, varios objetos y llaves dentro de cadenas de texto.
- `max_tokens` sube de 10 000 a 16 000: los modelos de razonamiento agotaban el presupuesto pensando y
  devolvían el contenido vacío (`finish_reason=length`), obligando a pasar al motor siguiente.
- Ambos servicios siguen disponibles: se pueden volver a agregar con `IA_CUALITATIVO_CADENA`.

## 2026-09-22 — Corrección: las bandejas de una misma encuesta se juntan en un solo CSV

- Si existieran dos bandejas de la misma encuesta, la segunda pisaba a la primera y se perdían respuestas.
  Ahora se agrupan por encuesta y se deduplica por `id_respuesta`.

## 2026-09-22 — La bandeja se convierte sola en el CSV que procesa el ETL

- **Nuevo**: `zoho-survey/scripts/zoho_a_csv.py` arma el CSV desde `data/zoho_pendientes/*.jsonl`
  (una fila por respuesta, cabeceras del ETL en su orden, nombre derivado del título de la encuesta) y lo deja
  en `data/`, donde el gate `Detectar CSVs a procesar` lo recoge.
- Corre **solo** cuando el disparo viene del portal (`repository_dispatch`): un push normal no ejecuta el ETL.
- Usa solo la biblioteca estándar (más las constantes de `lib.config`), así que corre antes de instalar
  dependencias, en el mismo punto que el gate.
- Escribe **sin BOM** por limpieza (el ETL ya lo quita al leer, pero no hay razón para arrastrarlo).
- **No pasan las respuestas parciales**: solo entran al CSV las de `Estado` = `COMPLETED`. Las `PARTIAL` quedan
  en la bandeja y el flujo informa cuántas omitió. Una respuesta sin el campo `Estado` se deja pasar.
- No borra la bandeja: es el acumulado del periodo. Falla con aviso explícito si no puede deducir el nivel
  o si una bandeja no trae respuestas con identificador.
- Pruebas nuevas en `zoho-survey/scripts/tests/test_zoho_a_csv.py`, incluida la comparación de la detección
  de nivel contra `build_json._detectar_nivel`.

## 2026-09-22 — El botón de refrescar del portal pide procesar los datos

- **Nuevo**: el botón `⟲` del portal envía `POST` a `/api/procesar-encuesta`, una función en Vercel
  (proyecto `survey-tracker`) que dispara `repository_dispatch: procesar_datos` sobre *Build and Deploy Survey*.
  La llave de GitHub vive en la variable de entorno `GITHUB_DISPATCH_TOKEN` de Vercel: el navegador nunca la recibe,
  así que no hay nada que pegar en la página.
- El disparo llega **sin** `release_tag`: no descarga CSV. Sirve para redesplegar y, cuando exista la conversión
  de la bandeja al CSV, para procesar lo acumulado.
- El flujo gana el disparador `repository_dispatch: [procesar_datos]`; `push` y `workflow_dispatch` siguen igual.
- La función aplica un corte de 10 minutos entre disparos y restringe CORS al origen del portal (`*` en el resto de endpoints).

## [Unreleased]

### Changed
- **Portal sin credenciales**: el portal es 100 % lectura (solo JSON publicados en GitHub Pages) y su botón de refrescar relee los datos. El ETL se lanza a mano (*Build and Deploy Survey* con el input `release_tag`) o se **pide** desde el botón de
refrescar del portal (ver la entrada del 2026-09-22 de arriba); sigue sin haber camino de subida desde el navegador.
- **Ingesta desde Zoho Survey**: el webhook pasa a llamar a la API de incidencias de GitHub en lugar de `repository_dispatch`, que Zoho Survey no puede usar (ese cuerpo exige `event_type` y `client_payload` como claves hermanas de primer nivel, y el webhook de Zoho arma los campos dentro de un único contenedor con nombre elegido por el usuario). `zoho_inbox.yml` reacciona a la incidencia: el cuerpo es la respuesta en JSON y el título, el nombre de la encuesta. El módulo acepta además la clave `ID` que envía el webhook real y un nombre de encuesta por defecto cuando el cuerpo no lo trae. Al registrar la respuesta, la incidencia se **cierra automáticamente** (el flujo declara `issues: write`), para no acumular pendientes en la pestaña de incidencias; si el registro falla, la incidencia queda abierta como aviso.
- **Motor cualitativo**: el esquema "DeepSeek + respaldo NVIDIA" se reemplaza por una **cadena de motores** (OpenCode → Google → NVIDIA) que se intentan en orden; orden y modelos configurables sin tocar código con `IA_CUALITATIVO_CADENA`. Por defecto el **primer motor es `opencode:deepseek-v4.1-flash`** (el más actual, decisión del usuario); Google y los cuatro modelos de NVIDIA quedan como respaldo. El servicio DeepSeek se retira del proyecto (clave `DEEPSEEK_API_KEY` en desuso). Claves de la cadena: `GOOGLE_API_KEY`, `NVIDIA_API_KEY`, `OPENCODE_API_KEY` (basta una).
- `dataset_cualitativo.schema.json`: el campo `motor` admite `google`, `nvidia`, `opencode`, `filtro` (descartado por el pre-filtro de ruido) y `desconocido` (comentario reutilizado).
- Workflow de pruebas: Node.js 18 → 22 (LTS); deploy solo desde `main`.
- Documentación sincronizada con la cadena de motores (`ARCHITECTURE.md`, `CONTRACTS.md`, `DEV_ENVIRONMENT.md`, `SECURITY.md`, `docs/*`, `AGENTS.md`).

### Removed
- Botón **"Subir datos"** y todo su rastro: `shared/js/portal-upload.js`, `shared/js/portal-upload-ui.js`, el modal de `zoho-survey/index.html`, sus estilos en `portal-components.css`, `zoho-survey/scripts/validate_upload_csv.py` y sus 55 tests (38 JS en `test-upload-validator.js` + 17 Python en `test_validate_upload_csv.py`).
- `zoho-survey/scripts/validar_ia_vs_manual.py` (herramienta manual sin entrada en CI) y su dependencia `openpyxl`.
- `python-dotenv` y `load_dotenv()`: el ETL no lee archivos `.env` (nada corre en local).

### Fixed
- Portal: los botones de periodos de los ítems 1.1 a 1.8 mostraban nombres de documentos (`AUDIT-REVIEW.md`, `AUDIT-REPORT-v2.md`) que ya no existen en el repositorio, en lugar de los periodos publicados del grupo correspondiente. Ahora todos los ítems usan su propio `periodos.json` mediante una única lista ítem→carpeta (`NIVELES_FASE`).
- Portal: la pestaña de periodo se muestra **aunque haya un solo periodo** (antes exigía dos), porque es la forma de saber a qué periodo corresponden los datos que se están viendo.
- Portal: el contador de avance del pie y el subtítulo de las tarjetas del resumen se calculan para todos los ítems (antes solo miraban 1.0 y 1.2).
- Portal: eliminados los campos `artifact`/`artifactLabel` de los 10 ítems (residuo de una etapa anterior; nombraban documentos inexistentes).
- Portal: los ítems 1.0 y 1.2 ya detectan por sí mismos su carpeta de datos (`nivelDeFase`), en lugar de tenerla escrita a mano en cuatro archivos.
- Portal: los ítems 1.0 (Estudiantes Pregrado) y 1.2 (Graduados Pregrado) quedaban en "Cargando dashboard…" de forma indefinida cuando el nivel solo tenía la entrada marcadora de `periodos.json` (proyecto sin datos). El marcador ya no se cuenta como periodo real (`periodosReales`), las fases sin datos muestran "PÁGINA EN CONSTRUCCIÓN" igual que el ítem 1.1 (`tieneDatosDeFase`), la vista de encuesta ya no lanza excepción cuando no hay datos y el contador de avance del pie deja de contar 1.0 y 1.2 como completados.
- Flujo de subida de CSVs (`portal-upload.js`, `portal-upload-ui.js`): `parseRepo` ahora detecta correctamente owner/repo desde GitHub Pages; `upload_id` usa UUID v4; el Release temporal ya no se publica (`publishRelease` eliminado); se limpia el Release en caso de error.
- Seguridad: escaping de `motivo_invalidez` en `sentiment-view.js`; escaping de nombres de dimensión en `formatters.js`; `comentario_original` en `sentimiento.json` se guarda ofuscado con `enmascarar_pii`.
- Modelo DeepSeek por defecto corregido a `deepseek-chat` en `ia_client.py`.
- Schema `dataset_cualitativo.schema.json` ahora acepta `motor: "nvidia"` para el fallback.
- Casing de directorios `facultystaff`/`nonfacultystaff` en `build_json.py`.
- Tests `test_etl_nivel2.py` reescritos para no depender de una carpeta `PDF/` externa.
- `health.html`: paths corregidos y datos dinámicos escapados.

### Changed
- Documentación actualizada (`README.md`, `DEV_ENVIRONMENT.md`, `docs/developer-guide.md`, `docs/onboarding.md`, `SECURITY.md`, `ARCHITECTURE.md`) para reflejar el flujo real local → GitHub Actions y el fallback NVIDIA.
- `package.json`: `name` cambiado a `survey-test`, `version` sincronizada a `3.8.2`, `dev` apunta al servidor estático.
- `requirements.txt`: agregado `python-dotenv`.
- `.github/workflows/tests.yml`: verifica sintaxis de `portal-upload.js`, `portal-upload-ui.js` y `bridge-local-dev.js`; el runner JS incluye `window.location` y `test-upload-validator.js`.

### Removed
- `docs/local-dev-guide.md` (obsoleto; el flujo de desarrollo local ya no requiere servidor FastAPI).

## [3.8.2] — Ingesta vía portal web ("Subir datos")

Arquitectura A (solo GitHub): el portal permite subir CSV(s) desde el navegador usando el PAT del owner en memoria → Release temporal DRAFT → `repository_dispatch[csv_upload]` → GitHub Actions (download + validate + sanitize + ETL + deploy + delete). **Cero servicios externos, cero CSV en git, cero exposición de token público.**

### Added
- `zoho-survey/shared/js/portal-upload.js` — validador cliente + helpers API GitHub (`createRelease`/`uploadAsset`/`dispatchWorkflow`). Límites: 1–10 CSVs, 5 MB c/u, 50 MB total; SHA-256 cliente.
- `zoho-survey/shared/js/portal-upload-ui.js` — modal `#uploadModalOverlay`; PAT en closure; estados IDLE/VALIDATING/VALID/UPLOADING/PROCESSING/…; limpia token+input al finalizar y en errores.
- `zoho-survey/scripts/validate_upload_csv.py` — validación server-side en Actions (nombre, headers, tamaño, duplicados); reusa `_detectar_nivel` y `read_csv_robust`.
- `tests/unit/test-upload-validator.js` — 28 tests (parseFilename, detectNivel, headers, formatBytes, límites).
- `zoho-survey/scripts/tests/test_validate_upload_csv.py` — 17 tests.

### Changed
- `.github/workflows/build_zoho_survey.yml` — trigger `repository_dispatch[csv_upload]` + concurrencia `csv-upload-{upload_id}` (`cancel-in-progress: false`); steps: download→copy→validate(server-side)→sanitize→build_json→validate JSON→artifact→deploy→health→cleanup (DELETE release + `rm data/temp`) gated `success()`; commit steps gated `if: github.event_name != 'repository_dispatch'`.
- `.gitignore` — `data/` añadido.
- `zoho-survey/index.html` — botón `#uploadBtn` + modal + script tags `portal-upload.js`/`portal-upload-ui.js`.
- `package.json` — `test:js` incluye `portal-upload.js` + `test-upload-validator.js`.
- `zoho-survey/shared/css/portal/portal-components.css` — estilos `.upload-modal-*`.

### Security
- El CSV viaja a un Release DRAFT temporal y se elimina tras procesar → no queda en el historial Git.
- El PAT del owner vive solo en memoria del navegador; GitHub Actions usa `GITHUB_TOKEN` (scopes `contents:write` + `pages:write`).
- PII directa (IP/UA/URL) redimida con `sanitize_csv_pii.py` antes del ETL; comentarios NPS ofuscados antes de DeepSeek (Fase 3.5).

### Hardening pendiente (3.8.3)
- Mantener el Release como DRAFT (no publicar) en repos públicos: remover `publishRelease`.
- Aislar el procesamiento por `upload_id` (la copia global a `data/` puede cruzarse entre uploads paralelos).

### Documentación
- Actualizados: `ARCHITECTURE.md`, `README.md`, `CONTRACTS.md`, `tests/README.md`, `SECURITY.md`, `AGENTS.md`. (Nota: `zoho-survey/scripts/README.md` fue eliminado por obsoleto en v3.2.0).
## [Limpieza 2026-08-24] — Migracion

### Fase 0 — Limpieza critica

#### Removed
- `zoho-survey/scripts/lib/ia_cache.py` (CacheManager — solo usado por tests) y `test_ia_cache.py` (18 tests).
- `SENTIMENT_CONFIDENCE_THRESHOLD` de `lib/config.py` + 4 tests asociados (constante zombie del motor `sentiment_engine.py`, eliminado v3.2.0).
- `PROMPT_VERSION` (importado sin uso) y bloque cache en `lib/prompts_cualitativo.py`.
- `zoho-survey/index_old.html` (sin referencias).

#### Fixed
- `tests/test_html_contract.py`: valida `index.html` (portal v5.0, 14 scripts) y `template/index.html` (13 scripts) por separado con ordenes correctos.
- `validar_ia_vs_manual.py`: removido `cache_path=` kwarg inexistente (crash latente).
- `tests/unit/test-formatters.js`: `formatPctSimple` espera `"30,00 %"` con espacio (consistente con `formatPercent`, `formatPctDecimal`, `formatScore`).

#### Changed
- `.env.example`: removida `IA_CUALITATIVO_CACHE`.
- `build_json.py`: removido comentario obsoleto sobre el cache IA (linea 163).
- `lib/config.py`: secciones renumeradas.

### Fase 1 — Sincronizacion de documentacion

#### Changed
- `README.md`: version 3.1.0 → 3.2.0, descripcion actualizada a portal v5.0 + ETL DeepSeek.
- `package.json`: version sincronizada a 3.2.0.
- `ARCHITECTURE.md`: reescrito — diagrama mermaid con portal v5.0, 12 modulos lib activos (era 13+ia_cache), 8 schemas (era 7), pipeline cualitativo DeepSeek (era spaCy), flujo deduplicacion por ID (era cache), outputs con `intermediate/`, ordenes de carga template+portal, whitelist sanitizer 9 tags (era 5), CSS sin `dashboard.css`.
- `CONTRACTS.md`: `dataset_cualitativo.json` marcado con schema formal, tabla con ubicacion `intermediate/`.
- `zoho-survey/scripts/README.md`: reescrito — pipeline 21 pasos con DeepSeek (pasos 17-19 eran spaCy), 12 modulos lib con lineas reales, 10 suites de tests con conteos reales (198 tests), `alias_aspectos.json` eliminado, sin dependencias spaCy/sentence-transformers.
- `zoho-survey/shared/README.md`: reescrito — portal v5.0 como flujo principal, `loader.js` marcado LEGACY, lineas reales por modulo (dashboard.js 1270, sentiment-view.js 1036), whitelist 9 tags, ordenes de carga template+portal, conteo tests 143.
- `AGENTS.md`: 12 modulos lib (era 13 con ia_cache), 8 schemas (era 7), linea `PROMPT_VERSION` removida, advertencias reescritas (sin `SENTIMENT_CONFIDENCE_THRESHOLD`, `ia_cache.json`, snapshot legacy obsoleto).
- `docs/developer-guide.md`: punto de entrada `loader.js` → `portal.js`, taxonomia en `prompts_cualitativo.py` (era `alias_aspectos.json`), env vars sin `IA_CUALITATIVO_CACHE`, seccion "Revertir cache IA" → "Revertir analisis cualitativo".
- `docs/onboarding.md`: ruta de clasificacion de comentarios → `prompts_cualitativo.py`.
- `SECURITY.md`: referencia a cache IA reemplazada por deduplicacion por ID.
- `docs/roadmap-mejora-tecnica.md`: items R2 y S1 actualizados (ia_cache eliminado).
- `requirements.txt`: env vars sin `IA_CUALITATIVO_CACHE`.
- `tests/README.md`: cobertura actual verificada (110 TestFramework + 33 jsdom = 143 tests), removido aviso de snapshot obsoleto.

### Fase 2 — Eliminacion de marca comercial del portal y codigo muerto

#### Removed
- `zoho-survey/shared/js/loader.js` (421 lineas, navegador de encuestas legacy con iframe) + `test-loader.js` (16 tests) + `css/loader.css` (636 lineas). Sin consumidores desde la eliminacion de `index_old.html` (Fase 0).
- Todas las referencias a la marca comercial del portal en codigo, CSS, HTML, tests y documentacion (84 coincidencias).
- CSS muerto en `components.css`: `.doughnut-segment`, `.category-row`, `.category-header`, `.category-bar-wrapper`, `.category-bar-fill`, `.category-intensity`, `.cualitativo-layout`, `.cualitativo-card` (~70 lineas sin referencias en JS).

#### Changed
- Clases CSS del scrollbar del portal renombradas a `portal-scrollbar` (HTML + CSS portal).
- Variable de fases del portal renombrada a `PORTAL_PHASES`; expuesta como `window.PORTAL_PHASES` (`portal.js`, `portal-dashboard.js`).
- Funcion de color de satisfaccion renombrada a `satColorPortal` (`portal-data.js`).
- Path de workspace del portal renombrado a `./portal-workspace/` (`portal.js`; directorio inexistente, fetch 404 manejado).
- Comentarios de la marca comercial reemplazados por "portal v5.0" en JS, CSS y docs.
- `package.json` `test:js`, `tests/run-tests.html` y `.github/workflows/tests.yml`: removido `test-loader.js`; syntax check de `tests.yml` incluye `shared/js/portal/*.js`.
- Docs sincronizadas: `ARCHITECTURE.md`, `README.md`, `CHANGELOG.md`, `AGENTS.md`, `shared/README.md`, `tests/README.md`, `docs/developer-guide.md`, `docs/roadmap-mejora-tecnica.md` (conteo tests JS 143 → 127).
- `AGENTS.md` y `shared/README.md`: corregida afirmacion falsa sobre `SurveyTooltip.move` (si existe, usado en `sentiment-view.js`); removida deuda tecnica inexistente sobre `window.cache`.

### Fase 2.5 — Normalizacion de carpetas de niveles

#### Changed
- `students/posgraduate/` → `students/postgraduate/` (corrige typo recurrente).
- `alumni/posgraduate/` → `alumni/postgraduate/`.
- `facultyStaff/` → `faculty-staff/` (PascalCase → kebab-case) con `undergraduate/` y `postgraduate/`.
- `nonfacultyStaff/` → `nonfaculty-staff/`.

#### Changed (referencias de codigo)
- `zoho-survey/scripts/build_json.py`: `SURVEY_DIRS` y `detect_nivel()` usan los nuevos paths.
- Dashboards por periodo (`students/*/index.html`): `SURVEY_TYPES` y paths actualizados a la nueva estructura de carpetas.
- `zoho-survey/scripts/tests/test_pipeline_integration.py`: `test_detect_postgraduate` espera `"postgraduate"`.
- Docs: `ARCHITECTURE.md`, `students/README.md`, `docs/CHANGELOG.md` (entrada historica anotada).

### Fase 2.6 — Referencias heredadas y normalizacion menor

#### Changed
- `zoho-survey/students/README.md`: referencias rotas a `FILTER_LOGIC.md` → `docs/filter-logic.md`; "11 pipeline steps" → 21; legacy files corregidos (`nps.json`/`csat.json`/`resumen.json` ya no se generan, solo `nps_carrera.json`/`csat_carrera.json`).
- `zoho-survey/students/JSON_SCHEMA.md`: workflow inexistente `validate-survey-json.yml` → `build_zoho_survey.yml`.
- `docs/roadmap-mejora-tecnica.md`: Q2 y D1 marcados resueltos en la migracion.
- `AGENTS.md`: conteos de `dashboard.js` sincronizados a 1270 lineas (eran 1015/1249).
- `zoho-survey/shared/js/portal/portal-data.js`: removida definicion duplicada de `satColorPortal` (L24 dead-shadowed por L39 que usa metas de config).

### Fase 2.7 — Roadmap A1/A2 resueltos y afirmaciones falsas corregidas

#### Changed
- `docs/roadmap-mejora-tecnica.md`: A1 y A2 marcados resueltos en la migracion (verificado: 96/96 IDs HTML identicos template vs 3 periodos; 8 schemas documentados como publicados/intermedio).
- `AGENTS.md`, `CONTRACTS.md`, `scripts/README.md`: corregida afirmacion falsa de que `validar_ia_vs_manual.py` usa `dataset_cualitativo.schema.json` como schema formal (lo carga sin validar contra el schema; validacion manual opcional).
- `validar_ia_vs_manual.py`: docstring L25 corregido — path `intermediate/dataset_cualitativo.json` (era `json/`, ruta inexistente).
- `docs/CHANGELOG.md`: deduplicada entrada Fase 2 (bloque repetido); secciones de migracion fusionadas en orden cronologico 0→1→2→2.5→2.6→2.7.

## [3.2.0] — 2026-07-10

### Fase 1 — Estabilizacion y Quick Wins

#### Added
- `zoho-survey/scripts/sanitize_csv_pii.py`: ampliado para redactar 3 columnas PII (Direccion IP, Agente Usuario, URL de la encuesta). Movido desde `scripts/` raiz.
- `docs/investigacion-2025-2.md`: documento de investigacion del bug CC-01 (causa raiz identificada).
- Step `Sanitize CSV PII` en workflow `build_zoho_survey.yml` (sanitizacion automatica en CI).
- Step `Exclude exports/ from Pages artifact` en workflow (ZIPs no se despliegan en Pages).

#### Changed
- `.gitignore`: eliminada linea `data/`. Los CSVs se commitean sanitizados.
- `requirements.txt`: anadido `openpyxl>=3.0.0`.
- `zoho-survey/scripts/lib/csv_exporter.py`: ZIPs se guardan en `exports/` (no en `json/`).
- `zoho-survey/shared/js/components/sentiment-view.js`: `alert()` reemplazado por modal estilizado.
- HTMLs: `lang="es"` unificado a `lang="es-PE"`.

#### Fixed
- **CC-02**: bug `cache_hits` siempre 0 en `ia_cache.py`/`ia_cualitativo.py`. Contador thread-safe anadido.
- `sanitizer.js`: comentario de whitelist corregido (9 tags, no 5).
- `developer-guide.md`: constante fantasma `CATEGORIAS_ASPECTOS` corregida a `CATEGORIA_DIMENSION_PREGRADO`.
- `developer-guide.md` y `CHANGELOG.md`: constante fantasma `IA_CUALITATIVO_MODE` aclarada como no implementada.

#### Removed
- `docs/zoho-api-integration.md` (Zoho no tiene API).
- `docs/MIGRACION_IA_CUALITATIVO.md` (historico, migracion completada).
- `zoho-survey/scripts/lib/sentimiento_builder.py` (modulo huerfano).
- `zoho-survey/shared/css/dashboard.css` (CSS muerto).
- 5 tests JS huerfanos con bug `assert.true`.
- 3 `<link rel="preload">` a `shared/json/` inexistente en templates.
- Imports sin uso en `build_json.py` y `csv_exporter.py`.

### Fase 2 — Seguridad, Testing y DevOps

#### Added
- `enmascarar_pii` reubicada en `io_helper.py` (redaccion PII en comentarios).
- Redaccion PII en `ia_validacion.py` (texto + justificacion_sentimiento).
- Redaccion PII en `csv_exporter.py` (CSV1 + CSV2).
- Step `Run Ruff linter` en `tests.yml` (informativo).
- Step `Run ESLint` en `tests.yml` (informativo).
- Step `Validate generated JSON contracts` en `build_zoho_survey.yml` (gate post-build).
- `eslint` anadido como devDependency en `package.json`.

#### Changed
- `.github/workflows/build_students.yml` renombrado a `build_zoho_survey.yml`.
- `_csv_escape` ampliado para escapar tab y CR (defensa CSV smuggling).
- `tests/README.md` reescrito (143 tests, 9 archivos JS).
- JSONs orphaned (`fragmentos_nps.json`, `dataset_cualitativo.json`) movidos de `json/` a `intermediate/`.
- Comentarios justificativos en 8 callsites `raw=true` de tooltips.

#### Removed
- `playwright.config.js` y `tests/e2e/` (no se ejecutaban en CI).

### Fase 3 — Eliminacion Legacy + Sincronizacion Documental

#### Added
- `test_ia_cache.py`: 14 tests para CacheManager (incluye thread-safety y hit counter).
- `test_ia_filtro_ruido.py`: 12 tests para pre-filtro de ruido.
- `test_ia_validacion.py`: 10 tests para validacion IA (incluye redaccion PII).
- Step `Verify DEEPSEEK_API_KEY` en workflow (gate temprano).

#### Changed
- `DEEPSEEK_API_KEY` ahora obligatoria (sin fallback legacy).
- `requirements.txt` reducido a 3 deps (pandas, jsonschema, openpyxl).
- Workflows: eliminados caches spaCy/HuggingFace y step `spacy download`.
- `ARCHITECTURE.md`: diagrama, tabla de modulos y deuda tecnica actualizados.
- `AGENTS.md`: seccion lib/, advertencias y modulos criticos actualizados.
- `docs/onboarding.md`: prerrequisitos actualizados (DEEPSEEK_API_KEY obligatoria).
- `build_json.py`: import inline redundante eliminado.

#### Removed
- **Motor legacy completo**: `lib/nlp.py`, `lib/segmentacion_nps.py`, `lib/aspect_extraction.py`, `lib/sentiment_engine.py`.
- 5 tests Python legacy: `test_segmentacion.py`, `test_aspect_extraction.py`, `test_sentiment_engine.py`, `test_alias_aspectos.py`, `test_calibracion.py`.
- `config/stop_aspectos.json` y `config/alias_aspectos.json` (solo usados por legacy).
- Constantes legacy en `config.py`: `IA_LEGACY_CONFIDENCE_THRESHOLD`, `IA_LEGACY_ASPECT_THRESHOLD_HIGH/LOW`.
- 5 items de deuda tecnica resueltos en `ARCHITECTURE.md`.

---

## [3.1.0] — 2026-07-03

### Added
- Extracción de `ALIAS_DICT_MANUAL` (~200 entradas) desde `lib/aspect_extraction.py` a archivo JSON externo `scripts/config/alias_aspectos.json` (Fase 1). Facilita mantenimiento y permite validación independiente.
- Nuevo test `test_alias_aspectos.py`: 5 tests que validan integridad del diccionario de alias (carga desde JSON, correspondencia con taxonomía oficial, no duplicados, estructura del JSON).
- Nuevo test `test_html_contract.py`: 5 tests que validan orden canónico de carga de scripts en `template/index.html`, `zoho-survey/index.html`, y todos los `index.html` de periodos generados.
- Nuevos tests unitarios JS: `test-sentiment-view.js` (8 tests), `test-filter-controller.js` (14 tests), `test-loader.js` (13 tests). Cobertura JS sube de 3/13 a 6/13 módulos.
- Extensión de `test_pipeline_integration.py` con 16 nuevos casos: NPS/CSAT edge cases, detección de nivel/periodo, hash de CSV.
- Extensión de `validate_period_html()` en `validate_generated_json.py`: ahora valida IDs de filtros en cascada (5 secciones × 4 IDs) e IDs de sección cualitativa (7 IDs).
- ~~Constante `IA_CUALITATIVO_MODE` en `lib/config.py`~~ — **NOTA: esta constante fue planificada pero NO implementada**. La configuración de motores cualitativos se controla via variables de entorno (`DEEPSEEK_API_KEY`, `IA_CUALITATIVO_FALLBACK`), no via constante en config.py.
- Documentación del motor IA en `ARCHITECTURE.md`: diagrama Mermaid con doble motor (IA + Legacy), tabla de 10 módulos ETL, sección de optimización `.csv_hash`.
- Integración documentada de la skill `qualitative_research_synthesis` en `docs/developer-guide.md` como herramienta complementaria de validación humana.

### Changed
- `AGENTS.md`: corregido conteo de módulos lib (7→10), actualizada referencia de `ALIAS_DICT_MANUAL` a `config/alias_aspectos.json`.
- `tests/run-tests.html`: agregados 6 nuevos scripts de dependencias + 3 nuevos tests.
- `.github/workflows/tests.yml`: Node test runner actualizado con 4 nuevos módulos + 3 nuevos tests + `metrics.js`.
- `ARCHITECTURE.md`: deuda técnica actualizada (código muerto eliminado, extracción de alias, coexistencia de motores).

### Fixed
- Eliminado `ALIAS_DICT_MANUAL` hardcodeado (~200 líneas) de `lib/aspect_extraction.py`. Ahora se carga desde JSON con fallback a dict vacío si el archivo no existe.
- Confirmado que `DEEPSEEK_API_KEY` está configurado y el motor IA está activo en producción. Sin acción requerida.

---

## [3.0.6] — 2026-06-23

### Fixed
- Agregado el mapeo de dimensiones faltantes (Académico, Administrativo y Bienestar, Infraestructura, Tecnología) a la constante `CATEGORIA_DIMENSION_GRADUADO` en `config.py` para asegurar que el pipeline ETL procese correctamente los datos y se rendericen los visuales de nivel de satisfacción y visibilidad de servicios en "Graduados Pregrado".

---

## [3.0.5] — 2026-06-23

### Changed
- Cambio del filtro "Tema" a "Tema Padre" en "Detalle de ideas", actualizando la etiqueta en todos los periodos y el selector dinámico de JavaScript para agrupar y filtrar comentarios mediante categorías de nivel superior (`c.categoria_padre || c.categoria`).
- Redistribución de anchos de columna en la tabla del explorador de comentarios (Carrera: 16%, Ciclo: 5%, NPS: 5%, Texto abierto: 34%, Idea analizada: 18%, Tema: 12%, Sentimiento: 5%, Intensidad: 5%).
- Modificación del renderizador de tabla cualitativa en `sentiment-view.js` para asegurar que la columna "Tema" muestre explícitamente el subtema/aspecto (`c.categoria`) en lugar del tema padre, y quitar el formato en negrita (font-weight:600) de la columna "Carrera".

### Fixed
- Reversión de los filtros redundantes agregados erróneamente en "Detalle de ideas" (Facultad, Carrera, Ciclo, Limpiar).
- Corrección de formato para el input de búsqueda de comentarios (`#explorador-search`) heredando la fuente institucional (`Roboto`) y tamaño de texto (`12px` / `var(--text-md)`), removiendo el icono de chevron y ajustando padding simétrico.
- Corrección de cálculo en la tabla "Respuestas por carrera — distribución NPS completa" (`renderCareerNPSTable`), diferenciando correctamente el número de comentarios únicos ("Texto abierto" usando Set de IDs) respecto al número total de fragmentos ("Ideas analizadas").
- Simplificación del validador de contratos JSON (`validate_generated_json.py`) y del archivo de esquema (`sentimiento.schema.json`) para ajustar el objeto de tópicos al contrato simplificado v3.0 (`topico`, `total_comentarios`, `positivos`, `negativos`, `neutros`).
- Actualización de documentación de contratos en `CONTRACTS.md` y `JSON_SCHEMA.md` para reflejar la eliminación de atributos obsoletos en tópicos y la remoción de filtros redundantes en el HTML de los periodos.

### Removed
- Eliminación del interruptor/checkbox de texto corregido (`#explorador-toggle-texto`) en "Detalle de ideas" de la plantilla y todas las páginas de periodos, configurando el visor para mostrar siempre la idea analizada (corregida) por defecto.

---

## [3.0.4] — 2026-06-23

### Fixed
- Remoción de los contenedores de filtros redundantes (`sent-aspectos`, `sent-npscarrera`, `sent-tabla`) en la sección de Análisis Cualitativo, centralizando el estado de filtrado hacia el selector global (`sent`) para simplificar la interacción.
- Corrección de la estructura de anidamiento en la lectura de `sentimiento.json` en `sentiment-view.js`. La función `init` ahora lee los comentarios desde la raíz del JSON sin requerir la clave `por_ciclo`, evitando sobrescrituras silenciosas de la variable global de comentarios.
- Corrección del desajuste de IDs estáticos del DOM ( `intensidad-positivos-container` e `intensidad-negativos-container`) y la función JavaScript `_renderList` que impedían el renderizado visual de los gráficos de intensidad de aspectos.
- Incorporación de reglas defensivas de strings ('todas') en `getFilteredSubset` para evitar filtros huérfanos que truncaban silenciosamente los paneles "Aspectos más positivos", "Aspectos más negativos" y "Respuestas por carrera" tras retenciones agresivas de estado local en ciertos navegadores.

---

## [3.0.3] — 2026-06-12

### Added
- Calibración de neutralidad sensible en el clasificador cualitativo (`nlp.py`), reduciendo el umbral de neutralidad de `abs(diff) < 0.20` a `abs(diff) < 0.12`. Esta calibración fue seleccionada tras evaluar experimentalmente cuatro escenarios, logrando un acierto del 66% general y 84% en la clasificación de quejas (Neutro → Negativo), recuperando críticas valiosas que antes quedaban ocultas.

### Changed
- Regeneración completa de los datasets de comentarios `sentimiento.json` para pregrado y graduados aplicando la nueva sensibilidad de polaridad, sin introducir cambios en la arquitectura de embeddings, tópicos ni en el esquema contractual.

### Backlog (Futuras Oportunidades)
- Implementación de reglas semánticas para prevenir falsos negativos ante declaraciones de desconocimiento ("no conozco", "no utilizo").
- Implementación de reglas lingüísticas de negación ("no ... bien", "dista de", "carece de") previas al embedding para mitigar falsos positivos.

---

## [3.0.2] — 2026-06-12

### Added
- Optimización de inferencia semántica por lotes (batch inference) en `nlp.py` con SentenceTransformers utilizando `batch_size=32`. Consigue paridad matemática del 100% de clasificaciones (sentimiento, categoría, tópico y fragmento) y reduce los tiempos de ejecución de build drásticamente.

### Changed
- Consolidación definitiva del módulo cualitativo v3.0: se retira el flag `USE_V3_SENTIMENT` del frontend y se unifican las llamadas de datos de comentarios cualitativos directamente sobre `sentimiento.json`.
- Minificación selectiva aplicada en el ETL (`build_json.py`) para los JSON de alto peso (`dimensiones.json`, `sentimiento.json`, `nps_ciclo_carrera.json`, `csat_ciclo_carrera.json`), disminuyendo en más de 160,000 líneas en blanco el volumen de transferencia sobre GitHub Pages, mientras se preservan legibles los JSON estructurales de filtros e identificadores.
- `validate_generated_json.py` actualizado para hacer obligatorio el esquema cualitativo de `sentimiento.json` (v3.0) y retirar la coexistencia paralela de `sentimiento_v3.json`.
- `CONTRACTS.md` y `ARCHITECTURE.md` actualizados para formalizar los nuevos esquemas contractuales y advertir que `nps_carrera.json` y `csat_carrera.json` continúan activos únicamente como fallback de carga síncrona en encuestas sin ciclos (`has_ciclo=false`).

### Removed
- Eliminación de archivos temporales redundantes `sentimiento_v3.json` y del cargador de fallback legacy `renderTablaSentimientoCarrera()` del frontend.

---

## [2.0.3] — 2026-06-11

### Added
- Persistencia del estado de navegación mediante `localStorage`, almacenando el tipo de encuesta (`ulima_selected_survey`) y el período seleccionado por tipo de encuesta (`ulima_selected_period_[survey_id]`).
- Navegación dinámica y adaptativa en la barra superior (`loader.js`): al seleccionar un elemento oculto dentro del menú desplegable "MÁS", este se fuerza a ser visible intercambiándose por el último elemento visible.
- Atributos semánticos ARIA en el menú desplegable "MÁS" (`aria-haspopup`, `aria-expanded`, `role="menu"`, `role="menuitem"`) para mejorar la accesibilidad de lectores de pantalla.
- Lógica de preservación y transferencia de foco para que al interactuar mediante teclado en el menú "MÁS", el foco se reasigne correctamente en lugar de perderse por la reestructuración del DOM.

### Changed
- `loader.js`: Se invocan los métodos `.schedule()` de reordenamiento de los objetos de overflow tras cambiar de encuesta o periodo académico para asegurar la reevaluación inmediata de anchos y visibilidad.

### Fixed
- Corrección de grosor asimétrico en barras de desplazamiento de `.table-scroll`: unificados los grosores horizontal (`height: 6px`) y vertical (`width: 6px`) en selectores webkit y añadidas propiedades estándar `scrollbar-*` de grosor delgado (`thin`) y combinación de color institucional como fallback para Firefox.

---

## [2.0.2] — 2026-06-11

### Added
- Cabecera fija (sticky header) responsiva en las tablas `.survey-table` del Análisis Detallado para mejorar la legibilidad durante el scroll vertical.

### Changed
- `layout.css`: Definido el token de altura `--sticky-header-h: 45px;` en `:root` y configurado `.sticky-header` con `height: var(--sticky-header-h)` para garantizar una altura fija y uniforme libre de variaciones por renderizado tipográfico.
- `components.css`: Configurado `.survey-table th` con `position: sticky`, `top: calc(var(--sticky-header-h) - 1px)` y `z-index: 10`, aplicando un solapamiento de seguridad de 1px para evitar filtraciones de texto.
- `components.css`: Ajustado el breakpoint de desktop en `.table-scroll` de `821px` a `769px` para alinear con el sistema de breakpoints.
- `sections.css`: Redefinida la variable `--sticky-header-h` en media queries de tablet y mobile. Configurado `.table-scroll` con `max-height` (`380px` en tablet, `300px` en mobile) y `overflow-y: auto`, y reajustado `.survey-table th` a `top: 0` para mantener las cabeceras fijas dentro de su propio contenedor de scroll en dispositivos móviles y evitar que se desactiven por el `overflow-x: auto`.

---

## [2.0.1] — 2026-06-10

### Added
- Documentación de subcomponentes JS modularizados (`filter-controller.js`, `radar-chart.js`, `sentiment-view.js`) en [ARCHITECTURE.md](ARCHITECTURE.md).
- Detalle del subdirectorio Python `scripts/lib/` y sus 4 submódulos en [ARCHITECTURE.md](ARCHITECTURE.md).
- Documentación de los workflows de CI/CD (`build_students.yml`, `deploy-legacy.yml`, `validate-survey-json.yml`) en [ARCHITECTURE.md](ARCHITECTURE.md).
- Advertencia técnica sobre el orden de dependencias en el cargador JS (`dom-helpers.js` antes de `custom-select.js`) en [docs/developer-guide.md](docs/developer-guide.md).

### Fixed
- Contratos de datos en [CONTRACTS.md](CONTRACTS.md): Unificación de claves NPS a minúsculas (`promotores`, `pasivos`, `detractores`) para concordar con la implementación real del ETL.
- Definición de propiedad en `ids.json` de [CONTRACTS.md](CONTRACTS.md): Corrección de `count` a `total` para reflejar la salida del backend.
- Carga de dependencias en el portal principal `index.html` (importación de `dom-helpers.js` añadida para solventar error de carga en `custom-select`).
- Referencias de espacio de nombres en `radar-chart.js` (añadido alias `_dh` para métodos utilitarios de DOM).
- Centrado y redimensión del gráfico de radar general: Ajuste dinámico de `viewBox` (`-80 0 760 500`) en SVG y `aspect-ratio` (`76 / 50`) en CSS para maximizar su tamaño (un 60% más grande) y eliminar el espacio vacío superior/inferior.
- Solapamiento de etiquetas en el radar: Algoritmo de dos pasadas para espaciado vertical mínimo (`15px`) y proyección circular adaptativa de textos polares/laterales.

---

## [2.0.0] — 2026-06-03

### Added
- Sanitización HTML (`escapeHTML`, `sanitizeHTML`) para prevención de XSS
- 8 módulos JS independientes: `constants.js`, `formatters.js`, `sanitizer.js`, `dom-helpers.js`, `tooltip.js`, `progress-bar.js`, `custom-select.js`, `multiselect.js`
- CSS modularizado en 5 capas: `tokens.css`, `reset.css`, `layout.css`, `components.css`, `sections.css`
- 34 tests unitarios con framework `test-framework.js` + runner HTML
- 3 JSON Schemas (draft-07): `dashboard_data`, `filtros`, `sentimiento`
- `lib/config.py` con configuración ETL externalizada
- `docs/ai-agent-guide.md` — guía para DeepSeek, Claude, Copilot
- Variables CSS de capa z-index (`--z-base` a `--z-splash`)
- `LOADER_CONFIG` en loader.js con constantes externalizadas
- `SURVEY_CONFIG` ampliado con `MAX_CICLOS_DEFAULT/ESPECIALES`, `RADAR_LABEL_MAXLEN`, etc.
- `version: "2.0"` en `dashboard_data.json`, `filtros.json`, `sentimiento.json`

### Changed
- `dashboard.js`: monolito 1717 líneas → orquestador que delega en 8 módulos con fallback inline
- `dashboard.css`: monolito 1176 líneas → entry point 16 líneas con `@import`
- ETL: 14→9 archivos JSON por periodo (eliminados `resumen.json`, `nps.json`, `csat.json`, `nps_ciclo.json`, `csat_ciclo.json`)
- `loader.css`: `DM Sans` → `Roboto`, `--font-family` variable agregada, `#fff` → `var(--white)`
- `etapa_map`: ciclo 6° corregido de "Intermedio" → "Avanzado" (según documento de contexto)
- `build_json.py` y `validate_generated_json.py`: paths corregidos (doble anidamiento `zoho-survey/zoho-survey/`)
- `package.json`: versión `2.0.0`, script `validate:json` corregido
- `loader.js`: strings y timeouts externalizados a `LOADER_CONFIG`

### Removed
- 15 archivos JSON legacy del repositorio (5 por periodo × 3 periodos)
- 4 archivos `.txt` placeholder en `postgraduate/` (entonces `posgraduate/`, renombrado en limpieza 2026-08-24)
- 4 archivos `.md` obsoletos/duplicados: `docs/architecture-overview.md`, `zoho-survey/shared/README.md`, `MIGRATION.md`, `zoho-survey/students/JSON_SCHEMA.md`

### Fixed
- XSS en `showTooltip()` — sanitización con whitelist de tags
- `PERIODS` mutable en `loader.js` documentado como variable de estado
- Hardcoded colors: `#F37021` → `var(--splash-bg)`, `#000000` → `var(--black)`
- Duplicación de `getSelectedValues`/`setSelectedValues` en 3 archivos → `utils/dom-helpers.js`
- **Header/loader redesign**: CSS Grid body layout elimina `position:fixed` y `--bar-h` hardcodeado
- **Iframe height bug**: `#frame-wrap` ahora usa grid `1fr` en vez de `top: 96px`, adaptándose automáticamente a la altura real del `#topbar`
- **Responsive**: agregado breakpoint 820px, corregidos gaps/paddings en 960px y 640px
- **Mobile selects**: integrado `SurveyCustomSelect` con tema oscuro institucional (fondo `#2a221c`, hover `--ulima-orange`, sin fondo blanco ni azul nativo)
- **Duplicate CSS**: eliminado segundo bloque `.survey-tab` en `loader.css`
- **Header visual polish (2ª iteración)**: gap vertical `.topbar-right` 1px→6px, badge NUEVO reposicionado debajo del pill, labels uniformizadas (11px), añadida etiqueta simétrica "ENCUESTA" junto a "PERIODO", font-size escalado en 3 breakpoints

### Migration Notes
- Patrón de delegación con fallback inline: backward compatible con dashboards existentes
- Todos los dashboards cargan sin los nuevos scripts (fallback inline en dashboard.js)
- Rollback disponible vía `git restore` por archivo
- Tag `v-pre-refactor` creado como punto de restauración

---

## [1.0.0] — 2025
- Versión inicial con dashboard monolítico
- ETL: CSV → 14 JSONs por periodo
- 4 secciones: Ejecutivo, Operativo, Detallado, Cualitativo
- Deploy en GitHub Pages vía `deploy-legacy.yml`
