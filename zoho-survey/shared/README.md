# shared

Componentes reutilizables compartidos entre todos los módulos de encuesta del sistema. Contiene estilos, JavaScript e imágenes utilizados por los dashboards de todos los niveles académicos.

## Purpose

Proveer la capa de presentación base (CSS, JS, imágenes) que consume cada instancia de dashboard de periodo y el portal v5.0, garantizando consistencia visual y comportamental sin duplicación de código.

## Architecture Role

Capa de presentación base. Proporciona el sistema de diseño (CSS), la lógica de visualización (JS) y los assets gráficos que consumen:
- **Portal v5.0** (`zoho-survey/index.html` + `portal.js`): navegación multi-fase entre tipos de encuesta y periodos.
- **Dashboards por periodo** (`template/index.html` + `dashboard.js`): renderizado de JSONs estáticos.

## Key Files

| File | Lines | Responsibility |
| --- | --- | --- |
| `css/tokens.css` | 118 | Design tokens: 13 colores institucionales, tipografía (Roboto), z-index (8 niveles), espaciados (9), radios (8), sombras (3). |
| `css/reset.css` | 69 | Reset universal + utilidades base (`.skip-link`, `.sr-only`, `.text-center`, `.mt-4`, `.software-italic`). |
| `css/layout.css` | 174 | Sticky header, nav links, progress bar, main-content grid, footer. |
| `css/components.css` | 864 | KPI cards, distribution bars, filter system, custom select/multiselect, bar charts, radar SVG, tables (sticky header), heatmap, tooltip. |
| `css/sections.css` | 244 | Selectores específicos de tabla + 3 media queries (1100/768/480px). |
| `css/portal/` | — | `portal-base.css`, `portal-components.css`, `portal-sections.css`: estilos del portal v5.0. |
| `js/portal.js` | 636 | Orquestador del portal v5.0: init, renderSidebar, navegación de fases, carga de periodos. |
| `js/portal/` | — | 5 módulos de vista del portal: `portal-data.js` (484), `portal-dashboard.js` (184), `portal-filters.js` (261), `portal-radar.js` (538), `portal-survey.js` (1050). |
| `js/dashboard.js` | 1,270 | Orquestador principal del dashboard SPA individual. 4 secciones, filtros en cascada, rendering SVG, tooltips, KPIs, tablas. |
| `js/config/constants.js` | 71 | `window.SURVEY_CONFIG`: metas, carreras/facultades 12 ciclos, SAT_KEYS, umbrales visuales, configuración radar. |
| `js/utils/formatters.js` | 105 | `window.SurveyFormatters`: formateo es-PE (integer, decimal, percent, pctSimple, pctDecimal, date, ciclo text, dimension name). |
| `js/utils/metrics.js` | 86 | `window.SurveyMetrics`: `calcBoxScore`, `calcPromedioPonderado`, `deriveT2B`, `derivePonderado`. Gemelo JS de `lib/metrics.py`. |
| `js/utils/sanitizer.js` | 100 | `window.SurveySanitizer`: `escapeHTML`, `sanitizeHTML` (whitelist: 9 tags — `br`, `strong`, `em`, `i`, `span`, `table`, `tr`, `td`, `th`). |
| `js/utils/dom-helpers.js` | 120 | `window.SurveyDOMHelpers`: `$`, `esEstudiosGen`, `sumKeys`, `getSelectedValues`, `setSelectedValues`, `formatMultiselectLabel`, placeholders. |
| `js/components/tooltip.js` | 141 | `window.SurveyTooltip`: `show`, `hide`, `move`, `bindToSegments`. |
| `js/components/progress-bar.js` | 77 | `window.SurveyProgressBar.init(options)`: barra de scroll con IntersectionObserver. |
| `js/components/custom-select.js` | 157 | `window.SurveyCustomSelect.create(sel, onChange)`: selectores desplegables personalizados con ARIA. |
| `js/components/multiselect.js` | 161 | `window.SurveyMultiselect.create(selCic, onChange, defaultLabel, itemName)`: listas de selección múltiple. |
| `js/components/filter-controller.js` | 181 | `window.SurveyFilterController.{setup, esEstudiosGen, getCiclosForFiltro}`: filtros en cascada. |
| `js/components/radar-chart.js` | 520 | `window.SurveyRadarChart.{render, dimensionAplica}`: radar SVG nativo con animaciones SMIL. |
| `js/components/sentiment-view.js` | 1,036 | `window.SurveySentimentView.{init, updateMacro, updateAspectos, updateNpsCarrera, updateDetalle, applyExploradorFilters}`: visual cualitativo v3.0.0. |
| `img/` | — | `logo-horizontal.png`, `logo-vertical.png`, `logo-isotipo.png`, `favicon.png`, `todo-posible.webp`. |

