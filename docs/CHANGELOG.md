# Changelog

Historial de cambios significativos del proyecto. Basado en [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Changed
- **Motor cualitativo**: el esquema "DeepSeek + respaldo NVIDIA" se reemplaza por una **cadena de motores** (OpenCode → Google → NVIDIA) que se intentan en orden; orden y modelos configurables sin tocar código con `IA_CUALITATIVO_CADENA`. Por defecto el **primer motor es `opencode:deepseek-v4.1-flash`** (el más actual, decisión del usuario); Google y los cuatro modelos de NVIDIA quedan como respaldo. El servicio DeepSeek se retira del proyecto (clave `DEEPSEEK_API_KEY` en desuso). Claves de la cadena: `GOOGLE_API_KEY`, `NVIDIA_API_KEY`, `OPENCODE_API_KEY` (basta una).
- `dataset_cualitativo.schema.json`: el campo `motor` admite `google`, `nvidia`, `opencode`, `filtro` (descartado por el pre-filtro de ruido) y `desconocido` (comentario reutilizado).
- Workflow de pruebas: Node.js 18 → 22 (LTS); deploy solo desde `main`.
- Documentación sincronizada con la cadena de motores (`ARCHITECTURE.md`, `CONTRACTS.md`, `DEV_ENVIRONMENT.md`, `SECURITY.md`, `docs/*`, `AGENTS.md`).

### Removed
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
