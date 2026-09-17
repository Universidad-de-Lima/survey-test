/**
 * Tests JS con jsdom — sentiment-view.js renderInsightsIA() y otros componentes.
 * Fase 9: blindaje de calidad frontend.
 *
 * Estos tests usan jsdom para simular el DOM del navegador y validar que
 * los componentes renderizan correctamente los datos del JSON.
 */
const { JSDOM } = require('jsdom');
const path = require('path');
const assert = require('assert');

// Setup jsdom con HTML mínimo que incluye los divs esperados
const dom = new JSDOM(`<!DOCTYPE html>
<html><body>
  <div id="insight-cualitativo"></div>
  <div id="insight-cualitativo-categorias"></div>
  <div id="sentiment-kpis"></div>
  <select id="test-select"><option value="">Todas</option><option value="a">A</option></select>
</body></html>`, { url: 'http://localhost/' });

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Cargar módulos en orden
// Usar __dirname para resolver rutas relativas (compatible con cualquier entorno: local, CI, GitHub Actions)
const basePath = path.resolve(__dirname, '..', '..');
require(path.join(basePath, 'zoho-survey/shared/js/config/constants.js'));
require(path.join(basePath, 'zoho-survey/shared/js/utils/formatters.js'));
require(path.join(basePath, 'zoho-survey/shared/js/utils/sanitizer.js'));
require(path.join(basePath, 'zoho-survey/shared/js/utils/dom-helpers.js'));
require(path.join(basePath, 'zoho-survey/shared/js/components/tooltip.js'));
require(path.join(basePath, 'zoho-survey/shared/js/components/sentiment-view.js'));

const SV = window.SurveySentimentView;
const S = window.SurveySanitizer;
const DH = window.SurveyDOMHelpers;

let passed = 0, failed = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passed++;
    results.push({ name, status: 'pass' });
  } catch (e) {
    failed++;
    results.push({ name, status: 'fail', error: e.message });
  }
}

function assertEqual(a, b, msg) {
  if (a !== b) throw new Error(`${msg || ''}: expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`);
}
function assertTrue(v, msg) { if (!v) throw new Error(msg || 'expected truthy'); }
function assertFalse(v, msg) { if (v) throw new Error(msg || 'expected falsy'); }

// ===== Tests renderInsightsIA =====

test('renderInsightsIA existe como función', () => {
  assertEqual(typeof SV.renderInsightsIA, 'function');
});

test('renderInsightsIA con datos completos pobla div global', () => {
  // Limpiar divs
  document.getElementById('insight-cualitativo').textContent = '';
  document.getElementById('insight-cualitativo-categorias').innerHTML = '';

  SV.renderInsightsIA({
    insights_ia: {
      global: 'El análisis revela tema X con 100 menciones.',
      por_categoria_padre: {
        'Académico': '500 menciones positivas.',
        'Tecnología': '50 comentarios sobre Wi-Fi.'
      }
    }
  });

  const global = document.getElementById('insight-cualitativo');
  assertEqual(global.textContent, 'El análisis revela tema X con 100 menciones.');
});

test('renderInsightsIA crea elementos por categoría', () => {
  document.getElementById('insight-cualitativo-categorias').innerHTML = '';

  SV.renderInsightsIA({
    insights_ia: {
      global: 'Global insight.',
      por_categoria_padre: {
        'Académico': 'Insight académico.',
        'Tecnología': 'Insight tecnología.',
        'Infraestructura': 'Insight infra.'
      }
    }
  });

  const cats = document.getElementById('insight-cualitativo-categorias');
  const items = cats.querySelectorAll('div[style*="border-left"]');
  assertEqual(items.length, 3, 'Debe crear 3 divs de categoría');
});

test('renderInsightsIA con datos nulos no rompe', () => {
  let threw = false;
  try {
    SV.renderInsightsIA(null);
    SV.renderInsightsIA(undefined);
    SV.renderInsightsIA({});
  } catch (e) { threw = true; }
  assertFalse(threw, 'No debe lanzar excepción con datos nulos');
});