## Data Flow

### Portal v5.0 (producción)

```
index.html → portal.js (IIFE)
    ↓
fetch periodos.json por fase (undergraduate/graduate/etc.)
    ↓
renderSidebar (pills por fase + periodos expandibles)
    ↓
Usuario selecciona fase → renderDashboardCards (NPS bar + KPIs por periodo)
    ↓
Usuario selecciona periodo → portal-survey.js renderiza vista completa (sin iframe)
    ↓
Consume JSONs del periodo directamente (dashboard_data, dimensiones, nps_ciclo_carrera, csat_ciclo_carrera, filtros, sentimiento, ids)
```

### Dashboard individual por periodo (template)

```
template/index.html → dashboard.js (IIFE, auto-init en DOMContentLoaded)
    ↓
Promise.all: dashboard_data.json + filtros.json + dimensiones.json (críticos)
    ↓
carga opcional (tolerante a fallos): nps_ciclo_carrera, csat_ciclo_carrera, nps_carrera, csat_carrera, ids, sentimiento
    ↓
Inicializa 5 grupos de filtros en cascada via SurveyFilterController.setup()
    ↓
Configura barra de progreso via SurveyProgressBar.init()
    ↓
Renderiza 4 secciones en orden: Ejecutivo → Operativo → Detallado → Cualitativo
```

## Design Tokens (CSS)

Variables CSS en `tokens.css` (`:root`):

- Colores institucionales: `--ulima-orange: #FF5117`, `--ulima-red: #FF0000`, escala de grises `--gray-50` a `--gray-900`.
- Estados semánticos: `--success-pastel/text`, `--warning-pastel/text`, `--danger-pastel/text`.
- Tipografía: `--font-family-primary: 'Roboto'`, pesos 300/400/500/700/900.
- Accesibilidad: `--focus-outline`, `--focus-outline-offset`.
- Z-index: 8 niveles (`--z-base: 1` a `--z-splash: 99999`).
- Espaciados: 9 escalas (`--space-xs: 4px` a `--space-5xl: 68px`).
- Radios: 8 niveles (`--radius-xs: 2px` a `--radius-full: 9999px`).
- Splash bg: `--splash-bg: #F37021`.

## APIs globales (`window.Survey*`)

