# Reglas Para Agentes IA

Este archivo define reglas operativas obligatorias para agentes que inspeccionan o modifican el repositorio.

## Fuentes Canonicas

- `README.md`: entrada general y mapa documental.
- `ARCHITECTURE.md`: arquitectura tecnica, capas, modulos y deuda vigente.
- `CONTRACTS.md`: contratos CSV/JSON e invariantes de datos (version humana).
- `zoho-survey/scripts/schemas/*.schema.json`: contratos formales JSON Schema Draft-07 (fuente de tipos).
- `docs/developer-guide.md`: guia operativa corta para cambios comunes.
- `tests/README.md`: ejecucion y extension de tests.

No duplicar estas fuentes en nuevos documentos.

## Arquitectura Real (leer antes de modificar)

Antes de tocar codigo, comprender la arquitectura real (no la documentacion previa a v3.0):

### ETL Python (`zoho-survey/scripts/`)

- **`build_json.py`** (~953 lineas): orquestador del pipeline CSV → JSON.
- **`lib/`** contiene **13 modulos activos** (motor legacy eliminado en v3.2.0, `ia_cache.py` eliminado en Fase 0):
  - `config.py` — mapeos de columnas y catalogos de negocio.
  - `metrics.py` — `calc_nps`, `calc_csat` (funciones puras).
  - `io_helper.py` — I/O seguro, hash para idempotencia, `enmascarar_pii` (redaccion PII).
  - `csv_exporter.py` — exportacion de CSVs/ZIPs con proteccion formula injection y redaccion PII.
  - `dashboard_builder.py` — ensamblado de `dashboard_data.json`.
  - `periodos_updater.py` — actualizacion de `periodos.json`.
  - `ia_cualitativo.py` — orquestador del analisis cualitativo por **cadena de motores** (OpenCode → NVIDIA), orden y modelos configurables con `IA_CUALITATIVO_CADENA`.
  - `prompts_cualitativo.py` — prompts Bardin/Braun&Clarke para los motores IA.
  - `ia_client.py` — cliente HTTP de la cadena de motores (Google Gemini, NVIDIA NIM, OpenCode; urllib stdlib) con reintentos.
  - `ia_filtro_ruido.py` — pre-filtro de comentarios ruidosos (15 criterios regex).
  - `ia_validacion.py` — validacion de respuestas de los motores IA + redaccion PII post-LLM.
  - `insights_generator.py` — sintesis determinista de insights (sin LLM).
- **`schemas/`** contiene **8 JSON Schemas Draft-07** (incluye `dataset_cualitativo.schema.json`).

### Frontend JS (`zoho-survey/shared/js/`)

- **19 archivos JS** en `shared/js/` (modulos IIFE + capa `portal/`), con **18 simbolos `window.Survey*`**.
- **`dashboard.js`**: orquestador principal del dashboard por periodo.
- **Orden de carga critico**: ver `shared/README.md`. `dom-helpers.js` debe cargarse antes que `custom-select.js`.
- Las funciones globales son `window.SurveyTooltip.show/hide` (NO `window.showTooltip/hideTooltip`).

## Principios Del Proyecto

Priorizar:

- delegacion de eventos
- reutilizacion de componentes
- separacion entre datos y renderizado
- separacion entre configuracion y logica
- cambios incrementales y verificables

Evitar:

- reescrituras completas sin necesidad critica
- breaking changes innecesarios
- abstracciones prematuras
- sobreingenieria
- documentos nuevos si uno existente puede actualizarse

## Reglas JSON

Los JSON generados deben:

- permanecer compactos
- minimizar redundancia
- evitar anidamientos innecesarios
- mantener compatibilidad backward
- mantener contratos consistentes con los schemas Draft-07 en `scripts/schemas/`
- estar desacoplados del layout visual

Nunca:

- modificar manualmente JSON generados
- generar payloads innecesariamente grandes
- duplicar metadata repetitiva
- acoplar JSON a implementaciones visuales especificas
- agregar campos no declarados en el schema correspondiente (usar `additionalProperties: false`)

### Convencion de claves

- **NPS**: minusculas (`promotores`, `pasivos`, `detractores`). El frontend acepta ambos casings via `??` por compatibilidad backward, pero el ETL siempre produce minusculas.
- **CSAT**: capitalizado (`Totalmente satisfecho`, `Muy satisfecho`, etc.) porque proviene del catalogo Zoho Survey `RESPUESTAS_TEXTO`.
- **`año`**: entero (ej. `2026`), no string.
- **`periodo`**: string identificador (`"2026-1"` o `"2026"`).

## Reglas ETL

`zoho-survey/scripts/build_json.py` es la unica fuente oficial de transformacion.

Debe:

- permanecer idempotente (con caveat: si el CSV no tiene fechas validas, se usa `pd.Timestamp.now()` como fallback, lo que rompe idempotencia en ese edge case)
- validar columnas esperadas
- fallar explicitamente ante CSV invalidos
- minimizar procesamiento redundante
- generar estructuras consistentes con los schemas en `scripts/schemas/`

No debe:

- introducir nuevos `print()` de depuracion en produccion

## Reglas Frontend

- Mantener Vanilla JS e IIFE con APIs `window.Survey*`.
- No introducir frameworks frontend ni dependencias runtime sin decision explicita.
- Sanitizar contenido externo antes de usar `innerHTML` (usar `SurveySanitizer.escapeHTML` o `sanitizeHTML`).
- Mantener compatibilidad con GitHub Pages y navegadores modernos.
- No usar inline event handlers (`onmousemove`, `onmouseleave`, etc.) — usar `addEventListener`.
- No referenciar `window.cache` (es privada en el IIFE de `dashboard.js`, siempre undefined).
- `SurveyTooltip.move(e)` existe y se usa para listeners `mousemove` tras un `show()` (boundary detection incluida).

