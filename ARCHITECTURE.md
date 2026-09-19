# Arquitectura Del Sistema De Encuestas De Satisfaccion

Este documento es la fuente canonica para entender la estructura tecnica de `survey-test`. Los contratos de datos viven en `CONTRACTS.md` y formalmente en `zoho-survey/scripts/schemas/*.schema.json`; las reglas para agentes viven en `AGENTS.md`.

## Mapa De Componentes

```mermaid
graph TD
    CSV[CSV de Zoho Survey] --> ETL[zoho-survey/scripts/build_json.py]
    ETL --> |genera| JSON[Contratos JSON por periodo]
    ETL --> |valida contra| SCHEMA[scripts/schemas/*.schema.json Draft-07]
    SCHEMA --> |cargado por| VAL[validate_generated_json.py]
    JSON --> PORTAL[zoho-survey/index.html + portal.js]
    PORTAL --> |navegacion multi-fase v5.0| DASH[dashboard.js o portal-survey.js]
    CSS[zoho-survey/shared/css] --> PORTAL
    JSON --> DASH
    CSV --> |hash| CACHE[.csv_hash<br/>detección de cambios]

    subgraph ETL Cualitativo IA [Motor IA — cadena: Google → NVIDIA → OpenCode]
        IA[lib/ia_cualitativo.py] --> |1.º| GOOGLE[Google Gemini API]
        IA --> |2.º a 5.º| NVIDIA[NVIDIA NIM API]
        IA --> |6.º| OPENCODE[OpenCode API]
        IAPROMPT[lib/prompts_cualitativo.py] --> IA
        IA --> |genera| DC2[dataset_cualitativo.json]
        DC2 --> ST2[sentimiento.json v3.0]
        IAGEN[lib/insights_generator.py] --> |síntesis determinista| ST2
    end
    ETL --> |cadena en IA_CUALITATIVO_CADENA; al menos una clave| IA

    subgraph Ingesta Web [Subir datos (Fase 3.8.2)]
        BROWSER[Browser GitHub Pages] -->|PAT owner (memoria)| GH[api.github.com]
        GH -->|1. Release DRAFT| REL[(Release temporal)]
        GH -->|2. PUT assets CSV| REL
        GH -->|3. repository_dispatch csv_upload| ACT[GitHub Actions]
        ACT -->|download| TEMP[data/temp/{upload_id}/]
        TEMP --> ETL
        ACT -->|DELETE release + rm temp| OK2[CSV procesado + borrado]
    end
```

## Estructura De Directorios

```text
survey-test/
├── .github/workflows/       # Workflows de CI/CD (build_zoho_survey.yml, tests.yml).
├── data/                    # CSVs de dev (solo local). .gitignore — NO se commitean. La ingesta web entra vía Release temporal, no acá.
├── docs/                    # Documentacion y guias del proyecto.
├── tests/                   # Mini-framework de pruebas unitarias en navegador.
├── zoho-survey/             # Aplicacion estatica principal.
│   ├── index.html           # Portal v5.0 publicado en GitHub Pages (multi-fase).
│   ├── health.html          # Pagina de health check de contratos JSON por periodo.
│   ├── shared/              # Recursos compartidos (CSS, JS, imagenes).
│   │   ├── css/             # Capas CSS (tokens, reset, layout, components, sections, loader) + portal/.
│   │   └── js/              # Modulos JS IIFE expuestos en window.Survey* + portal/ + upload (portal-upload.js, portal-upload-ui.js).
│   ├── template/            # Plantilla HTML para dashboards de periodo.
│   ├── scripts/             # ETL en Python, validacion de contratos, schemas y validacion de uploads (validate_upload_csv.py).
│   │   ├── lib/             # 12 modulos activos del ETL (motor legacy eliminado en v3.2.0).
│   │   ├── schemas/         # JSON Schemas Draft-07 (8 schemas formales).
│   │   ├── config/          # Configuracion estatica (contexto_universidad.json).
│   │   └── tests/           # Tests Python (10 modulos).
│   └── students/            # Dashboards y JSONs generados por nivel y periodo.
├── AGENTS.md                # Reglas y principios operativos para IA.
├── ARCHITECTURE.md          # Arquitectura tecnica global (este documento).
└── CONTRACTS.md             # Contratos CSV/JSON e invariantes de datos.
```

