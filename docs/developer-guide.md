# Guía de Desarrollo y Operaciones

Guía operativa para desarrolladores humanos y agentes de IA que necesitan mantener o modificar el sistema `survey-test`.

## Documentación de Referencia

Antes de realizar cambios, familiarízate con los siguientes documentos según tu necesidad:

| Necesidad | Documento |
| --- | --- |
| Reglas técnicas obligatorias | [AGENTS.md](AGENTS.md) |
| Arquitectura del sistema y carpetas | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Especificación y esquemas de datos | [CONTRACTS.md](CONTRACTS.md) |
| Ejecución y creación de pruebas | [tests/README.md](tests/README.md) |
| Lógica de filtros del frontend | [docs/filter-logic.md](docs/filter-logic.md) |
| Historial de versiones | [docs/CHANGELOG.md](docs/CHANGELOG.md) |

## Quick Facts

| Dato | Valor |
| --- | --- |
| Tipo | SPA estática para GitHub Pages |
| Stack | HTML, CSS, Vanilla JS, Python |
| Dependencias Runtime | 0 |
| Dependencias ETL | pandas, jsonschema, openpyxl, python-dotenv |
| Ejecución de Tests | Local (`npm run test:js`, `npm run test:py`) + CI GitHub Actions |

## Puntos de Entrada Comunes

| Archivo | Cuándo tocarlo |
| --- | --- |
| [zoho-survey/index.html](zoho-survey/index.html) | Portal v5.0: navegación multi-fase entre tipos de encuesta y periodos. |
| [zoho-survey/template/index.html](zoho-survey/template/index.html) | Plantilla base de dashboards por periodo. |
| [zoho-survey/shared/js/portal.js](zoho-survey/shared/js/portal.js) | Orquestador del portal (init, sidebar, fases). |
| [zoho-survey/shared/js/dashboard.js](zoho-survey/shared/js/dashboard.js) | Orquestación general del dashboard individual. |
| [zoho-survey/shared/js/config/constants.js](zoho-survey/shared/js/config/constants.js) | Metas, ciclos y constantes compartidas. |
| [zoho-survey/scripts/build_json.py](zoho-survey/scripts/build_json.py) | Transformación CSV -> JSON. |
| [zoho-survey/scripts/validate_generated_json.py](zoho-survey/scripts/validate_generated_json.py) | Validación estructural de JSON y HTML. |

> [!IMPORTANT]
> **Orden de carga de dependencias JS:**
> En los archivos HTML (`zoho-survey/index.html` y la plantilla `zoho-survey/template/index.html`), las dependencias de scripts deben importarse en un orden específico. Particularmente, `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` para evitar errores en tiempo de ejecución (`TypeError: window.SurveyDomHelpers is undefined`) que bloqueen el loader del portal.


---

## Tareas Comunes

### 1. Cambiar una Meta de NPS o CSAT
1. Edita el objeto correspondiente en [zoho-survey/shared/js/config/constants.js](zoho-survey/shared/js/config/constants.js).
2. Valida localmente con `npm run test:js`.
3. Haz `commit` y `push`; GitHub Actions ejecuta tests y despliega.
4. Verifica visualmente en GitHub Pages.

### 2. Agregar un Aspecto Semántico para NPS
1. La taxonomía y reglas viven en [zoho-survey/scripts/lib/prompts_cualitativo.py](zoho-survey/scripts/lib/prompts_cualitativo.py) (prompt system para DeepSeek).
2. Si el aspecto corresponde a una nueva categoría, agregala en [zoho-survey/scripts/lib/config.py](zoho-survey/scripts/lib/config.py) en `CATEGORIA_DIMENSION_PREGRADO` (o `CATEGORIA_DIMENSION_GRADUADO` según el nivel).
3. Haz `commit` y `push`; GitHub Actions regenera los JSONs con el nuevo prompt.
4. Valida que no haya errores de schema con `npm run validate:json` localmente (contra JSONs ya generados) o revisando el log de Actions.

### 3. Agregar un Nuevo Periodo de Encuesta (Ingesta de Datos)
1. Sanitiza el CSV con `python zoho-survey/scripts/sanitize_csv_pii.py <ruta_csv>`.
2. Sube el CSV mediante el botón **"Subir datos"** del portal en GitHub Pages.
3. GitHub Actions valida, procesa y genera los JSONs del nuevo periodo.
4. Verifica en GitHub Pages que el nuevo periodo aparece en el portal y carga correctamente.

### 4. Probar y Crear Utilidades JavaScript
Para detalles de adición y ejecución de pruebas unitarias, consulta [tests/README.md](tests/README.md).

---

## Checklist de Validación antes de Commitear

