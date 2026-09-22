# Ingesta de CSVs y generación de ZIPs — Flujo completo

> **Canónico.** Este documento es la única versión viva del flujo de ingestión y descarga de datos. Reemplaza referencias distribuidas en `SECURITY.md`, `CHANGELOG.md` y `tests/README.md`.

## Resumen ejecutivo

| Flujo | ¿Dónde corre? | ¿Toque en Git? | ¿Se guarda ZIP? | |
|---|---|---|---|---|
| **Recibir respuesta** | GitHub Actions (`zoho_inbox.yml`) | Sí: una línea por respuesta en `data/zoho_pendientes/<encuesta>.jsonl` (enmascarada) | No aplica | |
| **Procesar CSV** | GitHub (a mano o desde el botón del portal) + GitHub Actions | Nada: los CSV se borran antes del commit del bot | No aplica | |
| **Generar JSONs** | GitHub Actions (ETL `build_json.py`) | Sí (solo JSONs `dashboard_data.json`, `periodos.json`, etc.) | No (generados on-demand) | |
| **Descargar ZIP** | **GitHub Actions (on-demand)** | Nada: ZIP generado en artifact efímero, entregado, borrado | No (temporal) | |

---

## 1. Flujo de ENTRADA de datos

**Objetivo:** que las respuestas de Zoho Survey lleguen solas y **sin credenciales en el navegador**.

### Paso 1 — Webhook de Zoho Survey (acumular)

1. Cada respuesta enviada crea una **incidencia** en el repositorio (`https://api.github.com/repos/{owner}/{repo}/issues`), con el nombre de la encuesta en el título y la respuesta en JSON en el cuerpo.
2. `zoho_inbox.yml` la normaliza (`zoho_respuesta.py`), la **enmascara** y agrega una línea a `data/zoho_pendientes/<encuesta>.jsonl` (sin duplicados por identificador de respuesta).
3. La incidencia se **cierra** al registrarse; si el cuerpo no es JSON válido, el flujo falla y queda **abierta** como aviso.
4. Aquí **no** corre el ETL: las respuestas se acumulan.

> **Listo:** `zoho-survey/scripts/zoho_a_csv.py` arma el CSV desde la bandeja cuando el portal pide el proceso
> (`repository_dispatch`): una fila por respuesta, cabeceras del ETL y nombre derivado del título de la encuesta.
> La bandeja **no** se borra: es el acumulado del periodo, y borrarla dejaría el dashboard sin las respuestas anteriores.

### Paso 2 — Procesar (a mano o desde el portal, cuando se decide)

> El botón de refrescar del portal hace `POST` a `/api/procesar-encuesta` (función en Vercel del proyecto `survey-tracker`), que dispara este mismo flujo con `repository_dispatch: procesar_datos`. Llega **sin** `release_tag`, así que no descarga CSV: sirve para redesplegar y, cuando exista el paso pendiente, para convertir la bandeja. La llave de GitHub vive en Vercel; el navegador no la ve.

1. Se adjunta el CSV al **Release** correspondiente (preferiblemente DRAFT) y se lanza *Build and Deploy Survey* con el input `release_tag`.
2. `gh release download` lo baja a `data/` **solo en el runner** (nunca al historial).
3. **Verify claves de los motores IA** → gate temprano (falla si no hay ninguna).
4. **Sanitize PII** → `sanitize_csv_pii.py --all` redacta IP/UA/URL **in-place**.
5. **Run build_json.py** con las claves de los motores → ETL completo (ver sección 2).
6. **Validate JSON contracts** → `validate_generated_json.py` (schemas + invariantes `isNew`).
7. **Deploy a GitHub Pages** → artifact `./zoho-survey` + health check (curl `health.html` y `periodos.json`).
8. **Eliminar CSVs de `data/`** → `find data -iname "*.csv" -delete` antes del commit del bot (fail-closed: si queda un CSV en staging, el commit aborta).
9. **Commit del bot** → JSONs nuevos/modificados con `[skip ci]`. El Release **no** se elimina: es del owner.

### Resultado

- El CSV original **nunca entra al Git history**.
- Quedan en `main` solo los JSONs generados + `periodos.json` actualizado (`isNew: true`), más la bandeja enmascarada.

---

## 2. ETL y generación de ZIPs

Corre `build_json.py` **solo en GitHub Actions** (paso `Run build_json.py` del workflow de build, condicionado al gate `Detectar CSVs a procesar`). Los comandos canónicos de ejecución viven en `.github/workflows/*.yml`; `package.json` no define scripts de ejecución local (la regla del proyecto es que nada corre en local).

### Qué consumen los motores IA

- Comentarios NPS abiertos → enviados a los motores de la cadena (prompts de `prompts_cualitativo.py`).
- Salida: `sentimiento.json`, `intermediate/dataset_cualitativo.json`, `intermediate/fragmentos_nps.json`.
- Comentarios **ofuscados** antes de enviarlos (Fase 3.5) para proteger PII.

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

### Entrada de datos

| Archivo | Rol | |
|---|---|---|
| `.github/workflows/zoho_inbox.yml` | Recibe la incidencia del webhook y guarda la respuesta | |
| `zoho-survey/scripts/zoho_inbox.py` + `lib/zoho_respuesta.py` | Normaliza, enmascara y deduplica la respuesta | |
| `data/zoho_pendientes/<encuesta>.jsonl` | Bandeja de entrada (versionada, enmascarada) | |
| `.github/workflows/build_zoho_survey.yml` | Descarga del Release, sanitización, ETL, deploy y commit | |
| `zoho-survey/scripts/sanitize_csv_pii.py` | Redacción de IP/Agente Usuario/URL | |

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

> **Descartado:** la técnica de "misma técnica que la subida" (PAT en el navegador) ya no existe: el portal no usa credenciales. Cualquier disparo desde la página exigiría un intermediario: ese intermediario ya existe para el proceso (`/api/procesar-encuesta` en Vercel) y es el que se reutilizaría aquí si algún día se automatiza la descarga; hoy la descarga se resuelve con el ZIP publicado en `exports/` cuando esté disponible.

1. Al click "Descargar", el dashboard enlaza directamente al ZIP publicado (`./exports/data_*.zip`).
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
- **PAT**: solo en la cabecera del webhook dentro de Zoho (permiso *Issues: write*); `GITHUB_TOKEN` en Actions. El navegador no maneja credenciales.
- **PAT del portal**: el disparo desde el botón de refrescar usa `GITHUB_DISPATCH_TOKEN` en Vercel (permiso *Contents: Read and write* sobre este repositorio). El navegador tampoco lo maneja.
- **PII**: IP/UA/URL redimidos `sanitize_csv_pii.py`; comentarios ofuscados antes de enviarlos a los motores IA.