Para mayor detalle de responsabilidades:

| Ruta | Responsabilidad |
| --- | --- |
| `data/` | CSVs fuente exportados desde Zoho Survey (sanitizados en CI). |
| `zoho-survey/scripts/` | Scripts ETL, validacion de contratos y schemas de datos. |
| `zoho-survey/scripts/lib/` | Biblioteca de utilidades modularizadas del ETL (12 modulos activos). |
| `zoho-survey/scripts/schemas/` | JSON Schemas Draft-07 (fuente formal de tipos). |
| `zoho-survey/shared/js/` | Modulos compartidos del portal y dashboard (IIFE). |
| `zoho-survey/shared/css/` | Capas CSS modulares e imports del dashboard. |
| `zoho-survey/template/` | Template base HTML para la generacion automatica de periodos. |
| `zoho-survey/students/` | Dashboards y datos JSON generados de estudiantes. |
| `tests/` | Infraestructura y tests unitarios de navegador. |
| `.github/workflows/` | Automatizacion de build, validacion y deploy en GitHub Pages. |

## Pipeline De Datos

`zoho-survey/scripts/build_json.py` (856 lineas) transforma CSVs en contratos JSON estaticos. Delega en los siguientes submodulos en `scripts/lib/`:

### Modulos ETL (12 activos)

| Modulo | Lineas | Responsabilidad | Estado |
| --- | --- | --- | --- |
| `lib/config.py` | 485 | Mapeos de columnas, catalogos de negocio y constantes del motor IA. | Activo. |
| `lib/metrics.py` | 98 | Funciones puras de calculo de NPS (`calc_nps`), CSAT (`calc_csat`) y Promedio Ponderado. | Activo. |
| `lib/io_helper.py` | 227 | I/O seguro con encodings alternativos, formateo de fechas, hash para idempotencia, y redaccion PII (`enmascarar_pii`). | Activo. |
| `lib/ia_cualitativo.py` | 558 | Orquestador del analisis cualitativo por **cadena de motores** (Google -> NVIDIA -> OpenCode), retirado el motor unico DeepSeek en v3.9.0 (motor legacy eliminado en v3.2.0). Deduplicacion por ID de comentario (sin cache). Umbral fail-closed: aborta si mas del 20% de los comentarios falla por API (`IA_CUALITATIVO_MAX_FALLOS_API_PCT`). | Activo (requiere al menos una clave de motores IA). |
| `lib/prompts_cualitativo.py` | 779 | Prompts exactos para los motores IA (system + user). Fuente de verdad de los prompts usados en el ETL. | Activo (Fase IA). |
| `lib/insights_generator.py` | 262 | Generador de insights deterministas (sin LLM). Produce `insights_ia.global` y `insights_ia.por_categoria_padre` a partir de datos ya procesados. | Activo. |
| `lib/csv_exporter.py` | 169 | Exportacion de CSVs y ZIPs con proteccion formula injection y redaccion PII. ZIPs se guardan en `exports/` (no desplegados en Pages). | Activo. |
| `lib/dashboard_builder.py` | 57 | Ensamblado de `dashboard_data.json` desde metricas pre-calculadas. | Activo. |
| `lib/periodos_updater.py` | 58 | Actualizacion de `periodos.json` por nivel, marcando `isNew: true` en el mas reciente. | Activo. |
| `lib/ia_client.py` | 421 | Cliente de la cadena de motores (Google Gemini, NVIDIA NIM, OpenCode; urllib stdlib) con reintentos, backoff exponencial y limite de ritmo por motor. Orden y modelos configurables con `IA_CUALITATIVO_CADENA`. | Activo. |
| `lib/ia_filtro_ruido.py` | 147 | Pre-filtro de comentarios ruidosos (15 criterios regex) antes de llamar a los motores IA. | Activo. |
| `lib/ia_validacion.py` | 263 | Validacion y correccion de respuestas de los motores IA. Redaccion PII post-LLM. | Activo. |

