# Entorno de ejecución — survey-test

> **Regla del proyecto: nada se ejecuta en local.** El ETL, las pruebas, la validación de contratos y el despliegue ocurren **exclusivamente en GitHub Actions**. La verificación se hace sobre el resultado del workflow (paso a paso) y, cuando se requiere el log íntegro, sobre el log del run.

## Ciclo de trabajo

```
Editar archivos → commit → push a main → GitHub Actions (pruebas + ETL si hay CSV + deploy) → verificar en Actions
```

Ningún paso requiere Python, Node ni dependencias instaladas en el equipo: solo Git.

| Fase | Dónde corre | Workflow | Qué ejecuta |
|---|---|---|---|
| Pruebas | GitHub Actions | `tests.yml` | `unittest` (Python), tests JS en Node, tests DOM con jsdom, sintaxis de todos los módulos, validación de contratos JSON, Ruff y ESLint (informativos) |
| ETL + IA | GitHub Actions | `build_zoho_survey.yml` | Selección de CSV → gate `Detectar CSVs` → sanitización PII → `build_json.py` (DeepSeek + fallback NVIDIA) → validación de JSON |
| Despliegue | GitHub Actions | `build_zoho_survey.yml` | Artifact → GitHub Pages → health check → commit del bot si hay JSON nuevos |

Ambos workflows se disparan con **cualquier push a `main`** (sin filtros de `paths`), para que ningún cambio quede sin verificar.

## Cómo se envían los datos (sin entorno local)

1. **Portal "Subir datos"** (recomendado): `zoho-survey/index.html` → Release DRAFT temporal → `repository_dispatch[csv_upload]`.
2. **Release con tag + `workflow_dispatch`** (alternativa sin navegador): subir el CSV como asset de un Release (preferiblemente **DRAFT**) y lanzar *Build and Deploy Survey* con el input `release_tag`.

En ambos caminos el CSV se descarga **solo en el runner**, se sanitiza, se procesa y se **borra antes del commit del bot** (el commit aborta si detecta un CSV en staging).

Sin CSV en `data/`, el workflow **no** ejecuta el ETL ni exige `DEEPSEEK_API_KEY`: solo valida contratos y despliega el sitio.

## Secretos

| Secreto / variable | Dónde se configura | Para qué |
|---|---|---|
| `DEEPSEEK_API_KEY` | Settings → Secrets and variables → Actions | Motor IA principal del ETL |
| `NVIDIA_API_KEY` | Ídem (opcional) | Fallback cuando DeepSeek falla o no está configurado |

`.env` es local y **no** interviene en el ciclo: las claves viven en GitHub Secrets.

## Verificación del resultado

| Quiero saber… | Cómo |
|---|---|
| ¿Pasó o falló? ¿En qué paso? | Pestaña **Actions** → run → job → pasos con su conclusión |
| ¿Cuál fue el mensaje de error? | Anotaciones del check-run del job (`check-runs/<job_id>/annotations`) |
| ¿El sitio está en pie? | `https://universidad-de-lima.github.io/survey-test/` y `health.html` |
| ¿Los contratos JSON son válidos? | Paso `Validate generated JSON contracts` del workflow de build |

Documentación relacionada: [`README.md`](README.md), [`docs/developer-guide.md`](docs/developer-guide.md), [`docs/INGESTA_Y_DESCARGA.md`](docs/INGESTA_Y_DESCARGA.md), [`tests/README.md`](tests/README.md), [`SECURITY.md`](SECURITY.md).
