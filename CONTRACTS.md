# Contratos De Datos

Este documento es la fuente canonica para los datos que fluyen por el sistema. Define entradas CSV, salidas JSON, responsabilidades por capa e invariantes de validacion.

> **Fuente de verdad:** Para tipos formales, consultar los JSON Schemas Draft-07 en `zoho-survey/scripts/schemas/*.schema.json`. Para la implementacion de generacion, `zoho-survey/scripts/build_json.py`. Este documento es la version humana del contrato; en caso de discrepancia, el schema y el ETL prevalecen.

## Entrada CSV

Los CSV fuente viven en `data/` y provienen de Zoho Survey. El ETL oficial es `zoho-survey/scripts/build_json.py`.

Columnas criticas para encuestas estudiantiles:

- `ID de respuesta`: identificador unico.
- `Net Promoter Score (de un total de 10)`: escala 0-10 para NPS.
- `¿Que carrera profesional estudias?`: base para filtros por carrera.
- `¿Que ciclo es el que cursas?`: base para filtros por ciclo.
- `La Universidad de Lima`: columna base para CSAT global.

El mapeo real de columnas debe verificarse en `zoho-survey/scripts/build_json.py` y `zoho-survey/scripts/lib/config.py` (`COLUMN_RENAME_PREGRADO`, `COLUMN_RENAME_GRADUADO`).

## Contrato De Ingesta

Las respuestas entran por el **webhook de Zoho Survey**: se acumulan enmascaradas en `data/zoho_pendientes/<encuesta>.jsonl` y el ETL se ejecuta a mano sobre el CSV que se adjunta a un Release (*Build and Deploy Survey* con el input `release_tag`). El nombre del archivo define el nivel y el periodo; las reglas reales están en `zoho-survey/scripts/build_json.py` (`_detectar_nivel`) y `lib/config.py`. Este es el resumen humano.

#

## Formato de nombre

Regex tolerante a espacios (`\s*-\s*`) y a acentuación de la Ó:

```text
ENCUESTA DE SATISFACCI[ÓO]N {CATEGORÍA} - {NIVEL} - {PERIODO}.csv
                      {cat}            - {PRE|POS} - {20XX[-1]}
```

- **CATEGORÍA**: `ESTUDIANTIL | GRADUADOS | POSGRADO | DOCENTES | EGRESADOS | NO DOCENTES | EMPLEADORES`.
- **NIVEL**: `PREGRADO | POSGRADO` (opcional en `NO DOCENTE`, que no lo lleva).

**Separadores**: entre tokens se acepta espacio simple o guion (`EGRESADOS PREGRADO 2026` ≡ `EGRESADOS - PREGRADO - 2026`). Las variantes `DOCENTE`/`DOCENTES` y `NO DOCENTE`/`NO DOCENTES` (singular/plural) son equivalentes.
- **PERIODO**: **OPCIONAL**. Formato `20XX` (anual) ó `20XX-1` / `20XX-2` (semestral). Muchos CSV reales (ej. `NO DOCENTE 2026.csv`) lo omiten; el ETL lo deriva del nombre cuando está ausente.

**Periodicidad por categoría** (validada por `PERIODICIDAD` en el código):

| Categoría | Periodicidad | Nivel requerido | Periodo |
| --- | --- | --- | --- |
| `ESTUDIANTIL` | semestral | sí (PRE/PG) | `20XX-1`/`20XX-2` o ausente |
| `DOCENTES` | anual | sí (PRE/PG) | `20XX` o ausente |
| `NO DOCENTES` | anual | **no** | `20XX` o ausente |
| `GRADUADOS` | anual | sí (PRE) | `20XX` o ausente |
| `POSGRADO` | anual | sí | `20XX` o ausente |
| `EGRESADOS` | anual | sí (PRE/PG) | `20XX` o ausente |
| `EMPLEADORES` | anual | sí (PRE/PG) | `20XX` o ausente |

Ejemplos válidos: `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-1.csv`, `ENCUESTA DE SATISFACCION DOCENTES-POSGRADO-2026-2.csv`, `ENCUESTA DE SATISFACCION GRADUADOS - PREGRADO - 2026.csv`.

#

## Mapeo a nivel interno (== `build_json._detectar_nivel`)

| Substrings | Nivel interno |
| --- | --- |
| `ESTUDIANTIL` / `ESTUDIANTES` + `PREGRADO` | `undergraduate` |
| `ESTUDIANTIL` / `ESTUDIANTES` + `POSGRADO` | `postgraduate` |
| `GRADUADOS` | `graduate` |
| `EGRESADOS` + `POSGRADO` | `alumni-pg` (sin POSGRADO → `alumni-ug`) |
| `DOCENTES` + `POSGRADO` | `faculty-pg` (sin POSGRADO → `faculty-ug`) |
| `NO DOCENTES` | `nonfaculty` |
| `EMPLEADORES` | `employers` |

#

## Cuestionarios (preguntas del formulario)

Las preguntas de cada encuesta, con su orden, son las cabeceras de `CABECERAS_POR_NIVEL`
(`zoho-survey/scripts/zoho_a_csv.py`). Cada pregunta se declara una sola vez en
`PREGUNTAS_POR_NIVEL` (`zoho-survey/scripts/lib/config.py`): `id` estable, `nombre` publicado,
`tipo`, `pregunta` (el texto del formulario) y `escala`. Los mapas `COLUMN_RENAME_PREGRADO` y
`COLUMN_RENAME_GRADUADO` se derivan de esa declaración. Esta sección documenta lo que no
está en el código: las **secciones** del formulario, el **texto** de cada pregunta, sus **opciones**
y los **saltos**.

Fuente: los cuestionarios exportados de Zoho Survey. Los PDF no se versionan en el repositorio.

### Pregrado — ESTUDIANTIL + PREGRADO (2025-2 y 2026-1)