**Modulos eliminados en v3.2.0** (motor legacy): `lib/nlp.py`, `lib/segmentacion_nps.py`, `lib/aspect_extraction.py`, `lib/sentiment_engine.py`, `lib/sentimiento_builder.py`, `lib/ia_cache.py` (eliminado en limpieza Fase 0; reemplazado por deduplicacion por ID).

### Flujo cualitativo (v3.9.0) — Cadena de motores IA

Desde v3.9.0 el ETL usa una **cadena ordenada de motores IA** (Google -> NVIDIA -> OpenCode),
configurable con `IA_CUALITATIVO_CADENA`: si un motor falla o no valida su respuesta, se pasa al
siguiente. Basta con que UNA clave de la cadena este configurada. El motor legacy
(spaCy + sentence-transformers) fue eliminado en v3.2.0.

```
Comentario NPS (CSV)
    |  se intentan los motores en orden hasta que uno responda (15 workers; 60 RPM por motor, 15 en NVIDIA)
    v
ia_cualitativo.py → motores de la cadena (Google / NVIDIA / OpenCode)
    |  ejecuta 5 tareas en conjunto con coherencia de contexto:
    |  1. Segmentación en Meaning Units (Bardin, 2011)
    |  2. Clasificación de sentimiento con reglas de sesgo por contexto NPS
    |  3. Asignación de intensidad (1-5)
    |  4. Clasificación contra taxonomía oficial (Braun & Clarke, 2006)
    |  5. Triangulación con calificación CSAT por dimensión (cross-reference)
    v
dataset_cualitativo.json (intermedio ETL)
    |
    v
sentimiento.json v3.0 + insights_ia (vía insights_generator.py)
```

**Deduplicacion por ID (sin cache IA):** en lugar de un cache oculto (`ia_cache.json`,
eliminado), `build_json.py` usa `sentimiento.json` como fuente de verdad: si un comentario
ya fue procesado (su ID esta en el JSON existente), se salta. Solo se envian a los motores IA los
comentarios NUEVOS. Para forzar reprocesamiento, borrar el `sentimiento.json` del periodo.

### Optimizacion: deteccion de cambios por hash

`build_json.py` implementa una optimizacion de skip: antes de procesar un CSV, calcula su hash SHA256 y lo compara con `.csv_hash` (guardado en el directorio de salida del periodo). Si el CSV no cambio desde el ultimo build Y todos los JSONs ya existen, se salta el reprocesamiento completo. Esto ahorra tiempo de CPU, llamadas a los motores IA (costos), y reescritura de archivos identicos. La huella es versionada (`ETL_OUTPUT_VERSION` + hash) para forzar reproceso controlado cuando cambian reglas internas.

### Outputs generados por periodo

El ETL genera archivos en `zoho-survey/students/{level}/{period}/`:

En `json/` (consumidos por frontend):
1. `dashboard_data.json` (v2.0) — KPIs ejecutivos, hallazgos, distribuciones NPS/CSAT.
2. `dimensiones.json` — agregados por facultad/carrera/ciclo/categoria/dimension.
3. `ids.json` — conteos por facultad/carrera/ciclo.
4. `nps_ciclo_carrera.json` — NPS por carrera y ciclo.
5. `csat_ciclo_carrera.json` — CSAT por carrera y ciclo.
6. `filtros.json` (v2.0) — opciones de filtros en cascada.
7. `sentimiento.json` (v3.0) — analisis cualitativo completo (consumido por frontend).
8. `nps_carrera.json` (legacy) — NPS por carrera (fallback para encuestas sin ciclo).
9. `csat_carrera.json` (legacy) — CSAT por carrera (fallback para encuestas sin ciclo).