- [ ] Las rutas de archivos modificadas han sido validadas contra el árbol real.
- [ ] No se han realizado ediciones manuales a los archivos JSON generados en `zoho-survey/students/**/json/`.
- [ ] Si se modificó la estructura de datos, se actualizaron coherentemente los validadores de Python y [CONTRACTS.md](CONTRACTS.md).
- [ ] Se ejecutaron `npm run test:js` y `npm run test:py` localmente sin fallos.
- [ ] Se corrió con éxito `npm run validate:json` antes del commit.

---

## Configuración del Motor Cualitativo

Desde v3.2.0 el motor principal de análisis cualitativo es **DeepSeek IA**.
El motor legacy (spaCy + sentence-transformers) fue **eliminado**; `DEEPSEEK_API_KEY` es obligatoria.
Además, existe un **fallback a NVIDIA** (`NVIDIA_API_KEY`) que se activa automáticamente si DeepSeek falla o no está configurado.

| Variable | Valores | Efecto |
|---|---|---|
| `DEEPSEEK_API_KEY` | API key string | **Obligatoria** para el motor principal (DeepSeek). |
| `NVIDIA_API_KEY` | API key string | Opcional. Activa el fallback a modelos NVIDIA si DeepSeek falla. |
| `IA_CUALITATIVO_MODEL` | string (default `deepseek-chat`) | Modelo DeepSeek a utilizar. |
| `IA_CUALITATIVO_FALLBACK_MODEL` | string (default `nemotron-3-ultra-550b-a55b`) | Modelo NVIDIA fallback. |
| `IA_CUALITATIVO_WORKERS` | entero (default 15) | Workers concurrentes para IA. |
| `IA_CUALITATIVO_MAX_RPM` | entero (default 60) | Rate limit de API. |
| `IA_CUALITATIVO_TIMEOUT` | entero (default 60s) | Timeout por llamada. |

**Motor IA (DeepSeek + fallback NVIDIA):**
- Una sola llamada API ejecuta 5 tareas: segmentación → sentimiento con reglas NPS → intensidad → clasificación taxonómica → cross-reference CSAT.
- Deduplicación por ID: `build_json.py` usa `sentimiento.json` como fuente de verdad; solo envía a DeepSeek los comentarios nuevos (sin caché persistente).
- Rate limit: 60 RPM, 15 workers concurrentes. Timeout: 60s por llamada.
- Costo estimado: ~$0.50 por build completo (solo comentarios nuevos).

### Ejecutar el motor IA

El motor IA se ejecuta automáticamente en el workflow `Build and Deploy Survey` (GitHub Actions)
siempre que `DEEPSEEK_API_KEY` (u `NVIDIA_API_KEY` como fallback) esté configurada en GitHub Secrets.
El gate `Verify DEEPSEEK_API_KEY` verifica la clave antes de instalar dependencias.

---

## Validación Cualitativa Manual

El análisis cualitativo es automático, pero se recomienda una revisión periódica de muestras para mejorar la taxonomía:

- **Revisión mensual de "Pendiente de Clasificación"**: tomar una muestra de fragmentos que el ETL no pudo clasificar y revisarlos manualmente.
- **Validación de calidad**: comparar clasificaciones del ETL contra criterio humano en muestras aleatorias.
- **Síntesis narrativa para reportes**: generar interpretaciones cualitativas para stakeholders no técnicos.

### Flujo de revisión recomendado

1. Extraer una muestra de `sentimiento.json` — filtrar por `"categoria_padre": "Pendiente de Clasificación"`.
2. Si se identifican patrones (ej. una dimensión nueva que debería estar en la taxonomía), actualizar el prompt system en `scripts/lib/prompts_cualitativo.py` y las categorías en `scripts/lib/config.py`.
3. Hacer `push`; GitHub Actions regenera los JSONs y verifica que "Pendiente de Clasificación" disminuye.

---

## Rollback de Emergencia

### Revertir al último build bueno
1. Ir a GitHub → Commits. Buscar el último commit del bot (`github-actions`).
2. Copiar el hash del commit bueno.
3. En tu rama local: `git checkout <hash> -- zoho-survey/students/`
4. Commit y push: `git commit -m "Rollback: restaurar JSONs" && git push`

### Forzar re-build limpio
1. GitHub → Actions → **Build and Deploy Survey** → Run workflow.
2. Esto regenera todos los JSONs desde los CSVs en `data/`.
3. Verificar en GitHub Pages que los dashboards cargan.

### Revertir `periodos.json`
- Borrar el archivo y hacer push → el workflow lo regenera.
- O restaurar: `git checkout HEAD~1 -- zoho-survey/students/*/periodos.json`

### Revertir análisis cualitativo
- Para forzar reprocesamiento IA: borrar `sentimiento.json` del periodo y hacer push → el workflow lo regenera solo con comentarios nuevos (deduplicación por ID).