Mismo cuestionario en los dos períodos: las 33 preguntas coinciden en nombre y orden (comprobado).

| Sección | Pregunta del formulario | Columna publicada | Opciones en los datos* |
| --- | --- | --- | --- |
| DATOS PERSONALES | Carrera | `Carrera` | Administración, Arquitectura, Comunicación, Contabilidad y Finanzas, Derecho, Economía, … (14 valores) |
|  | Ciclo | `Ciclo` | 10° Ciclo, 11° Ciclo, 12° Ciclo, 1° Ciclo, 2° Ciclo, 3° Ciclo, 4° Ciclo, 5° Ciclo, 6° Ciclo, 7° Ciclo, 8° Ciclo, 9° Ciclo |
| SERVICIOS ACADÉMICOS | Perfil del egreso de la carrera | `Perfil del egreso de la carrera` | (sin respuesta), Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Plan curricular y perfil de egreso | `Plan curricular y perfil de egreso` | (sin respuesta), Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Cursos del programa y contenidos | `Cursos del programa y contenidos` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Calidad de la enseñanza en la carrera | `Calidad de la enseñanza en la carrera` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Claridad de los recursos académicos | `Claridad de los recursos académicos` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Evaluación del aprendizaje | `Evaluación del aprendizaje` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Intercambio estudiantil | `Intercambio estudiantil` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| SERVICIOS AL ESTUDIANTE | Información sobre el récord académico | `Información sobre el récord académico` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Material bibliográfico en la biblioteca | `Material bibliográfico en la biblioteca` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Atención del personal administrativo | `Atención del personal administrativo` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Procedimientos administrativos | `Procedimientos administrativos` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Ayuda financiera | `Ayuda financiera` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Servicio médico y su infraestructura | `Servicio médico y su infraestructura` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Servicio de atención psicopedagógica | `Servicio de atención psicopedagógica` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Talleres de actividades artísticas y culturales | `Talleres de actividades artísticas y culturales` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Actividades deportivas | `Actividades deportivas` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| RECURSOS E INFRAESTRUCTURA | Aulas de clase | `Aulas de clase` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Ambientes y salas para estudio | `Ambientes y salas para estudio` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Equipamiento tecnológico en laboratorios | `Equipamiento tecnológico en laboratorios` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Condiciones ambientales en laboratorios | `Condiciones ambientales en laboratorios` | (sin respuesta), Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| TECNOLOGÍAS DE INFORMACIÓN | Software especializado empleado en la carrera | `Software especializado empleado en la carrera` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Portal web de la Universidad (Mi Ulima) | `Portal web de la Universidad (Mi Ulima)` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Aula virtual | `Aula virtual` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Conexión Wi-Fi en el campus | `Conexión Wi-Fi en el campus` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Soporte técnico del sistema informático | `Soporte técnico del sistema informático` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| SATISFACCIÓN GLOBAL | Empleabilidad, vinculación y ALUMNI | `Empleabilidad, vinculación y ALUMNI` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Calidad de la formación académica | `Calidad de la formación académica` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | La carrera | `La carrera` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | La Universidad de Lima | `La Universidad de Lima` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Recomiendas la Universidad de Lima | `Recomiendas la Universidad de Lima` | 0, 10, 2, 3, 4, 5, 6, 7, 8, 9 |

> \* Las opciones listadas son las que **aparecieron** en el período, no siempre el catálogo completo:
> `Carrera` trae 12 valores en 2025-2 y 14 en 2026-1, y `Claridad de los recursos académicos` trae 1 valor
> en 2025-2 (las demás opciones quedaron sin respuesta en ese período).

Notas de Pregrado:

- La sección SATISFACCIÓN GLOBAL incluye `Calidad de la formación académica` (en Graduados esa misma
  pregunta va en SERVICIOS ACADÉMICOS).
- Pregrado **no** tiene las secciones PLANA DOCENTE ni DESARROLLO PROFESIONAL, ni la pregunta
  `Exigencia académica` (sí las tiene Graduados).

### Graduados — GRADUADOS + PREGRADO (2026)

48 preguntas = las 33 de Pregrado (todas, sin faltar ninguna) + 15 propias (comprobado).

