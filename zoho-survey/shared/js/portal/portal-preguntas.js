/* ============================================================
   SURVEY PORTAL PREGUNTAS — Asistente del item 1.9.
   Responde SOLO con lo que esta en los JSON publicados de las encuestas.
   Si un dato no esta en esos JSON, lo dice y no improvisa: no hay respuestas
   sobre hora, clima, noticias ni nada que no venga de las encuestas.
   Cada respuesta cita la encuesta de la que salio.
   ============================================================ */
window.SurveyPortalPreguntas = (function () {
  'use strict';

  var FASE_NIVEL = { '1.0': 'students/undergraduate', '1.2': 'students/graduate' };
  var FASE_NOMBRE = { '1.0': 'Estudiantes Pregrado', '1.2': 'Graduados Pregrado' };
  // Los cinco resumenes del periodo llegan juntos en resumenes.json.
  var ARCHIVOS = ['dashboard_data', 'resumenes', 'filtros'];

  // Primero dice qué datos hay que leer; después redacta con ellos.
  // No calcula ni inventa (ver survey-tracker/apps/backend/api/interpretar.js).
  var INTERPRETE_URL = 'https://qr-smoky-theta.vercel.app/api/interpretar';

  var CATALOGO = null;   // periodos con sus JSON chicos
  var TABLAS = {};       // respuestas.json por periodo (grande: se lee solo si hace falta)
  var CONTEXTO = null;   // el contexto del asistente (que es, como estan los datos, reglas)
  var MEMORIA = [];      // los ultimos turnos (pregunta y respuesta), para entender "y del 2025?"

  // ---------- utilidades ----------
  function esc(t) {
    if (window.SurveySanitizer && window.SurveySanitizer.escapeHTML) return window.SurveySanitizer.escapeHTML(t);
    return String(t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function sin(texto) {
    return String(texto == null ? '' : texto).toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  // Igual que sin(), pero sin la s final de cada palabra: asi "no disponibles para
  // trabajar" (como lo escribe la gente) encuentra "No disponible para trabajar" (la opcion).
  function sinS(texto) {
    return sin(texto).replace(/s\b/g, '');
  }

  // Un nombre de pregunta pegado a un "de" ("la carrera de Economia", "la facultad de
  // Derecho") no es el tema de la pregunta: ahi "carrera" o "facultad" describen el
  // grupo. Sin este candado, "que porcentaje de graduados de la carrera de economia
  // trabajan" elegia "La carrera" como objetivo y respondia otra cosa.
  function nombreComoCalificador(t, nombre) {
    var texto = sinS(t);
    var x = sinS(nombre);
    var i = texto.indexOf(x);
    if (i === -1) return false;
    return /^\s+de\s/.test(texto.slice(i + x.length, i + x.length + 8));
  }


  // Numeros como en el resto del proyecto: sin separador de miles, coma decimal.
  function n(valor) {
    if (valor == null || isNaN(valor)) return 'sin dato';
    var entero = Math.abs(valor) >= 1000 ? String(Math.round(valor)) : String(valor);
    if (!(Math.abs(valor) >= 1000)) entero = String(Math.round(valor * 100) / 100).replace('.', ',');
    return entero;
  }

  function pct(valor) {
    if (valor == null || isNaN(valor)) return 'sin dato';
    return (Math.round(valor * 100) / 100).toString().replace('.', ',') + ' %';
  }

  function leer(ruta) {
    return fetch(ruta, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('sin archivo');
      return r.json();
    });
  }

  // ---------- carga de los JSON publicados ----------
  function periodosDeFase(fase) {
    var nivel = FASE_NIVEL[fase];
    if (!nivel) return Promise.resolve([]);
    return leer(nivel + '/periodos.json').then(function (lista) {
      return (lista || []).filter(function (p) { return p && p.id && p.id !== 'proximamente'; })
        .map(function (p) { return p.id; });
    }).catch(function () { return []; });
  }

  function cargarPeriodo(fase, periodo) {
    var base = FASE_NIVEL[fase] + '/' + periodo + '/json/';
    return Promise.all(ARCHIVOS.map(function (a) {
      return leer(base + a + '.json').catch(function () { return null; });
    })).then(function (r) {
      var res = r[1] || {};
      return {
        fase: fase, nivel: FASE_NIVEL[fase], nombre: FASE_NOMBRE[fase], periodo: periodo,
        base: base,
        dash: r[0], resumenes: res,
        npsCarrera: res.nps_carrera || [], csatCarrera: res.csat_carrera || [],
        npsCiclo: res.nps_ciclo_carrera || [], csatCiclo: res.csat_ciclo_carrera || [],
        filtros: r[2] || {}, ids: res.ids || []
      };
    });
  }

  function cargar() {
    if (CATALOGO) return Promise.resolve(CATALOGO);
    var fases = Object.keys(FASE_NIVEL);
    return Promise.all(fases.map(function (f) {
      return periodosDeFase(f).then(function (periodos) {
        return Promise.all(periodos.map(function (p) { return cargarPeriodo(f, p); }));
      });
    })).then(function (grupos) {
      CATALOGO = [];
      grupos.forEach(function (g) { g.forEach(function (p) { if (p.dash) CATALOGO.push(p); }); });
      return CATALOGO;
    });
  }

  function deFase(fase) { return (CATALOGO || []).filter(function (p) { return p.fase === fase; }); }
  function dePeriodo(periodo) { return (CATALOGO || []).filter(function (p) { return p.periodo === periodo; }); }

  /** El nombre con el que se conoce una encuesta: "Estudiantes Pregrado 2026-1". */
  function etiquetaDe(p) {
    return p.nombre + ' ' + p.periodo;
  }

  /** La cita de una respuesta: la encuesta (y, si hace falta, de qué parte habla). */
  function fuente(p, detalle) {
    return 'Fuente: ' + etiquetaDe(p) + (detalle ? ' — ' + detalle : '');
  }

  /** Lee respuestas.json de un periodo (grande: solo cuando hace falta) y lo deja en memoria. */
  function cargarTabla(p) {
    if (TABLAS[p.periodo]) return Promise.resolve(TABLAS[p.periodo]);
    return leer(p.base + 'respuestas.json').then(function (r) {
      if (r && r.cabeceras) TABLAS[p.periodo] = r;
      return TABLAS[p.periodo] || null;
    }).catch(function () { return null; });
  }

  /** El contexto del asistente (el mismo para todas las preguntas). */
  function cargarContexto() {
    if (CONTEXTO) return Promise.resolve(CONTEXTO);
    return leer('shared/config/asistente_contexto.json').then(function (c) {
      CONTEXTO = c || {};
      return CONTEXTO;
    }).catch(function () { CONTEXTO = {}; return CONTEXTO; });
  }

  /** El contexto como texto, tal como viaja al modelo. */
  function textoDeContexto(c) {
    var partes = [];
    [['que_es', 'Qué es'], ['como_estan_los_datos', 'Cómo están los datos'],
      ['como_esta_organizado', 'Cómo está organizado el cuestionario'], ['reglas', 'Reglas'],
      ['equivalencias', 'Equivalencias'], ['palabras_coloquiales', 'Cómo se pregunta por las cosas']]
      .forEach(function (par) {
        var v = c && c[par[0]];
        if (!v) return;
        if (Array.isArray(v)) {
          partes.push('## ' + par[1] + '\n' + v.map(function (x) { return '- ' + x; }).join('\n'));
        } else if (typeof v === 'object') {
          partes.push('## ' + par[1] + '\n' + Object.keys(v).map(function (k) {
            return '- ' + k + ' → se pide como: ' + (Array.isArray(v[k]) ? v[k].join(', ') : v[k]);
          }).join('\n'));
        } else {
          partes.push('## ' + par[1] + '\n' + v);
        }
      });
    return ('# Contexto del asistente\n' + partes.join('\n\n')).slice(0, 6000);
  }

  /** El menú de un periodo: sus preguntas y las opciones publicadas. Sin cifras. */
  function construirMenu(p, tabla) {
    var cab = (tabla && tabla.cabeceras) || [];
    var ops = (tabla && tabla.opciones) || {};
    var lineas = ['## Menú — ' + etiquetaDe(p)];
    cab.forEach(function (q) {
      var valores = (ops[q] || []).filter(function (o) { return o && o !== '(sin respuesta)'; });
      lineas.push('- ' + q + (valores.length ? ': ' + valores.slice(0, 40).join(' | ') : ''));
    });
    return lineas.join('\n').slice(0, 12000);
  }

  // ---------- los datos: el portal los busca, el modelo los redacta ----------

  var PASO_PLAN = 'plan';
  var PASO_RESPUESTA = 'respuesta';
  var LIMITE_BLOQUES = 20000;
  var GRUPOS = ['Carrera', 'Facultad', 'Ciclo'];

  /** Una llamada al servicio: el plan (qué leer) o la redacción (con los datos). */
  function pedirAlServicio(cuerpo) {
    return fetch(INTERPRETE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo)
    }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }

  /** Paso 1: que datos hay que leer para responder la pregunta. */
  function planificar(texto, contexto, menu) {
    return pedirAlServicio({
      paso: PASO_PLAN,
      pregunta: String(texto).slice(0, 300),
      contexto: String(contexto || '').slice(0, 6000),
      menu: String(menu || '').slice(0, 40000)
    }).then(function (d) { return (d && d.plan) ? d.plan : null; });
  }

  /** Paso 2: la redaccion, con los datos que el portal encontro. */
  function redactar(texto, bloques) {
    return pedirAlServicio({
      paso: PASO_RESPUESTA,
      pregunta: String(texto).slice(0, 300),
      bloques: String(bloques || '').slice(0, LIMITE_BLOQUES)
    }).then(function (d) { return (d && d.respuesta) ? d.respuesta : null; });
  }

  /** Los numeros que aparecen en un texto (para comprobarlos contra los datos). */
  function numerosDe(texto) {
    return String(texto).match(/\d+(?:[.,]\d+)?/g) || [];
  }

  /** La linea de la fuente, leida de la respuesta del modelo. */
  function fuenteDelTexto(texto) {
    var m = String(texto).match(/^\s*Fuente:\s*(.+)$/im);
    return m ? m[1].trim() : '';
  }

  /** El texto sin la linea de la fuente (lo que se comprueba y lo que se muestra). */
  function sinFuente(texto) {
    return String(texto).replace(/^\s*Fuente:.*$/im, '').trim();
  }

  /** ¿Todo lo que dice la respuesta esta en los datos? (los numeros, uno por uno). */
  function respuestaSostenida(texto, bloques) {
    var datos = String(bloques);
    return numerosDe(sinFuente(texto)).every(function (num) {
      return datos.indexOf(num) !== -1 || datos.indexOf(num.replace('.', ',')) !== -1;
    });
  }

  /** La columna publicada que corresponde a un nombre pedido (exacto o parecido). */
  function nombrePublicado(tabla, pregunta) {
    var cab = tabla.cabeceras || [];
    var x = sin(pregunta);
    var exacta = cab.filter(function (c) { return sin(c) === x; })[0];
    if (exacta) return exacta;
    var parecidas = cab.filter(function (c) { return sin(c).indexOf(x) !== -1 || x.indexOf(sin(c)) !== -1; });
    return parecidas.length === 1 ? parecidas[0] : null;
  }

  /** Las filas que cumplen los filtros pedidos (los nombres se validan contra lo publicado). */
  function aplicarFiltros(tabla, filas, filtros) {
    return (filtros || []).reduce(function (acc, f) {
      var cab = tabla.cabeceras || [];
      var i = cab.indexOf(nombrePublicado(tabla, f.pregunta) || '');
      if (i === -1) return acc;
      var ops = tabla.opciones[nombrePublicado(tabla, f.pregunta)] || [];
      var ids = (f.valores || []).map(function (v) {
        return ops.filter(function (o) { return sin(o) === sin(v); })[0];
      }).filter(Boolean).map(function (o) { return ops.indexOf(o); });
      if (!ids.length) return acc;
      return acc.filter(function (fila) { return ids.indexOf(fila[i]) !== -1; });
    }, filas);
  }

  function textoDeFiltros(filtros) {
    return (filtros || []).map(function (f) { return f.pregunta + ' = ' + (f.valores || []).join(' o '); }).join('; ');
  }

  /** Cuenta y mide un grupo de filas: respuestas, NPS y satisfaccion (los tres mejores niveles). */
  function medir(tabla, filas) {
    var cab = tabla.cabeceras || [];
    var iNps = cab.indexOf('Recomiendas la Universidad de Lima');
    var iSat = cab.indexOf('La Universidad de Lima');
    var buenos = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho'];
    var prom = 0, pas = 0, det = 0, conNps = 0, conSat = 0, bien = 0;
    filas.forEach(function (f) {
      if (iNps !== -1) {
        var v = Number((tabla.opciones[cab[iNps]] || [])[f[iNps]]);
        if (!isNaN(v)) { conNps += 1; if (v >= 9) prom += 1; else if (v >= 7) pas += 1; else det += 1; }
      }
      if (iSat !== -1) {
        var s = (tabla.opciones[cab[iSat]] || [])[f[iSat]];
        if (s && s !== '(sin respuesta)') { conSat += 1; if (buenos.indexOf(s) !== -1) bien += 1; }
      }
    });
    return {
      respuestas: filas.length,
      nps: conNps ? Math.round(((prom - det) / conNps) * 10000) / 100 : null,
      promotores: prom, pasivos: pas, detractores: det,
      satisfaccion: conSat ? Math.round((bien / conSat) * 10000) / 100 : null
    };
  }

  /** Un renglon de un grupo: "Psicologia: 316 respuestas, NPS 71,2, satisfaccion 96,5 %." */
  function renglonDeGrupo(nombre, m) {
    var partes = [nombre + ': ' + n(m.respuestas) + ' respuestas'];
    if (m.nps !== null && m.nps !== undefined) partes.push('NPS ' + n(m.nps));
    if (m.satisfaccion !== null && m.satisfaccion !== undefined) partes.push('satisfaccion ' + pct(m.satisfaccion));
    return '- ' + partes.join(', ') + '.';
  }

  /** El bloque de un grupo (Carrera, Facultad, Ciclo): cuantas respuestas y sus numeros. */
  function bloqueDeGrupo(p, tabla, pregunta, filtros) {
    var campo = nombrePublicado(tabla, pregunta);
    if (!campo) return null;
    var cab = tabla.cabeceras || [];
    var i = cab.indexOf(campo);
    var filas = aplicarFiltros(tabla, tabla.filas, filtros);
    var valores = (tabla.opciones[campo] || []).filter(function (o) { return o && o !== '(sin respuesta)'; });
    var lineas = valores.map(function (v) {
      var suyas = filas.filter(function (f) { return (tabla.opciones[campo] || [])[f[i]] === v; });
      return suyas.length ? renglonDeGrupo(v, medir(tabla, suyas)) : null;
    }).filter(Boolean);
    if (!lineas.length) return null;
    return {
      titulo: campo + (filtros.length ? ' (' + textoDeFiltros(filtros) + ')' : '') + ' en ' + etiquetaDe(p),
      lineas: ['- Total: ' + n(filas.length) + ' respuestas.'].concat(lineas)
    };
  }

  /** El bloque del NPS del periodo. */
  function bloqueDeNps(p) {
    var rr = p.dash && p.dash.resumen && p.dash.resumen.nps;
    if (!rr) return null;
    return {
      titulo: 'NPS en ' + etiquetaDe(p),
      lineas: ['- NPS ' + n(rr.score) + ' sobre ' + n(rr.total) + ' respuestas (promotores ' + n(rr.promotores) +
               ', pasivos ' + n(rr.pasivos) + ', detractores ' + n(rr.detractores) + ').']
    };
  }

  /** El bloque de la satisfaccion general del periodo. */
  function bloqueDeSatisfaccion(p) {
    var c = p.dash && p.dash.resumen && p.dash.resumen.csat;
    if (!c) return null;
    return {
      titulo: 'Satisfaccion en ' + etiquetaDe(p),
      lineas: ['- ' + pct(c.score) + ' de satisfaccion (los tres mejores niveles: ' + n(c.t3b) + ' de ' + n(c.total) + ' respuestas).']
    };
  }

  /** El bloque del reparto de una pregunta: cuantas respuestas hay de cada opcion. */
  function bloqueDeReparto(p, tabla, pregunta, filtros) {
    var campo = nombrePublicado(tabla, pregunta);
    if (!campo) return null;
    var cab = tabla.cabeceras || [];
    var i = cab.indexOf(campo);
    var filas = aplicarFiltros(tabla, tabla.filas, filtros);
    var ops = tabla.opciones[campo] || [];
    var conteo = ops.map(function (o, k) {
      return { valor: o, cuenta: filas.filter(function (f) { return f[i] === k; }).length };
    }).filter(function (x) { return x.valor && x.valor !== '(sin respuesta)' && x.cuenta > 0; })
      .sort(function (a, b) { return b.cuenta - a.cuenta; });
    if (!conteo.length) return null;
    return {
      titulo: campo + (filtros.length ? ' (' + textoDeFiltros(filtros) + ')' : '') + ' en ' + etiquetaDe(p),
      lineas: ['- Total: ' + n(filas.length) + ' respuestas.'].concat(conteo.map(function (x) {
        return '- ' + x.valor + ': ' + n(x.cuenta) + ' (' + pct(filas.length ? 100 * x.cuenta / filas.length : 0) + ').';
      }))
    };
  }

  /** El bloque que corresponde a una pregunta pedida. */
  function bloqueDeUna(p, tabla, pregunta, filtros) {
    if (!pregunta) return null;
    var x = sin(pregunta);
    if (GRUPOS.some(function (g) { return sin(g) === x; })) return bloqueDeGrupo(p, tabla, pregunta, filtros);
    if (x.indexOf('recomiendas') !== -1 || x.indexOf('nps') !== -1) return bloqueDeNps(p);
    if (x.indexOf('universidad de lima') !== -1 && !nombrePublicado(tabla, pregunta)) return bloqueDeSatisfaccion(p);
    return bloqueDeReparto(p, tabla, pregunta, filtros);
  }

  /**
   * Los datos que pidio el plan, sacados de los JSON publicados. Devuelve el texto que se le
   * manda al modelo para redactar y las encuestas de las que salio.
   */
  function bloquesDe(plan, tablas) {
    var partes = [];
    var fuentes = [];
    (plan.periodos || []).forEach(function (dicho) {
      var x = tablas.filter(function (y) {
        return sin(etiquetaDe(y.p)) === sin(dicho) || sin(y.p.periodo) === sin(dicho) ||
          sin(etiquetaDe(y.p)).indexOf(sin(dicho)) !== -1;
      })[0];
      if (!x) return;
      if (fuentes.indexOf(etiquetaDe(x.p)) === -1) fuentes.push(etiquetaDe(x.p));
      var pedidas = (plan.preguntas || []).slice();
      if (!pedidas.length) pedidas = ['Carrera'];
      pedidas.forEach(function (preg) {
        var b = bloqueDeUna(x.p, x.tabla, preg, plan.filtros || []);
        if (b) partes.push('## Datos — ' + etiquetaDe(x.p) + '\n### ' + b.titulo + '\n' + b.lineas.join('\n'));
      });
    });
    return { texto: partes.join('\n\n').slice(0, LIMITE_BLOQUES), fuentes: fuentes };
  }

  /**
   * Responde: pide el plan, busca los datos publicados, deja que el modelo redacte con ellos y
   * comprueba que cada cifra escrita este en los datos. El modelo nunca calcula ni inventa.
   */
  function responderPregunta(texto) {
    return Promise.all([cargarTodasLasTablas(), cargarContexto()]).then(function (cargados) {
      var tablas = cargados[0];
      var ctx = cargados[1];
      if (!tablas.length) return { aviso: 'No se pudieron leer los datos publicados.' };
      var contexto = textoDeContexto(ctx);
      var reciente = conversacionReciente();
      if (reciente) contexto += '\n\n' + reciente;
      var menu = tablas.map(function (x) { return construirMenu(x.p, x.tabla); }).join('\n\n');
      return planificar(texto, contexto, menu).then(function (plan) {
        if (!plan) {
          return { aviso: 'No pude consultar al intérprete en este momento. Vuelve a intentarlo en unos segundos.' };
        }
        if (plan.se_puede === false) {
          return { aviso: plan.motivo || 'Solo respondo con los datos de las encuestas publicadas.' };
        }
        var datos = bloquesDe(plan, tablas);
        if (!datos.texto) {
          return { aviso: 'No encontre esos datos entre los publicados.' };
        }
        return redactar(texto, datos.texto).then(function (escrito) {
          if (!escrito) {
            return { aviso: 'No pude redactar la respuesta en este momento. Vuelve a intentarlo.' };
          }
          if (!respuestaSostenida(escrito, datos.texto)) {
            return {
              aviso: 'Preferí no responder: la respuesta traía cifras que no estan en los datos publicados.',
              datos: datos.texto
            };
          }
          return {
            texto: sinFuente(escrito),
            fuente: 'Fuente: ' + ((fuenteDelTexto(escrito) || datos.fuentes.join(' y '))),
            datos: datos.texto
          };
        });
      });
    });
  }

  // ---------- pantalla del item 1.9 ----------

  function render() {
    return '<div class="preguntas">' +
      '<div class="preguntas-aviso">' +
        '<p class="preguntas-aviso-titulo">Responde solo con los datos de las encuestas</p>' +
        '<p class="preguntas-aviso-texto">Todo lo que sale aquí viene de los JSON publicados de cada período ' +
        '(NPS, satisfacción, carreras, ciclos, dimensiones y comentarios) y cada respuesta dice de qué encuesta ' +
        'salió. Si la pregunta no se puede responder con esos datos —por ejemplo la hora, el clima o cualquier ' +
        'tema ajeno a las encuestas— lo digo, no la invento.</p>' +
      '</div>' +
      '<form class="preguntas-form" id="preguntasForm">' +
        '<label class="preguntas-etiqueta" for="preguntasTexto">Escribe tu pregunta</label>' +
        '<div class="preguntas-fila">' +
          '<input class="preguntas-campo" id="preguntasTexto" type="text" autocomplete="off">' +
          '<button class="preguntas-boton" type="submit">Preguntar</button>' +
        '</div>' +
      '</form>' +
      '<div class="preguntas-respuestas" id="preguntasRespuestas"></div>' +
      '</div>';
  }

  /** Pinta la respuesta: la pregunta en la burbuja de la derecha y el texto a la izquierda. */
  function pintar(contenedor, r, pregunta) {
    var bloque = document.createElement('div');
    bloque.className = 'preguntas-respuesta' + ((r && r.aviso) ? ' fuera-de-alcance' : '');
    var html = '';
    if (pregunta) {
      html += '<p class="preguntas-burbuja-pregunta"><span>' + esc(pregunta) + '</span></p>';
    }
    html += '<div class="preguntas-burbuja-respuesta">';
    html += '<p class="preguntas-resultado">' + esc((r && (r.texto || r.aviso)) || '').replace(/\n/g, '<br>') + '</p>';
    if (r && r.fuente && !r.aviso) {
      html += '<p class="preguntas-fuente">' + esc(r.fuente) + '</p>';
    }
    html += '</div>';
    bloque.innerHTML = html;
    contenedor.insertBefore(bloque, contenedor.firstChild);
  }

  // La respuesta puede tardar (la cadena gratuita de modelos): la pantalla avisa en el acto
  // y el aviso se quita cuando llega la respuesta.
  function avisoDeEspera(caja) {
    var bloque = document.createElement('div');
    bloque.className = 'preguntas-respuesta preguntas-espera';
    bloque.innerHTML = '<p class="preguntas-respuesta-titulo">Consultando…</p>' +
      '<ul class="preguntas-lista"><li>Buscando en los datos publicados. Puede tardar unos minutos.</li></ul>';
    caja.insertBefore(bloque, caja.firstChild);
  }

  function quitarAviso(caja) {
    if (!caja) return;
    var avisos = caja.querySelectorAll('.preguntas-espera');
    for (var i = 0; i < avisos.length; i++) avisos[i].parentNode.removeChild(avisos[i]);
  }

  /** Guarda el turno para que la próxima pregunta pueda referirse a él ("y del 2025?"). */
  function recordar(texto, r) {
    if (!r || (!r.texto && !r.aviso)) return;
    MEMORIA.unshift({
      pregunta: String(texto).trim().slice(0, 160),
      respuesta: String(r.texto || r.aviso).slice(0, 300)
    });
    MEMORIA = MEMORIA.slice(0, 2);
  }

  /** La conversacion reciente, tal como viaja al modelo (vacio si es la primera pregunta). */
  function conversacionReciente() {
    if (!MEMORIA.length) return '';
    return '## Conversación reciente (para entender "y del…", "y en…", "y eso")\n' +
      MEMORIA.map(function (m, i) {
        return '- ' + (i === 0 ? 'Última' : 'Anterior') + ' pregunta: ' + m.pregunta +
          '\n  Respuesta que se dio: ' + m.respuesta;
      }).join('\n');
  }

  /** Las tablas de TODOS los periodos publicados: el menu va con todas, no con una. */
  function cargarTodasLasTablas() {
    return cargar().then(function () {
      return Promise.all((CATALOGO || []).map(function (p) {
        return cargarTabla(p).then(function (tabla) {
          return (tabla && tabla.cabeceras) ? { p: p, tabla: tabla } : null;
        });
      }));
    }).then(function (x) { return x.filter(Boolean); });
  }

  /** Responde una pregunta: busca los datos publicados y pinta lo que el modelo redacte. */
  function preguntar(texto) {
    var caja = document.getElementById('preguntasRespuestas');
    if (!caja || !String(texto || '').trim()) return Promise.resolve(null);
    avisoDeEspera(caja);
    return responderPregunta(String(texto).trim()).then(function (r) {
      // La respuesta se pinta en la caja que está EN PANTALLA: si la persona se movió a otra
      // sección mientras esperaba, la caja vieja ya no existe y la respuesta se perdería.
      var viva = document.getElementById('preguntasRespuestas') || caja;
      quitarAviso(viva);
      pintar(viva, r, texto);
      recordar(texto, r);
      return r;
    }).catch(function () {
      var viva = document.getElementById('preguntasRespuestas') || caja;
      quitarAviso(viva);
      pintar(viva, { aviso: 'No se pudieron leer los datos publicados en este momento.' }, texto);
      return null;
    });
  }

  function enganchar() {
    var form = document.getElementById('preguntasForm');
    if (form) {
      form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        var campo = document.getElementById('preguntasTexto');
        preguntar(campo ? campo.value : '');
        if (campo) campo.value = '';
      });
    }
  }

  function iniciar() {
    return cargar().then(enganchar);
  }

  return {
    cargar: cargar,
    iniciar: iniciar,
    render: render,
    preguntar: preguntar,
    responderPregunta: responderPregunta,
    planificar: planificar,
    redactar: redactar,
    bloquesDe: bloquesDe,
    respuestaSostenida: respuestaSostenida,
    medir: medir,
    construirMenu: construirMenu,
    textoDeContexto: textoDeContexto,
    recordar: recordar,
    conversacionReciente: conversacionReciente,
    cargarTodasLasTablas: cargarTodasLasTablas,
    catalogo: function () { return CATALOGO; }
  };
})();