test('renderInsightsIA sin insights_ia muestra fallback', () => {
  document.getElementById('insight-cualitativo').textContent = '';
  SV.renderInsightsIA({ comentarios: [], topicos: [] });
  const global = document.getElementById('insight-cualitativo');
  assertTrue(global.textContent.includes('No hay análisis'), 'Debe mostrar mensaje de fallback');
});

test('renderInsightsIA con insights_ia vacío muestra fallback', () => {
  document.getElementById('insight-cualitativo').textContent = '';
  SV.renderInsightsIA({ insights_ia: {} });
  const global = document.getElementById('insight-cualitativo');
  assertTrue(global.textContent.includes('No hay análisis'));
});

test('renderInsightsIA usa textContent (no innerHTML) para prevenir XSS', () => {
  document.getElementById('insight-cualitativo').textContent = '';
  SV.renderInsightsIA({
    insights_ia: {
      global: '<script>alert(1)</script>',
      por_categoria_padre: {}
    }
  });
  const global = document.getElementById('insight-cualitativo');
  // textContent NO interpreta HTML
  assertEqual(global.innerHTML, '&lt;script&gt;alert(1)&lt;/script&gt;');
  // No debe haber un elemento script dentro
  assertEqual(global.querySelectorAll('script').length, 0);
});

test('renderInsightsIA no crea elementos para categorías con texto vacío', () => {
  document.getElementById('insight-cualitativo-categorias').innerHTML = '';
  SV.renderInsightsIA({
    insights_ia: {
      global: 'Global.',
      por_categoria_padre: {
        'Académico': 'Texto válido.',
        'Tecnología': '',
        'Infraestructura': null
      }
    }
  });
  const cats = document.getElementById('insight-cualitativo-categorias');
  const items = cats.querySelectorAll('div[style*="border-left"]');
  assertEqual(items.length, 1, 'Solo Académico debe renderizarse');
});

// ===== Tests sanitizer =====

test('sanitizeHTML permite tags whitelist', () => {
  assertEqual(S.sanitizeHTML('<strong>bold</strong>'), '<strong>bold</strong>');
  assertEqual(S.sanitizeHTML('<em>italic</em>'), '<em>italic</em>');
  assertEqual(S.sanitizeHTML('<br>'), '<br>');
});

test('sanitizeHTML escapa script tags', () => {
  const result = S.sanitizeHTML('<script>alert(1)</script>');
  assertTrue(result.includes('&lt;script&gt;'));
  assertFalse(result.includes('<script>'));
});

test('sanitizeHTML elimina atributos on* (bug Fase 6)', () => {
  const result = S.sanitizeHTML('<span onclick="alert(1)">texto</span>');
  assertEqual(result, '<span>texto</span>');
});

test('sanitizeHTML elimina atributos class de spans permitidos', () => {
  const result = S.sanitizeHTML('<span class="x">texto</span>');
  assertEqual(result, '<span>texto</span>');
});

test('escapeHTML escapa caracteres peligrosos', () => {
  assertEqual(S.escapeHTML('<>'), '&lt;&gt;');
  assertEqual(S.escapeHTML('&'), '&amp;');
  assertEqual(S.escapeHTML('"'), '&quot;');
  assertEqual(S.escapeHTML("'"), '&#039;');
});

test('escapeHTML retorna vacío para null/undefined/no-string', () => {
  assertEqual(S.escapeHTML(null), '');
  assertEqual(S.escapeHTML(undefined), '');
  assertEqual(S.escapeHTML(123), '');
});

// ===== Tests dom-helpers =====

test('getSelectedValues en select simple', () => {
  const sel = document.getElementById('test-select');
  sel.value = '';
  const val = DH.getSelectedValues(sel);
  assertEqual(val, '');
});

test('getSelectedValues en select con opción seleccionada', () => {
  const sel = document.getElementById('test-select');
  sel.value = 'a';
  const val = DH.getSelectedValues(sel);
  assertEqual(val, 'a');
});

