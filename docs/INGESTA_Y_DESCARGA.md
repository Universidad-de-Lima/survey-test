# Ingesta de CSVs y generación de ZIPs — Flujo completo

> **Canónico.** Este documento es la única versión viva del flujo de ingestión y descarga de datos. Reemplaza referencias distribuidas en `SECURITY.md`, `CHANGELOG.md` y `tests/README.md`.

## Resumen ejecutivo

| Flujo | ¿Dónde corre? | ¿Toque en Git? | ¿Se guarda ZIP? | |
|---|---|---|---|---|
| **Subir CSV** | GitHub Actions | Nada: CSVs + Release temporales se borran | No aplica | |
| **Generar JSONs** | GitHub Actions (ETL `build_json.py`) | Sí (solo JSONs `dashboard_data.json`, `periodos.json`, etc.) | No (generados on-demand) | |
| **Descargar ZIP** | **GitHub Actions (on-demand)** | Nada: ZIP generado en artifact efímero, entregado, borrado | No (temporal) | |

---

## 1. Flujo de SUBIDA de CSV — "Subir datos"

**Objetivo:** ingresar CSVs de Zoho Survey sin que **nada** persista en Git ni en GitHub.

### Paso 1 — Frontend (navegador del usuario)

1. El usuario abre el portal y click en **"Subir datos"** (`zoho-survey/index.html`, id `#uploadBtn`).
2. Se abre el modal (`portal-upload-ui.js`) con:
   - Campo **PAT** (Personal Access Token del owner).
   - Dropzone para arrastrar CSV(s).
3. **Validación cliente** (`portal-upload.js`):
   - Nombre debe iniciar con `ENCUESTA DE SATISFACCION` (tolerancia a espacios/guiones).
   - Extensión `.csv`
   - Periodo extraído con regex `20XX` o `20XX-1`
   - Categoría detectada: `ESTUDIANTIL`, `GRADUADOS`, `POSGRADO`, `DOCENTES`, `EGRESADOS`, `NO DOCENTES`, `EMPLEADORES`.
   - Headers requeridos validados: `ID de respuesta`, `Net Promoter Score`, + columna carrera/programa dependiendo de categoría.
   - Límites: 1–10 CSVs, 5 MB c/u, 50 MB total.
   - SHA-256 cliente-side.
4. **PAT vive solo en memoria** (`uploadState.token` en closure). Nunca persistido ni impreso.

### Paso 2 — GitHub (Release temporal)

Después de validar, `runUpload()` (`portal-upload-ui.js:131`):

5. `createRelease()` → crea un Release **DRAFT** con tag `csv-upload-{UUID}`.
6. `uploadAsset()` → sube cada CSV como asset del Release.
7. `publishRelease()` → convierte draft→published.
8. `dispatchWorkflow()` → dispara `repository_dispatch` tipo `csv_upload` con payload `{upload_id, release_id, files:[...]}`.

### Paso 3 — GitHub Actions (`build_zoho_survey.yml`)

El workflow se dispara con concurrencia aislada por `upload_id`:

9. **Download CSVs** → `data/temp/{upload_id}/` desde Release assets (NUNCA al tree).
10. **Copy a `data/`** → CSVs copiados `data/` para que ETL los descubra (`ENCUESTA DE SATISFACCION.*.csv`).
11. **Verify DEEPSEEK_API_KEY** → gate temprano (falla si falta).
12. **Server-side validate** → `validate_upload_csv.py` re-valida nombre/headers/tamaño/duplicados.
13. **Sanitize PII** → `sanitize_csv_pii.py --all` redacta IP/UA/URL **in-place** (defensa en profundidad).
14. **Run build_json.py** con `DEEPSEEK_API_KEY` → ETL completo (ver sección 2).
15. **Validate JSON contracts** → `validate_generated_json.py` (schemas + invariantes `isNew`).
16. **Eliminar temporalidades** → `find .../exports -exec rm`, `find .../intermediate -exec rm` (153-156).
17. **Deploy a GitHub Pages** → artifact `./zoho-survey`.
18. **Health check** → curl `health.html` + `periodos.json` (200).
19. **Eliminar CSVs de `data/`** → `find data -iname "*.csv" -delete` (187-196).
20. **Eliminar Release** → `gh api -X DELETE /releases/{release_id}` **solo si todo OK** (198-210).
21. **Commit del bot** → solo si **no** fue repository_dispatch (upload_id path NO commitea; el owner empuja manualmente). Commitea JSONs nuevos/modificados con `[skip ci]`.

### Resultado del upload

- El CSV original **nunca entra al Git history**.
- El Release temporal **se borra tras éxito** (o queda DRAFT si falla, para recovery manual).
- Quedan en `main` solo los JSONs generados + `periodos.json` actualizado (`isNew: true`).

---

## 2. ETL y generación de ZIPs

Corre `build_json.py` **solo en GitHub Actions** (paso `Run build_json.py` del workflow de build, condicionado al gate `Detectar CSVs a procesar`). Los scripts `npm run build:json` / `npm run validate:json` / `npm run test:*` de `package.json` son el **espejo** de los comandos que ejecuta el runner y no forman parte del flujo del proyecto.

### What consume DeepSeek

- Comentarios NPS abiertos → enviados a DeepSeek (prompts de `prompts_cualitativo.py`).
- Salida: `sentimiento.json`, `intermediate/dataset_cualitativo.json`, `intermediate/fragmentos_nps.json`.
- Comentarios **ofuscados** antes DeepSeek (Fase 3.5) para proteger PII.

