# students

Módulo de encuestas estudiantiles. Contiene scripts ETL, documentación de contratos e instancias de dashboard por nivel académico y periodo.

> ⚠️ **Los CSVs ahora residen en `../../data/` (raíz del proyecto).**  
> El template HTML está en `../template/` (compartido con todos los tipos de encuesta).

## Purpose

Implementar el pipeline de datos para encuestas estudiantiles: desde la ingesta de CSV hasta la generación de dashboards autónomos por nivel académico (pregrado, posgrado, graduados) y periodo.

## Architecture Role

Módulo del dominio de encuestas estudiantiles. Implementa el pipeline desde los datos crudos hasta los dashboards. Se organiza en tres niveles activos: `undergraduate/`, `graduate/` y `postgraduate/`.

## Submodules

| Submodule     | Path             | Status      | Responsibility                                                             |
| ------------- | ---------------- | ----------- | -------------------------------------------------------------------------- |
| Scripts       | `../scripts/`    | Active      | ETL pipeline (build_json.py) + JSON validator (validate_generated_json.py) |
| Undergraduate | `undergraduate/` | Active      | Dashboard instances for undergraduate surveys (2025-2, 2026-1)             |
| Graduate      | `graduate/`      | Active      | Dashboard instances for graduate surveys (2026)                            |
| Postgraduate  | `postgraduate/` | Placeholder | Empty structure awaiting postgraduate survey data                          |

## Key Files

| File                                                            | Responsibility                                  |
| --------------------------------------------------------------- | ----------------------------------------------- |
| `../../data/*.csv`                                              | Raw survey data from Zoho Survey (project root) |
| `../scripts/build_json.py`                                      | ETL: transforms CSV → JSON contracts per period |
| `../scripts/validate_generated_json.py`                         | Validates JSON contract compliance              |
| `../template/index.html`                                        | Scaffold copied to new periods                  |
| `../../docs/filter-logic.md`                                     | Filter cascade logic specification              |
| `../../CONTRACTS.md`                                             | Contratos de datos (version humana) + `../scripts/schemas/` |

## Data Flow

```
../../data/*.csv → build_json.py → {level}/{periodo}/json/*.json
                                       → {level}/{periodo}/index.html (from ../template/)
                                       → {level}/periodos.json (auto-updated)
```

## Execution Flow

Todo ocurre en GitHub Actions; no hay ejecución local.

1. El CSV se envía por el portal ("Subir datos") o se adjunta a un Release y se lanza `workflow_dispatch` con `release_tag`.
2. Actions lo descarga a `data/` (solo en el runner) y valida nombre y headers (`validate_upload_csv.py`).
3. Sanitiza PII (`sanitize_csv_pii.py`) y ejecuta `build_json.py`, que detecta el nivel por palabras clave del nombre (GRADUADOS, PREGRADO, POSGRADO, …) y el periodo por regex `(20\d{2}(?:-[12])?)`.
4. Transforma el CSV en 21 pasos (mapeo de columnas, agregación, NPS/CSAT, IA cualitativa con DeepSeek, insights).
5. Escribe los JSON del periodo en `{level}/{period}/json/`, copia `../template/index.html` si falta y actualiza `{level}/periodos.json`.

## Dependencies

- **Internal**: Consumes `shared/` CSS, JS and images for rendering
- **Scripts**: `build_json.py` y `validate_generated_json.py` son independientes entre sí
- **CSV source**: `../../data/` (project root)

## Configuration

- `periodos.json` por nivel — auto-generado por `build_json.py`. Define orden cronológico y flag `isNew`.
- La detección de nivel se hace por nombre de archivo. Orden de prioridad: `NO DOCENTES` → `EMPLEADORES` → `EGRESADOS` → `DOCENTES` → `GRADUADOS` → `ESTUDIANTIL/ESTUDIANTES`.

## Deuda técnica y mejoras

El registro único de deuda técnica del proyecto vive en [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) (§ "Deuda Técnica Vigente"). No se duplica aquí.

## AI Agent Notes

- Contratos de datos: `../../CONTRACTS.md` y los schemas de `../scripts/schemas/`. Lógica de filtros: `../../docs/filter-logic.md`.
- El ETL copia `../template/index.html` solo si no existe en el directorio del periodo.
- La validación de contratos y los tests corren **solo en GitHub Actions**; no se ejecutan comandos en local.
- Los CSV llegan al runner por el portal o por un Release con tag (prefijo `ENCUESTA` en el nombre) y nunca se commitean.
- El entry point del navegador es `zoho-survey/index.html` (no `students/undergraduate/index.html`).
