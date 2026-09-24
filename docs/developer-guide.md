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
| Dependencias ETL | pandas, jsonschema |
| Ejecución de Tests | **Solo** GitHub Actions (`tests.yml`): unittest + JS + jsdom + sintaxis |

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
2. Haz `commit` y `push`: GitHub Actions ejecuta la suite completa y despliega.
3. Verifica visualmente en GitHub Pages.

### 2. Agregar un Aspecto Semántico para NPS
1. La taxonomía y reglas viven en [zoho-survey/scripts/lib/prompts_cualitativo.py](zoho-survey/scripts/lib/prompts_cualitativo.py) (prompt system para los motores IA).
2. Si el aspecto corresponde a una nueva categoría, agregala en [zoho-survey/scripts/lib/config.py](zoho-survey/scripts/lib/config.py) en `CATEGORIA_DIMENSION_PREGRADO` (o `CATEGORIA_DIMENSION_GRADUADO` según el nivel).
3. Haz `commit` y `push`; GitHub Actions regenera los JSONs con el nuevo prompt.
4. Verifica en el log del run (o en la pestaña Actions) que no hay errores de schema: el paso `Validate generated JSON contracts` es el gate.

### 3. Agregar un Nuevo Periodo de Encuesta (Ingesta de Datos)
1. Verifica el nombre del CSV contra las reglas canónicas (ver `CONTRACTS.md`); la sanitización de PII la hace el workflow, no el equipo.
2. Adjunta el CSV a un Release (DRAFT) y lanza *Build and Deploy Survey* con el input `release_tag`.
3. GitHub Actions descarga, sanitiza, procesa y genera los JSONs del nuevo periodo.
4. Verifica en GitHub Pages que el nuevo periodo aparece en el portal y carga correctamente.

### 4. Probar y Crear Utilidades JavaScript
Para detalles de adición y ejecución de pruebas unitarias, consulta [tests/README.md](tests/README.md).

---

## Checklist de Validación antes de Commitear

- [ ] Las rutas de archivos modificadas han sido validadas contra el árbol real.
- [ ] No se han realizado ediciones manuales a los archivos JSON generados en `zoho-survey/students/**/json/`.
- [ ] Si se modificó la estructura de datos, se actualizaron coherentemente los validadores de Python y [CONTRACTS.md](CONTRACTS.md).
- [ ] El push ejecutó `tests.yml` en verde (Python + JS + jsdom + sintaxis).
- [ ] El paso `Validate generated JSON contracts` del workflow de build pasó sin errores.

---

## Configuración del Motor Cualitativo

Desde v3.9.0 el análisis cualitativo usa una **cadena de motores** que se intentan en orden
(OpenCode → NVIDIA): si un motor falla o devuelve una respuesta inválida, se pasa al
siguiente. El motor legacy (spaCy + sentence-transformers) fue **eliminado** en v3.2.0 y el
servicio DeepSeek se **retiró** en v3.9.0.

| Variable | Valores | Efecto |
|---|---|---|
| `IA_CUALITATIVO_CADENA` | `servicio:modelo,servicio:modelo` | **Orden y modelos** de la cadena. Se define como *variable* (no secreto): Settings → Secrets and variables → Actions → pestaña **Variables**. Vacío = cadena por defecto. |
| `GOOGLE_API_KEY` | API key string | Clave de Google Gemini. No se usa en la cadena por defecto (salió por sus 503); sin ella, sus motores se omiten de la cadena. |
| `NVIDIA_API_KEY` | API key string | Clave de NVIDIA NIM (7 modelos en la cadena por defecto). |
| `OPENCODE_API_KEY` | API key string | Clave de OpenCode. |
| `IA_CUALITATIVO_OPENCODE_URL` | URL | Dirección de OpenCode: plan **Go** (por defecto) o plan Zen. |
| `IA_CUALITATIVO_WORKERS` | entero (default 15) | Workers concurrentes para IA. |
| `IA_CUALITATIVO_MAX_RPM` | entero (default 60) | Rate limit de API. |
| `IA_CUALITATIVO_TIMEOUT` | entero (default 60s) | Timeout por llamada. |
| `IA_CUALITATIVO_MAX_FALLOS_API_PCT` | entero (default 20) | Umbral fail-closed: si un porcentaje mayor de comentarios falla por API (cualquier motor de la cadena), el ETL aborta y no publica `sentimiento.json` para ese periodo. `0` = estricto; `100` = desactivado. |