| Sección | Pregunta del formulario | Columna publicada | Opciones en los datos* |
| --- | --- | --- | --- |
| DATOS PERSONALES | Carrera | `Carrera` | Administración, Arquitectura, Comunicación, Contabilidad y Finanzas, Derecho, Economía, Ingeniería Ambiental, Ingeniería Civil, Ingeniería Industrial, Ingeniería de Sistemas, Negocios Internacionales, Psicología |
|  | Situación laboral | `Situación laboral` | En búsqueda de empleo, No disponible para trabajar, Prácticas pre - profesionales, Prácticas profesionales, Trabajador dependiente, Trabajador independiente |
|  | Tiempo laboral | `Tiempo laboral` | (sin respuesta), Tiempo completo, Tiempo parcial |
| SERVICIOS ACADÉMICOS | Perfil del egreso de la carrera | `Perfil del egreso de la carrera` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Plan curricular y perfil de egreso | `Plan curricular y perfil de egreso` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Cursos del programa y contenidos | `Cursos del programa y contenidos` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Calidad de la enseñanza en la carrera | `Calidad de la enseñanza en la carrera` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Claridad de los recursos académicos | `Claridad de los recursos académicos` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Calidad de la formación académica | `Calidad de la formación académica` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Exigencia académica | `Exigencia académica` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Evaluación del aprendizaje | `Evaluación del aprendizaje` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Intercambio estudiantil | `Intercambio estudiantil` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| PLANA DOCENTE | Transmisión de conocimientos | `Transmisión de conocimientos` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Transmisión de experiencias | `Transmisión de experiencias` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Metodologías | `Metodologías` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Conocimientos actualizados | `Conocimientos actualizados` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Compromiso | `Compromiso` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Retroalimentación | `Retroalimentación` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Disponibilidad para asesorías | `Disponibilidad para asesorías` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Cumplimiento de normas y programas | `Cumplimiento de normas y programas` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
| DESARROLLO PROFESIONAL | Habilidades para trabajar en equipo | `Habilidades para trabajar en equipo` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Habilidades de comunicación | `Habilidades de comunicación` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Habilidades para aportar nuevas ideas | `Habilidades para aportar nuevas ideas` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Mejora en perspectivas de empleo | `Mejora en perspectivas de empleo` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| SERVICIOS AL ESTUDIANTE | Información sobre el récord académico | `Información sobre el récord académico` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Material bibliográfico en la biblioteca | `Material bibliográfico en la biblioteca` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Atención del personal administrativo | `Atención del personal administrativo` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Procedimientos administrativos | `Procedimientos administrativos` | (sin respuesta), Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Ayuda financiera | `Ayuda financiera` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Servicio médico y su infraestructura | `Servicio médico y su infraestructura` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Servicio de atención psicopedagógica | `Servicio de atención psicopedagógica` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Talleres de actividades artísticas y culturales | `Talleres de actividades artísticas y culturales` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Actividades deportivas | `Actividades deportivas` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Empleabilidad, vinculación y ALUMNI | `Empleabilidad, vinculación y ALUMNI` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| RECURSOS E INFRAESTRUCTURA | Aulas de clase | `Aulas de clase` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Ambientes y salas para estudio | `Ambientes y salas para estudio` | Insatisfecho, Muy satisfecho, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Equipamiento tecnológico en laboratorios | `Equipamiento tecnológico en laboratorios` | (sin respuesta), Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Condiciones ambientales en laboratorios | `Condiciones ambientales en laboratorios` | (sin respuesta), Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
| TECNOLOGÍAS DE INFORMACIÓN | Software especializado empleado en la carrera | `Software especializado empleado en la carrera` | (sin respuesta), Insatisfecho, Muy satisfecho, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Portal web de la Universidad (Mi Ulima) | `Portal web de la Universidad (Mi Ulima)` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Aula virtual | `Aula virtual` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Conexión Wi-Fi en el campus | `Conexión Wi-Fi en el campus` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
|  | Soporte técnico del sistema informático | `Soporte técnico del sistema informático` | Insatisfecho, Muy satisfecho, No conozco, No utilizo, Satisfecho, Totalmente insatisfecho, Totalmente satisfecho |
| SATISFACCIÓN GLOBAL | La carrera | `La carrera` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | La Universidad de Lima | `La Universidad de Lima` | Insatisfecho, Muy satisfecho, Satisfecho, Totalmente satisfecho |
|  | Recomiendas la Universidad de Lima | `Recomiendas la Universidad de Lima` | 10, 3, 4, 5, 6, 7, 8, 9 |

Las 15 propias de Graduados: `Situación laboral`, `Tiempo laboral`, `Exigencia académica`,
las 8 de la sección PLANA DOCENTE y las 4 de DESARROLLO PROFESIONAL.

### Saltos y preguntas anidadas

| Pregunta o caso | Cómo se comporta | Comprobación |
| --- | --- | --- |
| ¿Cuál es el tiempo dedicado a tu trabajo? | Solo se les pregunta a quienes trabajan (`Trabajador dependiente` o `Trabajador independiente`) | 598 respuestas: 322 trabajan y las 276 restantes quedaron en blanco |
| El perfil de egreso de tu carrera | La pregunta y su columna son una sola, pero el **texto del perfil cambia según la carrera** (14 bloques en el formulario) | El formulario trae un bloque por carrera, todos bajo el encabezado "Sabiendo que el perfil de egreso es:" |
| No utilizo / No conozco | Solo existen como opción en algunas preguntas | Pregrado 2026-1: 15 columnas con `No utilizo` y 15 con `No conozco`; Graduados 2026: 13 y 11 |
| ¿Qué ciclo es el que cursas? | Solo en Pregrado (12 ciclos) | En Graduados la columna `Ciclo` existe con un solo valor: no es pregunta del formulario |

### Columnas que no son preguntas

`Facultad` (Pregrado y Graduados) y `Ciclo` en Graduados no salen del formulario: las deriva el ETL.
El comentario libre (columna `Comentario NPS` del ETL, máximo 100 caracteres) no se publica en
`respuestas.json`: se analiza y aparece en `sentimiento.json` (`comentarios`).

## Headers críticos (por nivel)

Obligatorias siempre: `ID de respuesta`, `Net Promoter Score (de un total de 10)`, `La Universidad de Lima`.
Más la columna de carrera propia de cada nivel (ver *Columna de identidad por nivel*).
Las cabeceras completas de cada encuesta salen de su declaración en
`zoho-survey/scripts/lib/config.py` (`PREGUNTAS_POR_NIVEL` / `PREGUNTAS_FORMULARIO`),
derivadas por `cabeceras_de()` de `zoho-survey/scripts/zoho_a_csv.py`. Solo los niveles
que aún no declaran sus preguntas (egresados y empleadores) conservan su lista literal
en `CABECERAS_POR_NIVEL`; si Zoho agrega o quita preguntas, se actualiza la declaración.

> **Discrepancia documentada (no automatizar):** el validador exige la columna de carrera también para **empleadores**, idéntico a `build_json.py`, aunque la especificación original de empleadores podría no incluirla. Mantiene coherrencia con el ETL; revisar con el owner si se debe aflojar para `employers`.

#

## Límites

| Regla | Valor (cliente + server) |
| --- | --- |
| Archivos por upload | 1–10 |
| Tamaño por archivo | ≤ 5 MB |
| Tamaño total | ≤ 50 MB |
| Mismo nombre + mismo hash | ❌ error (duplicado) |
| Mismo hash, nombre distinto | ⚠️ advertencia (no bloquea) |
| Codificación | UTF-8; fallback Latin-1 |

#

## PII

