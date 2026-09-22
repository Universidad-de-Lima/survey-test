# survey-test v3.9.0

[![Build and Deploy](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/build_zoho_survey.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/build_zoho_survey.yml)
[![Tests](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/tests.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/tests.yml)

Sistema estático de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte CSV exportados desde Zoho Survey en dashboards interactivos, sin backend ni base de datos, desplegables en GitHub Pages.

Arquitectura: Portal v5.0 (`index.html` + `portal.js` + módulos `portal/*`) para navegación multi-fase; dashboards individuales por periodo (`template/index.html` + `dashboard.js` + componentes) renderizan JSONs estáticos generados por ETL Python (`build_json.py`) con cadena de motores IA (OpenCode, Google, NVIDIA).

## Quick Start

**Regla del proyecto: nada se ejecuta en local.** El procesamiento de CSVs, la generación de JSONs, las pruebas y el despliegue ocurren exclusivamente en **GitHub Actions**; la verificación se hace sobre los resultados del workflow.

```bash
# 1. Clonar el repositorio
git clone https://github.com/Universidad-de-Lima/survey-test.git
cd survey-test

# 2. Editar los archivos necesarios

# 3. Commit y push (cada push a main se prueba y se despliega en Actions)
git add .
git commit -m "descripción del cambio"
git push origin main

# 4. Verificar en GitHub Actions: cada push dispara "Tests" (unittest + JS + jsdom
#    + sintaxis + contratos JSON) y "Build and Deploy Survey" (deploy a Pages).
#    Los datos de entrada del ETL se envían por Release + workflow_dispatch:
#    ver docs/INGESTA_Y_DESCARGA.md
```

Punto de entrada técnico del ciclo: `docs/developer-guide.md`.

## Ingesta de encuestas

- **Webhook de Zoho Survey**: cada respuesta crea una incidencia y `zoho_inbox.yml` la guarda **enmascarada** en `data/zoho_pendientes/`. Ver `ARCHITECTURE.md` § "Ingesta De Encuestas".
- **Sin credenciales en el navegador**: el portal solo lee los JSON publicados en GitHub Pages. El único PAT (Personal Access Token - Token de Acceso Personal) vive en la cabecera del webhook dentro de Zoho.
- **Sin servicios externos**: GitHub Pages + API + GitHub Actions (no hay Cloudflare, Supabase ni backend).
- **Sin CSV en el historial**: el CSV entra por un Release y se borra antes del commit del bot; `data/` está en `.gitignore`.
- Los CSVs se limpian (IP/Agente Usuario/URL) antes del ETL y los comentarios NPS se ofuscan antes de enviarlos a los motores IA.
## Documentación del Proyecto

Este repositorio sigue una estructura de documentación modularizada con responsabilidades únicas para evitar duplicación de contenido:

* **Reglas Operativas:** [AGENTS.md](AGENTS.md) contiene las directivas obligatorias de codificación para agentes de IA y desarrolladores.
* **Diseño Técnico:** [ARCHITECTURE.md](ARCHITECTURE.md) describe la arquitectura del sistema, el mapa de componentes, la estructura física de directorios (incluyendo la aplicación `zoho-survey/`) y el registro único de deuda técnica del código.
* **Contratos de Datos:** [CONTRACTS.md](CONTRACTS.md) especifica las entradas CSV, salidas JSON, schemas estructurados, invariantes matemáticas y deuda técnica de datos.
* **Guías de Procedimiento:** [docs/developer-guide.md](docs/developer-guide.md) detalla flujos comunes como la adición de periodos, cambio de metas u otros tópicos.
* **Lógica del Dashboard:** [docs/filter-logic.md](docs/filter-logic.md) describe las reglas del negocio aplicadas a los filtros en cascada del frontend.
* **Pruebas de Unidad:** [tests/README.md](tests/README.md) detalla cómo ejecutar y extender los tests unitarios.
* **Health Check:** [zoho-survey/health.html](zoho-survey/health.html) verifica la integridad de todos los dashboards y JSONs por periodo.
* **Changelog:** [docs/CHANGELOG.md](docs/CHANGELOG.md) contiene el historial de cambios del proyecto.
* **Onboarding:** [docs/onboarding.md](docs/onboarding.md) es la guía de inicio para nuevos desarrolladores y analistas.
* **Entrada y salida de datos:** [docs/INGESTA_Y_DESCARGA.md](docs/INGESTA_Y_DESCARGA.md) es la fuente única del flujo (webhook, bandeja, ETL y descargas).
* **Seguridad:** [SECURITY.md](SECURITY.md) resume el tratamiento de datos personales y credenciales.
* **Entorno y ejecución:** [DEV_ENVIRONMENT.md](DEV_ENVIRONMENT.md) describe cómo corre todo en GitHub Actions y qué secretos hacen falta.
* **Módulos del frontend:** [zoho-survey/shared/README.md](zoho-survey/shared/README.md) documenta los módulos JS, el orden de carga y su deuda técnica.