En `intermediate/` (no consumidos por frontend):
10. `fragmentos_nps.json` — Meaning Units extraidas.
11. `dataset_cualitativo.json` — dataset detallado de fragmentos clasificados por los motores IA.

Adicionalmente:
- `json/.csv_hash` — huella versionada del CSV fuente (deteccion de cambios).
- `exports/` — ZIP con CSVs de auditoria (NO se despliegan en GitHub Pages).
- Por nivel: `periodos.json` (actualizado con `isNew: true` en el mas reciente).
- Por periodo: `index.html` copiado desde `template/` con `{{SHARED_PATH}}` reemplazado.

### Responsabilidades del ETL

- Normalizar columnas de Zoho Survey a nombres internos definidos en `lib/config.py`.
- Calcular agregados NPS, CSAT y empleabilidad cuando corresponde.
- Generar datos por facultad, carrera, ciclo y dimension.
- Enviar comentarios NPS a los motores IA para analisis cualitativo (sentimiento, intensidad, aspectos, categoria).
- Copiar el template del periodo y actualizar `periodos.json`.
- Mantener idempotencia: correr el script dos veces con la misma entrada debe producir el mismo resultado (con caveat: si el CSV no tiene fechas validas, se usa `pd.Timestamp.now()` como fallback, lo que rompe idempotencia en ese edge case).

Los esquemas, archivos requeridos e invariantes estan definidos en `CONTRACTS.md` y formalmente en `zoho-survey/scripts/schemas/*.schema.json` (8 schemas Draft-07).

## Validacion

`zoho-survey/scripts/validate_generated_json.py` valida los JSONs generados aplicando:

1. **JSON Schema Draft-07** (fuente formal de tipos): carga cada schema desde `scripts/schemas/` y ejecuta `Draft7Validator.iter_errors()`.
2. **Invariantes de negocio cruzadas** (no expresables en JSON Schema): suma total > 0, `facultad_carrera` cubre todas las facultades, al menos una fila con `total > 0` en `dimensiones.json`, exactamente un `isNew: true` en `periodos.json`.
3. **Validacion de HTML del periodo**: verifica que cada `index.html` contenga los fragmentos requeridos para la seccion cualitativa.

El validador NO debe ser mas permisivo que el schema. Si el schema rechaza, el validador rechaza.

## Frontend

La aplicacion es una SPA estatica en Vanilla JS, sin backend ni dependencias runtime.

### Portal (v5.0)

- `zoho-survey/index.html`: entrada publicada en GitHub Pages. Portal multi-fase (Estudiantes Pregrado/Posgrado, Graduados, Egresados, Docentes, Personal, Empleadores).
- `zoho-survey/shared/js/portal.js`: orquestador del portal (init, renderSidebar, navegacion de fases).
- `zoho-survey/shared/js/portal/`: 5 modulos de vista:
  - `portal-data.js` — carga y normalizacion de datos (SurveyPortalCore + SurveyPortalData).
  - `portal-dashboard.js` — tarjetas de satisfaccion por fase + barra NPS.
  - `portal-survey.js` — vista 1.0: KPIs, distribuciones CSAT/NPS, hallazgos, top3, radar, tabla detalle.
  - `portal-filters.js` — filtros en cascada por grupo (top3/radar/detalle).
  - `portal-radar.js` — grafico radar SVG del portal.
- NO usa iframes: renderiza directamente los JSONs de cada periodo.

### Dashboard (por periodo)

