# Onboarding — survey-test

Guía para nuevos desarrolladores o analistas que necesitan entender y operar el sistema.

---

## ¿Qué es survey-test?

Sistema de dashboards estáticos para visualizar encuestas de satisfacción de la **Universidad de Lima**. Toma archivos CSV exportados de Zoho Survey y los convierte en dashboards web interactivos, sin backend ni base de datos. Todo se despliega gratuitamente en GitHub Pages.

**No se requiere entorno local.** El procesamiento de CSVs (ETL + IA), las pruebas y el despliegue ocurren exclusivamente en GitHub Actions; del equipo solo se necesita Git para subir los cambios.

---

## Flujo de trabajo completo

```
1. Exportar CSV desde Zoho Survey
         ↓
2. (OBLIGATORIO) Sanitizar PII localmente:
   python zoho-survey/scripts/sanitize_csv_pii.py <ruta_csv>
   Redacta columnas Dirección IP, Agente Usuario, URL de la encuesta.
   Los CSVs no se commitean nunca; data/ está en .gitignore.
         ↓
3. Subir CSV(s) desde el portal en GitHub Pages con el botón "Subir datos"
   (el frontend crea un Release DRAFT temporal y dispara GitHub Actions)
         ↓
4. GitHub Actions ejecuta el pipeline automáticamente:
   - Descarga los assets del Release temporal
   - Valida y sanitiza los CSVs
   - Ejecuta build_json.py (ETL + IA)
   - Valida JSONs generados
   - Elimina el Release temporal
   - Despliega a GitHub Pages
         ↓
5. El dashboard se actualiza en GitHub Pages (~3-5 min)
         ↓
6. Verificar en: https://universidad-de-lima.github.io/survey-test/zoho-survey/
```

---

## ¿Dónde está cada cosa?

| Si necesitas... | Ve a... |
|---|---|
| Ver los dashboards | `zoho-survey/` en GitHub Pages |
| Agregar un nuevo periodo | Portal **Subir datos** (`zoho-survey/index.html` en GitHub Pages) o un Release + `workflow_dispatch` |
| Cambiar metas (NPS, CSAT) | `zoho-survey/shared/js/config/constants.js` |
| Cambiar cómo se clasifican los comentarios | `zoho-survey/scripts/lib/prompts_cualitativo.py` (taxonomía del análisis IA) |
| Ver si todo está bien | `zoho-survey/health.html` en GitHub Pages (verifica integridad de dashboards/JSONs) |
| Ver historial de cambios | `docs/CHANGELOG.md` |
| Entender la arquitectura | `ARCHITECTURE.md` |
| Entender los datos | `CONTRACTS.md` |
| Reglas para código | `AGENTS.md` |

---

## Roles y responsabilidades

| Rol | Qué hace | Frecuencia |
|---|---|---|
| **Analista / Dueño de encuesta** | Exporta CSV de Zoho Survey, lo sanitiza y lo sube desde el portal | Por cada periodo nuevo (~2-4 veces/año) |
| **Desarrollador** | Mantiene el código (ETL, frontend), agrega features, corrige bugs | Según necesidad |
| **Revisor cualitativo** | Revisa muestras de clasificaciones dudosas y propone mejoras en prompts/taxonomía | Mensual (opcional) |
| **GitHub Actions (bot)** | Ejecuta el pipeline, genera JSONs, despliega | Automático en cada push o repository_dispatch |

---

## Troubleshooting común

### 1. "El dashboard no muestra el nuevo periodo"

**Causa probable**: El CSV no tiene el nombre correcto o no se subió desde el portal.
**Solución**: El archivo debe contener el patrón `ENCUESTA` y el periodo (`2026-1`, `2026`). Ej: `ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-1.csv`. Subirlo con el botón **"Subir datos"** del portal en GitHub Pages.

### 2. "El build falló en GitHub Actions"

**Causa probable**: Columnas faltantes en el CSV.
**Solución**: Verificar que el CSV tenga las columnas requeridas: `ID de respuesta`, `Net Promoter Score (de un total de 10)`, `La Universidad de Lima`, y la columna de carrera correspondiente. Revisar logs del workflow para el error específico.

### 3. "La sección cualitativa no carga"

**Causa probable**: `sentimiento.json` no se generó.
**Solución**: Verificar que el CSV tenga la columna `Comentario NPS` con texto. Si está vacía, el análisis cualitativo se omite (comportamiento esperado).

### 4. "El health check muestra ❌"

**Causa probable**: JSONs no se generaron para algún periodo.
**Solución**: Ir a GitHub Actions → Build and Deploy Survey → Run workflow para forzar re-generación.

### 5. "Quiero volver a la versión anterior"

**Solución**: Ver sección "Rollback de Emergencia" en `docs/developer-guide.md`.

### 6. "La sección Cualitativo aparece vacía o con 0 comentarios"

**Causa probable**: La pregunta abierta NPS es **opcional**. No todos los encuestados responden.
**Solución**: Esto es comportamiento esperado cuando ning��n encuestado dejó comentario.
El dashboard debe ocultar la sección Cualitativo en lugar de mostrar "0 comentarios analizados".
Si la sección aparece con error, verificar que `sentimiento.json` existe y que
`total_con_comentario > 0` en el resumen.

---

## Verificación de cambios

El proyecto se verifica **en GitHub Actions**; no se ejecuta nada en local.

```
Flujo: editar archivos → commit → push a main → verificar el run en Actions
```

Cada push dispara:

| Workflow | Qué verifica |
|---|---|
| `tests.yml` | `unittest` (Python), tests JS en Node, tests DOM con jsdom, sintaxis de todos los módulos, contratos JSON, Ruff y ESLint (informativos) |
| `build_zoho_survey.yml` | Gate `Detectar CSVs` (el ETL solo corre si hay CSV en `data/`), validación de contratos y deploy a GitHub Pages |

Los datos de entrada del ETL se envían por el portal **"Subir datos"** o por un **Release con tag + `workflow_dispatch`** (ver `docs/INGESTA_Y_DESCARGA.md`).

---

## Glosario

| Término | Significado |
|---|---|
| **NPS** | Net Promoter Score — mide lealtad (0-10). Promotores ≥9, Pasivos 7-8, Detractores ≤6 |
| **CSAT** | Customer Satisfaction — % de respuestas positivas (Top 3 Box) |
| **T2B / T3B** | Top 2 Box / Top 3 Box — agrupaciones de respuestas más positivas |
| **Meaning Unit** | Fragmento mínimo de un comentario que expresa una sola idea evaluable |
| **ETL** | Extract, Transform, Load — pipeline que convierte CSV en JSON |
| **IIFE** | Immediately Invoked Function Expression — patrón JS usado en todos los módulos |
| **Draft-07** | Versión del estándar JSON Schema usada para validar contratos |