| Módulo | API pública | Dependencias internas |
| --- | --- | --- |
| `constants.js` | `window.SURVEY_CONFIG` (objeto plano) | Ninguna. |
| `formatters.js` | `window.SurveyFormatters.{formatInteger, formatDecimal, formatPercent, formatPctSimple, formatPctDecimal, formatDate, formatCicloText, cortarTexto, formatDimensionName, formatDimensionNameSVG, formatDimensionNameForAttr}` | Ninguna. Funciones puras. |
| `sanitizer.js` | `window.SurveySanitizer.{escapeHTML, sanitizeHTML}` | Ninguna. |
| `dom-helpers.js` | `window.SurveyDOMHelpers.{$, esEstudiosGen, sumKeys, getSelectedValues, setSelectedValues, getPlaceholderText, formatCustomLabel, formatMultiselectLabel}` | Ninguna. Helpers de negocio acceden a `SURVEY_CONFIG` internamente. |
| `tooltip.js` | `window.SurveyTooltip.{show, hide, bindToSegments}` | `SurveySanitizer` (opcional, fallback a escape manual). `move` NO existe. |
| `progress-bar.js` | `window.SurveyProgressBar.init(options)` | Ninguna. |
| `custom-select.js` | `window.SurveyCustomSelect.create(sel, onChange)` → `{update, close, button, wrapper}` | `SurveyDOMHelpers` (requerida). |
| `multiselect.js` | `window.SurveyMultiselect.create(selCic, onChange, defaultLabel, itemName)` → wrapper HTMLElement con `.update()` | `SurveyDOMHelpers` (requerida). |
| `filter-controller.js` | `window.SurveyFilterController.{setup, esEstudiosGen, getCiclosForFiltro}` | `SurveyCustomSelect`, `SurveyMultiselect`, `SurveyDOMHelpers`. |
| `radar-chart.js` | `window.SurveyRadarChart.{render, dimensionAplica}` | `SurveyFormatters`, `SurveySanitizer`, `SurveyMultiselect`, `SurveyDOMHelpers`, `SURVEY_CONFIG`. |
| `sentiment-view.js` | `window.SurveySentimentView.{init, updateMacro, updateAspectos, updateNpsCarrera, updateDetalle, applyExploradorFilters}` | `SurveyFormatters`, `SurveyDOMHelpers`, `SurveySanitizer`, `SurveyTooltip`, `SurveyCustomSelect`, `SURVEY_CONFIG`. |
| `dashboard.js` | (privado, ejecuta `init()` automáticamente) | Todos los anteriores. |
| `portal.js` | `window.selectSurvey(id)`, `window.loadPeriod(id)` (compatibilidad inline) | `SurveyPortalCore`, `SurveyPortalData`, `SurveyPortalDashboard`, `SurveyPortalFilters`, `SurveyPortalRadar`, `SurveyPortalSurvey`. |

## Order of Script Loading (Critical)

El orden de carga es crítico y verificado por `scripts/tests/test_html_contract.py`.

### Template (`template/index.html` y `students/*/*/index.html`) — 13 scripts

```html
<!-- 1. Config primero -->
<script src=".../config/constants.js"></script>
<!-- 2. Utils (sin dependencias internas) -->
<script src=".../utils/formatters.js"></script>
<script src=".../utils/sanitizer.js"></script>
<script src=".../utils/dom-helpers.js"></script>
<!-- 3. Components simples -->
<script src=".../components/tooltip.js"></script>
<script src=".../components/progress-bar.js"></script>
<!-- 4. Components con dependencias -->
<script src=".../components/custom-select.js"></script>
<script src=".../components/multiselect.js"></script>
<script src=".../components/filter-controller.js"></script>
<script src=".../components/radar-chart.js"></script>
<script src=".../components/sentiment-view.js"></script>
<!-- 5. Orquestador al final -->
<script src=".../dashboard.js"></script>
```

> **Advertencia crítica:** `dom-helpers.js` debe cargarse **siempre antes** que `custom-select.js` y `multiselect.js`. Sin esto, `window.SurveyDOMHelpers` es undefined al evaluar el IIFE de custom-select y cualquier interacción falla con `TypeError`.

### Portal (`zoho-survey/index.html`) — 14 scripts

```html
<script src=".../config/constants.js"></script>
<script src=".../utils/sanitizer.js"></script>
<script src=".../components/tooltip.js"></script>
<script src=".../utils/dom-helpers.js"></script>
<script src=".../utils/formatters.js"></script>
<script src=".../components/sentiment-view.js"></script>
<script src=".../components/custom-select.js"></script>
<script src=".../components/multiselect.js"></script>
<script src=".../portal/portal-data.js"></script>
<script src=".../portal/portal-dashboard.js"></script>
<script src=".../portal/portal-radar.js"></script>
<script src=".../portal/portal-filters.js"></script>
<script src=".../portal/portal-survey.js"></script>
<script src=".../portal.js"></script>
```