- `zoho-survey/template/index.html`: estructura HTML base de cada periodo.
- `zoho-survey/shared/js/dashboard.js`: orquestador principal (1.270 lineas).
- `zoho-survey/shared/js/config/constants.js`: metas, ciclos y constantes compartidas.
- `zoho-survey/shared/js/utils/`: `formatters.js` (formateo es-PE), `metrics.js` (calculos), `sanitizer.js` (XSS), `dom-helpers.js` (utilidades DOM).
- `zoho-survey/shared/js/components/`:
  - `tooltip.js`: Globos interactivos flotantes.
  - `progress-bar.js`: Barra superior de scroll de pagina.
  - `custom-select.js`: Selectores desplegables personalizados.
  - `multiselect.js`: Listas de seleccion multiple.
  - `filter-controller.js`: Coordinacion de filtros en cascada (Facultad/Carrera/Ciclo).
  - `radar-chart.js`: Grafico radar dinamico en SVG nativo (sin librerias externas).
  - `sentiment-view.js`: Renders cualitativos y comentarios NPS (1.036 lineas, v3.0.0).

Los modulos usan IIFE y exponen APIs globales `window.Survey*`. No usan ES Modules.

### Orden de carga de scripts

El orden de carga es critico y debe respetarse. Verificado por `scripts/tests/test_html_contract.py`.

**Template** (`template/index.html`, 13 scripts):

1. `config/constants.js` → 2. `utils/formatters.js` → 3. `utils/metrics.js` → 4. `utils/sanitizer.js` → 5. `utils/dom-helpers.js` → 6. `components/tooltip.js` → 7. `components/progress-bar.js` → 8. `components/custom-select.js` → 9. `components/multiselect.js` → 10. `components/filter-controller.js` → 11. `components/radar-chart.js` → 12. `components/sentiment-view.js` → 13. `dashboard.js`.

**Portal** (`index.html`, 14 scripts):

1. `config/constants.js` → 2. `utils/sanitizer.js` → 3. `components/tooltip.js` → 4. `utils/dom-helpers.js` → 5. `utils/formatters.js` → 6. `components/sentiment-view.js` → 7. `components/custom-select.js` → 8. `components/multiselect.js` → 9. `portal/portal-data.js` → 10. `portal/portal-dashboard.js` → 11. `portal/portal-radar.js` → 12. `portal/portal-filters.js` → 13. `portal/portal-survey.js` → 14. `portal.js`.

> **Advertencia:** `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` para evitar errores `TypeError: window.SurveyDomHelpers is undefined`.

## CSS

`zoho-survey/shared/css/` contiene:

- `tokens.css`: design tokens y variables CSS (colores institucionales, tipografia, espaciados, z-index, radios, sombras).
- `reset.css`: reset y utilidades base (`.skip-link`, `.sr-only`).
- `layout.css`: header, navegacion, grid y footer.
- `components.css`: KPIs, filtros, barras, tooltips y tablas (la capa mas grande).
- `sections.css`: secciones, responsive y ajustes visuales.
- `portal/`: `portal-base.css`, `portal-components.css`, `portal-sections.css` (estilos del portal v5.0).

`dashboard.css` fue eliminado en v3.2.0 (CSS muerto; los imports viven en las capas base).
`loader.css` fue eliminado en Fase 2 junto con `loader.js` (navegador de encuestas legacy, sin consumidores).

## Patrones Arquitectonicos

- **Datos precomputados**: el frontend consume JSON, no recalcula agregados que pertenecen al ETL.
- **Separacion de datos y vista**: los JSON no deben depender del layout visual.
- **Delegacion progresiva**: `dashboard.js` delega en modulos compartidos cuando existen; mantiene fallback inline para KPIs, distribuciones y tablas detalladas.
- **Compatibilidad backward**: los contratos legacy se conservan cuando todavia hay consumidores (ej. `nps_carrera.json`/`csat_carrera.json` como fallback para encuestas sin ciclo).
- **Degradacion controlada**: errores de carga JSON opcionales se tratan con `console.warn` sin romper toda la pagina. Endpoints criticos (`dashboard_data`, `filtros`, `dimensiones`) fallan rapido via `Promise.all`.
- **Resolucion de dependencias en runtime**: los modulos IIFE referencian `window.Survey*` al momento de uso, no al de carga. Esto permite que el dashboard funcione aunque falten modulos opcionales.

