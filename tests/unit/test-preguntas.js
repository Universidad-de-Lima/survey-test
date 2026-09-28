/**
 * Tests JS con jsdom — asistente de preguntas del item 1.9 (portal-preguntas.js).
 *
 * Lo que se comprueba: que las respuestas salgan de los JSON publicados (con su fuente),
 * que el periodo se elija bien y que lo que no está en los datos NO se responda.
 * El `fetch` de prueba lee los JSON del propio repositorio: son los mismos que sirve la página.
 */
const { JSDOM } = require('jsdom');
const path = require('path');
const fs = require('fs');
const assert = require('assert');

const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost/' });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

const basePath = path.resolve(__dirname, '..', '..');
const raiz = path.join(basePath, 'zoho-survey');

require(path.join(raiz, 'shared/js/utils/sanitizer.js'));
require(path.join(raiz, 'shared/js/utils/formatters.js'));
require(path.join(raiz, 'shared/js/portal/portal-preguntas.js'));

const llamadasExternas = [];
global.fetch = function (url, opciones) {
  // Las direcciones externas (el registro de preguntas) no se piden de verdad:
  // se anotan y se responde lo que se quiera comprobar.
  if (/^https?:\/\//.test(String(url))) {
    llamadasExternas.push({ url: String(url), opciones: opciones || {} });
    if (String(url).indexOf('/preguntas') !== -1 && !(opciones && opciones.method === 'POST')) {
      return Promise.resolve({
        ok: true,
        json: function () { return Promise.resolve({ frecuentes: [{ texto: '¿Cuál es el NPS de 2026-1?', veces: 7 }] }); }
      });
    }
    return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ ok: true }); } });
  }
  const rel = String(url).replace(/^\.\//, '');
  const destino = path.join(raiz, rel.split('/').join(path.sep));
  return new Promise(function (ok) {
    fs.readFile(destino, function (err, buf) {
      if (err) return ok({ ok: false, json: function () { return Promise.resolve(null); } });
      ok({ ok: true, json: function () { return Promise.resolve(JSON.parse(buf.toString('utf8'))); } });
    });
  });
};
window.fetch = global.fetch;

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
function assertIncludes(texto, trozo, msg) {
  assert.ok(String(texto).indexOf(trozo) !== -1, (msg || '') + ' (no contiene "' + trozo + '": ' + texto + ')');
}

const P = window.SurveyPortalPreguntas;
let nps2026, respuestas2026, comparacion, hora, clima, npsIngenieria;

(async function () {
  nps2026 = await P.responder('¿Cuál es el NPS de 2026-1?');
  respuestas2026 = await P.responder('¿Cuántas respuestas tenemos en 2026-1?');
  comparacion = await P.responder('¿Cómo cambió el NPS de 2025-2 a 2026-1?');
  npsIngenieria = await P.responder('¿Cuál es el NPS de Ingeniería de Sistemas?');
  hora = await P.responder('¿Qué hora es?');
  clima = await P.responder('¿Cómo estará el clima mañana?');

  const texto = (r) => (r.lineas || []).join(' | ') + ' ' + (r.titulo || '');
  const fuentes = (r) => (r.fuentes || []).join(' ');

  test('el NPS de 2026-1 sale del dato publicado', () => {
    assertIncludes(texto(nps2026), '72,61', 'NPS esperado');
    assertIncludes(texto(nps2026), '4239', 'respuestas del periodo');
  });

  test('la respuesta del NPS dice de qué archivo salió', () => {
    assertIncludes(fuentes(nps2026), 'dashboard_data.json', 'fuente del NPS');
    assertIncludes(fuentes(nps2026), '2026-1', 'periodo de la fuente');
  });

  test('elegir periodo: 2026-1 no se confunde con el 2026 de graduados', () => {
    assertIncludes(texto(respuestas2026), '4239', 'respuestas de pregrado 2026-1');
    assertTrue(texto(respuestas2026).indexOf('598') === -1, 'no debe responder con graduados');
  });

  test('la comparación usa los dos periodos nombrados', () => {
    assertIncludes(texto(comparacion), '2025-2', 'periodo viejo');
    assertIncludes(texto(comparacion), '2026-1', 'periodo nuevo');
    assertIncludes(texto(comparacion), '61,31', 'NPS de 2025-2');
    assertIncludes(texto(comparacion), '72,61', 'NPS de 2026-1');
  });

  test('una carrera concreta devuelve su NPS y su satisfacción', () => {
    assertIncludes(texto(npsIngenieria), '68,34', 'NPS de Ingeniería de Sistemas');
    assertIncludes(fuentes(npsIngenieria), 'nps_carrera.json', 'fuente por carrera');
  });

  test('la hora no se responde', () => {
    assertTrue(hora.alcance === false, 'debe quedar fuera de alcance');
    assertIncludes(texto(hora), 'encuestas', 'debe explicar de qué sí responde');
  });

  test('el clima no se responde', () => {
    assertTrue(clima.alcance === false, 'debe quedar fuera de alcance');
  });

  test('toda respuesta dentro de alcance cita un archivo JSON', () => {
    [nps2026, respuestas2026, comparacion, npsIngenieria].forEach(function (r) {
      assertIncludes(fuentes(r), '.json', 'fuente citada');
    });
  });

  test('registrar manda la pregunta al contador de más frecuentes', () => {
    const post = llamadasExternas.filter(c => c.opciones && c.opciones.method === 'POST');
    assertTrue(post.length >= 1, 'debe haber al menos un envío');
    assertIncludes(post[0].url, '/api/preguntas', 'dirección del registro');
    assertIncludes(post[0].opciones.body, 'NPS de 2026-1', 'la pregunta enviada');
  });

  test('lo que se registra va acotado (no crece sin control)', () => {
    const post = llamadasExternas.filter(c => c.opciones && c.opciones.method === 'POST');
    assertTrue(post[0].opciones.body.length <= 300, 'el cuerpo no debe crecer sin control');
    assertTrue(post[0].opciones.body.indexOf('intencion') !== -1, 'debe decir qué tipo de pregunta fue');
  });

  test('la pantalla del 1.9 se puede dibujar', () => {
    const html = P.render();
    assertIncludes(html, 'preguntasForm', 'formulario');
    assertIncludes(html, 'preguntasTexto', 'campo de texto');
    assertIncludes(html, 'preguntas-sugerencia', 'preguntas sugeridas');
  });

  await (async function () {
    const P2 = window.SurveyPortalPreguntas;
    await P2.registrar('¿Cuál es el NPS de 2026-1?', 'NPS');
    let lista = null;
    try { lista = await P2.cargarFrecuentes(); } catch (e) { lista = null; }
    test('las más frecuentes se pueden leer del registro', () => {
      assertTrue(Array.isArray(lista), 'debe devolver una lista');
      assertEqual(lista[0].texto, '¿Cuál es el NPS de 2026-1?');
      assertEqual(lista[0].veces, 7);
    });
  })();

  console.log('\n=== Tests JS del asistente 1.9 (jsdom) ===');
  console.log('passed=' + passed + ' failed=' + failed + ' total=' + (passed + failed));
  if (failed > 0) {
    results.filter(r => r.status === 'fail').forEach(r => console.log('  FAIL: ' + r.name + ' -> ' + r.error));
    process.exit(1);
  }
})();
