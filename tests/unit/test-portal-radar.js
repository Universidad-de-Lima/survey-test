/**
 * Tests JS con jsdom — portal-radar.js: la dimensión "Software" del radar.
 *
 * Lo que se comprueba: que el radar reconozca la dimensión "Software" por su id
 * declarado (el bloque `preguntas` que el portal carga en los resúmenes) y no por
 * su nombre publicado. Con otro nombre pero el mismo id, la cursiva sigue cayendo.
 */
const { JSDOM } = require('jsdom');
const path = require('path');
const assert = require('assert');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost/' });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

const basePath = path.resolve(__dirname, '..', '..');
const raiz = path.join(basePath, 'zoho-survey');

require(path.join(raiz, 'shared/js/config/constants.js'));
require(path.join(raiz, 'shared/js/utils/sanitizer.js'));
require(path.join(raiz, 'shared/js/utils/formatters.js'));
require(path.join(raiz, 'shared/js/utils/dom-helpers.js'));
require(path.join(raiz, 'shared/js/portal/portal-data.js'));
require(path.join(raiz, 'shared/js/portal/portal-radar.js'));

// portal-radar usa el formateador que re-exporta portal-survey; se enlaza aquí.
window.SurveyPortalSurvey = { formatDimensionName: window.SurveyFormatters.formatDimensionName };

let passed = 0, failed = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passed++;
    results.push({ status: 'pass', name: name });
  } catch (e) {
    failed++;
    results.push({ status: 'fail', name: name, error: e.message });
  }
}
function assertTrue(cond, msg) { assert.ok(cond, msg); }
function assertEqual(a, b) { assert.strictEqual(a, b, 'se esperaba ' + b + ' y llegó ' + a); }

const R = window.SurveyPortalRadar;
const ID_SOFTWARE = 'software_especializado_empleado_en_la_carrera';
const NOMBRE_HEREDADO = 'Software especializado empleado en la carrera';

// Publica un nombre para el id de Software (como lo deja el bloque `preguntas`).
function conNombrePublicado(nombre, fn) {
  const D = window.SurveyPortalData;
  const original = D.getSurveyData;
  D.getSurveyData = function () {
    return { filtros: { preguntas: [{ id: ID_SOFTWARE, nombre: nombre, tipo: 'medida', escala: 'CSAT' }] } };
  };
  try {
    fn();
  } finally {
    D.getSurveyData = original;
  }
}

test('el radar marca en cursiva la dimensión Software por su id, no por su nombre', function () {
  conNombrePublicado('Herramientas de software', function () {
    const svg = R.formatDimensionNameSVG('Herramientas de software', 26);
    assertTrue(svg.indexOf('<tspan') === 0, 'esperaba un tspan: ' + svg);
    assertTrue(svg.indexOf('>Herramientas<') !== -1, 'la primera palabra va en cursiva: ' + svg);
  });
});

test('las demás dimensiones no llevan cursiva', function () {
  assertEqual(R.formatDimensionNameSVG('Aulas de clase', 26), 'Aulas de clase');
});

test('con el nombre publicado de hoy, la cursiva cae sobre Software', function () {
  const svg = R.formatDimensionNameSVG(NOMBRE_HEREDADO, 26);
  assertTrue(svg.indexOf('>Software<') !== -1, svg);
});

console.log('\n=== radar del portal (jsdom) ===');
results.filter(function (r) { return r.status === 'fail'; }).forEach(function (r) {
  console.log('❌ ' + r.name + ' → ' + r.error);
});
console.log('\n' + passed + ' passed, ' + failed + ' failed, ' + (passed + failed) + ' total');
process.exit(failed === 0 ? 0 : 1);