## Reglas GitHub Actions

**Regla de ejecucion: nada corre en local.** El ETL, los tests, la validacion de contratos y el despliegue ocurren unicamente en GitHub Actions; la verificacion se hace sobre el run.

Los workflows deben:

- ser la unica via de ejecucion del proyecto (sin pasos manuales locales)
- dispararse con cualquier push a `main` (sin filtros de `paths` que dejen cambios sin verificar)
- condicionar los pasos que exigen secretos a que exista trabajo real (p. ej. CSV en `data/`)
- minimizar commits innecesarios
- evitar loops automaticos
- evitar regeneraciones redundantes
- validar paths antes de commit
- minimizar tiempo de ejecucion y uso de runners

## Modulos Criticos (no modificar sin validacion)

Los siguientes archivos son single points of failure. Modificarlos requiere actualizar capas relacionadas en el mismo PR:

| Archivo | Impacto si se rompe |
| --- | --- |
| `zoho-survey/scripts/build_json.py` | ETL completo falla. |
| `zoho-survey/scripts/lib/config.py` | Mapeos de columnas y catalogos de negocio. Cambios requieren CSV fuente compatible. |
| `zoho-survey/scripts/validate_generated_json.py` | Validacion de contratos. Cambios deben sincronizarse con schemas. |
| `zoho-survey/scripts/schemas/*.schema.json` | Fuente formal de tipos. Cambios deben propagarse a ETL, validador y CONTRACTS.md. |
| `zoho-survey/template/index.html` | IDs HTML son contratos publicos con `dashboard.js` y `filter-controller.js`. |
| `zoho-survey/shared/js/dashboard.js` | Orquestador monolitico del dashboard por periodo. |
| `zoho-survey/shared/js/config/constants.js` | Metas y reglas de negocio consumidas por 4 modulos. |

## Respuestas Tecnicas

Antes de recomendar cambios, inspeccionar el repositorio cuando sea posible.

Toda respuesta tecnica debe incluir, cuando aplique:

- diagnostico
- causa raiz
- impacto tecnico
- riesgos
- archivos afectados
- compatibilidad backward
- solucion concreta
- rutas reales
- validacion de que los schemas y el validador siguen siendo consistentes

## Checklist Antes de Modificar JSON Contracts

Si se modifica la estructura de cualquier JSON generado:

- [ ] Actualizar el schema correspondiente en `scripts/schemas/`.
- [ ] Actualizar `validate_generated_json.py` si hay nuevas invariantes de negocio.
- [ ] Actualizar `CONTRACTS.md` con el nuevo contrato.
- [ ] Actualizar `build_json.py` para producir la nueva estructura.
- [ ] Actualizar el frontend (`dashboard.js` o componente relevante) para consumir la nueva estructura.
- [ ] Verificar que el paso `Validate generated JSON contracts` del workflow pasa.
- [ ] Verificar que los JSONs existentes siguen siendo validos (o regenerarlos).

## Advertencias Importantes Para Agentes IA

1. **No confiar en documentación de motor legacy**: el motor spaCy/keyword matching fue eliminado en v3.2.0. La versión actual usa una **cadena de motores IA** (`lib/ia_cualitativo.py`): OpenCode (`deepseek-v4.1-flash`) → NVIDIA (7 modelos), con el orden y los modelos configurables con `IA_CUALITATIVO_CADENA`. Google (Gemini) salió de la cadena por defecto el 2026-09-24 (503 constantes) y `deepseek-ai/deepseek-v4-pro-0813` porque NVIDIA lo retiró (410). No existe `scripts/README.md` (eliminado por obsoleto).
2. **Motor legacy eliminado** (v3.2.0): los modulos `nlp.py`, `segmentacion_nps.py`, `aspect_extraction.py`, `sentiment_engine.py` fueron eliminados. `enmascarar_pii` se reubico a `io_helper.py`. Desde v3.9.0 basta con UNA clave de la cadena (`GOOGLE_API_KEY`, `NVIDIA_API_KEY` u `OPENCODE_API_KEY`); el servicio DeepSeek quedo retirado.
3. **`lib/config.py` constantes legacy**: ~~`TOPICOS` y `STOPWORDS` no se usan en modulos activos.~~ **ELIMINADO**.
4. **Sin spaCy desde v3.2.0**: el motor legacy (spaCy + sentence-transformers) fue eliminado. `requirements.txt` ya no incluye `spacy`, `sentence-transformers`, ni `scikit-learn`.
5. **`dataset_cualitativo.json` TIENE schema formal**: `dataset_cualitativo.schema.json` existe (archivo intermedio, validación manual opcional). `fragmentos_nps.json` no tiene schema formal (intermedio sin consumidores externos).
6. **Trabajo sin commitear**: el repositorio puede tener cambios pendientes. Revisar `git status` antes de modificar.
7. **`periodos.json` por nivel**: debe tener exactamente un item con `isNew: true`. El validador falla si no se cumple.
8. **Tests Python se ejecutan en CI**: workflow `tests.yml` ejecuta unittest + JS tests + sintaxis en cada PR.
9. **Tests JS**: suite JS 108 tests TestFramework (94 base + 14 de `test-portal-data.js`) + 33 tests jsdom = 141 tests (fuente canonica: `tests/README.md`).
10. **`SENTIMENT_CONFIDENCE_THRESHOLD` eliminado** (Fase 0): motor `sentiment_engine.py` eliminado v3.2.0; la constante zombie fue removida junto con sus tests. No existe en el codigo actual.
