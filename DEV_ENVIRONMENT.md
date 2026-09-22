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
| ETL + IA | GitHub Actions | `build_zoho_survey.yml` | Selección de CSV → gate `Detectar CSVs` → sanitización PII → `build_json.py` (cadena de motores IA: OpenCode → Google → NVIDIA) → validación de JSON |
| Despliegue | GitHub Actions | `build_zoho_survey.yml` | Artifact → GitHub Pages → health check → commit del bot si hay JSON nuevos |
| Ingesta Zoho | GitHub Actions | `zoho_inbox.yml` | Recibe la incidencia que crea el webhook de Zoho Survey (cuerpo = respuesta en JSON, título = nombre de la encuesta), la enmascara y la guarda en `data/zoho_pendientes/`. No ejecuta el ETL |

Los workflows de pruebas y de build se disparan con **cualquier push a `main`** (sin filtros de `paths`), para que ningún cambio quede sin verificar. El de ingesta (`zoho_inbox.yml`) no depende de un push: lo dispara la incidencia que crea el webhook de Zoho (o se ejecuta a mano desde Actions con un JSON de prueba).

## Cómo se envían los datos (sin entorno local)

El detalle del flujo de entrada y salida de datos vive en **`docs/INGESTA_Y_DESCARGA.md`** (fuente única). En resumen: el webhook acumula las respuestas enmascaradas en `data/zoho_pendientes/` y el ETL se lanza a mano desde un Release con el input `release_tag`.

El CSV se descarga **solo en el runner**, se sanitiza, se procesa y se **borra antes del commit del bot** (el commit aborta si detecta un CSV en staging).

Sin CSV en `data/`, el workflow **no** ejecuta el ETL ni exige claves de los motores IA: solo valida contratos y despliega el sitio.

## Secretos

| Secreto / variable | Dónde se configura | Para qué |
|---|---|---|
| `GOOGLE_API_KEY` | Settings → Secrets and variables → Actions | Primer motor de la cadena (Google Gemini) |
| `NVIDIA_API_KEY` | Ídem (opcional) | Motores 2.º a 5.º (NVIDIA NIM: kimi-k3, deepseek-v4-pro, nemotron, muse-glimmer) |
| `OPENCODE_API_KEY` | Ídem (opcional) | Último motor de la cadena (OpenCode) |
| `IA_CUALITATIVO_CADENA` (variable, no secreto) | Ídem → pestaña **Variables** | Orden y modelos de la cadena, sin tocar código |

Al menos **una** de las tres claves debe estar configurada cuando hay CSV que procesar.

`.env` es local y **no** interviene en el ciclo: las claves viven en GitHub Secrets.

## Verificación del resultado

| Quiero saber… | Cómo |
|---|---|
| ¿Pasó o falló? ¿En qué paso? | Pestaña **Actions** → run → job → pasos con su conclusión |
| ¿Cuál fue el mensaje de error? | Anotaciones del check-run del job (`check-runs/<job_id>/annotations`) |
| ¿El sitio está en pie? | `https://universidad-de-lima.github.io/survey-test/` y `health.html` |
| ¿Los contratos JSON son válidos? | Paso `Validate generated JSON contracts` del workflow de build |

Documentación relacionada: [`README.md`](README.md), [`docs/developer-guide.md`](docs/developer-guide.md), [`docs/INGESTA_Y_DESCARGA.md`](docs/INGESTA_Y_DESCARGA.md), [`tests/README.md`](tests/README.md), [`SECURITY.md`](SECURITY.md).