## Seguridad

- Cualquier contenido externo usado en HTML debe pasar por `escapeHTML()` o `sanitizeHTML()`.
- `sanitizeHTML()` permite solo una lista reducida de etiquetas necesarias para tooltips y textos enriquecidos: `br, strong, em, i, span, table, tr, td, th` (9 tags, sin atributos).
- No introducir dependencias runtime para sanitizacion sin justificar el costo operacional.

## Ingesta De Encuestas (Subir datos)

El portal (`zoho-survey/index.html`) incluye el botón **"Subir datos"**, que permite al propietario del repo enviar uno o varios CSV de encuesta directamente desde el navegador. La arquitectura (*Arquitectura A*, Fase 3.8.2) prioriza: **cero servicios externos**, **cero exposición de tokens públicos**, **cero CSV en el historial Git**, y **eliminación automática** tras procesar.

### Flujo

```mermaid
graph TD
    BROWSER[Browser — GitHub Pages] -->|PAT owner (memoria)| API[api.github.com]
    API -->|1. Release DRAFT (tag=upload_id)| REL[Release temporal]
    API -->|2. PUT assets CSV| REL
    API -->|3. repository_dispatch csv_upload| ACT[GitHub Actions]
    ACT -->|download| TMP[data/temp/{upload_id}/]
    TMP --> VAL(validate_upload_csv.py]
    VAL --> SAN[sanitize_csv_pii.py]
    SAN --> ETL[build_json.py]
    ETL --> DEPLOY[deploy Pages]
    DEPLOY -->|DELETE release + rm temp| OK[Done]
```

Pasos:
1. El owner abre el portal, introduce su PAT (**solo en memoria**) y selecciona CSVs. El validador cliente (`shared/js/portal-upload.js`) valida nombre/headers/tamaño, calcula SHA-256 y expone `window.SurveyUpload`.
2. `createRelease` crea un **Release temporal DRAFT** con `tag_name = upload_id` (UUID v4).
3. `uploadAsset` sube cada CSV como asset (**máx 10 archivos**, **5 MB c/u**, **50 MB total**).
4. `dispatchWorkflow` dispara `repository_dispatch` (`event_type=csv_upload`) con `client_payload={upload_id, release_id, files[]}`.
5. GitHub Actions (`build_zoho_survey.yml`, on `repository_dispatch[csv_upload]`) descarga los assets a `data/temp/{upload_id}/`, valida **server-side** (`validate_upload_csv.py`), los **sane** (`sanitize_csv_pii.py`), procesa (`build_json.py`), valida JSON, despliega a Pages y **elimina** el Release + los temporalos.

### Especificaciones de la carpeta temporal (Release)

| Característica | Valor |
| --- | --- |
| Tipo | GitHub Release (no GitHub Artifact; el API público no admite subida de artifacts) |
| Tag / ID | `upload_id` = UUID v4 generado en el navegador |
| Visibilidad durante el proceso | **DRAFT** (oculto). `GITHUB_TOKEN` del mismo repo accede a drafts sin problema |
| Límite por archivo | 5 MB (cliente) / 2 GB (asset GitHub) |
| Límite total por upload | 50 MB (cliente) |
| Cantidad de archivos | 1–10 |
| Codificación aceptada | UTF-8; fallback Latin-1 (`read_csv_robust`) |
| Aislamiento | cada `upload_id` → su propio Release + `data/temp/{upload_id}/` + su propio run |
| Eliminación | `DELETE /repos/{owner}/{repo}/releases/{id}` al finalizar con éxito (+ borrado del runner efímero) |
| Retención en fallo | el Release DRAFT persiste para recovery manual; el reintento usa **nuevo** upload_id (el tag UUID colisiona si se reusa) |
| Ventana de exposición | cero si se mantiene DRAFT; si se publica (`draft:false`), el asset es descargable públicamente hasta el cleanup (riesgo en repos públicos) |
| Ventana de PII | solo durante download→sanitize→ETL→delete; IP/UA/URL redimidos antes del ETL |