### Qué produce `exports/`

`csv_exporter.py:31` genera CSVs de análisis cualitativo + respuestas por dimensión, empaquetados en `exports/data_{nombre}_{fecha}.zip` → **este es el ZIP que el dashboard descarga** (ver sección 3).

### Qué produce `intermediate/`

JSONs intermedios no consumidos por frontend (regenerables, `.gitignore` los excluye):

- `intermediate/dataset_cualitativo.json`
- `intermediate/fragmentos_nps.json` (validación manual opcional, no consumer externo)

---

## 3. Flujo de DESCARGA de ZIP — estado actual

**Archivo:** `zoho-survey/shared/js/components/sentiment-view.js` (líneas 766-790).
**Llamado desde:** botón "Mostrar más" → sección Cualitativo dentro del dashboard individual.

### Paso 1 — UI

1. Dashboard por periodo (`students/undergraduate/2026-1/index.html`).
2. Sección Cualitativo → `sentiment-view.js` lee `state.exportConfig` (config embedida por `build_json.py` en `dashboard_data.json`).
3. `exportConfig` contiene: `nombre_encuesta`, `fecha_generacion`.

### Paso 2 — Construcción URL

```js
const zipName = `data_${exp.nombre_encuesta}_${exp.fecha_generacion}.zip`;
const zipUrl = `./exports/${zipName}`;
```

URL relativa: `./exports/data_*.zip` desde el dashboard periodo.

### Paso 3 — HTTP HEAD check

```js
fetch(zipUrl, { method: 'HEAD' }).then(resp => {
  if (resp.ok) → descarga;
  else → muestra modal: "La exportación ZIP no está disponible para este período."
});
```

### Estado actual en GitHub Pages

- **CI borra exports/** (línea 153-156 `build_zoho_survey.yml`).
- **Resultado**: todos los ZIPs → 404. El fallback JS (`_showExportModal`) muestra "no disponible". **No crashea el dashboard, pero no sirve la descarga.**
- **El código lo anticipó** (HEAD check + fallback), pero el comportamiento es: download siempre falla en producción.

---

## 4. Archivos clave para este flujo

### Subida

| Archivo | Rol | |
|---|---|---|
| `zoho-survey/shared/js/portal-upload-ui.js` | Modal, PAT en closure, states, `runUpload()` | |
| `zoho-survey/shared/js/portal-upload.js` | Validación cliente, helpers GitHub API, `dispatchWorkflow` | |
| `zoho-survey/index.html` | Botón `#uploadBtn`, modal markup | |
| `.github/workflows/build_zoho_survey.yml` | Steps 5-21 del flujo | |
| `zoho-survey/scripts/validate_upload_csv.py` | Validación server-side | |
| `zoho-survey/scripts/sanitize_csv_pii.py` | Redacción IP/UA/URL | |
| `tests/unit/test-upload-validator.js` | 28 tests validación frontend | |
| `zoho-survey/scripts/tests/test_validate_upload_csv.py` | 17 tests server-side | |

### Descarga

| Archivo | Rol | |
|---|---|---|
| `zoho-survey/shared/js/components/sentiment-view.js:766-790` | `exportCSV()`, HEAD check, fallback modal | |
| `zoho-survey/scripts/lib/csv_exporter.py:31` | Genera ZIPs en `exports/` | |
| `docs/developer-guide.md:1-28` | Task 5 (subir CSV) describe flujo completo | |

---

## 5. Plan de arreglo para DESCARGA (Opción B)

Hacer que el flujo de descarga siga el mismo patrón que el upload: **temp en GitHub → descarga → delete → nada en Git**.

### Propuesta

1. Al click "Descargar", frontend dispara un `repository_dispatch` tipo `zip_download` con `{periodo, nivel}` via `fetch` a `api.github.com/repos/{owner}/{repo}/dispatches` usando PAT (misma técnica upload).
2. GitHub Actions (`workflow_dispatch` o `repository_dispatch[zip_download]`) corre en `data/` generado (o regenera on-demand desde JSONs) el script `csv_exporter.py` → produce ZIP en artifact efímero.
3. Sube ZIP a un objeto temporal (Release DRAFT o `actions/upload-artifact` descargable) con TTL breve.
4. Notifica URL de descarga (vía Issues o API).
5. Usuario descarga → **Actions borra ZIP + artifact + Release** (`if: success()`).
6. **Nada queda en Git** (ZIP generado on-demand, no persiste).

### Alternativas |
- **Mantener exports/ fuera del deploy**: mover `exports/*.zip` a un artifact por separado (no Pages), servido por un handler.
- **Serverless function (GitHub Actions + API)**: endpoint on-demand que genera ZIP y devuelve.
- **Descarga directa desde artifact CI**: usar `actions/download-artifact` si se expone.

---

## 6. Seguridad

- **CSV originales**: nunca en Git (sanitizados + borrados CI).
- **ZIPs**: actualmente NO se publican en Pages (borrados CI). Bajo el plan de arreglo, tampoco se persistirían.
- **PAT del owner**: solo memoria del navegador (frontend); `GITHUB_TOKEN` en Actions.
- **PII**: IP/UA/URL redimidos `sanitize_csv_pii.py`; comentarios ofuscados antes DeepSeek.