- **IP / User-Agent / URL de encuesta**: redimidos por `sanitize_csv_pii.py` antes del ETL (no llegan a los motores IA ni a Pages).
- **Comentario NPS**: ofuscado con `ofuscar_pii_para_llm` antes de enviarlo a los motores IA (Fase 3.5).
- **Nunca** se commitean: `data/` está en `.gitignore`; el Release temporal se elimina tras procesar.

## Salida JSON v2.0

El pipeline genera hasta 11 archivos por periodo en `zoho-survey/students/{level}/{period}/json/` y `zoho-survey/students/{level}/{period}/intermediate/`.

| Archivo | Ubicacion | Tipo | Version | Estado | Schema |
| --- | --- | --- | --- | --- | --- |
| `dashboard_data.json` | `json/` | object | `"2.1"` | requerido | `dashboard_data.schema.json` |
| `dimensiones.json` | `json/` | array | implicita | requerido | `dimensiones.schema.json` |
| `filtros.json` | `json/` | object | `"2.1"` | requerido | `filtros.schema.json` |
| `resumenes.json` | `json/` | objeto | `"1.1"` | requerido | `resumenes.schema.json` (+ 5 schemas, uno por parte) |
| `sentimiento.json` | `json/` | object | `"3.0"` | requerido | `sentimiento.schema.json` |
| `fragmentos_nps.json` | `intermediate/` | array | implicita | intermedio ETL | sin schema formal |
| `dataset_cualitativo.json` | `intermediate/` | object | implicita | intermedio ETL | `dataset_cualitativo.schema.json` |

> **Nota sobre `fragmentos_nps.json` y `dataset_cualitativo.json`:** Son archivos intermedios del ETL consumidos internamente por `build_json.py` para producir `sentimiento.json`. El frontend no los consume directamente. `dataset_cualitativo.json` tiene schema formal (`dataset_cualitativo.schema.json`, validación manual opcional); `fragmentos_nps.json` no tiene schema formal porque es un dato de trabajo sin consumidores externos.

> **Umbral fail-closed de calidad (C-1):** `metadata` incluye `fallos_api`, `intentos_api` y `tasa_fallos_api`. Si `tasa_fallos_api` supera `IA_CUALITATIVO_MAX_FALLOS_API_PCT` (default 20%, con muestra mínima de 10 intentos), el ETL **aborta** y no escribe `sentimiento.json` para ese periodo: los indicadores cualitativos no son representativos y no deben publicarse.

Los cinco resúmenes llegan juntos en `resumenes.json` y cada parte se valida contra su schema; ya no hay archivos legacy por período.

## Convencion de claves NPS

El ETL produce todas las claves NPS en **minúsculas**: `promotores`, `pasivos`, `detractores`. Esta es la convencion canonica del contrato.

El frontend (`dashboard.js`) acepta ambos casings via nullish coalescing (`nps.Promotores ?? nps.promotores ?? 0`) por compatibilidad backward con periodos antiguos. **Los nuevos periodos siempre se generan en minúsculas.**

El CSAT mantiene las claves capitalizadas (`Totalmente satisfecho`, etc.) porque provienen directamente del catálogo de respuestas Zoho Survey (`RESPUESTAS_TEXTO` en `lib/config.py`).

## Convención de formato numérico (presentación)

Contrato de **presentación** aplicable a TODO número visible en el frontend (dashboard, portal, análisis cualitativo, KPIs, tooltips, leyendas, tablas y gráficos SVG). No depende de la función que lo genere: una misma regla rige enteros, decimales, porcentajes, NPS, CSAT, promedios, cantidades y cualquier otro valor numérico mostrado al usuario.

> **Fuente de verdad:** Las funciones canónicas son `window.SurveyFormatters` en `zoho-survey/shared/js/utils/formatters.js` (`formatInteger`, `formatDecimal`, `formatPercent`, `formatPctSimple`, `formatPctDecimal`, `formatScore`). Todo formato numérico visible debe pasar por ellas. NO se debe interpolar números con `toFixed()`, `toLocaleString()`, `Math.round() + '%'` o concatenación directa en el HTML renderizado.

#

## Reglas

1. **Enteros:** SIN separador de miles. Locale `es-PE` con `useGrouping: false`.
   - Incorrecto: `1,000`, `10,000`
   - Correcto: `1000`, `10000`
   - Función: `formatInteger(n)`

2. **Decimales:** separador decimal = COMA (nunca punto).
   - Incorrecto: `99.99`
   - Correcto: `99,99`
   - Función: `formatDecimal(n, digits)`

3. **Precisión decimal:** SIEMPRE exactamente 2 decimales cuando el valor es conceptualmente decimal y se muestra.
   - Incorrecto: `99,9`, `100` (cuando corresponde mostrar decimales)
   - Correcto: `99,90`, `100,00`
   - Función: `formatDecimal(n, 2)`, `formatPercent(n, 2)`, `formatPctSimple(v, t)`, `formatPctDecimal(v, t)`

4. **Porcentajes:** coma decimal + 2 decimales + UN ESPACIO entre el número y el signo `%`.
   - Incorrecto: `99.99%`, `99,99%`, `99,9 %`
   - Correcto: `99,99 %`
   - Funciones: `formatPercent(n, 2)`, `formatPctSimple(v, t)`, `formatPctDecimal(v, t)` (todas incluyen el espacio)

#

## invariantes de validación (manual)

- Ningún porcentaje visible debe terminar en `%` sin espacio previo.
- Ningún decimal visible debe usar punto (`.`) como separador.
- Ningún entero visible debe contener separador de miles (`,` o `.`).
- Cualquier `toFixed()`/`Math.round()`/`toLocaleString()` en HTML renderizado es una violación a menos que sea exclusivamente para ancho CSS (donde el estándar exige punto y sin espacio).

## `dashboard_data.json`

Contiene agregados globales, hallazgos y distribuciones NPS/CSAT.