test('formatMultiselectLabel con 0 elementos', () => {
  assertEqual(DH.formatMultiselectLabel([], 'Todas'), 'Todas');
});

test('formatMultiselectLabel con 1 elemento', () => {
  assertEqual(DH.formatMultiselectLabel(['A'], 'Todas'), 'A');
});

test('formatMultiselectLabel con múltiples elementos usa itemName', () => {
  assertEqual(DH.formatMultiselectLabel(['A', 'B', 'C'], 'Todas', 'categorías'), '3 categorías seleccionados');
  assertEqual(DH.formatMultiselectLabel(['A', 'B'], 'Todos', 'ciclos'), '2 ciclos seleccionados');
});

test('formatMultiselectLabel default itemName es ciclos', () => {
  assertEqual(DH.formatMultiselectLabel(['A', 'B'], 'Todos'), '2 ciclos seleccionados');
});

// ===== Tests formatters =====

const F = window.SurveyFormatters;

test('formatDecimal respeta digits=2 por defecto', () => {
  assertEqual(F.formatDecimal(3.14159), '3,14');
});

test('formatDecimal SIEMPRE muestra 2 decimales incluso si son cero (v1.1.0)', () => {
  assertEqual(F.formatDecimal(3.0), '3,00');
});

test('formatDecimal con precisión personalizada', () => {
  assertEqual(F.formatDecimal(1.2351, 3), '1,235');
  assertEqual(F.formatDecimal(1.2344, 3), '1,234');
});

test('formatPercent añade % y SIEMPRE 2 decimales (v1.1.0)', () => {
  assertEqual(F.formatPercent(93.5), '93,50 %');
  assertEqual(F.formatPercent(100.0), '100,00 %');
});

test('formatPctSimple con 2 decimales (v1.1.0)', () => {
  assertEqual(F.formatPctSimple(3, 10), '30,00 %');
  assertEqual(F.formatPctSimple(5, 0), '0,00 %');
});

test('formatInteger casos edge', () => {
  assertEqual(F.formatInteger(42), '42');
  assertEqual(F.formatInteger(0), '0');
  assertEqual(F.formatInteger(-5), '-5');
});

test('cortarTexto trunca con elipsis', () => {
  const result = F.cortarTexto('ABCDEFGHIJKLMNOP', 10);
  assertTrue(result.endsWith('…'));
  assertTrue(result.length <= 10);
});

test('cortarTexto no modifica texto corto', () => {
  assertEqual(F.cortarTexto('Hola', 10), 'Hola');
});

test('formatDimensionName aplica cursiva a Software', () => {
  const result = F.formatDimensionName('Software especializado empleado en la carrera');
  assertTrue(result.includes('<i>Software</i>'));
});

// ===== Tests tooltip =====

const TT = window.SurveyTooltip;

test('SurveyTooltip expone show, move, hide, bindToSegments', () => {
  assertEqual(typeof TT.show, 'function');
  assertEqual(typeof TT.move, 'function');
  assertEqual(typeof TT.hide, 'function');
  assertEqual(typeof TT.bindToSegments, 'function');
});

test('tooltip.show crea elemento tooltip en DOM', () => {
  TT.show({ clientX: 100, clientY: 100 }, 'Test content');
  const el = document.getElementById('tooltip');
  assertTrue(el !== null, 'Elemento tooltip debe existir');
  assertTrue(el.style.display !== 'none', 'Tooltip debe estar visible');
});

test('tooltip.hide oculta tooltip', () => {
  TT.show({ clientX: 100, clientY: 100 }, 'Test');
  TT.hide();
  const el = document.getElementById('tooltip');
  assertEqual(el.style.display, 'none');
});

// ===== Resumen =====

console.log('\n=== Tests JS con jsdom ===');
console.log(`passed=${passed} failed=${failed} total=${passed + failed}`);
if (failed > 0) {
  results.filter(r => r.status === 'fail').forEach(r => {
    console.log(`  FAIL: ${r.name} -> ${r.error}`);
  });
  process.exit(1);
}