## Configuration

Constantes en `config/constants.js` (`window.SURVEY_CONFIG`):

- `META_NPS = 50` — umbral target NPS.
- `META_CSAT = 93` — umbral target CSAT.
- `META_EMPLEABILIDAD = 85` — umbral target empleabilidad.
- `CARRERAS_12_CICLOS = ['Derecho', 'Psicología']` — carreras con 12 ciclos.
- `FACULTADES_12_CICLOS` — facultades con 12 ciclos.
- `CICLOS_ESTUDIOS_GENERALES = ['1° Ciclo', '2° Ciclo']` — ciclos limitados para Estudios Generales.
- `SAT_KEYS` — 5 niveles Zoho Survey (`Totalmente satisfecho`, `Muy satisfecho`, `Satisfecho`, `Insatisfecho`, `Totalmente insatisfecho`).
- Umbrales visuales: `>= META_CSAT (93) → high`, `>= 80 → medium`, `< 80 → low`.
- Visibilidad: `>= 50% → critico`, `25-50% → moderado`.

`dashboard.js` mantiene constantes duplicadas con fallback `??` a `SURVEY_CONFIG` por compatibilidad backward.

## Technical Debt

- **Módulos JS sin tests unitarios directos**: `portal.js`, `portal/*` (5), `custom-select.js`, `multiselect.js`, `filter-controller.js`, `radar-chart.js`, `sentiment-view.js`, `dashboard.js` (9 de 19 módulos). Suite JS: 94 tests TestFramework + 33 jsdom = 127 tests (fuente: `tests/README.md`).
- **No hay sistema de módulos ES**: usa IIFE + closures. El orden de carga es crítico.
- **Custom select dropdowns**: implementación manual (~200 líneas entre `custom-select.js` y `multiselect.js`). Posible fuente de bugs cross-browser.
- **`tooltip.move(e)`**: implementado en `tooltip.js` (boundary detection); usado en `sentiment-view.js` para listeners `mousemove`.

## Improvement Opportunities

- Migrar a ES modules (`<script type="module">`) para eliminar dependencia de orden de carga.
- Implementar boundary detection y `move()` en `tooltip.js`.
- Agregar tests con jsdom para `dashboard.js`, `filter-controller`, `radar-chart`, `sentiment-view`, módulos portal.
- Implementar carga lazy de JSON por sección.
- Unificar lógica duplicada entre `portal/*` y `components/*` + `dashboard.js`.

## AI Agent Notes

- Los **IDs HTML son contratos públicos** con `dashboard.js`, `filter-controller.js` y módulos portal. No renombrar sin actualizar simultáneamente el JS.
- IDs críticos del template: `kpi-csat-value/bar/meta`, `kpi-nps-value/bar/meta`, `csat-bar`, `nps-bar`, `radar-chart`, `filter-facultad-{top3,radar,preguntas,detalle,visibilidad}`, `filter-carrera-{...}`, `filter-ciclo-{...}`, `reset-{...}`, `tabla-explorador-comentarios`, `intensidad-positivos-container`, etc.
- Las funciones globales son `window.SurveyTooltip.show` / `window.SurveyTooltip.hide` (NO `window.showTooltip` / `window.hideTooltip`).
- `dashboard.js` espera que los `<select>` tengan atributo `data-multiselect="true"` para activar el dropdown multiselect.
- La sección cualitativa usa `id="cualitativo"` y `id="cualitativo-heading"` como IDs técnicos aunque la etiqueta visible sea "Cualitativo" y "ANÁLISIS CUALITATIVO".
- `#progress-fill` es requerido para la barra de progreso de scroll.
- **`SurveyTooltip.move(e)`** implementado; usado en `sentiment-view.js` para listeners `mousemove`.
- **NO referenciar `window.cache`** (es privada en el IIFE de `dashboard.js`, siempre undefined).