### Reglas de nombres CSV (Fase 3.8.3) — CANON

Fuente de verdad para el validador (`portal-upload.js` + `validate_upload_csv.py`). Las secciones previas sobre periodicidad estricta e `La Universidad de Lima` obligatoria están **OBSOLETAS**; esta sección prevalece.

**Formato:** `ENCUESTA DE SATISFACCIÓN {CATEGORÍA} [- NIVEL] [- PERIODO].csv`

- **CATEGORÍA**: `ESTUDIANTIL | GRADUADOS | POSGRADO | DOCENTES | EGRESADOS | NO DOCENTES | EMPLEADORES`
- **NIVEL**: `PREGRADO | POSGRADO` (opcional en `NO DOCENTES`, que no lo lleva)
- **PERIODO**: **opcional**. `20XX` (anual) o `20XX-1`/`20XX-2` (semestral). Varios CSV reales lo omiten (ej. `NO DOCENTE 2026.csv`)
- **Separadores**: espacio simple o guion son equivalentes
- **Singular/plural**: `DOCENTE`/`DOCENTES` y `NO DOCENTE`/`NO DOCENTES` son equivalentes

**Headers obligatorias por encuesta EXACTA** (no por nivel genérico). Siempre: `ID de respuesta` + `Net Promoter Score (de un total de 10)`. Más la columna propia de carrera/programa/dependencia:

| Encuesta (CATEGORÍA + NIVEL) | Columna de carrera/programa/dependencia |
| --- | --- |
| `ESTUDIANTIL` + `PREGRADO` | `¿Qué carrera profesional estudias?` |
| `ESTUDIANTIL` + `POSGRADO` | `¿Qué programa de posgrado estudias?` |
| `GRADUADOS` + `PREGRADO` | `¿Qué carrera profesional estudiaste?` |
| `EGRESADOS` + `PREGRADO` | `¿Qué carrera profesional estudiaste?` |
| `EGRESADOS` + `POSGRADO` | `¿Qué programa de posgrado estudiaste?` |
| `DOCENTES` + `PREGRADO` | `¿Qué carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?` |
| `DOCENTES` + `POSGRADO` | `¿Qué programa de posgrado dictas en la Universidad de Lima?` |
| `NO DOCENTES` | `¿A qué dependencia perteneces?` |
| `EMPLEADORES` + `PREGRADO` | `¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?` |
| `EMPLEADORES` + `POSGRADO` | `¿Cuál posgrado es el que procede el profesional de la Universidad de Lima contratado por su organización?`

> **`La Universidad de Lima` NO es universal** (CSAT). El ETL la detecta por encuesta; el validador no la exige. Los **10 CSVs de `PDF/` son la referencia canónica**.

> **Nota EMPLEADORES (futura actualización):** `ENCUESTA DE SATISFACCIÓN EMPLEADORES` tiene tipos `PREGRADO` y `POSGRADO`. Se está evaluando si el CSV es único para ambos niveles (misma fuente Zoho). Hasta definirse, el validador acepta ambos nombres y el ETL los trata como `employers`.

### Procesamiento ETL (Fase 2) - 7 categorias

build_json.py procesa las 7 categorias. resolver_config_etl (lib/config.py) resuelve por nivel la columna de identidad, CSAT (empleadores carece de ella -> ceros), ciclo (solo estudiantil pregrado) y facultad. Las dimensiones de los 5 niveles nuevos se auto-detectan por escala Likert (_detectar_dimensiones + clasificar_categoria_dimension).



> **Nota de hardening (Fase 3.8.3):** el flujo actual llama a `publishRelease` (`draft:false`) tras subir los assets. Para repos **públicos**, mantener el Release como DRAFT siempre y remover `publishRelease` — `GITHUB_TOKEN` accede a drafts del mismo repo.

