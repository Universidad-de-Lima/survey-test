# survey-test v3.8.2

[![Build and Deploy](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/build_zoho_survey.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/build_zoho_survey.yml)
[![Tests](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/tests.yml/badge.svg)](https://github.com/Universidad-de-Lima/survey-test/actions/workflows/tests.yml)

Sistema estático de visualización de encuestas de satisfacción para la Universidad de Lima. Convierte CSV exportados desde Zoho Survey en dashboards interactivos, sin backend ni base de datos, desplegables en GitHub Pages.

Arquitectura: Portal v5.0 (`index.html` + `portal.js` + módulos `portal/*`) para navegación multi-fase; dashboards individuales por periodo (`template/index.html` + `dashboard.js` + componentes) renderizan JSONs estáticos generados por ETL Python (`build_json.py`) con motor IA DeepSeek y fallback NVIDIA.

## Quick Start

El procesamiento de CSVs y la generación de JSONs se ejecutan en **GitHub Actions**. Para trabajar localmente solo se editan archivos; las pruebas funcionales ocurren tras el `push`:

```bash
# 1. Clonar el repositorio

git clone https://github.com/Universidad-de-Lima/survey-test.git
cd survey-test

# 2. Validar sintaxis y tests unitarios (no requieren API keys)
npm run test:js
npm run test:py

# 3. Hacer cambios, commit y push

git add .
git commit -m "descripción del cambio"
git push origin main

# 4. GitHub Actions compila, valida y despliega automáticamente
#    Ver progreso en: https://github.com/Universidad-de-Lima/survey-test/actions
```

Para una vista local estática (solo HTML/JS, sin JSONs generados):

```bash
npm start
# Abrir http://localhost:8080/zoho-survey/
```

## Subir datos (Ingesta de encuestas)

- El portal `zoho-survey/index.html` incluye el botón **"Subir datos"**: el propietario sube CSV(s) desde el navegador y GitHub los procesa solo.
- **Sin servicios externos**: GitHub Pages + API + GitHub Actions (no hay Cloudflare, Supabase ni backend).
- **Sin tokens expuestos**: el PAT del owner vive solo en memoria del navegador y se usa contra `api.github.com`; Actions usa `GITHUB_TOKEN`.
- **Sin CSV en el historial**: el CSV viaja a un Release temporal que se borra; `data/` está en `.gitignore` y el commit está desactivado para uploads.
- Los CSVs se limpian (IP/UA/URL) antes del ETL y los comentarios NPS se ofuscan antes de DeepSeek.

> Ingesta implementada en Fase 3.8.2. Ver `ARCHITECTURE.md` § "Ingesta De Encuestas" y `docs/INGESTA_Y_DESCARGA.md`.
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
