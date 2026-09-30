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

// Respuesta simulada del traductor (se cambia en cada prueba).
// Respuesta simulada del formulario (se cambia en cada prueba).
let consultaSimulada = { se_puede: true, operacion: 'satisfaccion', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Psicología', orden: '', motivo: '' };
const llamadasExternas = [];
// Cuantas veces debe fallar /interpretar antes de responder (para probar el reintento).
let fallosInterpretar = 0;
global.fetch = function (url, opciones) {
  // Las direcciones externas (el registro de preguntas) no se piden de verdad:
  // se anotan y se responde lo que se quiera comprobar.
  if (/^https?:\/\//.test(String(url))) {
    llamadasExternas.push({ url: String(url), opciones: opciones || {} });
    if (String(url).indexOf('/interpretar') !== -1) {
      if (fallosInterpretar > 0) {
        fallosInterpretar -= 1;
        return Promise.resolve({ ok: false, json: function () { return Promise.resolve(null); } });
      }
      return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ consulta: consultaSimulada }); } });
    }
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
let porAnio, porCarrera, enTotal, alumnos20261;
let cruceGraduados, cruceTiempo, cruceAlumnos, cruceSinFiltro;

(async function () {
  nps2026 = await P.responder('¿Cuál es el NPS de 2026-1?');
  porAnio = await P.responder('¿Cuántos alumnos se encuestaron en el 2026?');
  porCarrera = await P.responder('¿Cuántos alumnos respondieron de Psicología?');
  enTotal = await P.responder('¿Cuántos se encuestaron en total?');
  alumnos20261 = await P.responder('cuantos alumnos se encuestaron en 2026-1');
  respuestas2026 = await P.responder('¿Cuántas respuestas tenemos en 2026-1?');
  comparacion = await P.responder('¿Cómo cambió el NPS de 2025-2 a 2026-1?');
  npsIngenieria = await P.responder('¿Cuál es el NPS de Ingeniería de Sistemas?');
  hora = await P.responder('¿Qué hora es?');
  clima = await P.responder('¿Cómo estará el clima mañana?');
  cruceGraduados = await P.responder('De los graduados que están en búsqueda de empleo o no disponibles para trabajar, ¿cuántos están satisfechos con su perfil de egreso?');
  cruceTiempo = await P.responder('De los graduados que trabajan a tiempo completo, ¿cuál es su satisfacción con la Universidad de Lima?');
  cruceAlumnos = await P.responder('De los alumnos de Economía, ¿cuántos están satisfechos con su perfil de egreso?');
  cruceSinFiltro = await P.responder('¿Cuál es la satisfacción con la Universidad de Lima en 2026-1?');

  // El formulario con contexto y menu: el caso del usuario (Economia) y dos fallos.
  // Las dos preguntas de fallo son las que YA se sabe que no alcanzan a las reglas: la
  // familia de conteos responde "cuantos alumnos..." con el total del periodo aunque no
  // reconozca la carrera, asi que aqui no sirve para probar el formulario.
  consultaSimulada = { se_puede: true, operacion: 'porcentaje', periodo: '', filtros: [{ pregunta: 'Carrera', valores: ['Economía'] }], pregunta_objetivo: 'Situación laboral', valores_objetivo: ['Trabajador dependiente', 'Trabajador independiente', 'Prácticas profesionales', 'Prácticas pre - profesionales'], entidad: '', orden: '', motivo: '' };
  const formEconomia = await P.responderConIA('¿qué porcentaje de graduados de la carrera de economía trabajan?');
  consultaSimulada = { se_puede: true, operacion: 'contar', periodo: '', filtros: [{ pregunta: 'Carrera', valores: ['Carrera Inexistente'] }], pregunta_objetivo: '', valores_objetivo: [], entidad: '', orden: '', motivo: '' };
  const formRaro = await P.responderConIA('¿qué tan contentos están los alumnos de Psicología?');
  consultaSimulada = { se_puede: false, operacion: 'ninguna', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: '', orden: '', motivo: 'Eso no está en las encuestas.' };
  const formNo = await P.responderConIA('¿cómo estará el clima mañana?');
  consultaSimulada = { se_puede: true, operacion: 'satisfaccion', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Psicología', orden: '', motivo: '' };
  consultaSimulada = { se_puede: true, operacion: 'porcentaje', periodo: '', filtros: [{ pregunta: 'Carrera', valores: ['Economía'] }, { pregunta: 'Situación laboral', valores: ['Trabajador dependiente', 'Trabajador independiente', 'Prácticas profesionales', 'Prácticas pre - profesionales'] }], pregunta_objetivo: '', valores_objetivo: [], entidad: '', orden: '', motivo: '' };
  const formFiltros = await P.responderConIA('¿qué porcentaje de graduados de la carrera de economía trabajan?');
  consultaSimulada = { se_puede: true, operacion: 'satisfaccion', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Psicología', orden: '', motivo: '' };
  // Las reglas ya NO responden la pregunta de Economia: la resuelve el formulario.
  const reglasEconomia = await P.responder('¿qué porcentaje de graduados de la carrera de economía trabajan?');

  // Aviso de espera + la respuesta llega a la caja que esta EN PANTALLA (aunque se navegue).
  document.body.innerHTML = P.render();
  const enVuelo = P.preguntar('¿Cuál es el NPS de 2026-1?');
  const cajaEnVuelo = document.getElementById('preguntasRespuestas');
  const avisoAlPreguntar = cajaEnVuelo ? cajaEnVuelo.textContent : '';
  document.body.innerHTML = P.render(); // se "navega" a otra pantalla y se vuelve mientras espera
  const respuestaEnVuelo = await enVuelo;
  const cajaViva = document.getElementById('preguntasRespuestas');
  const textoCajaViva = cajaViva ? cajaViva.textContent : '';

  // Reintento del interprete: falla una vez (responde igual) y falla dos (aviso propio).
  fallosInterpretar = 1;
  const reintento = await P.responderConIA('¿qué tan contentos están los alumnos de Psicología?');
  fallosInterpretar = 2;
  const sinInterprete = await P.responderConIA('¿qué tan contentos están los alumnos de Psicología?');
  fallosInterpretar = 0;

  // Forma del bloque de respuesta: pregunta arriba, etiqueta, dato y resultado separado.
  consultaSimulada = { se_puede: true, operacion: 'porcentaje', periodo: '', filtros: [{ pregunta: 'Carrera', valores: ['Economía'] }], pregunta_objetivo: 'Situación laboral', valores_objetivo: ['Trabajador dependiente', 'Trabajador independiente', 'Prácticas profesionales', 'Prácticas pre - profesionales'], entidad: '', orden: '', motivo: '' };
  document.body.innerHTML = P.render();
  await P.preguntar('¿qué porcentaje de graduados de la carrera de economía trabajan?');
  const leer = (sel) => { const e = document.querySelector(sel); return e ? e.textContent : ''; };
  const textoRotulo = leer('.preguntas-rotulo');
  const textoDato = leer('.preguntas-respuesta-titulo');
  const textoContexto = leer('.preguntas-contexto');
  const textoResultado = leer('.preguntas-resultado');
  const textoFuente = leer('.preguntas-fuente');
  const hayListaEnCruce = !!document.querySelector('.preguntas-lista');

  // Una respuesta de lista (varios periodos) sigue siendo lista, sin resultado destacado.
  consultaSimulada = { se_puede: true, operacion: 'satisfaccion', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Psicología', orden: '', motivo: '' };
  document.body.innerHTML = P.render();
  await P.preguntar('¿Cuántos se encuestaron en total?');
  const hayListaTotal = !!document.querySelector('.preguntas-lista');
  const hayResultadoTotal = !!document.querySelector('.preguntas-resultado');

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
    assertIncludes(fuentes(npsIngenieria), 'resumenes.json (NPS y CSAT por carrera)', 'fuente por carrera');
  });

  test('la hora no se responde', () => {
    assertTrue(hora.alcance === false, 'debe quedar fuera de alcance');
    assertIncludes(texto(hora), 'encuestas', 'debe explicar de qué sí responde');
  });

  test('el clima no se responde', () => {
    assertTrue(clima.alcance === false, 'debe quedar fuera de alcance');
  });

  test('cruce: graduados sin trabajo -> su perfil de egreso (76 personas, 70 satisfechas)', () => {
    assertTrue(cruceGraduados.alcance !== false, 'debe responder');
    assertIncludes(texto(cruceGraduados), '76', 'el filtro (búsqueda de empleo + no disponible)');
    assertIncludes(texto(cruceGraduados), '70', 'los tres mejores');
    assertIncludes(texto(cruceGraduados), '92,11', 'el porcentaje');
    assertIncludes(fuentes(cruceGraduados), 'respuestas.json', 'la cita de la tabla');
  });

  test('cruce: graduados a tiempo completo -> satisfacción con la Universidad (297, 295)', () => {
    assertTrue(cruceTiempo.alcance !== false, 'debe responder');
    assertIncludes(texto(cruceTiempo), '297', 'los que trabajan a tiempo completo');
    assertIncludes(texto(cruceTiempo), '295', 'los tres mejores');
    assertIncludes(texto(cruceTiempo), '99,33', 'el porcentaje');
  });

  test('cruce: alumnos de Economía -> perfil de egreso (232, 198)', () => {
    assertTrue(cruceAlumnos.alcance !== false, 'debe responder');
    assertIncludes(texto(cruceAlumnos), '232', 'los de Economía');
    assertIncludes(texto(cruceAlumnos), '198', 'los tres mejores');
    assertIncludes(texto(cruceAlumnos), '85,34', 'el porcentaje');
    assertIncludes(fuentes(cruceAlumnos), 'respuestas.json', 'la cita de la tabla');
  });

  test('sin filtro no es un cruce: la pregunta normal sigue respondiéndose igual', () => {
    assertTrue(cruceSinFiltro.alcance !== false, 'debe responder');
    assertIncludes(fuentes(cruceSinFiltro), 'resumenes.json', 'la fuente de siempre');
  });

  test('el formulario con el menú responde el cruce de Economía que trabajan (14 de 14)', () => {
    assertTrue(formEconomia.alcance !== false, 'debe responder');
    assertIncludes(texto(formEconomia), '14', 'los graduados de Economía');
    assertIncludes(texto(formEconomia), '100', 'el porcentaje');
    assertIncludes(texto(formEconomia), 'Trabajador dependiente', 'los valores contados');
    assertIncludes(fuentes(formEconomia), 'respuestas.json', 'la cita de la tabla');
  });

  test('si el formulario nombra una opción que no existe, se avisa y no se cuenta', () => {
    assertTrue(formRaro.alcance === false, 'no debe responder de más');
    assertIncludes(texto(formRaro), 'No encontré', 'debe decir que no la encontró');
  });

  test('si el formulario dice que no se puede, se respeta el motivo', () => {
    assertTrue(formNo.alcance === false, 'queda fuera de alcance');
    assertIncludes(texto(formNo), 'no está en las encuestas', 'el motivo');
  });

  test('si el modelo cuenta por filtros, igual sale "de los 14, cuantos" (14 de 14)', () => {
    assertTrue(formFiltros.alcance !== false, 'debe responder');
    assertIncludes(texto(formFiltros), '14', 'el grupo y la cuenta');
    assertIncludes(texto(formFiltros), '100', 'el porcentaje');
    assertIncludes(texto(formFiltros), 'Carrera = Economía', 'el grupo');
    assertIncludes(fuentes(formFiltros), 'respuestas.json', 'la cita de la tabla');
  });

  test('la pregunta de Economía ya no la responde el cruce de reglas (la resuelve el formulario)', () => {
    assertTrue(reglasEconomia.alcance === false, 'las reglas no deben responderla');
    assertTrue(texto(reglasEconomia).indexOf('La carrera') === -1, 'no debe hablar de "La carrera"');
  });

  test('mientras espera, la pantalla avisa "Consultando…" en el acto', () => {
    assertIncludes(avisoAlPreguntar, 'Consultando', 'aviso inmediato');
  });

  test('la respuesta llega a la caja que está en pantalla (aunque se navegue mientras espera)', () => {
    assertIncludes(textoCajaViva, '72,61', 'el NPS respondido');
    assertTrue(textoCajaViva.indexOf('Consultando') === -1, 'el aviso de espera se quita al responder');
  });

  test('si el intérprete falla una vez, reintenta y responde igual', () => {
    assertTrue(reintento.alcance !== false, 'debe responder tras el reintento');
    assertIncludes(texto(reintento), 'Psicología', 'la carrera traducida');
  });

  test('si el intérprete no responde ni al reintento, el aviso es propio (no el genérico)', () => {
    assertTrue(sinInterprete.alcance === false, 'queda fuera de alcance');
    assertIncludes(texto(sinInterprete), 'No pude consultar al intérprete', 'aviso propio del servicio');
  });

  test('el bloque muestra la pregunta, la etiqueta y el dato', () => {
    assertIncludes(textoRotulo, 'Pregunta:', 'la etiqueta de la pregunta');
    assertIncludes(textoRotulo, 'economía', 'la pregunta tal como se escribió');
    assertIncludes(textoDato, 'Cruce: Situación laboral', 'el dato');
  });

  test('el filtro queda como contexto y el resultado separado, con su archivo', () => {
    assertIncludes(textoContexto, 'Filtro: Carrera = Economía', 'el filtro');
    assertIncludes(textoResultado, 'de 14', 'el resultado');
    assertIncludes(textoFuente, 'respuestas.json', 'la fuente conserva el archivo');
    assertTrue(hayListaEnCruce === false, 'el cruce no usa lista: el resultado va aparte');
  });

  test('una respuesta de lista sigue siendo lista (sin resultado destacado)', () => {
    assertTrue(hayListaTotal === true, 'debe quedar la lista de periodos');
    assertTrue(hayResultadoTotal === false, 'no debe haber un resultado destacado');
  });

  test('el mensaje que se manda lleva el contexto y el menú del período', () => {
    const envios = llamadasExternas.filter(function (c) { return String(c.url).indexOf('/interpretar') !== -1; });
    const envio = envios.filter(function (c) { return String(c.opciones.body).indexOf('economía trabajan') !== -1; })[0];
    assertTrue(!!envio, 'debe existir el envío de la pregunta de Economía');
    const cuerpo = String(envio.opciones.body);
    assertIncludes(cuerpo, 'Portal de resultados', 'el contexto del proyecto');
    assertIncludes(cuerpo, '## Menú — Graduados Pregrado 2026', 'el menú del período de graduados');
    assertIncludes(cuerpo, 'se pide como: trabajan', 'las palabras coloquiales');
    assertIncludes(cuerpo, 'Trabajador dependiente', 'las opciones reales');
  });

  test('toda respuesta dentro de alcance cita un archivo JSON', () => {
    [nps2026, respuestas2026, comparacion, npsIngenieria].forEach(function (r) {
      assertIncludes(fuentes(r), '.json', 'fuente citada');
    });
  });

  test('la pantalla del 1.9 se puede dibujar', () => {
    const html = P.render();
    assertIncludes(html, 'preguntasForm', 'formulario');
    assertIncludes(html, 'preguntasTexto', 'campo de texto');
    assertTrue(!html.includes('data-pregunta'), 'la caja arranca sin preguntas ya escritas');
  });

  await (async function () {
    const P2 = window.SurveyPortalPreguntas;
    await P2.registrar('¿Cuál es el NPS de 2026-1?', 'NPS');

    // La IA traduce una pregunta que las palabras clave NO reconocen.
    const conIA = await P2.responderConIA('¿qué tan contentos están los alumnos de Psicología?');
    // Y cuando el traductor dice que no es de las encuestas, no se responde.
    consultaSimulada = { se_puede: false, operacion: 'ninguna', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: '', orden: '', motivo: '' };
    const noEsDeEncuestas = await P2.responderConIA('¿cómo estará el clima mañana?');
    // Y si inventa un nombre que no está en los datos, se avisa.
    consultaSimulada = { se_puede: true, operacion: 'nps', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Carrera Inexistente', orden: '', motivo: '' };
    const entidadRara = await P2.responderConIA('quiero saber el resultado de la Carrera Inexistente');
    consultaSimulada = { se_puede: true, operacion: 'satisfaccion', periodo: '', filtros: [], pregunta_objetivo: '', valores_objetivo: [], entidad: 'Psicología', orden: '', motivo: '' };

    test('la IA que traduce hace que el motor responda con los datos', () => {
      assertIncludes(texto(conIA), 'Psicología', 'la carrera traducida');
      assertIncludes(texto(conIA), '97,22', 'satisfacción de Psicología');
      assertIncludes(fuentes(conIA), 'resumenes.json (CSAT por carrera)', 'la respuesta cita su archivo');
    });

    test('si la pregunta no es de las encuestas, la IA tampoco responde', () => {
      assertTrue(noEsDeEncuestas.alcance === false, 'debe quedar fuera de alcance');
    });

    test('si la IA nombra algo que no existe en los datos, se avisa', () => {
      assertTrue(entidadRara.alcance === false, 'no debe responder de más');
      assertIncludes(texto(entidadRara), 'No encontre', 'debe decir que no lo encontró');
    });

    test('"cuántos alumnos se encuestaron en el 2026" lista los períodos de ese año', () => {
      assertIncludes(texto(porAnio), '2026-1', 'período de pregrado');
      assertIncludes(texto(porAnio), '4239', 'respuestas de pregrado 2026-1');
      assertIncludes(texto(porAnio), 'Graduados', 'encuesta de graduados');
      assertIncludes(texto(porAnio), '598', 'respuestas de graduados');
    });

    test('con un período escrito completo responde solo ese período', () => {
      assertIncludes(texto(alumnos20261), '4239', 'respuestas de 2026-1');
      assertTrue(texto(alumnos20261).indexOf('598') === -1, 'no debe mezclar graduados');
    });

    test('"cuántos alumnos respondieron de Psicología" usa el total de esa carrera', () => {
      assertIncludes(texto(porCarrera), 'Psicología', 'la carrera pedida');
      assertIncludes(texto(porCarrera), '431', 'respuestas de Psicología');
      assertIncludes(fuentes(porCarrera), 'resumenes.json (ids)', 'fuente por carrera');
    });

    test('"en total" muestra todos los períodos publicados', () => {
      assertIncludes(texto(enTotal), '2026-1', 'período 2026-1');
      assertIncludes(texto(enTotal), '2025-2', 'período 2025-2');
      assertIncludes(texto(enTotal), 'Graduados', 'encuesta de graduados');
    });

  test('registrar manda la pregunta al contador de más frecuentes', () => {
    const post = llamadasExternas.filter(c => c.opciones && c.opciones.method === 'POST' && String(c.url).indexOf('/api/preguntas') !== -1);
    assertTrue(post.length >= 1, 'debe haber al menos un envío');
    assertIncludes(post[0].url, '/api/preguntas', 'dirección del registro');
    assertIncludes(post[0].opciones.body, 'NPS de 2026-1', 'la pregunta enviada');
  });

  test('lo que se registra va acotado (no crece sin control)', () => {
    const post = llamadasExternas.filter(c => c.opciones && c.opciones.method === 'POST' && String(c.url).indexOf('/api/preguntas') !== -1);
    assertTrue(post[0].opciones.body.length <= 300, 'el cuerpo no debe crecer sin control');
    assertTrue(post[0].opciones.body.indexOf('intencion') !== -1, 'debe decir qué tipo de pregunta fue');
  });

    let lista = null;
    try { lista = await P2.cargarFrecuentes(); } catch (e) { lista = null; }
    test('las más frecuentes se pueden leer del registro', () => {
      assertTrue(Array.isArray(lista), 'debe devolver una lista');
      assertEqual(lista[0].texto, '¿Cuál es el NPS de 2026-1?');
      assertEqual(lista[0].veces, 7);
    });
  })();

    test('las palabras coloquiales del contexto apuntan a preguntas publicadas', () => {
    const ctx = JSON.parse(fs.readFileSync(path.join(raiz, 'shared/config/asistente_contexto.json'), 'utf8'));
    const cabeceras = [
      'students/undergraduate/2025-2/json/respuestas.json',
      'students/undergraduate/2026-1/json/respuestas.json',
      'students/graduate/2026/json/respuestas.json'
    ].reduce(function (todas, rel) {
      const d = JSON.parse(fs.readFileSync(path.join(raiz, rel), 'utf8'));
      return todas.concat(d.cabeceras);
    }, []);
    const huerfanas = Object.keys(ctx.palabras_coloquiales).filter(function (c) {
      return cabeceras.indexOf(c) === -1;
    });
    assertEqual(huerfanas.join(', '), '', 'claves que ya no son preguntas publicadas');
    assertTrue(Array.isArray(ctx.que_es) && ctx.que_es.length > 0, 'falta que_es');
    assertTrue(Array.isArray(ctx.reglas) && ctx.reglas.length > 0, 'falta reglas');
    assertTrue(Array.isArray(ctx.equivalencias) && ctx.equivalencias.length > 0, 'falta equivalencias');
    Object.keys(ctx.palabras_coloquiales).forEach(function (c) {
      assertTrue(ctx.palabras_coloquiales[c].length > 0, 'la lista de ' + c + ' no puede estar vacia');
    });
  });

  console.log('\n=== Tests JS del asistente 1.9 (jsdom) ===');
  console.log('passed=' + passed + ' failed=' + failed + ' total=' + (passed + failed));
  if (failed > 0) {
    results.filter(r => r.status === 'fail').forEach(r => console.log('  FAIL: ' + r.name + ' -> ' + r.error));
    process.exit(1);
  }
})();
