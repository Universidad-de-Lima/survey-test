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

## Contrato De Ingesta (Subir datos — Fase 3.8.2)

El owner sube CSVs con el botón "Subir datos" del portal. Nombre, estructura y tamaño se validan ANTES del ETL. Las reglas reales viven en `shared/js/portal-upload.js` (cliente) y `zoho-survey/scripts/validate_upload_csv.py` (server-side); este es el resumen humano.

### Formato de nombre

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

### Mapeo a nivel interno (== `build_json._detectar_nivel`)

| Substrings | Nivel interno |
| --- | --- |
| `ESTUDIANTIL` / `ESTUDIANTES` + `PREGRADO` | `undergraduate` |
| `ESTUDIANTIL` / `ESTUDIANTES` + `POSGRADO` | `postgraduate` |
| `GRADUADOS` | `graduate` |
| `EGRESADOS` + `POSGRADO` | `alumni-pg` (sin POSGRADO → `alumni-ug`) |
| `DOCENTES` + `POSGRADO` | `faculty-pg` (sin POSGRADO → `faculty-ug`) |
| `NO DOCENTES` | `nonfaculty` |
| `EMPLEADORES` | `employers` |

### Headers críticos (por nivel)

Obligatorias siempre: `ID de respuesta`, `Net Promoter Score (de un total de 10)`, `La Universidad de Lima`.
Más una de carrera:
- `graduate` → `¿Qué carrera profesional estudiaste?`
- resto → `¿Qué carrera profesional estudias?`

> **Discrepancia documentada (no automatizar):** el validador exige la columna de carrera también para **empleadores**, idéntico a `build_json.py`, aunque la especificación original de empleadores podría no incluirla. Mantiene coherrencia con el ETL; revisar con el owner si se debe aflojar para `employers`.

### Límites

| Regla | Valor (cliente + server) |
| --- | --- |
| Archivos por upload | 1–10 |
| Tamaño por archivo | ≤ 5 MB |
| Tamaño total | ≤ 50 MB |
| Mismo nombre + mismo hash | ❌ error (duplicado) |
| Mismo hash, nombre distinto | ⚠️ advertencia (no bloquea) |
| Codificación | UTF-8; fallback Latin-1 |

### PII

- **IP / User-Agent / URL de encuesta**: redimidos por `sanitize_csv_pii.py` antes del ETL (no llegan a los motores IA ni a Pages).
- **Comentario NPS**: ofuscado con `ofuscar_pii_para_llm` antes de enviarlo a los motores IA (Fase 3.5).
- **Nunca** se commitean: `data/` está en `.gitignore`; el Release temporal se elimina tras procesar.

## Salida JSON v2.0

El pipeline genera hasta 11 archivos por periodo en `zoho-survey/students/{level}/{period}/json/` y `zoho-survey/students/{level}/{period}/intermediate/`.

| Archivo | Ubicacion | Tipo | Version | Estado | Schema |
| --- | --- | --- | --- | --- | --- |
| `dashboard_data.json` | `json/` | object | `"2.0"` | requerido | `dashboard_data.schema.json` |
| `dimensiones.json` | `json/` | array | implicita | requerido | `dimensiones.schema.json` |
| `ids.json` | `json/` | array | implicita | requerido | `ids.schema.json` |
| `nps_ciclo_carrera.json` | `json/` | array | implicita | requerido | `nps_ciclo_carrera.schema.json` |
| `csat_ciclo_carrera.json` | `json/` | array | implicita | requerido | `csat_ciclo_carrera.schema.json` |
| `filtros.json` | `json/` | object | `"2.0"` | requerido | `filtros.schema.json` |
| `sentimiento.json` | `json/` | object | `"3.0"` | requerido | `sentimiento.schema.json` |
| `fragmentos_nps.json` | `intermediate/` | array | implicita | intermedio ETL | sin schema formal |
| `dataset_cualitativo.json` | `intermediate/` | object | implicita | intermedio ETL | `dataset_cualitativo.schema.json` |
| `nps_carrera.json` | `json/` | array | implicita | legacy opcional | sin schema formal |
| `csat_carrera.json` | `json/` | array | implicita | legacy opcional | sin schema formal |

