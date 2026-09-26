# Reglas que el portal y las fichas escriben distinto (a proposito)

Son 48 selectores con el mismo nombre en dos hojas, con cuerpos distintos. **No se unen**:
cada familia los necesita con sus propios valores (el portal usa su paleta y su tamano de
texto; las fichas por periodo usan el semaforo verde/ambar/rojo). Quedan aqui para que nadie
los "arregle" por error: unirlos cambiaria el aspecto de una de las dos paginas.

Las reglas que SI son iguales no viven aqui: viven una sola vez en `common.css`.

Generado con las herramientas de auditoria de CSS descritas en ARCHITECTURE.md.

| Selector | Donde vive | Que cambia entre las dos |
| --- | --- | --- |
| `.bar-chart` | dashboard/components.css, portal/sections.css | padding-left: (no lo pone) / 12px |
| `.bar-container` | dashboard/components.css, portal/sections.css | border-radius: var(--radius-sm) / var(--radius-md) |
| `.bar-fill` | dashboard/components.css, portal/sections.css | border-radius: var(--radius-sm) / var(--radius-md) |
| `.bar-fill.high` | dashboard/components.css, portal/sections.css | background: var(--success-text) / var(--gray-700) |
| `.bar-fill.medium` | dashboard/components.css, portal/sections.css | background: var(--success-pastel) / var(--gray-400) |
| `.bar-label` | dashboard/components.css, portal/sections.css | align-items: center / (no lo pone) ; display: flex / (no lo pone) ; justify-content: flex-end / (no lo pone) |
| `.bar-label  @media (max-width: 480px)` | dashboard/sections.css, portal/sections.css | justify-content: flex-start / (no lo pone) |
| `.bar-label  @media (max-width: 768px)` | dashboard/sections.css, portal/sections.css | font-size: var(--text-xs) / var(--text-sm) ; width: 140px / 230px ; line-height: 15px / 17px |
| `.card-title` | dashboard/components.css, portal/sections.css | margin-top: (no lo pone) / 4px ; padding-left: (no lo pone) / 12px ; text-transform: uppercase / (no lo pone) |
| `.csat-bar, #nps-bar` | dashboard/components.css, portal/sections.css | border-radius: var(--radius-md) / var(--radius-lg) |
| `.csat-bar-row` | dashboard/components.css, portal/sections.css | animation: stackedGrow 0.8s ease-out forwards / (no lo pone) ; border-radius: var(--radius-md) / var(--radius-lg) |
| `.csat-distribution` | dashboard/components.css, portal/sections.css | background: var(--white) / rgba(245,245,245,0.3) |
| `.csat-label` | dashboard/components.css, portal/sections.css | line-height: 18px / (no lo pone) |
| `.distribution-bar` | dashboard/components.css, portal/sections.css | border-radius: var(--radius-xs) / var(--radius-md) |
| `.distribution-segment` | dashboard/components.css, portal/sections.css | cursor: pointer / default ; transition: opacity 0.2s / (no lo pone) |
| `.filter-container  @media (max-width: 1100px)` | dashboard/sections.css, portal/sections.css | gap: var(--space-sm) / var(--space-md) |
| `.filter-container-wrap` | dashboard/components.css, portal/components.css | align-items: (no lo pone) / center ; flex-wrap: (no lo pone) / wrap ; gap: (no lo pone) / var(--space-sm) |
| `.filter-group  @media (max-width: 480px)` | dashboard/sections.css, portal/sections.css | flex: 1 1 100% / 1 1 calc(33.333% - var(--space-sm)) |
| `.filter-group  @media (max-width: 768px)` | dashboard/sections.css, portal/sections.css | min-width: 140px / 0 ; flex: 1 1 calc(50% - 6px) / 1 1 0 |
| `.filter-label` | dashboard/components.css, portal/components.css | text-transform: uppercase / (no lo pone) |
| `.filter-multiselect-toggle` | dashboard/components.css, portal/components.css | min-width: 130px / 0 |
| `.filter-reset` | dashboard/components.css, portal/components.css | margin-left: var(--space-sm) / (no lo pone) |
| `.filter-reset  @media (max-width: 768px)` | dashboard/sections.css, portal/sections.css | min-width: (no lo pone) / 64px ; padding: (no lo pone) / 4px 8px ; text-align: (no lo pone) / center |
| `.footer` | dashboard/layout.css, portal/base.css | -webkit-backdrop-filter: (no lo pone) / blur(8px) ; align-items: (no lo pone) / center ; backdrop-filter: (no lo pone) / blur(8px) |
| `.heat-high` | dashboard/components.css, portal/sections.css | background: var(--success-text) / var(--gray-700) |
| `.heat-medium` | dashboard/components.css, portal/sections.css | color: var(--success-text) / white ; background: var(--success-pastel) / var(--gray-400) |
| `.heatmap-cell` | dashboard/components.css, portal/sections.css | white-space: (no lo pone) / nowrap |
| `.insight-box` | dashboard/components.css, portal/components.css | border-radius: 0 6px 6px 0 / var(--radius-lg) |
| `.insight-title` | dashboard/components.css, portal/components.css | text-transform: uppercase / (no lo pone) |
| `.kpi-bar-fill` | dashboard/components.css, generated.css | border-radius: var(--radius-sm) / (no lo pone) ; height: 100% / (no lo pone) ; width: (no lo pone) / var(--w) |
| `.kpi-card` | dashboard/components.css, portal/components.css | border: (no lo pone) / 1px solid var(--gray-200) ; border-radius: (no lo pone) / var(--radius-lg) ; padding: (no lo pone) / var(--space-xl) |
| `.legend-item` | dashboard/components.css, portal/sections.css | transition: font-size 0.15s ease, font-weight 0.15s ease / text-decoration 0.15s ease, text-decoration-color 0.15s ease, text-underline-offset 0.15s ease |
| `.legend-item.highlight` | dashboard/components.css, portal/sections.css | font-weight: var(--font-bold) / (no lo pone) ; text-underline-offset: (no lo pone) / 3px ; font-size: var(--text-xl) / (no lo pone) |
| `.progress-bar` | dashboard/layout.css, portal/components.css | background: var(--gray-200) / var(--muted) ; border-radius: (no lo pone) / 9999px ; height: (no lo pone) / 6px |
| `.ring-aro` | generated.css, portal/components.css | border-radius: (no lo pone) / var(--radius-full) ; height: (no lo pone) / 88px ; margin: (no lo pone) / 0 auto 7px |
| `.sat-bar` | generated.css, portal/components.css | background: var(--c) / (no lo pone) ; border-radius: (no lo pone) / var(--radius-md) ; transition: (no lo pone) / width .4s ease |
| `.sat-pct` | generated.css, portal/components.css | font-weight: (no lo pone) / var(--font-bold) ; min-width: (no lo pone) / 40px ; text-align: (no lo pone) / right |
| `.section` | dashboard/layout.css, portal/base.css | scroll-margin-top: 91px / (no lo pone) ; margin-bottom: var(--space-5xl) / 24px |
| `.sr-only` | portal/components.css, reset.css | white-space: nowrap / (no lo pone) |
| `.survey-table` | dashboard/components.css, portal/sections.css | border-collapse: collapse / separate ; border-spacing: (no lo pone) / 0 |
| `.survey-table td` | dashboard/components.css, portal/sections.css | border-bottom: 1px solid var(--gray-200) / (no lo pone) ; color: (no lo pone) / rgba(26,26,26,0.85) ; padding: (no lo pone) / var(--space-sm) var(--space-md) |
| `.survey-table th` | dashboard/components.css, portal/sections.css | top: calc(var(--sticky-header-h) - 1px) / 0 ; white-space: (no lo pone) / nowrap |
| `.table-scroll` | common.css, portal/sections.css | border-radius: (no lo pone) / var(--radius-lg) ; margin: var(--space-lg) 0 / (no lo pone) ; scrollbar-color: var(--gray-400) var(--gray-100) / (no lo pone) |
| `.visibility-segment.conocido` | common.css, generated.css | color: var(--gray-800) / (no lo pone) ; background: var(--gray-300) / (no lo pone) ; width: (no lo pone) / var(--w) |
| `.visibility-segment.no-conozco` | dashboard/components.css, generated.css | color: var(--gray-50) / (no lo pone) ; background: var(--gray-800) / (no lo pone) ; width: (no lo pone) / var(--w) |
| `.visibility-segment.no-utilizo` | dashboard/components.css, generated.css | color: var(--gray-50) / (no lo pone) ; background: var(--gray-500) / (no lo pone) ; width: (no lo pone) / var(--w) |
| `:root` | dashboard/layout.css, tokens.css | --amber: (no lo pone) / #F59E0B ; --amber-50: (no lo pone) / #fffbeb ; --black: (no lo pone) / #000000 |
| `body` | portal/base.css, reset.css | -webkit-overflow-scrolling: (no lo pone) / touch ; background: var(--background) / var(--white) ; color: var(--foreground) / var(--gray-800) |
