# Tests

Infraestructura de tests unitarios para `survey-test`. No usa dependencias npm ni Vitest; se ejecuta en navegador con un mini-framework propio (`tests/test-framework.js`) o en Node con jsdom.

## Ejecutar Tests

### Opción 1: Navegador (recomendado para desarrollo)

Abrir directamente:

```text
tests/run-tests.html
```

O servir el repositorio y abrir la ruta en navegador:

```bash
npm start
# http://localhost:8080/tests/run-tests.html
```

### Opción 2: Node (sin DOM, para CI)

```bash
npm run test:js
```

Ejecuta los tests que no requieren DOM real (usan un stub mínimo de `window`/`document`).

### Opción 3: Node con jsdom (para tests que necesitan DOM real)

```bash
npm run test:js:dom
```

Ejecuta `tests/unit/test-dom.js` con jsdom.

### Opción 4: CI (GitHub Actions)

Los tests se ejecutan automáticamente en cada PR y push a `main` vía `.github/workflows/tests.yml`:
- `python-tests`: ejecuta `python -m unittest discover tests/` en `zoho-survey/scripts/`.
- `js-tests`: ejecuta `npm run test:js` + `npm run test:js:dom` + verificación de sintaxis con `node -c`.

## Estructura

```text
tests/
├── run-tests.html              # Runner HTML para navegador
├── test-framework.js           # Mini-framework: assert, describe, it, renderTo
└── unit/
    ├── test-config.js          # SURVEY_CONFIG (9 tests)
    ├── test-formatters.js      # SurveyFormatters (26 tests)
    ├── test-metrics.js         # SurveyMetrics (11 tests)
    ├── test-sanitizer.js       # SurveySanitizer (22 tests)
    ├── test-sentiment-view.js  # SurveySentimentView API surface (9 tests)
    ├── test-filter-controller.js  # SurveyFilterController (16 tests)
    ├── test-insights-ia.js     # Insights IA (4 tests)
    ├── test-upload-validator.js # Validación ingesta CSV (35 tests, TestFramework)
    └── test-dom.js             # Tests con jsdom (33 tests, dialecto propio)
```

## Agregar Un Test

### Tests con TestFramework (recomendado)

1. Crear `tests/unit/test-<nombre>.js`.
2. Usar el patrón IIFE y `window.TestFramework`.
3. Registrar el archivo con `<script>` en `tests/run-tests.html`.
4. Para ejecución en CI, añadir el archivo al script inline en `package.json` (`test:js`) y en `.github/workflows/tests.yml`.
5. Abrir el runner y verificar el resultado.

```javascript
(() => {
  'use strict';
  const { assert, describe, it } = window.TestFramework;
  const modulo = window.SurveyMiModulo;

  describe('miModulo', () => {
    it('hace X', () => {
      assert.equal(modulo.miFuncion('input'), 'expected');
    });
  });
})();
```

### Tests con jsdom (para tests que necesitan DOM real)

Usar el patrón de `tests/unit/test-dom.js` con su propio runner inline (`test()`, `assertEqual()`, `assertTrue()`).

## Cobertura Actual

Estado verificado sobre el repositorio completo (2026-07, Fase 1 de limpieza).

### Tests con TestFramework

| Archivo | Tests reales | Módulo bajo prueba |
| --- | --- | --- |
| `test-config.js` | 9 | `SurveyConfig` (SURVEY_CONFIG) |
| `test-formatters.js` | 26 | `SurveyFormatters` |
| `test-metrics.js` | 11 | `SurveyMetrics` |
| `test-sanitizer.js` | 22 | `SurveySanitizer` |
| `test-sentiment-view.js` | 9 | `SurveySentimentView` API surface |
| `test-filter-controller.js` | 16 | `SurveyFilterController` |
| `test-insights-ia.js` | 4 | Insights IA |
| `test-upload-validator.js` | 35 | Validación de nombre/headers/tamaño de CSVs de ingesta (`portal-upload.js`) |

### Tests con jsdom

| Archivo | Tests reales | Módulo bajo prueba |
| --- | --- | --- |
| `test-dom.js` | 33 | `SurveyFormatters`, `SurveySanitizer`, `SurveyDomHelpers`, `SurveyTooltip` (con DOM real) |

### Total: 132 tests TestFramework (97 base + 35 de `test-upload-validator.js`) + 33 tests jsdom = 165 tests

> **Historial:** un snapshot previo de auditoría reportaba `test-sanitizer.js` vacío y
> `test-sentiment-view.js` ausente; ambos fueron verificados y restaurados/implementados
> en su totalidad. `test-formatters.js` fue corregido en Fase 0 (esperaba `"30,00%"` sin
> espacio; la implementación — consistente con `formatPercent`, `formatPctDecimal`,
> `formatScore` — retorna `"30,00 %"` con espacio; el test ahora espera el espacio).
> `test-loader.js` (16 tests) fue eliminado en Fase 2 junto con `loader.js` (código muerto).

## Tests Python

Los tests Python viven en `zoho-survey/scripts/tests/` y se ejecutan con:

```bash
cd zoho-survey/scripts && python -m unittest discover tests/ -v
```

Ver `zoho-survey/scripts/tests/` para detalle de cobertura Python (tests `test_*.py`).

## Notas

- **Tests eliminados en Fase 1**: `test-tooltip.js`, `test-multiselect.js`, `test-progress-bar.js`, `test-radar-chart.js`, `test-custom-select.js` fueron eliminados porque nunca se cargaban en ningún runner y tenían un bug latente (`assert.true` no existe en el framework, solo `assert.isTrue`).
- **Tests E2E**: Playwright fue eliminado en Fase 2 porque nunca se integró al CI. Si se quiere E2E real, planificar en una fase futura con cobertura más amplia.
- **Linting**: Ruff (Python) y ESLint (JS) se ejecutan en CI de forma informativa desde Fase 2. Se harán estrictos en Fase 3 tras auto-fixear las violaciones existentes.
- **Validación de ingesta**: cliente (`tests/unit/test-upload-validator.js`, 28 tests) y server-side (`zoho-survey/scripts/tests/test_validate_upload_csv.py`, 17 tests).
