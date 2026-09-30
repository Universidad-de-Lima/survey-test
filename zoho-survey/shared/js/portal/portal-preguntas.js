/* ============================================================
   SURVEY PORTAL PREGUNTAS — Asistente del item 1.9.
   Responde SOLO con lo que esta en los JSON publicados de las encuestas.
   Si un dato no esta en esos JSON, lo dice y no improvisa: no hay respuestas
   sobre hora, clima, noticias ni nada que no venga de las encuestas.
   Cada respuesta dice de que archivo salio.
   ============================================================ */
window.SurveyPortalPreguntas = (function () {
  'use strict';

  var FASE_NIVEL = { '1.0': 'students/undergraduate', '1.2': 'students/graduate' };
  var FASE_NOMBRE = { '1.0': 'Estudiantes Pregrado', '1.2': 'Graduados Pregrado' };
  // Los cinco resumenes del periodo llegan juntos en resumenes.json.
  var ARCHIVOS = ['dashboard_data', 'resumenes', 'filtros'];

  // Registro de preguntas y conteo de las mas frecuentes (funcion en Vercel).
  var REGISTRO_URL = 'https://qr-smoky-theta.vercel.app/api/preguntas';
  // Traduce la pregunta a una consulta ordenada cuando las palabras no alcanzan.
  // No responde: solo dice que dato se pide (ver survey-tracker/apps/backend/api/interpretar.js).
  var INTERPRETE_URL = 'https://qr-smoky-theta.vercel.app/api/interpretar';;

  var CATALOGO = null;   // periodos con sus JSON chicos
  var DIMS = null;       // dimensiones.json (grande: se lee solo si hace falta)
  var SENT = null;       // sentimiento.json (grande: se lee solo si hace falta)
  var TABLA = null;      // respuestas.json (grande: se lee solo si hace falta)
  var FRECUENTES = [];   // preguntas mas consultadas (vienen del registro)

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

  function mencionaPeriodo(t) {
    // Se busca el periodo mas largo que aparezca en la pregunta: asi "2026-1" gana a "2026".
    var m = (CATALOGO || []).filter(function (p) { return t.indexOf(sin(p.periodo)) !== -1; })
      .sort(function (a, b) { return sin(b.periodo).length - sin(a.periodo).length; });
    return m.length ? m[0] : null;
  }

  function mencionados(t) {
    return (CATALOGO || []).filter(function (p) { return t.indexOf(sin(p.periodo)) !== -1; });
  }

  // Un periodo escrito completo ("2026-1") manda; si solo dice el anio ("2026"),
  // la respuesta abarca todos los periodos publicados de ese anio.
  function periodoExplicito(t) {
    var largos = (CATALOGO || []).filter(function (p) {
      return sin(p.periodo).indexOf('-') !== -1 && t.indexOf(sin(p.periodo)) !== -1;
    }).sort(function (a, b) { return sin(b.periodo).length - sin(a.periodo).length; });
    return largos.length ? largos[0] : null;
  }

  function anioMencionado(t) {
    var m = String(t).match(/(^|[^0-9])(20[0-9]{2})([^0-9]|$)/);
    return m ? m[2] : null;
  }

  function periodosDelAnio(t) {
    var anio = anioMencionado(t);
    if (!anio) return [];
    return (CATALOGO || []).filter(function (p) { return sin(p.periodo).indexOf(anio) === 0; });
  }

  function faseMencionada(t) {
    if (t.indexOf('graduad') !== -1) return '1.2';
    if (t.indexOf('pregrado') !== -1 || t.indexOf('estudiante') !== -1) return '1.0';
    return null;
  }

  function periodoDeLaPregunta(t, fasePorDefecto) {
    return periodoExplicito(t) || mencionaPeriodo(t) || ultimo(faseMencionada(t) || fasePorDefecto || '1.0');
  }

  function ultimo(fase) {
    var l = deFase(fase);
    return l.length ? l[0] : null;   // periodos.json viene del mas nuevo al mas viejo
  }

  function fuente(p, archivo) {
    return 'Fuente: ' + p.nombre + ' ' + p.periodo + ' — ' + archivo;
  }

  function buscaNombre(t, lista) {
    var mejor = null;
    (lista || []).forEach(function (nombre) {
      var x = sin(nombre);
      if (t.indexOf(x) !== -1 && (!mejor || x.length > sin(mejor).length)) mejor = nombre;
    });
    return mejor;
  }

  // Un cruce se reconoce por su forma: empieza con "de los/de las..." y nombra una pregunta
  // que la gente pide con sus propias palabras (perfil de egreso, satisfaccion con la
  // universidad...). Si no es un cruce, o si la tabla no lo puede resolver, siguen las
  // familias de siempre: esto nunca quita respuestas, solo agrega.
  function esPosibleCruce(t) {
    var marcador = t.indexOf('de los ') !== -1 || t.indexOf('de las ') !== -1 ||
                   t.indexOf('de quienes ') !== -1 || t.indexOf('de los que') !== -1;
    if (!marcador) return false;
    return ALIAS_PREGUNTA.some(function (par) {
      return sinS(t).indexOf(sinS(par[0])) !== -1;
    });
  }

  function respuesta(t) {
    if (esPosibleCruce(t)) {
      return cruceConTabla(t).then(function (r) { return r || respuestaBase(t); });
    }
    return respuestaBase(t);
  }

  // ---------- respuestas ----------
  function respuestaBase(t) {
    var trae = function (l) { return t.indexOf(l) !== -1; };

    // 1) Que hay publicado
    if (trae('qué datos') || trae('qué información') || trae('qué periodos') || trae('qué encuestas hay')) {
      return {
        titulo: 'Datos publicados',
        lineas: (CATALOGO || []).map(function (p) {
          return p.nombre + ' ' + p.periodo + ': ' + n(p.dash.resumen.encuestas) + ' respuestas, ' +
            'NPS ' + n(p.dash.resumen.nps.score) + ', satisfaccion ' + pct(p.dash.resumen.csat.score);
        }),
        fuentes: ['Fuente: dashboard_data.json de cada periodo publicado']
      };
    }

    // 2) Cuantas respuestas / cuantos alumnos o estudiantes se encuestaron
    if (trae('cuantas respuestas') || trae('cuantos respondieron') || trae('cuantas encuestas') ||
        trae('participaron') || trae('se encuest') || trae('fueron encuest') || trae('encuestados') ||
        trae('cuantos alumnos') || trae('cuantas alumnas') || trae('cuantos estudiantes') ||
        trae('cuanta gente') || trae('cuantas personas') || trae('tamano de la muestra') || trae('muestra')) {
      var p = periodoDeLaPregunta(t, '1.0');

      // Si la pregunta nombra una carrera, se responde con el total de esa carrera.
      var car = buscaNombre(t, p.filtros && p.filtros.carreras);
      if (car) {
        var filaI = (p.ids || []).filter(function (x) { return x.carrera === car; });
        var total = filaI.reduce(function (a, x) { return a + (Number(x.total) || 0); }, 0);
        if (total) {
          return {
            titulo: 'Alumnos encuestados de ' + car,
            lineas: [p.nombre + ' ' + p.periodo + ': ' + n(total) + ' respuestas de ' + car + '.'],
            fuentes: [fuente(p, 'resumenes.json (ids)')]
          };
        }
      }

      // Si la pregunta habla de un anio (2026, 2025...), se muestran todos los periodos de ese anio.
      var delAnio = periodosDelAnio(t);
      if (!periodoExplicito(t) && delAnio.length) {
        return {
          titulo: 'Alumnos encuestados en ' + anioMencionado(t),
          lineas: delAnio.map(function (x) {
            return x.nombre + ' ' + x.periodo + ': ' + n(x.dash.resumen.encuestas) + ' respuestas.';
          }),
          fuentes: delAnio.map(function (x) { return fuente(x, 'dashboard_data.json'); })
        };
      }

      if (trae('total') || trae('en general') || trae('todos los periodos') || trae('todas las encuestas')) {
        return {
          titulo: 'Respuestas recibidas (todos los periodos publicados)',
          lineas: (CATALOGO || []).map(function (x) {
            return x.nombre + ' ' + x.periodo + ': ' + n(x.dash.resumen.encuestas) + ' respuestas.';
          }),
          fuentes: (CATALOGO || []).map(function (x) { return fuente(x, 'dashboard_data.json'); })
        };
      }

      return {
        titulo: 'Respuestas recibidas',
        lineas: [p.nombre + ' ' + p.periodo + ': ' + n(p.dash.resumen.encuestas) + ' respuestas.'],
        fuentes: [fuente(p, 'dashboard_data.json')]
      };
    }

    // 3) Fechas del levantamiento
    if (trae('cuando') || trae('fecha') || trae('desde') || trae('dias')) {
      var p2 = periodoDeLaPregunta(t, '1.0');
      var r = p2.dash.resumen;
      return {
        titulo: 'Período de levantamiento',
        lineas: [p2.nombre + ' ' + p2.periodo + ': del ' + r.fecha_inicio + ' al ' + r.fecha_fin +
                 ' (' + n(r.dias) + ' dias, ' + n(r.dias_recoleccion) + ' dias de recoleccion).'],
        fuentes: [fuente(p2, 'dashboard_data.json')]
      };
    }

    // 3) Comparacion entre periodos (va antes que NPS y CSAT: la pregunta puede nombrar los dos)
    // Solo compara si nombra dos periodos, o si usa una palabra de comparacion.
    var dichos = mencionados(t);
    if (dichos.length >= 2 || trae('compar') || trae('diferencia') || trae('evolucion') ||
        trae('cambio') || trae('cambia') || trae('subio') || trae('bajo el nps')) {
      var enPregunta = mencionados(t).sort(function (a, b) { return sin(b.periodo).length - sin(a.periodo).length; });
      var grupo = enPregunta.length >= 2 ? enPregunta.filter(function (p) { return p.fase === enPregunta[0].fase; })
                                         : deFase('1.0');
      if (grupo.length >= 2) {
        var nuevo = grupo[0], viejo = grupo[grupo.length - 1];
        var dNps = Math.round((nuevo.dash.resumen.nps.score - viejo.dash.resumen.nps.score) * 100) / 100;
        var dCsat = Math.round((nuevo.dash.resumen.csat.score - viejo.dash.resumen.csat.score) * 100) / 100;
        return {
          titulo: 'Comparación ' + viejo.periodo + ' → ' + nuevo.periodo + ' (' + nuevo.nombre + ')',
          lineas: ['NPS: ' + n(viejo.dash.resumen.nps.score) + ' → ' + n(nuevo.dash.resumen.nps.score) +
                   ' (' + (dNps >= 0 ? '+' : '') + n(dNps) + ').',
                   'Satisfacción: ' + pct(viejo.dash.resumen.csat.score) + ' → ' + pct(nuevo.dash.resumen.csat.score) +
                   ' (' + (dCsat >= 0 ? '+' : '') + pct(Math.abs(dCsat)).replace(' %', ' puntos') + ').',
                   'Respuestas: ' + n(viejo.dash.resumen.encuestas) + ' → ' + n(nuevo.dash.resumen.encuestas) + '.'],
          fuentes: ['Fuente: dashboard_data.json de ' + viejo.periodo + ' y de ' + nuevo.periodo]
        };
      }
    }

    // 4) NPS: global, por carrera o por ciclo
    if (trae('nps')) {
      var p3 = periodoDeLaPregunta(t, '1.0');
      var carrera = buscaNombre(t, p3.filtros && p3.filtros.carreras);
      var facultad = buscaNombre(t, p3.filtros && p3.filtros.facultades);
      var ciclo = buscaNombre(t, p3.filtros && p3.filtros.ciclos);

      if (carrera) {
        var fila = (p3.npsCarrera || []).filter(function (x) { return x.carrera === carrera; })[0];
        var filaCsat = (p3.csatCarrera || []).filter(function (x) { return x.carrera === carrera; })[0];
        if (!fila) return noSe('No hay NPS publicado para la carrera "' + carrera + '".');
        return {
          titulo: 'NPS de ' + carrera,
          lineas: [p3.nombre + ' ' + p3.periodo + ': NPS ' + n(fila.score) + ' (promotores ' + n(fila.promotores) +
                   ', pasivos ' + n(fila.pasivos) + ', detractores ' + n(fila.detractores) + ').' +
                   (filaCsat ? ' Satisfacción: ' + pct(filaCsat.score) + '.' : '')],
          fuentes: [fuente(p3, 'resumenes.json (NPS y CSAT por carrera)')]
        };
      }

      if (facultad) {
        var suyas = (p3.npsCarrera || []).filter(function (x) { return sin(x.facultad || '') === sin(facultad); });
        if (!suyas.length) {
          var nombres = (p3.filtros && p3.filtros.facultad_carrera && p3.filtros.facultad_carrera[facultad]) || [];
          suyas = (p3.npsCarrera || []).filter(function (x) { return nombres.indexOf(x.carrera) !== -1; });
        }
        return {
          titulo: 'NPS de las carreras de ' + facultad,
          lineas: suyas.map(function (x) { return x.carrera + ': NPS ' + n(x.score); }),
          fuentes: [fuente(p3, 'resumenes.json (NPS por carrera)')]
        };
      }

      if (ciclo) {
        var fc = (p3.npsCiclo || []).filter(function (x) { return x.ciclo === ciclo; })[0];
        if (!fc) return noSe('No hay NPS publicado para el ' + ciclo + '.');
        return {
          titulo: 'NPS del ' + ciclo,
          lineas: [p3.nombre + ' ' + p3.periodo + ': NPS ' + n(fc.score) + ' (promotores ' + n(fc.promotores) +
                   ', pasivos ' + n(fc.pasivos) + ', detractores ' + n(fc.detractores) + ').'],
          fuentes: [fuente(p3, 'resumenes.json (NPS por ciclo y carrera)')]
        };
      }

      if (trae('mejor') || trae('mayor') || trae('mas alto') || trae('peor') || trae('menor') || trae('mas bajo') || trae('ranking')) {
        var esMejor = !(trae('peor') || trae('menor') || trae('mas bajo'));
        var porCiclo = trae('ciclo');
        var lista = porCiclo ? (p3.npsCiclo || []) : (p3.npsCarrera || []);
        var campo = porCiclo ? 'ciclo' : 'carrera';
        var orden = lista.slice().sort(function (a, b) { return b.score - a.score; });
        if (!orden.length) return noSe('No hay NPS publicado por ' + campo + ' en ese periodo.');
        var top = esMejor ? orden.slice(0, 3) : orden.slice(-3).reverse();
        return {
          titulo: 'NPS por ' + campo + ' (' + (esMejor ? 'más alto' : 'más bajo') + ')',
          lineas: top.map(function (x) { return x[campo] + ': ' + n(x.score); }),
          fuentes: [fuente(p3, porCiclo ? 'resumenes.json (NPS por ciclo y carrera)' : 'resumenes.json (NPS por carrera)')]
        };
      }

      var delAnioNps = periodosDelAnio(t);
      if (!periodoExplicito(t) && delAnioNps.length) {
        return {
          titulo: 'NPS de ' + anioMencionado(t),
          lineas: delAnioNps.map(function (x) {
            return x.nombre + ' ' + x.periodo + ': NPS ' + n(x.dash.resumen.nps.score) +
              ' (' + n(x.dash.resumen.encuestas) + ' respuestas).';
          }),
          fuentes: delAnioNps.map(function (x) { return fuente(x, 'dashboard_data.json'); })
        };
      }

      var rr = p3.dash.resumen.nps;
      return {
        titulo: 'NPS ' + p3.nombre + ' ' + p3.periodo,
        lineas: ['NPS ' + n(rr.score) + ' (promotores ' + n(rr.promotores) + ', pasivos ' + n(rr.pasivos) +
                 ', detractores ' + n(rr.detractores) + ', sobre ' + n(rr.total) + ' respuestas).',
                 'Clasificación: ' + p3.dash.hallazgos.nps_tipo + '.'],
        fuentes: [fuente(p3, 'dashboard_data.json')]
      };
    }

    // 5) Satisfaccion (CSAT)
    if (trae('satisfaccion') || trae('csat') || trae('satisfechos') || trae('insatisfechos')) {
      var p4 = periodoDeLaPregunta(t, '1.0');
      var c = p4.dash.resumen.csat;
      var nombreCar = buscaNombre(t, p4.filtros && p4.filtros.carreras);
      if (nombreCar) {
        var f2 = (p4.csatCarrera || []).filter(function (x) { return x.carrera === nombreCar; })[0];
        if (!f2) return noSe('No hay satisfacción publicada para la carrera "' + nombreCar + '".');
        return {
          titulo: 'Satisfacción de ' + nombreCar,
          lineas: [p4.nombre + ' ' + p4.periodo + ': ' + pct(f2.score) + ' (totalmente satisfecho ' +
                   n(f2['Totalmente satisfecho']) + ', muy satisfecho ' + n(f2['Muy satisfecho']) +
                   ', satisfecho ' + n(f2['Satisfecho']) + ', insatisfecho ' + n(f2['Insatisfecho']) +
                   ', totalmente insatisfecho ' + n(f2['Totalmente insatisfecho']) + ').'],
          fuentes: [fuente(p4, 'resumenes.json (CSAT por carrera)')]
        };
      }
      // El detalle por nivel no viene en dashboard_data: se suma de csat_carrera.json,
      // que es la misma fuente que usa el dashboard para su grafico de distribucion.
      var niveles = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho', 'Insatisfecho', 'Totalmente insatisfecho'];
      var suma = {};
      niveles.forEach(function (k) { suma[k] = 0; });
      (p4.csatCarrera || []).forEach(function (x) {
        niveles.forEach(function (k) { suma[k] += Number(x[k]) || 0; });
      });
      var totalSuma = niveles.reduce(function (a, k) { return a + suma[k]; }, 0);
      return {
        titulo: 'Satisfacción ' + p4.nombre + ' ' + p4.periodo,
        lineas: ['Satisfacción: ' + pct(c.score) + ' (sobre ' + n(c.total) + ' respuestas).',
                 'Totalmente satisfecho ' + n(suma[niveles[0]]) + ', muy satisfecho ' + n(suma[niveles[1]]) +
                 ', satisfecho ' + n(suma[niveles[2]]) + ', insatisfecho ' + n(suma[niveles[3]]) +
                 ', totalmente insatisfecho ' + n(suma[niveles[4]]) + ' (suma de las carreras: ' + n(totalSuma) + ').'],
        fuentes: [fuente(p4, 'dashboard_data.json y resumenes.json (CSAT por carrera)')]
      };
    }

    // 7) Cuantas carreras o facultades
    if (trae('cuantas carreras') || trae('cuantas facultades')) {
      var p5 = periodoDeLaPregunta(t, '1.0');
      var f3 = p5.filtros || {};
      return {
        titulo: 'Carreras y facultades',
        lineas: [p5.nombre + ' ' + p5.periodo + ': ' + n((f3.carreras || []).length) + ' carreras y ' +
                 n((f3.facultades || []).length) + ' facultades.'],
        fuentes: [fuente(p5, 'filtros.json')]
      };
    }

    // 8) Dimensiones (Top 3 Box) — se leen solo si la pregunta las pide
    if (trae('dimension') || trae('top 3') || trae('t3b') || trae('aspecto')) {
      return conDimensiones(t);
    }

    // 9) Comentarios y sentimiento
    if (trae('comentario') || trae('sentimiento') || trae('positivo') || trae('negativo') ||
        trae('topico') || trae('tema') || trae('opinion')) {
      return conSentimiento(t);
    }

    // 10) Cruces entre dos preguntas: un filtro (una opcion de la tabla) y una pregunta objetivo.
    //     Lo resuelve la tabla de respuestas; si no es un cruce, el aviso de siempre.
    return cruceConTabla(t).then(function (r) { return r || noSe(null); });
  }

  function noSe(motivo) {
    return {
      alcance: false,
      titulo: 'No puedo responder eso',
      lineas: [motivo || ('Solo respondo con los datos de las encuestas publicadas: NPS, satisfacción, ' +
               'carreras, ciclos, dimensiones, comentarios y períodos.')],
      fuentes: []
    };
  }

  function conDimensiones(t) {
    var p = periodoDeLaPregunta(t, '1.0');
    return cargarDimensiones(p).then(function (filas) {
      if (!filas.length) return noSe('No hay dimensiones publicadas para ese periodo.');
      var porDim = {};
      filas.forEach(function (x) {
        var k = x.dimension;
        if (!k) return;
        if (!porDim[k]) porDim[k] = { dimension: k, t3b: 0, total: 0, categoria: x.categoria };
        porDim[k].t3b += Number(x.t3b) || 0;
        porDim[k].total += Number(x.total) || 0;
      });
      var lista = Object.keys(porDim).map(function (k) {
        var d = porDim[k];
        return { dimension: d.dimension, categoria: d.categoria, pct: d.total ? 100 * d.t3b / d.total : null };
      }).sort(function (a, b) { return b.pct - a.pct; });
      var pedida = buscaNombre(t, lista.map(function (x) { return x.dimension; }));
      if (pedida) {
        var una = lista.filter(function (x) { return x.dimension === pedida; })[0];
        return {
          titulo: 'Dimensión: ' + una.dimension,
          lineas: ['Top 3 Box: ' + pct(una.pct) + ' (categoria ' + una.categoria + ').'],
          fuentes: [fuente(p, 'dimensiones.json')]
        };
      }
      var esMejor = !(t.indexOf('peor') !== -1 || t.indexOf('menor') !== -1 || t.indexOf('más bajo') !== -1);
      var top = esMejor ? lista.slice(0, 5) : lista.slice(-5).reverse();
      return {
        titulo: 'Dimensiones por Top 3 Box (' + (esMejor ? 'mejor evaluadas' : 'peor evaluadas') + ')',
        lineas: top.map(function (x) { return x.dimension + ': ' + pct(x.pct) + ' (' + x.categoria + ')'; }),
        fuentes: [fuente(p, 'dimensiones.json')]
      };
    });
  }

  function conSentimiento(t) {
    var p = periodoDeLaPregunta(t, '1.0');
    return cargarSentimiento(p).then(function (s) {
      if (!s || !s.resumen) return noSe('No hay comentarios publicados para ese periodo.');
      var r = s.resumen;
      var d = r.distribucion_sentimiento || {};
      if (t.indexOf('topico') !== -1 || t.indexOf('tema') !== -1) {
        var tops = (s.topicos || []).slice().sort(function (a, b) { return b.total_comentarios - a.total_comentarios; }).slice(0, 5);
        return {
          titulo: 'Temas más comentados',
          lineas: tops.map(function (x) {
            return x.topico + ': ' + n(x.total_comentarios) + ' comentarios (positivos ' + n(x.positivos) +
              ', negativos ' + n(x.negativos) + ', neutros ' + n(x.neutros) + ').';
          }),
          fuentes: [fuente(p, 'sentimiento.json')]
        };
      }
      return {
        titulo: 'Comentarios de ' + p.nombre + ' ' + p.periodo,
        lineas: ['Respuestas con comentario: ' + n(r.total_con_comentario) + '; analizados: ' + n(r.total_analizados) + '.',
                 'Sentimiento: positivos ' + n(d.positivo) + ', neutros ' + n(d.neutro) + ', negativos ' + n(d.negativo) + '.'],
        fuentes: [fuente(p, 'sentimiento.json')]
      };
    });
  }

  function cargarDimensiones(p) {
    if (DIMS && DIMS[p.nivel + p.periodo]) return Promise.resolve(DIMS[p.nivel + p.periodo]);
    DIMS = DIMS || {};
    return leer(p.base + 'dimensiones.json').catch(function () { return []; }).then(function (f) {
      DIMS[p.nivel + p.periodo] = f || [];
      return DIMS[p.nivel + p.periodo];
    });
  }

  function cargarSentimiento(p) {
    if (SENT && SENT[p.nivel + p.periodo]) return Promise.resolve(SENT[p.nivel + p.periodo]);
    SENT = SENT || {};
    return leer(p.base + 'sentimiento.json').catch(function () { return null; }).then(function (s) {
      SENT[p.nivel + p.periodo] = s;
      return s;
    });
  }

  // ---------- cruces: filtrar con una pregunta y contar otra (tabla de respuestas) ----------
  // La tabla (respuestas.json) es una fila por respuesta con un numero por pregunta; es lo
  // unico que permite contestar cruces, que por definicion no se pueden precalcular.
  var ESCALA_SAT = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho', 'Insatisfecho', 'Totalmente insatisfecho'];

  // Nombres con los que la gente pide una pregunta que el ETL nombra distinto.
  var ALIAS_PREGUNTA = [
    ['perfil de egreso', 'perfil del egreso de la carrera'],
    ['perfil del egreso', 'perfil del egreso de la carrera'],
    ['satisfaccion con la universidad', 'la universidad de lima'],
    ['satisfaccion con ulima', 'la universidad de lima'],
    ['satisfecho con la universidad', 'la universidad de lima'],
    ['recomiendas', 'recomiendas la universidad de lima'],
    ['recomendaria', 'recomiendas la universidad de lima'],
    ['situacion laboral', 'situacion laboral'],
    ['situacion de trabajo', 'situacion laboral'],
    ['tiempo laboral', 'tiempo laboral'],
    ['tiempo dedicado a tu trabajo', 'tiempo laboral']
  ];

  function cargarTabla(p) {
    if (TABLA && TABLA[p.nivel + p.periodo]) return Promise.resolve(TABLA[p.nivel + p.periodo]);
    TABLA = TABLA || {};
    return leer(p.base + 'respuestas.json').catch(function () { return null; }).then(function (x) {
      TABLA[p.nivel + p.periodo] = x;
      return x;
    });
  }

  // Las opciones de la tabla que aparecen en la pregunta (cada una es un filtro).
  function opcionesQueAparecen(tabla, t) {
    var res = [];
    (tabla.cabeceras || []).forEach(function (c) {
      var elegidas = [];
      (tabla.opciones[c] || []).forEach(function (o) {
        var x = sin(o);
        if (!x || x.length < 4 || x === sin('(sin respuesta)')) return;
        // Los niveles de la escala miden el objetivo, no filtran: "satisfechos" en la
        // pregunta no es la opcion "Satisfecho".
        if (ESCALA_SAT.indexOf(o) !== -1) return;
        if (sinS(t).indexOf(sinS(x)) !== -1) elegidas.push(o);
      });
      if (elegidas.length) res.push({ pregunta: c, opciones: elegidas });
    });
    return res;
  }

  // La pregunta que se quiere contar: la nombrada en la pregunta, o la que se pide con un alias.
  function objetivoDelCruce(tabla, t, filtros) {
    var esFiltro = function (c) {
      return filtros.some(function (f) { return f.pregunta === c; });
    };
    var mejor = null;
    (tabla.cabeceras || []).forEach(function (c) {
      if (esFiltro(c)) return;
      var x = sin(c);
      if (x.length >= 5 && sinS(t).indexOf(sinS(x)) !== -1 && !nombreComoCalificador(t, c) &&
          (!mejor || x.length > sin(mejor).length)) mejor = c;
    });
    if (mejor) return mejor;
    for (var k = 0; k < ALIAS_PREGUNTA.length; k++) {
      if (sinS(t).indexOf(sinS(ALIAS_PREGUNTA[k][0])) === -1) continue;
      var buscada = ALIAS_PREGUNTA[k][1];
      var hallada = (tabla.cabeceras || []).filter(function (c) {
        return sin(c) === buscada && !esFiltro(c);
      })[0];
      if (hallada) return hallada;
    }
    return null;
  }

  function contarEnTabla(tabla, sub, pregunta, opciones) {
    var i = tabla.cabeceras.indexOf(pregunta);
    var mapa = {};
    (tabla.opciones[pregunta] || []).forEach(function (o, k) { mapa[o] = k; });
    var ids = opciones.filter(function (o) { return o in mapa; }).map(function (o) { return mapa[o]; });
    return sub.filter(function (f) { return ids.indexOf(f[i]) !== -1; }).length;
  }

  // Devuelve la respuesta del cruce, o null si no es un cruce (siguen las demas familias).
  function cruceConTabla(t) {
    var p = periodoDeLaPregunta(t, '1.0');
    if (!p) return Promise.resolve(null);
    return cargarTabla(p).then(function (tabla) {
      if (!tabla || !tabla.cabeceras || !tabla.filas) return null;
      var filtros = opcionesQueAparecen(tabla, t);
      if (!filtros.length) return null;
      var objetivo = objetivoDelCruce(tabla, t, filtros);
      if (!objetivo) return null;
      var sub = tabla.filas.filter(function (f) {
        return filtros.every(function (fl) {
          var i = tabla.cabeceras.indexOf(fl.pregunta);
          return fl.opciones.some(function (o) {
            return (tabla.opciones[fl.pregunta] || []).indexOf(o) === f[i];
          });
        });
      });
      var filtroTexto = filtros.map(function (fl) {
        return fl.pregunta + ' = ' + fl.opciones.join(' o ');
      }).join('; ');
      if (!sub.length) {
        return noSe('Con ese filtro (' + filtroTexto + ') no hay respuestas en ' + p.nombre + ' ' + p.periodo + '.');
      }
      var lineaFiltro = 'Filtro: ' + filtroTexto + ' -> ' + n(sub.length) + ' respuestas de ' + n(tabla.respuestas) + '.';
      var escala = ESCALA_SAT.filter(function (x) {
        return (tabla.opciones[objetivo] || []).indexOf(x) !== -1;
      });
      // Basta con tres niveles para tratarla como escala de satisfaccion (la pregunta de la
      // Universidad de Lima tiene cuatro: no incluye "totalmente insatisfecho").
      if (escala.length >= 3) {
        var c3 = contarEnTabla(tabla, sub, objetivo, escala.slice(0, 3));
        var c2 = contarEnTabla(tabla, sub, objetivo, escala.slice(0, 2));
        var cSat = contarEnTabla(tabla, sub, objetivo, ['Satisfecho']);
        return {
          titulo: 'Cruce: ' + objetivo + ' — ' + filtroTexto,
          lineas: [lineaFiltro,
                   'Tres mejores (totalmente satisfecho, muy satisfecho, satisfecho): ' + n(c3) +
                     ' de ' + n(sub.length) + ' (' + pct(100 * c3 / sub.length) + ').',
                   'Dos mejores (totalmente satisfecho, muy satisfecho): ' + n(c2) +
                     ' (' + pct(100 * c2 / sub.length) + '). "Satisfecho" exacto: ' + n(cSat) + '.'],
          fuentes: [fuente(p, 'respuestas.json')]
        };
      }
      var conteo = (tabla.opciones[objetivo] || []).map(function (o) {
        return { o: o, c: contarEnTabla(tabla, sub, objetivo, [o]) };
      }).filter(function (x) { return x.c > 0; }).sort(function (a, b) { return b.c - a.c; });
      return {
        titulo: 'Cruce: ' + objetivo + ' — ' + filtroTexto,
        lineas: [lineaFiltro].concat(conteo.slice(0, 6).map(function (x) {
          return x.o + ': ' + n(x.c) + ' (' + pct(100 * x.c / sub.length) + ')';
        })),
        fuentes: [fuente(p, 'respuestas.json')]
      };
    });
  }

  // ---------- contexto del asistente (documento base) y menu del periodo ----------
  var CONTEXTO = null;   // asistente_contexto.json (chico: se lee una vez por carga)

  function cargarContexto() {
    if (CONTEXTO) return Promise.resolve(CONTEXTO);
    return leer('shared/config/asistente_contexto.json').catch(function () { return null; }).then(function (x) {
      CONTEXTO = x || {};
      return CONTEXTO;
    });
  }

  // El texto que viaja como contexto: solo las secciones de prosa (las palabras
  // coloquiales ya van dentro del menu).
  function textoDeContexto(ctx) {
    if (!ctx) return '';
    var partes = [];
    [['que_es', 'Qué es'], ['como_estan_los_datos', 'Cómo están los datos'],
     ['como_esta_organizado', 'Cómo está organizado el cuestionario'],
     ['reglas', 'Reglas'], ['equivalencias', 'Equivalencias']].forEach(function (par) {
      var lista = ctx[par[0]];
      if (lista && lista.length) {
        partes.push('## ' + par[1] + '\n' + lista.map(function (x) { return '- ' + x; }).join('\n'));
      }
    });
    return partes.join('\n\n');
  }

  function etiquetaDe(p) { return p.nombre + ' ' + p.periodo; }

  // El menu del periodo: que preguntas hay, con que palabras se piden y que opciones
  // tienen. Es lo unico que el modelo puede elegir.
  function construirMenu(p, tabla, ctx) {
    var palabras = (ctx && ctx.palabras_coloquiales) || {};
    var lineas = ['## Menú — ' + etiquetaDe(p) + ' (' + n(tabla.respuestas) + ' respuestas, ' +
                  tabla.cabeceras.length + ' preguntas)'];
    tabla.cabeceras.forEach(function (c) {
      var ops = (tabla.opciones[c] || []).filter(function (o) { return sin(o) !== sin('(sin respuesta)'); });
      var coloq = palabras[c] || [];
      lineas.push('- ' + c + (coloq.length ? ' (se pide como: ' + coloq.join(', ') + ')' : '') +
                  ' -> ' + ops.join(' · '));
    });
    return lineas.join('\n');
  }

  // Ejecuta el formulario sobre la tabla: valida cada nombre contra lo publicado y
  // cuenta. Devuelve la respuesta, o {problema: motivo} si algun nombre no existe.
  function ejecutarFormulario(p, tabla, f) {
    var cab = tabla.cabeceras || [];
    function exacto(nombre) {
      var x = sin(nombre);
      var halladas = cab.filter(function (c) { return sin(c) === x; });
      return halladas.length ? halladas[0] : null;
    }
    function valoresDe(pregunta, lista) {
      var ops = tabla.opciones[pregunta] || [];
      var malos = (lista || []).filter(function (v) {
        return !ops.some(function (o) { return sin(o) === sin(v); });
      });
      if (malos.length) return { problema: 'No encontré estas opciones en "' + pregunta + '": ' + malos.join(', ') + '.' };
      return { valores: (lista || []).map(function (v) {
        return ops.filter(function (o) { return sin(o) === sin(v); })[0];
      }) };
    }
    var filtros = [];
    var listaFiltros = f.filtros || [];
    for (var i = 0; i < listaFiltros.length; i++) {
      var pregunta = exacto(listaFiltros[i].pregunta);
      if (!pregunta) return { problema: 'No encontré la pregunta "' + listaFiltros[i].pregunta + '" en las encuestas publicadas.' };
      var v = valoresDe(pregunta, listaFiltros[i].valores);
      if (v.problema) return v;
      filtros.push({ pregunta: pregunta, opciones: v.valores });
    }
    var sub = tabla.filas.filter(function (fila) {
      return filtros.every(function (cada) {
        var idx = cab.indexOf(cada.pregunta);
        return cada.opciones.some(function (o) {
          return (tabla.opciones[cada.pregunta] || []).indexOf(o) === fila[idx];
        });
      });
    });
    var filtroTexto = filtros.map(function (cada) {
      return cada.pregunta + ' = ' + cada.opciones.join(' o ');
    }).join('; ');
    var denom = sub.length;
    var cabecera = (filtroTexto ? 'Filtro: ' + filtroTexto + ' -> ' : 'Total: ') +
                   n(denom) + ' respuestas de ' + n(tabla.respuestas) + '.';

    if (f.pregunta_objetivo) {
      var objetivo = exacto(f.pregunta_objetivo);
      if (!objetivo) return { problema: 'No encontré la pregunta "' + f.pregunta_objetivo + '" en las encuestas publicadas.' };
      var vo = valoresDe(objetivo, f.valores_objetivo);
      if (vo.problema) return vo;
      if (!vo.valores.length) return { problema: 'No se indicó qué valores contar de "' + objetivo + '".' };
      var cuenta = contarEnTabla(tabla, sub, objetivo, vo.valores);
      return {
        titulo: 'Cruce: ' + objetivo + ' — ' + (filtroTexto || 'todas las respuestas'),
        lineas: [cabecera,
                 vo.valores.join(' / ') + ': ' + n(cuenta) + ' de ' + n(denom) +
                   ' (' + pct(denom ? 100 * cuenta / denom : 0) + ').'],
        fuentes: [fuente(p, 'respuestas.json')]
      };
    }
    if (!filtros.length) return null;   // no hay nada que contar
    // El modelo a veces expresa la cuenta como un filtro mas ("y que su situacion laboral
    // sea trabajador o practicas"): se informa el grupo sin ese ultimo filtro y el
    // porcentaje que lo cumple, para no perder la lectura "de los N, cuantos".
    var ultimo = filtros[filtros.length - 1];
    var grupo = filtros.slice(0, -1);
    var subGrupo = tabla.filas.filter(function (fila) {
      return grupo.every(function (cada) {
        var idx = cab.indexOf(cada.pregunta);
        return cada.opciones.some(function (o) {
          return (tabla.opciones[cada.pregunta] || []).indexOf(o) === fila[idx];
        });
      });
    });
    var lineaGrupo = grupo.length
      ? 'De los ' + n(subGrupo.length) + ' con ' + grupo.map(function (cada) {
          return cada.pregunta + ' = ' + cada.opciones.join(' o ');
        }).join('; ') + ', cumplen ' + ultimo.pregunta + ' = ' + ultimo.opciones.join(' o ') +
        ': ' + n(denom) + ' (' + pct(subGrupo.length ? 100 * denom / subGrupo.length : 0) + ').'
      : 'Cumplen ' + ultimo.pregunta + ' = ' + ultimo.opciones.join(' o ') + ': ' + n(denom) +
        ' de ' + n(tabla.respuestas) + ' (' + pct(tabla.respuestas ? 100 * denom / tabla.respuestas : 0) + ').';
    return {
      titulo: 'Cruce: ' + filtroTexto,
      lineas: [cabecera, lineaGrupo],
      fuentes: [fuente(p, 'respuestas.json')]
    };
  }

  // ---------- registro de preguntas y mas frecuentes ----------
  // Se manda la pregunta tal cual (el servidor le quita correos, telefonos y
  // numeros largos antes de guardarla). Si el registro falla, la respuesta al
  // usuario no se ve afectada: se ignora en silencio.
  function registrar(texto, intencion) {
    if (!texto || !String(texto).trim()) return Promise.resolve(null);
    return fetch(REGISTRO_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: String(texto).slice(0, 160), intencion: intencion || '' })
    }).catch(function () { return null; });
  }

  function cargarFrecuentes() {
    return fetch(REGISTRO_URL, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { FRECUENTES = (d && d.frecuentes) || []; return FRECUENTES; })
      .catch(function () { FRECUENTES = []; return FRECUENTES; });
  }

  // ---------- IA que entiende la pregunta (solo traduce) ----------
  // Cada dato que devuelve el traductor se convierte en una frase que el motor de datos
  // ya sabe leer: asi los numeros siguen saliendo de los JSON y no del modelo.
  var FRASE_DEL_DATO = {
    nps: 'nps',
    satisfaccion: 'satisfaccion',
    respuestas: 'cuantos alumnos se encuestaron',
    carreras: 'cuantas carreras',
    facultades: 'cuantas facultades',
    ciclos: 'nps por ciclo',
    dimensiones: 'dimensiones',
    comentarios: 'comentarios',
    temas: 'temas mas comentados',
    comparacion: 'comparar periodos',
    fechas: 'cuando fue el levantamiento',
    periodos: 'que datos hay'
  };

  // Manda la pregunta con el contexto y el menu; el modelo devuelve el formulario
  // (nunca cifras: los numeros los saca la pagina de los JSON publicados).
  function interpretarConIA(texto, contexto, menu) {
    return fetch(INTERPRETE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pregunta: String(texto).slice(0, 300),
        contexto: String(contexto || '').slice(0, 6000),
        menu: String(menu || '').slice(0, 16000)
      })
    }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { return (d && d.consulta) ? d.consulta : null; })
      .catch(function () { return null; });
  }

  function fraseDeConsulta(c) {
    var base = FRASE_DEL_DATO[c.dato];
    if (!base) return null;
    var partes = [base];
    if (c.periodo) partes.push(c.periodo);
    if (c.entidad) partes.push(c.entidad);
    if (c.orden) partes.push(c.orden);
    return partes.join(' ');
  }

  // El nombre que devolvio el traductor tiene que existir en los datos publicados:
  // si no existe, se dice; no se responde de mas.
  function entidadConocida(nombre) {
    if (!nombre) return true;
    var p = periodoDeLaPregunta('', '1.0');
    var listas = [].concat(
      (p.filtros && p.filtros.carreras) || [],
      (p.filtros && p.filtros.facultades) || [],
      (p.filtros && p.filtros.ciclos) || [],
      Object.keys((p.filtros && p.filtros.facultad_carrera) || {})
    );
    return !!buscaNombre(sin(nombre), listas);
  }

  // Responde: primero con las palabras conocidas; si no alcanzan, con la IA; y si tampoco,
  // el aviso de siempre. En ningun caso el numero sale del modelo.
  // Responde: primero las palabras conocidas; si no alcanzan, el contexto + el menu
  // del periodo + la IA; y lo que devuelve se valida contra los datos publicados
  // antes de responder. En ningun caso el numero sale del modelo.
  function responderConIA(texto) {
    return cargar().then(function () {
      return Promise.resolve(respuesta(sin(texto)));
    }).then(function (r) {
      if (r && r.alcance !== false) return r;

      var p = periodoDeLaPregunta(sin(texto), '1.0');
      if (!p || !p.base) return noSe(null);
      return Promise.all([cargarTabla(p), cargarContexto()]).then(function (cargados) {
        var tabla = cargados[0];
        var ctx = cargados[1];
        if (!tabla || !tabla.cabeceras) return null;
        var contexto = textoDeContexto(ctx);
        var menu = construirMenu(p, tabla, ctx);
        // Si el interprete no responde (los modelos gratuitos tienen momentos malos), se
        // intenta una vez mas; si tampoco, se avisa que fue el servicio, no los datos.
        return interpretarConIA(texto, contexto, menu)
          .then(function (f) { return f || interpretarConIA(texto, contexto, menu); })
          .then(function (f) { return { p: p, tabla: tabla, f: f }; });
      }).then(function (x) {
        if (!x || !x.f) {
          return noSe('No pude consultar al intérprete en este momento. Vuelve a intentarlo en unos segundos.');
        }
        var f = x.f;
        if (f.se_puede === false || f.operacion === 'ninguna') {
          return noSe(f.motivo ? String(f.motivo) : null);
        }
        if (f.pregunta_objetivo || (f.filtros || []).length) {
          var r2 = ejecutarFormulario(x.p, x.tabla, f);
          if (r2 && r2.problema) return noSe(r2.problema);
          if (r2) return r2;
        }
        if (f.entidad && !entidadConocida(f.entidad)) {
          return noSe('No encontre "' + f.entidad + '" entre las carreras, facultades o ciclos publicados.');
        }
        var frase = fraseDeConsulta({ dato: f.operacion, entidad: f.entidad || '', orden: f.orden || '' });
        if (!frase) return noSe(null);
        return Promise.resolve(respuesta(sin(frase))).then(function (r3) {
          return (r3 && r3.alcance !== false) ? r3 : noSe(null);
        });
      });
    });
  }

  // ---------- pantalla del item 1.9 ----------

  function render() {
    return '<div class="preguntas">' +
      '<div class="preguntas-aviso">' +
        '<p class="preguntas-aviso-titulo">Responde solo con los datos de las encuestas</p>' +
        '<p class="preguntas-aviso-texto">Todo lo que sale aquí viene de los JSON publicados de cada periodo ' +
        '(NPS, satisfacción, carreras, ciclos, dimensiones y comentarios), y cada respuesta dice de qué archivo ' +
        'salió. Si la pregunta no se puede responder con esos datos —por ejemplo la hora, el clima o cualquier ' +
        'tema ajeno a las encuestas— lo digo, no la invento. Las preguntas se guardan de forma anónima, sin correos ' +
        'ni números, para saber cuáles se consultan más.</p>' +
      '</div>' +
      '<form class="preguntas-form" id="preguntasForm">' +
        '<label class="preguntas-etiqueta" for="preguntasTexto">Escribe tu pregunta</label>' +
        '<div class="preguntas-fila">' +
          '<input class="preguntas-campo" id="preguntasTexto" type="text" autocomplete="off">' +
          '<button class="preguntas-boton" type="submit">Preguntar</button>' +
        '</div>' +
      '</form>' +
      '<div class="preguntas-frecuentes" id="preguntasFrecuentes" hidden>' +
        '<p class="preguntas-etiqueta">Las más preguntadas</p>' +
        '<div class="preguntas-sugerencias" id="preguntasMasUsadas"></div>' +
      '</div>' +
      '<div class="preguntas-respuestas" id="preguntasRespuestas"></div>' +
      '</div>';
  }

  /**
   * Pinta una respuesta. Arriba va la pregunta (asi cada bloque se explica solo), luego la
   * etiqueta "Respuesta:" y el dato. Cuando la respuesta es un cruce o tiene una sola linea,
   * esa linea se muestra como resultado (separada); si son varias de una lista, queda la lista.
   */
  function pintar(contenedor, r, pregunta) {
    var bloque = document.createElement('div');
    bloque.className = 'preguntas-respuesta' + (r.alcance === false ? ' fuera-de-alcance' : '');
    var html = '';
    if (pregunta) {
      html += '<p class="preguntas-pregunta">Pregunta: ' + esc(pregunta) + '</p>';
    }
    html += '<p class="preguntas-rotulo preguntas-rotulo-respuesta">Respuesta:</p>' +
      '<p class="preguntas-respuesta-titulo">' + esc(r.titulo) + '</p>';
    var lineas = (r.lineas || []).slice();
    var esCruce = /^Cruce:/.test(r.titulo || '');
    if (r.alcance !== false && lineas.length && (esCruce || lineas.length === 1)) {
      if (lineas.length > 1) {
        html += '<p class="preguntas-contexto">' + esc(lineas.shift()) + '</p>';
      }
      lineas.forEach(function (l) { html += '<p class="preguntas-resultado">' + esc(l) + '</p>'; });
    } else {
      html += '<ul class="preguntas-lista">';
      lineas.forEach(function (l) { html += '<li>' + esc(l) + '</li>'; });
      html += '</ul>';
    }
    (r.fuentes || []).forEach(function (f) { html += '<p class="preguntas-fuente">' + esc(f) + '</p>'; });
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

  function preguntar(texto) {
    var caja = document.getElementById('preguntasRespuestas');
    if (!caja || !String(texto || '').trim()) return Promise.resolve(null);
    var t = sin(texto);
    avisoDeEspera(caja);
    return cargar().then(function () {
      return respuesta(t);
    }).then(function (r0) {
      return (r0 && r0.alcance !== false) ? r0 : responderConIA(texto);
    }).then(function (r) {
      // La respuesta se pinta en la caja que esta EN PANTALLA: si la persona se movio a
      // otra seccion mientras esperaba, la caja vieja ya no existe y la respuesta se
      // perderia (por eso se busca de nuevo aqui).
      var viva = document.getElementById('preguntasRespuestas') || caja;
      quitarAviso(viva);
      pintar(viva, r, texto);
      registrar(texto, (r && r.titulo) || '');
      actualizarContadorDeUso((r && r.titulo) || '');
      return r;
    }).catch(function () {
      var viva = document.getElementById('preguntasRespuestas') || caja;
      quitarAviso(viva);
      pintar(viva, noSe('No se pudieron leer los datos publicados en este momento.'), texto);
      return null;
    });
  }

  // Deja a la vista las preguntas mas consultadas por todos.
  function pintarFrecuentes() {
    var caja = document.getElementById('preguntasMasUsadas');
    var bloque = document.getElementById('preguntasFrecuentes');
    if (!caja || !bloque) return;
    if (!FRECUENTES.length) { bloque.hidden = true; return; }
    caja.innerHTML = FRECUENTES.slice(0, 6).map(function (f) {
      return '<button type="button" class="preguntas-sugerencia" data-pregunta="' + esc(f.texto) + '">' +
        esc(f.texto) + ' <span class="preguntas-veces">' + esc(String(f.veces)) + '</span></button>';
    }).join('');
    bloque.hidden = false;
    caja.querySelectorAll('.preguntas-sugerencia').forEach(function (b) {
      b.addEventListener('click', function () { preguntar(b.getAttribute('data-pregunta')); });
    });
  }

  function actualizarContadorDeUso(titulo) {
    if (!titulo) return;
    setTimeout(function () { cargarFrecuentes().then(pintarFrecuentes); }, 1500);
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
    return cargar().then(function () {
      enganchar();
      return cargarFrecuentes().then(pintarFrecuentes);
    });
  }

  return {
    cargar: cargar,
    preguntar: preguntar,
    responder: function (texto) { return cargar().then(function () { return respuesta(sin(texto)); }); },
    iniciar: iniciar,
    responderConIA: responderConIA,
    interpretarConIA: interpretarConIA,
    registrar: registrar,
    cargarFrecuentes: cargarFrecuentes,
    frecuentes: function () { return FRECUENTES; },
    render: render,
    catalogo: function () { return CATALOGO; }
  };
})();