### Auth

- **PAT del owner** (runtime; scopes mínimos `contents:write` + `actions:write`). NUNCA en localStorage/sessionStorage/logs; **nunca** pasa por GitHub Actions (que usa `GITHUB_TOKEN`).
- El navegador habla directo a `api.github.com` (CORS `*` soportado) → no hay backend ni Cloudflare de por medio.

### PII (puntos 2-6 de la auditoría Fase 3.7)

| # | Dónde puede aparecer | Estado en Arquitectura A |
| --- | --- | --- |
| 1 | Comentario NPS hacia los motores IA | 🔴 Ofuscado con `ofuscar_pii_para_llm` (Fase 3.5) antes del LLM |
| 2 | PII temporal (Release + runner) | 🟡 Draft + `data/temp/{upload_id}/` efímero; redimido en ETL |
| 3 | PII en Git | 🟢 Cero — `data/` gitignored; commit gated `!= repository_dispatch` |
| 4 | PII publicada en Pages | 🟢 Cero — solo JSON/HTML sanitizados |
| 5 | PII en logs de Actions | 🟢 Cero — los steps registran nombre de archivo, no contenido |
| 6 | PII en artifacts | 🟢 Cero — artifact publicado excluye `exports/` e `intermediate/` |

Los CSV de prueba con IP están cubiertos por `sanitize_csv_pii.py` (redime `Dirección IP`, `Agente Usuario`, `URL de la encuesta`). La única PII sensible identificada en la ingesta es la **dirección IP**.

### Concurrencia

- `concurrency.group: csv-upload-{upload_id}`, `cancel-in-progress: false` → uploads simultáneos **no** se cancelan.
- Cada upload: su propio Release (tag UUID) + su propio `data/temp/{upload_id}/` + su propio run.
- **Riesgo vigente:** el step `cp *.csv → data/` y `build_json.py` (que procesa todo `data/*.csv`) son globales; dos uploads paralelos pueden cruzarse. Fase futura: serializar (group único) o procesar solo `data/temp/{upload_id}/`.

### Errores y reintentos

- Upload/Actions falla → el Release DRAFT persiste; reintento con **nuevo** `upload_id`.
- Un motor falla o no valida su respuesta → se pasa al siguiente de la cadena; cada motor reintenta con backoff (`ia_client.py`).
- Validate/JSON/Deploy falla → job falla; cleanup no corre (gated `success()`); recovery manual.


## Deuda Tecnica Vigente

- La logica de ciclos esta externalizada en `SURVEY_CONFIG`, pero todavia no es dinamica por periodo.
- `nps_carrera.json` y `csat_carrera.json` son legacy; el frontend los usa como fallback para encuestas sin ciclo (`has_ciclo=false`, ej. Graduados).
- `postgraduate/` y los directorios de niveles sin datos (`alumni/`, `employers/`, `faculty-staff/`, `nonfaculty-staff/`) existen como placeholders sin datos procesados.
- El template `zoho-survey/template/index.html` no tiene version de contrato propia.
- El portal y el dashboard por periodo renderizan vistas similares con codigo parcialmente duplicado (`portal/*.js` vs `components/*.js` + `dashboard.js`); unificar en una sola fuente es deuda planificada.

## Convenciones

- **JavaScript**: camelCase para variables y funciones; APIs compartidas bajo `window.Survey*`.
- **CSS**: kebab-case para clases e IDs; usar tokens antes que valores hardcodeados.
- **Python**: snake_case para funciones y variables; constantes en UPPER_SNAKE_CASE.
- **JSON**: claves NPS en minusculas (`promotores`, `pasivos`, `detractores`); claves CSAT capitalizadas (`Totalmente satisfecho`, etc.) por provenir del catalogo Zoho.
- **Compatibilidad**: GitHub Pages, navegadores modernos y Python para ETL.