Schema: `zoho-survey/scripts/schemas/dashboard_data.schema.json` (Draft-07, `additionalProperties: false`).

Ejemplo real (undergraduate 2026-1):

```json
{
  "version": "2.1",
  "preguntas": [
    { "id": "carrera", "nombre": "Carrera", "tipo": "agrupacion", "escala": "" },
    { "id": "csat_universidad", "nombre": "La Universidad de Lima", "tipo": "medida", "escala": "CSAT" }
  ],
  "resumen": {
    "encuestas": 4239,
    "carreras": 14,
    "facultades": 7,
    "fecha_inicio": "2026-05-11",
    "fecha_fin": "2026-06-17",
    "dias": 38,
    "dias_recoleccion": 26,
    "año": 2026,
    "periodo": "2026-1",
    "nps": {
      "score": 72.61,
      "promotores": 3231,
      "pasivos": 855,
      "detractores": 153,
      "total": 4239
    },
    "csat": {
      "score": 97.85,
      "t3b": 4148,
      "total": 4239,
      "t2b": 3087,
      "t2b_pct": 72.82,
      "ponderado": 82.58079735786743
    }
  },
  "hallazgos": {
    "csat_pct": 97,
    "nps_score": 72,
    "nps_tipo": "Excelente",
    "nps_etapas": {
      "Avanzado": 69.97,
      "Inicial": 73.61,
      "Intermedio": 75.78
    },
    "tendencia": "disminuye",
    "delta": 3,
    "top_dimensiones": [
      { "name": "Perfil del egreso de la carrera", "score": 96.99 }
    ],
    "top_facultades": [
      { "name": "Facultad de Ingeniería", "score": 98.53 }
    ]
  },
  "nps": {
    "promotores": 3231,
    "pasivos": 855,
    "detractores": 153,
    "score": 72.61
  },
  "csat": {
    "Totalmente satisfecho": 1806,
    "Muy satisfecho": 1281,
    "Satisfecho": 1061,
    "Insatisfecho": 75,
    "Totalmente insatisfecho": 16,
    "No utilizo": 0,
    "No conozco": 0
  }
}
```

**`preguntas` (desde la versión 2.1):** la declaración compacta de cada columna publicada —
`id`, `nombre`, `tipo` y `escala`—, la misma que publica `respuestas.json` del período, pero **sin el
texto largo de la pregunta** para que el archivo siga pesando pocos KB. Es lo que permite que los
módulos del portal sepan qué es cada columna (si es una `medida`, una `agrupacion`, una `fecha` o un
`identificador`) sin comparar por nombre escrito a mano. Los `dashboard_data.json` de la versión 2.0
(anteriores a este cambio) no traen el bloque y siguen siendo válidos. Invariante: si el archivo trae
`preguntas`, sus `id` coinciden con los del `respuestas.json` del mismo período
(`validate_preguntas_cruzadas`).

#

## Enums

- `hallazgos.nps_tipo`: `Excelente` (≥60), `Bueno` (≥30), `Regular` (≥0), `Pésimo` (<0).
- `hallazgos.tendencia`: `disminuye`, `aumenta`, `se mantiene` (comparando NPS Inicial vs Avanzado).
- `resumen.empleabilidad`: solo aparece cuando la encuesta lo soporta (graduados). Requiere `score`, `empleados`, `total`.
- `resumen.año`: entero (ej. `2026`), **no** string.

> **Nota sobre la pregunta abierta NPS**: La pregunta "Explica con tus palabras, las razones de la calificación"
> es **opcional**. No todos los encuestados responden. Por ello:
> - `total_respuestas` = total de filas en el CSV (todas las respuestas recibidas).
> - `total_con_comentario` = filas donde la columna de comentario tiene texto no vacío (puede ser < `total_respuestas`).
> - `total_analizados` = comentarios que pasaron el filtro de ruido y fueron procesados por la IA.
> - `comentarios_invalidos` = comentarios con texto que la IA marcó como inválidos.
>
> Cuando `total_con_comentario = 0`, la sección Cualitativo del dashboard debe ocultarse
> (no mostrar "0 comentarios analizados").
- `resumen.periodo`: string identificador del periodo (`"2026-1"` o `"2026"`).
- `resumen.csat.t2b` / `t2b_pct` / `ponderado`: indicadores extendidos de satisfacción (Top 2 Box y Promedio Ponderado). **Opcionales** por compatibilidad con periodos generados antes de su incorporación; los nuevos periodos siempre los incluyen. El frontend deriva ambos desde la distribución `csat` top-level como fallback vía `utils/metrics.js` (gemelo JS de `lib/metrics.py`). `t2b_pct` se redondea a 2 decimales (mismo patrón que `score`); `ponderado` se almacena sin redondear (precisión interna, redondeo solo al mostrar). Invariante: `t2b ≤ t3b ≤ total`. Pesos Likert: `[5,4,3,2,1]` alineados a `RESPUESTAS_TEXTO[:5]` (definidos en `lib/config.py` y `config/constants.js`).

## `dimensiones.json`

Array de resultados por facultad, carrera, ciclo, categoria y dimension.

Schema: `zoho-survey/scripts/schemas/dimensiones.schema.json`.

Cada fila incluye:

- `facultad`, `carrera`, `ciclo`
- `categoria`, `dimension`
- `t3b`, `b2b`, `total`, `t3b_pct`, `no_utilizo`, `no_conozco` (minúsculas)
- `Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho` (capitalizadas)
- `No utilizo`, `No conozco` (capitalizadas)

Invariante: debe existir al menos una fila con `total > 0`.

> **Nota:** estos cinco campos del borde de la escala **sí se publican y no se pueden retirar sin
> quitar la barra de visibilidad de cada dimensión**: esa barra dibuja tres segmentos («conocido»,
> «no-utilizo» y «no-conozco») usando `no_utilizo` y `no_conozco` (minúsculas), y el `b2b` es la suma
> de `Insatisfecho` + `Totalmente insatisfecho`. El frontend compone los nombres de esos segmentos en
> tiempo de ejecución, así que no aparecen como texto literal en el código: una búsqueda por nombre
> no los encuentra. Queda documentado en el CHANGELOG del 2026-09-29.
## `filtros.json`

