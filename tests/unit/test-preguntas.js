/**
 * Tests JS con jsdom — asistente de preguntas del item 1.9 (portal-preguntas.js).
 *
 * Lo que se comprueba: que el portal busque los datos en los JSON publicados, que se los mande
 * al modelo para que redacte, que cada cifra escrita exista en los datos y que la respuesta
 * cite la encuesta de la que salió. Lo que no está en los datos NO se responde.
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

require(path.join(raiz, 'shared/js/config/constants.js'));
require(path.join(raiz, 'shared/js/utils/sanitizer.js'));
require(path.join(raiz, 'shared/js/utils/formatters.js'));
require(path.join(raiz, 'shared/js/portal/portal-preguntas.js'));

// El plan y la redacción simulados (se cambian en cada prueba, como haría el servicio).
let planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [], motivo: '' };
let redaccionSimulada = 'Hay 4239 respuestas en 2026-1.\nFuente: Estudiantes Pregrado 2026-1';
let fallaLaRedaccion = false;
const peticiones = [];            // lo que el portal le manda al servicio

global.fetch = function (url, opciones) {
  if (/^https?:\/\//.test(String(url))) {
    const cuerpo = opciones && opciones.body ? JSON.parse(opciones.body) : {};
    peticiones.push({ url: String(url), cuerpo: cuerpo });
    if (String(url).indexOf('/interpretar') !== -1) {
      if (cuerpo.paso === 'respuesta') {
        if (fallaLaRedaccion) {
          return Promise.resolve({ ok: false, json: function () { return Promise.resolve(null); } });
        }
        return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ respuesta: redaccionSimulada }); } });
      }
      return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ plan: planSimulado }); } });
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
function assertNoIncludes(texto, trozo, msg) {
  assert.ok(String(texto).indexOf(trozo) === -1, (msg || '') + ' (no debería contener "' + trozo + '")');
}

const P = window.SurveyPortalPreguntas;

(async function () {
  // --- los datos publicados ---
  const tablas = await P.cargarTodasLasTablas();
  const contexto = P.textoDeContexto(await (await fetch('shared/config/asistente_contexto.json')).json());
  const menu = tablas.map(function (x) { return P.construirMenu(x.p, x.tabla); }).join('\n\n');

  // Bloques del caso del usuario: Psicología entre dos períodos.
  planSimulado = {
    se_puede: true,
    periodos: ['Estudiantes Pregrado 2025-2', 'Estudiantes Pregrado 2026-1'],
    preguntas: ['Carrera'],
    filtros: [{ pregunta: 'Carrera', valores: ['Psicología'] }],
    motivo: ''
  };
  const bloquesComparacion = P.bloquesDe(planSimulado, tablas);

  // Bloques de una pregunta con reparto (Graduados 2026: situación laboral).
  planSimulado = { se_puede: true, periodos: ['Graduados Pregrado 2026'], preguntas: ['Situación laboral'], filtros: [], motivo: '' };
  const bloquesGraduados = P.bloquesDe(planSimulado, tablas);

  // Las dos lecturas de "trabajan" con el filtro de una carrera (Graduados 2026).
  planSimulado = { se_puede: true, periodos: ['Graduados Pregrado 2026'], preguntas: ['Situación laboral'], filtros: [{ pregunta: 'Carrera', valores: ['Economía'] }], motivo: '' };
  const bloquesTrabajo = P.bloquesDe(planSimulado, tablas);

  // Bloques del NPS y de la satisfacción del período.
  // El plan lo arma el modelo desde el menú (nombres publicados); el portal los
  // reconoce por su id declarado (bloqueDeNps / bloqueDeSatisfaccion).
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Recomendación (0 al 10)'], filtros: [], motivo: '' };
  const bloquesNps = P.bloquesDe(planSimulado, tablas);
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['La Universidad de Lima'], filtros: [], motivo: '' };
  const bloquesSatisfaccion = P.bloquesDe(planSimulado, tablas);

  // --- el flujo completo, en pantalla ---
  document.body.innerHTML = P.render();

  // 1. Una respuesta normal: el texto con la fuente, en dos burbujas.
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [{ pregunta: 'Carrera', valores: ['Psicología'] }], motivo: '' };
  redaccionSimulada = 'En 2026-1 respondieron 431 personas de Psicología.\nFuente: Estudiantes Pregrado 2026-1';
  const respuesta = await P.preguntar('¿Cuántos alumnos respondieron de Psicología?');
  const caja = document.getElementById('preguntasRespuestas');
  const pintado = caja ? caja.textContent : '';

  // 2. Un seguimiento: la segunda pregunta lleva la conversación anterior.
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2025-2'], preguntas: ['Carrera'], filtros: [{ pregunta: 'Carrera', valores: ['Psicología'] }], motivo: '' };
  redaccionSimulada = 'En 2025-2 respondieron 316 personas de Psicología.\nFuente: Estudiantes Pregrado 2025-2';
  await P.preguntar('¿y del 2025?');
  const planes = peticiones.filter(function (x) { return x.cuerpo.paso === 'plan'; });
  const conSeguimiento = planes[planes.length - 1].cuerpo.contexto;

  // 3. Fuera de alcance: lo que no está en los datos.
  planSimulado = { se_puede: false, periodos: [], preguntas: [], filtros: [], motivo: 'No hay datos de clima en las encuestas.' };
  const fuera = await P.preguntar('¿Cómo estará el clima mañana?');
  const cajaFuera = caja ? caja.querySelector('.preguntas-respuesta') : null;
  const pintadoFuera = cajaFuera ? cajaFuera.textContent : '';
  const claseFuera = cajaFuera ? cajaFuera.className : '';

  // 4. Una cifra que no está en los datos: no se muestra.
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [], motivo: '' };
  redaccionSimulada = 'En 2026-1 hubo 99999 respuestas.\nFuente: Estudiantes Pregrado 2026-1';
  const inventada = await P.preguntar('¿Cuántas respuestas hay?');
  const pintadoInventado = caja ? caja.textContent : '';

  // 5. Si la redacción no llega, se avisa (no se queda en "Consultando…").
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [], motivo: '' };
  fallaLaRedaccion = true;
  const sinRedaccion = await P.preguntar('¿Cuántas respuestas hay?');
  const pintadoSinRedaccion = caja ? caja.textContent : '';
  fallaLaRedaccion = false;

  // 6. Una respuesta con bloque de tabla: se dibuja como tabla (no como texto).
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [], motivo: '' };
  redaccionSimulada = 'Ingeniería Industrial tiene la satisfacción más alta.\n' +
    'Tabla: Carrera | Satisfacción\nIngeniería Industrial | 98,87 %\nPsicología | 97,22 %\n' +
    'Fuente: Estudiantes Pregrado 2026-1';
  caja.innerHTML = '';
  await P.preguntar('compara las carreras');
  const tablaDibujada = caja.querySelector('table.survey-table');
  const envoltorioTabla = caja.querySelector('.table-scroll');
  const columnasTabla = tablaDibujada ? tablaDibujada.querySelectorAll('th').length : 0;
  const filasTabla = tablaDibujada ? tablaDibujada.querySelectorAll('tbody tr').length : 0;
  const pintadoTabla = caja.textContent;

  // 7. Una tabla con una cifra que no está en los datos: no se dibuja.
  //    (88,88 % no aparece en los datos ni sale de ninguna cuenta entre las cifras publicadas.)
  planSimulado = { se_puede: true, periodos: ['Estudiantes Pregrado 2026-1'], preguntas: ['Carrera'], filtros: [], motivo: '' };
  redaccionSimulada = 'Comparación de carreras.\n' +
    'Tabla: Carrera | Satisfacción\nAdministración | 88,88 %\nPsicología | 97,22 %\n' +
    'Fuente: Estudiantes Pregrado 2026-1';
  caja.innerHTML = '';
  await P.preguntar('compara las carreras');
  const tablaSinRespaldo = caja.querySelector('table.survey-table');

  // --- las pruebas ---
  test('se cargan las tres encuestas publicadas', function () {
    assertEqual(tablas.length, 3);
  });

  test('el menú lleva todas las encuestas y ninguna cifra', function () {
    tablas.forEach(function (x) { assertIncludes(menu, '## Menú — ' + x.p.nombre + ' ' + x.p.periodo); });
    assertIncludes(menu, 'Situación laboral', 'el menú nombra las preguntas');
    assertNoIncludes(menu, '4239', 'el menú no lleva conteos');
    assertNoIncludes(menu, '72,61', 'el menú no lleva el NPS');
  });

  test('el menú distingue las columnas de agrupación de las preguntas que se miden', function () {
    const pregrado = tablas.filter(function (x) { return x.p.fase === '1.0' && x.p.periodo === '2026-1'; })[0];
    const m = P.construirMenu(pregrado.p, pregrado.tabla);
    assertIncludes(m, '### Agrupación', 'hay un grupo de columnas de agrupación');
    assertIncludes(m, '### Medida', 'hay un grupo de preguntas que se miden');
    assertIncludes(m, 'escala CSAT', 'las medidas de satisfacción dicen su escala');
    assertIncludes(m, 'escala NPS', 'la recomendación del 0 al 10 dice su escala');
    const iAgrup = m.indexOf('### Agrupación');
    const iMedida = m.indexOf('### Medida');
    assertTrue(iAgrup !== -1 && iMedida !== -1 && iAgrup < iMedida, 'la agrupación va antes que las medidas');
    const iCarrera = m.indexOf('- Carrera:');
    assertTrue(iCarrera > iAgrup && iCarrera < iMedida, 'Carrera se anuncia como columna de agrupación');
    assertTrue(m.indexOf('- Satisfacción con tu carrera') > iMedida, 'la satisfacción con tu carrera se anuncia como medida');
    assertTrue(m.indexOf('- Satisfacción con la Universidad:') > iMedida, 'la satisfacción con la Universidad se anuncia como medida');
    assertTrue(m.indexOf('- Recomendación (0 al 10)') > iMedida, 'la recomendación se anuncia como medida');
  });

  test('el menú se arma con el bloque preguntas publicado y no con nombres fijos', function () {
    const tabla = {
      cabeceras: ['Carrera', 'Cohorte'],
      opciones: { Carrera: ['Derecho'], Cohorte: ['2019', '2020'] },
      preguntas: [
        { id: 'carrera', nombre: 'Carrera', tipo: 'medida', pregunta: 'Tu carrera', escala: 'CSAT' },
        { id: 'cohorte', nombre: 'Cohorte', tipo: 'agrupacion', pregunta: '¿De qué cohorte egresaste?', escala: '' }
      ]
    };
    const m = P.construirMenu({ nombre: 'Prueba', periodo: '2026-1' }, tabla);
    const iAgrup = m.indexOf('### Agrupación');
    const iMedida = m.indexOf('### Medida');
    assertTrue(iAgrup !== -1 && iMedida !== -1, 'arma los dos grupos del dato');
    const iCohorte = m.indexOf('- Cohorte:');
    assertTrue(iCohorte > iAgrup && iCohorte < iMedida, 'la columna de agrupación va en su grupo');
    assertTrue(m.indexOf('- Carrera:') > iMedida, 'una columna declarada medida va en el grupo de medidas');
  });

  test('el contexto del asistente sale del archivo de configuración', function () {
    assertIncludes(contexto, '## Qué es');
    assertIncludes(contexto, '## Cómo están los datos');
    assertIncludes(contexto, '## Cómo se pregunta por las cosas', 'las palabras coloquiales');
    assertIncludes(contexto, '## El cierre de la encuesta', 'el cierre: los dos ítems y cómo leerlo');
    assertIncludes(contexto, 'De manera global', 'el texto de la pregunta global del cierre');
    assertNoIncludes(contexto, 'secciones del formulario', 'la enumeración larga de preguntas ya no está');
    assertIncludes(contexto, '## Dimensiones', 'las dimensiones con sus preguntas');
    assertIncludes(contexto, 'Docencia', 'una dimensión que solo existe en Graduados');
    assertIncludes(contexto, '## Columnas que no son preguntas', 'el ID y las fechas');
    assertTrue(contexto.length > 500, 'el contexto no puede quedar vacío');
  });

  test('los bloques de Psicología traen sus respuestas, de cada período', function () {
    assertIncludes(bloquesComparacion.texto, 'Psicología');
    assertIncludes(bloquesComparacion.texto, '431 respuestas');
    assertIncludes(bloquesComparacion.texto, '2025-2');
    assertIncludes(bloquesComparacion.texto, '2026-1');
    assertEqual(bloquesComparacion.fuentes.length, 2);
  });

  test('los bloques de un reparto traen los conteos publicados', function () {
    assertIncludes(bloquesGraduados.texto, 'Situación laboral');
    assertIncludes(bloquesGraduados.texto, 'Trabajador dependiente: 260');
    assertIncludes(bloquesGraduados.texto, '598 respuestas');
  });

  test('para "trabajan" van las dos lecturas y el tiempo laboral', function () {
    assertIncludes(bloquesTrabajo.texto, 'Trabajan (trabajo formal');
    assertIncludes(bloquesTrabajo.texto, '8 de 14 (57,14 %)');
    assertIncludes(bloquesTrabajo.texto, '14 de 14 (100 %)');
    assertIncludes(bloquesTrabajo.texto, 'El tiempo laboral de esos 8: Tiempo completo 8 (100 %)');
  });

  test('los bloques del NPS y de la satisfacción salen del dashboard', function () {
    assertIncludes(bloquesNps.texto, 'NPS 72,61');
    assertIncludes(bloquesSatisfaccion.texto, '97,85 %');
  });

  test('una cifra que está en los datos sostiene la respuesta', function () {
    assertTrue(P.respuestaSostenida('Hay 4239 respuestas.\nFuente: Estudiantes Pregrado 2026-1', 'Total: 4239 respuestas'), 'debería sostenerla');
  });

  test('una cuenta simple entre cifras publicadas sí sostiene la respuesta', function () {
    const datos = '## Datos\n- NPS 61,31 sobre 3998 respuestas.\n- NPS 72,61 sobre 4239 respuestas.';
    assertTrue(P.respuestaSostenida('El NPS subió 11,3 puntos (de 61,31 a 72,61).', datos), 'debería aceptar la resta');
    assertTrue(P.respuestaSostenida('Respondieron 8237 personas en total (3998 y 4239).', datos), 'debería aceptar la suma');
    assertTrue(!P.respuestaSostenida('El NPS subió 20 puntos.', datos), 'no debería aceptar una resta que no da');
  });

  test('dividir una cifra publicada sostiene la respuesta, pero una parecida NO', function () {
    const datos = '## Datos\n- Total: 598 respuestas.\n- Carrera = Economía: 14 respuestas.\n- NPS 72,61.';
    assertTrue(P.respuestaSostenida('Economía es 14 de 598 (2,34 %).', datos), 'acepta la proporción');
    assertTrue(!P.respuestaSostenida('El NPS fue de 73.', datos), 'no acepta 73 por 72,61: eso es otra cifra');
    assertTrue(!P.respuestaSostenida('El NPS fue de 85.', datos), 'no acepta una cifra que no sale de los datos');
  });

  test('los números se muestran como pide el proyecto', function () {
    assertEqual(P.formatearNumeros('4,239 respuestas y 72.61 %'), '4239 respuestas y 72,61 %');
    assertEqual(P.formatearNumeros('1.234.567'), '1234567');
    assertEqual(P.formatearNumeros('97.85%'), '97,85 %');
    assertEqual(P.formatearNumeros('Son 598 de 4239'), 'Son 598 de 4239');
  });

  test('una cifra que no está en los datos NO sostiene la respuesta', function () {
    assertTrue(!P.respuestaSostenida('Hay 99999 respuestas.', 'Total: 4239 respuestas'), 'debería rechazarla');
  });

  test('la respuesta se pinta con su fuente y su burbuja de pregunta', function () {
    assertIncludes(pintado, '¿Cuántos alumnos respondieron de Psicología?');
    assertIncludes(pintado, '431 personas de Psicología');
    assertIncludes(pintado, 'Fuente: Estudiantes Pregrado 2026-1');
  });

  test('el turno queda en memoria para el seguimiento', function () {
    assertIncludes(conSeguimiento, 'Conversación reciente');
    assertIncludes(conSeguimiento, '¿Cuántos alumnos respondieron de Psicología?');
  });

  test('lo que no está en los datos se responde con un aviso, sin fuente', function () {
    assertIncludes(pintadoFuera, '¿Cómo estará el clima mañana?');
    assertIncludes(pintadoFuera, 'No hay datos de clima en las encuestas.');
    assertNoIncludes(pintadoFuera, 'Fuente:');
    assertIncludes(claseFuera, 'fuera-de-alcance');
    assertTrue(fuera && fuera.aviso, 'devuelve un aviso');
  });

  test('una cifra inventada por el modelo no se muestra', function () {
    assertNoIncludes(pintadoInventado, '99999');
    assertIncludes(pintadoInventado, 'no estan en los datos publicados');
  });

  test('si no hay redacción, se avisa en pantalla', function () {
    assertNoIncludes(pintadoSinRedaccion, 'Consultando');
    assertIncludes(pintadoSinRedaccion, 'No pude redactar la respuesta');
    assertTrue(sinRedaccion && sinRedaccion.aviso, 'devuelve un aviso');
  });

  test('cada pregunta se manda al servicio con su contexto y su menú', function () {
    const planes = peticiones.filter(function (x) { return x.cuerpo.paso === 'plan'; });
    assertTrue(planes.length >= 5, 'las preguntas pasan por el plan');
    planes.forEach(function (p) {
      assertIncludes(p.cuerpo.menu, '## Menú —', 'el plan viaja con el menú');
      assertIncludes(p.cuerpo.contexto, 'Contexto del asistente');
      assertTrue(p.cuerpo.pregunta.length > 3, 'el plan viaja con la pregunta');
    });
  });

  test('los datos que se le mandan al modelo son pocos (no es la tabla completa)', function () {
    assertTrue(bloquesComparacion.texto.length < 4000, 'los bloques deben ser chicos');
    assertNoIncludes(bloquesComparacion.texto, '"filas"', 'no se manda la tabla cruda');
    assertTrue(respuesta && respuesta.texto, 'la respuesta trae texto');
  });

  test('las palabras coloquiales del contexto apuntan a preguntas publicadas', function () {
    const ctx = JSON.parse(fs.readFileSync(path.join(raiz, 'shared/config/asistente_contexto.json'), 'utf8'));
    const cabeceras = tablas.reduce(function (todas, x) { return todas.concat(x.tabla.cabeceras); }, []);
    const huerfanas = Object.keys(ctx.palabras_coloquiales).filter(function (c) {
      return cabeceras.indexOf(c) === -1;
    });
    assertEqual(huerfanas.join(', '), '', 'claves que ya no son preguntas publicadas');
  });

  test('una respuesta con bloque de tabla se dibuja con el estilo del portal', function () {
    assertTrue(tablaDibujada, 'la tabla se dibuja');
    assertTrue(envoltorioTabla, 'usa el envoltorio que ya existe');
    assertEqual(columnasTabla, 2);   // dos columnas: Carrera y Satisfacción
    assertEqual(filasTabla, 2);      // dos filas: una por carrera
    assertIncludes(pintadoTabla, 'Ingeniería Industrial', 'la tabla trae sus filas');
    assertNoIncludes(pintadoTabla, 'Tabla:', 'el bloque no se muestra como texto');
  });

  test('una tabla con una cifra que no está en los datos no se dibuja', function () {
    assertTrue(!tablaSinRespaldo, 'no se dibuja una tabla sin respaldo');
  });

  // --- las columnas se resuelven por su id declarado, no por su nombre publicado ---
  // Tabla mínima: el mismo dato publicado con otros nombres (mismos ids y misma escala).
  function tablaSintetica(nombres) {
    var tabla = {
      cabeceras: [nombres.carrera, nombres.nps, nombres.csat],
      opciones: {},
      preguntas: [
        { id: 'carrera', nombre: nombres.carrera, tipo: 'agrupacion', escala: '' },
        { id: 'nps', nombre: nombres.nps, tipo: 'medida', escala: 'NPS' },
        { id: 'csat_universidad', nombre: nombres.csat, tipo: 'medida', escala: 'CSAT' }
      ],
      // Tres de Derecho y uno de Psicología; las tres medidas de cierre con su valor.
      filas: [[0, 0, 0], [0, 0, 0], [0, 2, 2], [1, 1, 1]]
    };
    tabla.opciones[nombres.carrera] = ['Derecho', 'Psicología'];
    tabla.opciones[nombres.nps] = ['10', '9', '8'];
    tabla.opciones[nombres.csat] = window.SURVEY_CONFIG.SAT_KEYS.slice();
    return tabla;
  }

  function periodoSintetico(extra) {
    return { nombre: 'Prueba', periodo: '2026-1', fase: '1.0', dash: extra || {} };
  }

  test('el NPS y la satisfacción se miden por su id, no por su nombre', function () {
    var originales = tablaSintetica({ carrera: 'Carrera', nps: 'Recomiendas la Universidad de Lima', csat: 'La Universidad de Lima' });
    var otros = tablaSintetica({ carrera: 'Programa', nps: 'Recomendación (0-10)', csat: 'Satisfacción Ulima' });
    var a = P.medir(originales, originales.filas);
    var b = P.medir(otros, otros.filas);
    assertEqual(JSON.stringify(b), JSON.stringify(a));
    assertEqual(a.nps, 75);
    assertEqual(a.satisfaccion, 100);
  });

  test('la columna de agrupación se reconoce por su id, no por su nombre', function () {
    var tabla = tablaSintetica({ carrera: 'Programa', nps: 'Recomendación (0-10)', csat: 'Satisfacción Ulima' });
    var out = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['Programa'], filtros: [] },
      [{ p: periodoSintetico(), tabla: tabla }]);
    assertIncludes(out.texto, 'Programa', 'el bloque nombra la columna pedida');
    assertIncludes(out.texto, 'Derecho:', 'agrupa por sus valores');
    assertIncludes(out.texto, 'satisfaccion', 'un grupo se mide (NPS y satisfacción del grupo)');
  });

  test('sin preguntas en el plan se usa la columna de agrupación por su id', function () {
    var tabla = tablaSintetica({ carrera: 'Programa', nps: 'Recomendación (0-10)', csat: 'Satisfacción Ulima' });
    var out = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: [], filtros: [] },
      [{ p: periodoSintetico(), tabla: tabla }]);
    assertIncludes(out.texto, 'Programa', 'la columna por defecto se resuelve por id');
    assertIncludes(out.texto, 'satisfaccion', 'y se mide como grupo');
  });

  test('la satisfacción del período se reconoce por el id de la Universidad', function () {
    var tabla = tablaSintetica({ carrera: 'Carrera', nps: 'Recomiendas la Universidad de Lima', csat: 'Satisfacción Ulima' });
    var out = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['Satisfacción Ulima'], filtros: [] },
      [{ p: periodoSintetico({ resumen: { csat: { score: 97.85 } } }), tabla: tabla }]);
    assertIncludes(out.texto, 'Satisfacción del período: 97,85 %');
  });

  test('el tiempo laboral se reconoce por su id, no por su nombre', function () {
    function tablaGraduado(prog, sit, tiempo) {
      var o = {};
      o[prog] = ['Economía'];
      o[sit] = ['Trabajador dependiente', 'Trabajador independiente', 'Prácticas profesionales', 'Prácticas pre - profesionales'];
      o[tiempo] = ['Tiempo completo', 'Tiempo parcial'];
      var filas = [];
      for (var i = 0; i < 8; i++) filas.push([0, 0, 0]);   // trabajadores dependientes
      for (var j = 0; j < 6; j++) filas.push([0, 2, 1]);   // prácticas, tiempo parcial
      return {
        cabeceras: [prog, sit, tiempo],
        opciones: o,
        preguntas: [
          { id: 'carrera', nombre: prog, tipo: 'agrupacion', escala: '' },
          { id: 'situacion_laboral', nombre: sit, tipo: 'agrupacion', escala: '' },
          { id: 'tiempo_laboral', nombre: tiempo, tipo: 'agrupacion', escala: '' }
        ],
        filas: filas
      };
    }
    var p = periodoSintetico();
    var esperado = 'El tiempo laboral de esos 8: Tiempo completo 8 (100 %)';
    var conOriginales = tablaGraduado('Carrera', 'Situación laboral', 'Tiempo laboral');
    var conOtros = tablaGraduado('Programa', 'Estado laboral', 'Dedicación laboral');
    var a = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['Situación laboral'], filtros: [{ pregunta: 'Carrera', valores: ['Economía'] }] },
      [{ p: p, tabla: conOriginales }]);
    var b = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['Estado laboral'], filtros: [{ pregunta: 'Programa', valores: ['Economía'] }] },
      [{ p: p, tabla: conOtros }]);
    assertIncludes(a.texto, esperado);
    assertIncludes(b.texto, esperado, 'con otros nombres el tiempo laboral sigue saliendo');
  });

  test('el NPS se elige por el id de la declaración, con cualquier nombre', function () {
    var tabla = {
      cabeceras: ['Puntaje de recomendación'],
      opciones: {},
      preguntas: [
        { id: 'nps', nombre: 'Puntaje de recomendación', tipo: 'medida', pregunta: 'Otra pregunta', escala: 'NPS' }
      ],
      filas: []
    };
    var p = periodoSintetico({ resumen: { nps: { score: 55.5, total: 10, promotores: 6, pasivos: 3, detractores: 1 } } });
    var out = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['Puntaje de recomendación'], filtros: [] },
      [{ p: p, tabla: tabla }]);
    assertIncludes(out.texto, 'NPS 55,5', 'el NPS sale del dashboard por el id, con el nombre que sea');
  });

  test('la satisfacción global se elige por el id, aunque su pregunta tenga otro nombre', function () {
    var tabla = {
      cabeceras: ['Satisfacción Ulima'],
      opciones: { 'Satisfacción Ulima': window.SURVEY_CONFIG.SAT_KEYS.slice() },
      preguntas: [
        { id: 'csat_universidad', nombre: 'Satisfacción Ulima', tipo: 'medida', pregunta: 'La universidad en general', escala: 'CSAT' }
      ],
      filas: [[0]]
    };
    var p = periodoSintetico({ resumen: { csat: { score: 97.85 } } });
    var out = P.bloquesDe({ periodos: ['Prueba 2026-1'], preguntas: ['La universidad en general'], filtros: [] },
      [{ p: p, tabla: tabla }]);
    assertIncludes(out.texto, 'Satisfaccion en Prueba 2026-1', 'se reconoce por el id de la declaración');
    assertIncludes(out.texto, '97,85 %');
  });

  console.log('\n=== asistente del item 1.9 (portal-preguntas) ===');
  results.filter(function (r) { return r.status === 'fail'; }).forEach(function (r) { console.log('❌ ' + r.name + ' → ' + r.error); });
  console.log('\n' + passed + ' passed, ' + failed + ' failed, ' + (passed + failed) + ' total');
  if (inventada && inventada.datos) { /* los datos usados quedan disponibles para depurar */ }
  process.exit(failed === 0 ? 0 : 1);
})();