> **Nota sobre `fragmentos_nps.json` y `dataset_cualitativo.json`:** Son archivos intermedios del ETL consumidos internamente por `build_json.py` para producir `sentimiento.json`. El frontend no los consume directamente. `dataset_cualitativo.json` tiene schema formal (`dataset_cualitativo.schema.json`, validación manual opcional); `fragmentos_nps.json` no tiene schema formal porque es un dato de trabajo sin consumidores externos.

> **Umbral fail-closed de calidad (C-1):** `metadata` incluye `fallos_api`, `intentos_api` y `tasa_fallos_api`. Si `tasa_fallos_api` supera `IA_CUALITATIVO_MAX_FALLOS_API_PCT` (default 20%, con muestra mínima de 10 intentos), el ETL **aborta** y no escribe `sentimiento.json` para ese periodo: los indicadores cualitativos no son representativos y no deben publicarse.

Los archivos legacy (`nps_carrera.json`, `csat_carrera.json`) se validan solo si existen; el validador emite advertencia. El frontend los carga como fallback síncrono solo en encuestas sin ciclos (`has_ciclo=false`, ej. graduados).

## Convencion de claves NPS

El ETL produce todas las claves NPS en **minúsculas**: `promotores`, `pasivos`, `detractores`. Esta es la convencion canonica del contrato.

El frontend (`dashboard.js`) acepta ambos casings via nullish coalescing (`nps.Promotores ?? nps.promotores ?? 0`) por compatibilidad backward con periodos antiguos. **Los nuevos periodos siempre se generan en minúsculas.**

El CSAT mantiene las claves capitalizadas (`Totalmente satisfecho`, etc.) porque provienen directamente del catálogo de respuestas Zoho Survey (`RESPUESTAS_TEXTO` en `lib/config.py`).

## Convención de formato numérico (presentación)

Contrato de **presentación** aplicable a TODO número visible en el frontend (dashboard, portal, análisis cualitativo, KPIs, tooltips, leyendas, tablas y gráficos SVG). No depende de la función que lo genere: una misma regla rige enteros, decimales, porcentajes, NPS, CSAT, promedios, cantidades y cualquier otro valor numérico mostrado al usuario.

> **Fuente de verdad:** Las funciones canónicas son `window.SurveyFormatters` en `zoho-survey/shared/js/utils/formatters.js` (`formatInteger`, `formatDecimal`, `formatPercent`, `formatPctSimple`, `formatPctDecimal`, `formatScore`). Todo formato numérico visible debe pasar por ellas. NO se debe interpolar números con `toFixed()`, `toLocaleString()`, `Math.round() + '%'` o concatenación directa en el HTML renderizado.

### Reglas

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

### invariantes de validación (manual)

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
  "version": "2.0",
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

### Enums

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

> **Nota:** El ETL produce ambos casings para `no_utilizo`/`No utilizo` y `no_conozco`/`No conozco` por compatibilidad. Los schemas los declaran ambos.

## `filtros.json`

Schema: `zoho-survey/scripts/schemas/filtros.schema.json`.

Claves requeridas:

- `version` (`"2.0"`)
- `has_ciclo` (booleano)
- `facultades` (lista no vacía)
- `carreras` (lista no vacía)
- `ciclos` (lista, puede ser vacía cuando `has_ciclo=false`)
- `facultad_carrera` (objeto no vacío)

Invariante: `facultad_carrera` debe mapear TODAS las facultades listadas en `facultades`.

## `ids.json`

Schema: `zoho-survey/scripts/schemas/ids.schema.json`.

Cada fila incluye:

- `facultad`
- `carrera`
- `ciclo`
- `total` (clave canónica; `count` se acepta como legacy en el validador pero el ETL siempre produce `total`)

Invariante: la suma total de `total` debe ser mayor a 0.

## `nps_ciclo_carrera.json` y `csat_ciclo_carrera.json`

Schemas: `nps_ciclo_carrera.schema.json`, `csat_ciclo_carrera.schema.json`.

Cada fila requiere `facultad`, `carrera` y `ciclo`.

NPS requiere (minúsculas, canónicas):