Schema: `zoho-survey/scripts/schemas/filtros.schema.json`.

Claves requeridas:

- `version` (`"2.1"`)
- `has_ciclo` (booleano)
- `facultades` (lista no vacía)
- `carreras` (lista no vacía)
- `ciclos` (lista, puede ser vacía cuando `has_ciclo=false`)
- `facultad_carrera` (objeto no vacío)
- `preguntas` (desde la versión 2.1; declaración compacta de cada columna publicada, con los mismos
  `id` que `respuestas.json` del período)

Invariante: `facultad_carrera` debe mapear TODAS las facultades listadas en `facultades`. Y, si el
archivo trae `preguntas`, sus `id` coinciden con los del `respuestas.json` del mismo período.

## `resumenes.json`

Schema del archivo completo: `zoho-survey/scripts/schemas/resumenes.schema.json` (además, cada parte
se valida contra su propio schema; ver más abajo).

Un solo archivo por período con los cinco resúmenes que antes iban sueltos: `ids` (conteo de
respuestas por facultad, carrera y ciclo), `nps_carrera`, `csat_carrera`, `nps_ciclo_carrera` y
`csat_ciclo_carrera`. Desde la versión 1.1 trae además el bloque `preguntas` (la declaración compacta
de cada columna publicada, con los mismos `id` que `respuestas.json` del período); los archivos 1.0
anteriores no lo llevan y siguen siendo válidos.

```json
{
  "version": "1.1",
  "preguntas": [
    { "id": "carrera", "nombre": "Carrera", "tipo": "agrupacion", "escala": "" }
  ],
  "ids": [ ... ],
  "nps_carrera": [ ... ],
  "csat_carrera": [ ... ],
  "nps_ciclo_carrera": [ ... ],
  "csat_ciclo_carrera": [ ... ]
}
```

**Cada parte conserva su contrato formal**: el validador valida `ids` contra `ids.schema.json` y
cada tabla NPS/CSAT contra su schema (`nps_carrera.schema.json`, `csat_carrera.schema.json`,
`nps_ciclo_carrera.schema.json`, `csat_ciclo_carrera.schema.json`). Los cinco schemas se mantienen;
lo que desaparece son los cinco archivos.

**Invariantes:** las cinco partes son obligatorias y no pueden estar vacías; `ids` además cumple las
reglas de `validate_id_rows_invariants`. Si el archivo trae `preguntas`, sus `id` coinciden con los del
`respuestas.json` del mismo período.

**Por qué existe:** los tres cargadores del sitio (`dashboard.js`, `portal/portal-data.js` y
`portal/portal-preguntas.js`) pedían los cinco archivos por separado, seis peticiones por período
para datos que siempre se usan juntos. Ahora piden uno y lo reparten en memoria.

## `sentimiento.json`

Schema: `zoho-survey/scripts/schemas/sentimiento.schema.json`.

Claves requeridas a top-level (5):

- `version` (`"3.0"`)
- `resumen`
- `insights_ia`
- `topicos`
- `comentarios`

> **Nota:** `por_carrera`, `por_ciclo` y `distribucion_intensidad` ya no se publican: ningún módulo
> del frontend los lee. El análisis por carrera y por ciclo que sí se muestra sale de
> `dimensiones.json`, `nps_*` y `csat_*`.

`resumen` requiere:

- `total_respuestas`, `total_con_comentario`, `total_analizados`, `comentarios_invalidos`
- `distribucion_sentimiento` (objeto con `positivo`, `neutro`, `negativo`)
- `pasivos`, `detractores`, `nota` (string)

`insights_ia` requiere:

- `global` (string)
- `por_categoria_padre` (objeto con insights por categoría)

Cada tópico requiere:

- `topico`, `total_comentarios`, `positivos`, `negativos`, `neutros`

Cada comentario requiere:

- `id`, `carrera`, `facultad`, `ciclo`
- `nps_score` (0-10)
- `sentimiento` (enum: `positivo`, `negativo`, `neutro`)
- `intensidad` (1-5)
- `categoria`, `categoria_padre`
- `fragmento_original`, `fragmento_mostrar`
- `es_valido` (booleano)
- `motivo_invalidez` (string o `null` cuando `es_valido=true`)

Campos opcionales adicionales en comentarios (producidos por el ETL):

- `aspecto_normalizado`, `comentario_id_original`, `comentario_original`
- `fragmento_secuencia`, `es_fragmento`

## `respuestas.json`

**La tabla de respuestas del período: una fila por respuesta, con números en vez de texto.** Es la
hoja que usa el asistente del ítem 1.9 para filtrar y contar: permite contestar cruces entre dos o
más preguntas, que por definición no se pueden precalcular.

```json
{
  "version": "1.1",
  "nivel": "undergraduate",
  "periodo": "2026-1",
  "respuestas": 4239,
  "cabeceras": ["Carrera", "Ciclo", "..."],
  "preguntas": [
    { "id": "carrera", "nombre": "Carrera", "tipo": "agrupacion", "pregunta": "¿Qué carrera profesional estudias?", "escala": "" },
    { "id": "csat_universidad", "nombre": "La Universidad de Lima", "tipo": "medida", "pregunta": "La Universidad de Lima", "escala": "CSAT" }
  ],
  "opciones": { "Carrera": ["Administración", "..."], "Ciclo": ["1", "..."] },
  "filas": [[0, 3, 1, ...], [1, 3, 0, ...]],
  "ids": ["...", "..."],
  "fechas": ["2026-04-16", "..."],
  "excluidas": [{ "pregunta": "Comentario NPS", "motivo": "no es una pregunta" }]
}
```