**Cadena de motores IA:**
- Una sola llamada API ejecuta 5 tareas: segmentación → sentimiento con reglas NPS → intensidad → clasificación taxonómica → cross-reference CSAT.
- Deduplicación por ID: `build_json.py` usa `sentimiento.json` como fuente de verdad; solo envía a los motores los comentarios nuevos (sin caché persistente).
- Límite de ritmo: 60 RPM por motor (NVIDIA: 15, por su plan gratuito) y 15 workers; si el primer motor es NVIDIA, el pool baja a 3. Timeout: 60s por llamada.
- Fail-closed de calidad: si más del 20% de los comentarios fracasa por API, el build falla y no se publica `sentimiento.json` (en vez de publicar indicadores calculados sobre una muestra irrelevante).
- Costo: cada servicio factura sus propios tokens; el resumen del run registra los tokens y las llamadas de toda la cadena.
- Identificación ante OpenCode: OpenCode Go descarta con 403 (Cloudflare 1010) a los clientes que no se identifican; su documentación pide un agente propio y un identificador de sesión. `lib/ia_client.py` envía `User-Agent: survey-storytelling-etl/1.0` y `x-opencode-session` (uno por corrida) **solo** en las llamadas a OpenCode.

### Ejecutar el motor IA

## Ingesta automática desde Zoho Survey (Fase 1)

Zoho Survey puede **empujar** cada respuesta al repositorio (Builder → Hub → Triggers → Webhook).
El webhook **no puede** usar la API de envíos de GitHub (`repository_dispatch`): su cuerpo exige
`event_type` y `client_payload` como claves hermanas de primer nivel, y el webhook de Zoho Survey
arma los campos dentro de un único contenedor con un nombre elegido por el usuario. Por eso llama a
la **API de incidencias**: crea una incidencia cuyo **cuerpo** es la respuesta en JSON y cuyo
**título** es el nombre de la encuesta (por ejemplo `ESTUDIANTIL 2026-2`).

El flujo `zoho_inbox.yml` reacciona a esa incidencia (`issues[opened]`, ignorando las incidencias
cuyo cuerpo no empiece por `{`) y `zoho-survey/scripts/zoho_inbox.py` deja la respuesta en
`data/zoho_pendientes/<encuesta>.jsonl`, **enmascarada antes de guardar** (el repositorio es
público) y sin duplicados. Al registrarla, la incidencia se **cierra automáticamente** (si el
registro fallara, quedaría abierta como aviso).

**No ejecuta el ETL**: el análisis se hace después, agrupado, para no lanzar una corrida de IA por
cada respuesta.

Para probarlo sin depender de Zoho: (a) crear una incidencia a mano cuyo cuerpo sea la respuesta en
JSON, o (b) GitHub → Actions → **Zoho Inbox** → *Run workflow*, pegando la respuesta. Debe incluir
un campo con el identificador de respuesta (`ID` es el que envía el webhook real) y, si la
incidencia se crea a mano, el nombre de la encuesta en el título (por ejemplo `ESTUDIANTIL 2026-2`);
si falta alguno, el flujo **falla con un mensaje explícito** que indica qué agregar.

Falta decidir la cadencia de procesamiento de los pendientes.

El motor IA se ejecuta automáticamente en el workflow `Build and Deploy Survey` (GitHub Actions)
siempre que al menos **una** clave de la cadena esté configurada en GitHub Secrets.
El gate **Verify claves de los motores IA** comprueba cuáles están presentes antes de instalar
dependencias y avisa de las ausentes (sus motores se omiten de la cadena).

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