- `promotores`, `pasivos`, `detractores`, `score` (opcional)

CSAT requiere (capitalizadas, catálogo Zoho):

- `Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho`
- `No utilizo`, `No conozco` (opcionales)
- `score` (CSAT score calculado)

## `sentimiento.json`

Schema: `zoho-survey/scripts/schemas/sentimiento.schema.json`.

Claves requeridas a top-level (7):

- `version` (`"3.0"`)
- `resumen`
- `insights_ia`
- `topicos`
- `comentarios`
- `por_carrera`
- `por_ciclo`

`resumen` requiere:

- `total_respuestas`, `total_con_comentario`, `total_analizados`, `comentarios_invalidos`
- `distribucion_sentimiento` (objeto con `positivo`, `neutro`, `negativo`)
- `distribucion_intensidad` (objeto con `alta`, `media`, `baja`)
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

## Responsabilidades Por Capa

| Capa | Responsabilidad |
| --- | --- |
| ETL Python (`build_json.py`) | Transformar CSV en JSON deterministico y validable contra schemas Draft-07. |
| JSON | Transportar datos precomputados, sin decisiones de layout. |
| Frontend JS | Consumir contratos y renderizar; no recalcular agregados del ETL. |
| Schemas Draft-07 | Fuente formal de tipos. El validador no debe ser mas permisivo que el schema. |
| Validador (`validate_generated_json.py`) | Aplicar schema + invariantes de negocio cruzadas. Fallar explicitamente ante cualquier rompimiento. |

## Invariantes de negocio (no expresables en JSON Schema)

- La suma de `total` en `ids.json` debe ser mayor a 0.
- `filtros.facultad_carrera` debe cubrir todas las facultades listadas en `filtros.facultades`.
- `dimensiones.json` debe contener al menos una fila con `total > 0`.
- `periodos.json` debe tener exactamente un item con `isNew: true`.
- NPS debe estar entre -100 y 100.
- CSAT debe estar entre 0 y 100.
- Los IDs de carrera en `filtros.json` deben coincidir con los usados por los JSON de NPS/CSAT.
- Los JSON generados no deben modificarse manualmente.
- Cambios incompatibles requieren actualizar el ETL, schemas, validador, frontend y este documento en el mismo PR.

## Deuda Tecnica De Contratos

- `nps_carrera.json` y `csat_carrera.json` siguen como legacy (fallback de carga síncrona en encuestas sin ciclos).
- `fragmentos_nps.json` y `dataset_cualitativo.json` no tienen schema formal porque son intermedios del ETL, no contratos públicos.
- Solo algunos objetos tienen version explicita (`"2.0"`, `"3.0"`); los arrays mantienen version implicita.
- El frontend acepta ambos casings para NPS por compatibilidad backward; los nuevos periodos siempre se generan en minúsculas.

---

## Reglas de nombres CSV (Fase 3.8.3) — CANON

Fuente de verdad para el validador (portal-upload.js + validate_upload_csv.py). Las secciones previas de Fase 3.8.2 sobre periodicidad estricta e La Universidad de Lima obligatoria están OBSOLETAS; esta sección prevalece.

**Formato:** ENCUESTA DE SATISFACCIÓN {CATEGORÍA} [- NIVEL] [- PERIODO].csv

- CATEGORÍA: ESTUDIANTIL | GRADUADOS | POSGRADO | DOCENTES | EGRESADOS | NO DOCENTES | EMPLEADORES
- NIVEL: PREGRADO | POSGRADO (opcional en NO DOCENTES, que no lo lleva)
- PERIODO: OPCIONAL. 20XX (anual) o 20XX-1/20XX-2 (semestral). Varios CSV reales lo omiten (ej. NO DOCENTE 2026.csv)
- Separadores: espacio simple o guion son equivalentes
- Singular/plural: DOCENTE/DOCENTES y NO DOCENTE/NO DOCENTES son equivalentes

### Headers obligatorias por encuesta EXACTA

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

> La Universidad de Lima NO es universal (CSAT). El ETL la detecta por encuesta; el validador no la exige. Los 10 CSVs de PDF/ son la referencia canónica.

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