- **`cabeceras`**: las preguntas que se pueden filtrar, en orden. Cada una tiene sus opciones en
  `opciones` (una sola vez para todas las filas) y un `(sin respuesta)` al inicio cuando la pregunta
  se puede dejar en blanco (los saltos de la encuesta se cuentan, no se esconden).
- **`preguntas`** (desde la versión 1.1): la declaración de cada columna publicada, la misma que vive
  en `lib/config.py` (`PREGUNTAS_POR_NIVEL`). Cada entrada trae `id` (estable, el que debe usar el
  código en vez del nombre), `nombre` (lo que se publica y se muestra), `tipo` (`medida`,
  `agrupacion`, `fecha` o `identificador`), `pregunta` (el texto del cuestionario) y `escala` (`CSAT`
  o `NPS`, solo en las medidas). Los archivos que quedaron en la versión 1.0 (anteriores a este
  cambio) no traen el bloque y siguen siendo válidos.
- **`filas`**: un número por pregunta y por respuesta; ese número apunta a la opción. Una fila por
  respuesta, en el mismo orden que `ids` y `fechas`.
- **`ids`** enlaza cada fila con el análisis de los comentarios (`sentimiento.json` lleva el mismo
  identificador); **`fechas`** permite contar por día o por semana.
- **`excluidas`** deja constancia de lo que no entró y por qué: texto libre (más de 50 valores
  distintos), el comentario abierto, el estado del webhook y los campos que viajan aparte.

**Sin datos personales**: no hay nombre, correo, documento ni código de alumno; tampoco el texto de
la pregunta abierta, que vive en `sentimiento.json` ya analizado.

**Invariantes** (`validate_respuestas_invariants`): `respuestas` coincide con el número de filas; cada
fila tiene un valor por pregunta; cada valor apunta a una opción existente de esa pregunta; `ids` y
`fechas`, si están, tienen el mismo largo que las filas. Si el archivo trae `preguntas` (versión 1.1):
cada `id` es único y no vacío, cada `tipo` es válido, cada medida declara `escala`, y toda cabecera
publicada tiene su declaración.
## Responsabilidades Por Capa

| Capa | Responsabilidad |
| --- | --- |
| ETL Python (`build_json.py`) | Transformar CSV en JSON deterministico y validable contra schemas Draft-07. |
| JSON | Transportar datos precomputados, sin decisiones de layout. |
| Frontend JS | Consumir contratos y renderizar; no recalcular agregados del ETL. |
| Schemas Draft-07 | Fuente formal de tipos. El validador no debe ser mas permisivo que el schema. |
| Validador (`validate_generated_json.py`) | Aplicar schema + invariantes de negocio cruzadas. Fallar explicitamente ante cualquier rompimiento. |

## Invariantes de negocio (no expresables en JSON Schema)

- La suma de `total` en la parte `ids` de `resumenes.json` debe ser mayor a 0.
- `filtros.facultad_carrera` debe cubrir todas las facultades listadas en `filtros.facultades`.
- `dimensiones.json` debe contener al menos una fila con `total > 0`.
- `periodos.json` debe tener exactamente un item con `isNew: true`.
- Un nivel **sin datos publicados** puede tener `periodos.json` con una única entrada *marcadora*: `{"id":"proximamente","label":"Próximamente","url":"underconstruction.html","isNew":true}`. Esa entrada **no es un periodo real**: el validador la omite (no existe carpeta de periodo que validar) y el portal muestra "PÁGINA EN CONSTRUCCIÓN" en lugar del dashboard. El portal la identifica por `url` (`URL_PLACEHOLDER` en `zoho-survey/shared/js/portal/portal-data.js`); por eso, al publicar un periodo real, basta con que su entrada no apunte a `underconstruction.html`.
- NPS debe estar entre -100 y 100.
- CSAT debe estar entre 0 y 100.
- Los IDs de carrera en `filtros.json` deben coincidir con los usados por los JSON de NPS/CSAT.
- Si un resumido (`dashboard_data.json`, `filtros.json` o `resumenes.json`) trae el bloque `preguntas`,
  sus `id` deben coincidir con los del `respuestas.json` del mismo período.
- Los JSON generados no deben modificarse manualmente.
- Cambios incompatibles requieren actualizar el ETL, schemas, validador, frontend y este documento en el mismo PR.

## Deuda Tecnica De Contratos

- Los cinco resúmenes del período viven en `resumenes.json`; los cargadores piden un archivo en vez de cinco.
- `fragmentos_nps.json` y `dataset_cualitativo.json` no tienen schema formal porque son intermedios del ETL, no contratos públicos.
- Solo algunos objetos tienen version explicita (`"2.0"`, `"3.0"`); los arrays mantienen version implicita.
- El frontend acepta ambos casings para NPS por compatibilidad backward; los nuevos periodos siempre se generan en minúsculas.

---

## Reglas de nombres CSV (Fase 3.8.3) — CANON

Las secciones previas de Fase 3.8.2 sobre periodicidad estricta e `La Universidad de Lima` obligatoria están **OBSOLETAS**; esta sección prevalece. Quien aplica estas reglas es el ETL: `build_json.py` deriva el nivel y el periodo del nombre del archivo.

**Formato:** ENCUESTA DE SATISFACCIÓN {CATEGORÍA} [- NIVEL] [- PERIODO].csv

- CATEGORÍA: ESTUDIANTIL | GRADUADOS | POSGRADO | DOCENTES | EGRESADOS | NO DOCENTES | EMPLEADORES
- NIVEL: PREGRADO | POSGRADO (opcional en NO DOCENTES, que no lo lleva)
- PERIODO: OPCIONAL. 20XX (anual) o 20XX-1/20XX-2 (semestral). Varios CSV reales lo omiten (ej. NO DOCENTE 2026.csv)
- Separadores: espacio simple o guion son equivalentes
- Singular/plural: DOCENTE/DOCENTES y NO DOCENTE/NO DOCENTES son equivalentes

#

## Headers obligatorias por encuesta EXACTA

Siempre: ID de respuesta + Net Promoter Score (de un total de 10). Más la columna propia de carrera/programa/dependencia:

| Encuesta (CATEGORÍA + NIVEL) | Columna de carrera/programa/dependencia |
| --- | --- |
| ESTUDIANTIL + PREGRADO | ¿Qué carrera profesional estudias? |
| ESTUDIANTIL + POSGRADO | ¿Qué programa de posgrado estudias? |
| GRADUADOS + PREGRADO | ¿Qué carrera profesional estudiaste? |
| EGRESADOS + PREGRADO | ¿Qué carrera profesional estudiaste? |
| EGRESADOS + POSGRADO | ¿Qué programa de posgrado estudiaste? |
| DOCENTES + PREGRADO | ¿Qué carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima? |
| DOCENTES + POSGRADO | ¿Qué programa de posgrado dictas en la Universidad de Lima? |
| NO DOCENTES | ¿A qué dependencia perteneces? |
| EMPLEADORES + PREGRADO | ¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización? |
| EMPLEADORES + POSGRADO | ¿Cuál posgrado es el que procede el profesional de la Universidad de Lima contratado por su organización? |

> `La Universidad de Lima` NO es universal (CSAT): el ETL la detecta por encuesta. Los CSVs de referencia no se versionan en el repositorio (contienen datos personales); el contrato vive en este documento y en `zoho-survey/scripts/lib/config.py`.

> Nota EMPLEADORES (futura actualización): ENCUESTA DE SATISFACCIÓN EMPLEADORES tiene tipos PREGRADO y POSGRADO. Se está evaluando si el CSV es único para ambos niveles (misma fuente Zoho). Hasta definirse, el validador acepta ambos nombres y el ETL los trata como employers.

## Procesamiento ETL (Fase 2) — 7 categorias

build_json.py procesa las 7 categorias (no solo pregrado/graduados). Por nivel interno
(_detectar_nivel), resolver_config_etl (en lib/config.py) resuelve:

- Columna de identidad (carrera/programa/dependencia) -> renombrada a Carrera.
- CSAT: encuestas con La Universidad de Lima usan esa columna de texto (escala
  RESPUESTAS_TEXTO). Empleadores NO traen columna CSAT (ni texto ni CSAT Score,
  que esta vacia en los CSV reales) -> su objeto csat se genera con ceros (valido para el
  schema, pero sin datos de satisfaccion). Ver nota EMPLEADORES arriba.
- Ciclo: solo estudiantil pregrado lo trae; los demas usan NA.
- Facultad: pregrado/egresados-ug mapean via CARRERA_FACULTAD; los demas -> Otra.
- Dimensiones: pregrado/graduados usan CATEGORIA_DIMENSION_*. Los 5 niveles nuevos
  se auto-detectan: columnas cuyos valores son subconjunto de RESPUESTAS_TEXTO
  (escala Likert) se clasifican en categoria padre por palabra clave
  (clasificar_categoria_dimension). El schema de dimensiones.json no exige enum de
  categoria, por lo que cualquier etiqueta es valida.

## Contrato de `/api/interpretar` (asistente del portal)

Solo lo consume `zoho-survey/shared/js/portal/portal-preguntas.js`; no forma parte de los JSON por periodo.
Atiende **dos pasos**, según el campo `paso`:

| `paso` | Qué manda el portal | Qué devuelve la funcion |
| --- | --- | --- |
| `plan` | `{ paso, pregunta (<=300), contexto (<=8000), menu (<=40000) }` | `{ plan: { se_puede, periodos[], preguntas[], filtros[{pregunta, valores[]}], motivo } }` |
| `respuesta` | `{ paso, pregunta (<=300), bloques (<=20000) }` | `{ respuesta: "texto en español (<=1200)" }` |

- **`plan`**: el modelo dice **que datos hay que leer**. `periodos`, `preguntas` y `filtros` se copian del
  menu (nombres exactos); `se_puede: false` + `motivo` significa que la respuesta no esta en los datos.
  No escribe cifras.
- **`respuesta`**: el modelo **redacta** con los `bloques` que le manda el portal y cierra con una linea
  `Fuente: …`. El portal descarta la respuesta si trae alguna cifra que no este en los bloques.
- **`bloques`**: los arma el portal con los JSON publicados (repartos de una pregunta, NPS, satisfaccion,
  los tres mejores niveles, NPS y satisfaccion por carrera, facultad o ciclo, y las **dos lecturas de
  "trabajan"** —con practicas / solo trabajo formal— con el tiempo laboral de quienes trabajan, segun
  `VALORES_TRABAJO`/`VALORES_PRACTICA` de `constants.js`). Son la unica fuente de las cifras: **el modelo no
  calcula**.
- **`menu`**: las preguntas publicadas con sus opciones, de **todos** los periodos; nunca lleva cifras.
- **`contexto`**: sale de `zoho-survey/shared/config/asistente_contexto.json` (que es el proyecto, como estan
  los datos, como esta organizado el cuestionario, reglas y palabras coloquiales); la
  **conversacion reciente** viaja primero, para que ningun tope la recorte.
- Errores: `400` si falta la pregunta (menos de 3 letras); `502` si ningun modelo responde.
- Cadena de modelos: **Google `gemini-3.5-flash-lite`** (llave `GOOGLE_API_KEY`; corte a los 20 s) y, si
  falla, **NVIDIA** (llave `NVIDIA_API_KEY`): `nvidia/nemotron-3.5-lightning-30b-a3b` -> `z-ai/glm-5.3-flash`
  -> `poolside/laguna-xs-2.1` (corte a los 90 s). Si falta una llave, ese proveedor se omite.
- El paso `formulario` (el catalogo de operaciones) sigue en la funcion mientras se retira; el portal ya no
  lo usa.
