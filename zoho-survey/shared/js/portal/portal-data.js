/* ============================================================
   SURVEY PORTAL DATA — Carga y normalización de datos de encuesta
   para la vista 1.0 (Estudiantes Pregrado) del portal v5.0.
   Expone helpers base (SurveyPortalCore) y acceso a datos (SurveyPortalData).
   Debe cargarse ANTES de los demás módulos portal-*.
   ============================================================ */
(function () {
  'use strict';

  // ── Helpers base compartidos (requeridos por los demás módulos portal) ──
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function fmtNum(n, dec) {
    // Enteros SIN separador de miles (1000, no 1,000);
    // decimales con COMA decimal garantizada (97,85), sin depender del ICU.
    const num = Number(n);
    const d = dec || 0;
    if (d > 0) {
      return num.toFixed(d).replace('.', ',');
    }
    return String(Math.round(num));
  }
  function formatCicloText(ciclo) {
    const m = ciclo.match(/^(\d+)/);
    if (!m) return ciclo;
    const n = m[1];
    return (n === '1' || n === '3') ? n + '.ᵉʳ ciclo' : n + '.º ciclo';
  }

  // ── Constantes de filtros (desde constants.js, fuente canónica) ──
  const PROGRAMA_ESTUDIOS_GENERALES = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.PROGRAMA_ESTUDIOS_GENERALES) ?? 'Programa de Estudios Generales';
  const CICLOS_ESTUDIOS_GENERALES = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.CICLOS_ESTUDIOS_GENERALES) ?? ['1° Ciclo', '2° Ciclo'];
  const CARRERAS_12_CICLOS = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.CARRERAS_12_CICLOS) ?? ['Derecho', 'Psicología'];
  const FACULTADES_12_CICLOS = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.FACULTADES_12_CICLOS) ?? ['Facultad de Derecho', 'Facultad de Psicología'];
  const MAX_CICLOS_DEFAULT = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.MAX_CICLOS_DEFAULT) ?? 10;
  const MAX_CICLOS_ESPECIALES = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.MAX_CICLOS_ESPECIALES) ?? 12;

  function satColorPortal(val) {
    const metaCsat = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_CSAT) ?? 93;
    const metaPond = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_PONDERADO) ?? 80;
    return val >= metaCsat ? 'var(--emerald)' : val >= metaPond ? 'var(--amber)' : 'var(--rose)';
  }
  function esEstudiosGen(facultad) {
    return facultad === PROGRAMA_ESTUDIOS_GENERALES;
  }

  let SURVEY_DATA = null;
  const SURVEY_DATA_CACHE = {};
  let GRADUATE_DATA = null;

  // Entrada marcadora de "todavía no hay nada publicado" en periodos.json.
  const URL_PLACEHOLDER = 'underconstruction.html';

  // ── Helper puro: solo periodos reales (el marcador no es un periodo) ──
  function periodosReales(entradas) {
    return (Array.isArray(entradas) ? entradas : [])
      .filter(p => p && typeof p.id === 'string' && p.id.trim() !== '' && p.url !== URL_PLACEHOLDER)
      .map(p => p.id);
  }

  // ── Qué carpeta de datos corresponde a cada ítem del portal ──
  // (misma lista de niveles que usa health.html; el ítem 1.9 es el asistente
  // de preguntas y no tiene carpeta de datos propia)
  const NIVELES_FASE = {
    '1.0': 'students/undergraduate',
    '1.1': 'students/postgraduate',
    '1.2': 'students/graduate',
    '1.3': 'alumni/undergraduate',
    '1.4': 'alumni/postgraduate',
    '1.5': 'facultystaff/undergraduate',
    '1.6': 'facultystaff/postgraduate',
    '1.7': 'nonfacultystaff',
    '1.8': 'employers'
  };

  function nivelDeFase(phaseId) {
    return NIVELES_FASE[phaseId] || null;
  }

  // Periodos publicados por ítem: { '1.0': ['2026-1', '2025-2'], ... }
  let PERIODOS_POR_FASE = {};
  // Periodo marcado como nuevo (isNew) por ítem, o el primero disponible
  let PERIODO_NUEVO_POR_FASE = {};

  // ── Helpers puros (reciben el mapa, así se prueban sin red) ──
  function periodosDeFase(phaseId, mapa) {
    const m = mapa || PERIODOS_POR_FASE;
    return m[phaseId] || [];
  }

  function faseConDatos(phaseId, mapa) {
    return periodosDeFase(phaseId, mapa).length > 0;
  }

  // ── Con el estado real ya cargado ──
  function tieneDatosDeFase(phaseId) {
    return faseConDatos(phaseId);
  }

  function getPeriodoDeFase(phaseId) {
    return PERIODO_NUEVO_POR_FASE[phaseId] || null;
  }

  // ── Carga del periodos.json de TODOS los niveles, de una vez ──
  async function loadPeriodosDeNiveles() {
    PERIODOS_POR_FASE = {};
    PERIODO_NUEVO_POR_FASE = {};
    for (const phaseId of Object.keys(NIVELES_FASE)) {
      const nivel = NIVELES_FASE[phaseId];
      try {
        const res = await fetch('./' + nivel + '/periodos.json', { cache: 'no-store' });
        const periodos = await res.json();
        const reales = periodosReales(periodos);
        PERIODOS_POR_FASE[phaseId] = reales;
        const nuevo = (Array.isArray(periodos) ? periodos : [])
          .find(p => p && p.isNew === true && reales.indexOf(p.id) !== -1);
        PERIODO_NUEVO_POR_FASE[phaseId] = nuevo ? nuevo.id : (reales[0] || null);
      } catch (e) {
        PERIODOS_POR_FASE[phaseId] = [];
        PERIODO_NUEVO_POR_FASE[phaseId] = null;
        console.warn('[portal] No se pudo cargar periodos.json de ' + nivel + ':', e);
      }
    }
  }

  // ── Carga de datos de encuesta (críticos + opcionales) ──
  async function loadSurveyData(nivel, periodo) {
    const cacheKey = nivel + '/' + periodo;
    if (SURVEY_DATA_CACHE[cacheKey]) {
      return SURVEY_DATA_CACHE[cacheKey];
    }

    try {
      const basePath = `./${nivel}/${periodo}/json/`;

      const [dashboard, filtros, dimensiones, sentimiento] = await Promise.all([
        fetch(basePath + 'dashboard_data.json', { cache: 'no-store' }).then(r => r.json()),
        fetch(basePath + 'filtros.json', { cache: 'no-store' }).then(r => r.json()),
        fetch(basePath + 'dimensiones.json', { cache: 'no-store' }).then(r => r.json()),
        fetch(basePath + 'sentimiento.json', { cache: 'no-store' }).then(r => r.json()).catch(() => null)
      ]);

      const [npsCarreraRes, csatCarreraRes, npsCicloCarreraRes, csatCicloCarreraRes] = await Promise.allSettled([
        fetch(basePath + 'nps_carrera.json').then(r => r.json()),
        fetch(basePath + 'csat_carrera.json').then(r => r.json()),
        fetch(basePath + 'nps_ciclo_carrera.json').then(r => r.json()),
        fetch(basePath + 'csat_ciclo_carrera.json').then(r => r.json())
      ]);

      const npsCarrera = npsCarreraRes.status === 'fulfilled' ? npsCarreraRes.value : [];
      const csatCarrera = csatCarreraRes.status === 'fulfilled' ? csatCarreraRes.value : [];
      const npsCicloCarrera = npsCicloCarreraRes.status === 'fulfilled' ? npsCicloCarreraRes.value : [];
      const csatCicloCarrera = csatCicloCarreraRes.status === 'fulfilled' ? csatCicloCarreraRes.value : [];

      if (npsCarreraRes.status === 'rejected') {
        console.warn('[portal] nps_carrera.json no disponible (' + cacheKey + '):', npsCarreraRes.reason);
      }
      if (csatCarreraRes.status === 'rejected') {
        console.warn('[portal] csat_carrera.json no disponible (' + cacheKey + '):', csatCarreraRes.reason);
      }
      if (npsCicloCarreraRes.status === 'rejected') {
        console.warn('[portal] nps_ciclo_carrera.json no disponible (' + cacheKey + '):', npsCicloCarreraRes.reason);
      }
      if (csatCicloCarreraRes.status === 'rejected') {
        console.warn('[portal] csat_ciclo_carrera.json no disponible (' + cacheKey + '):', csatCicloCarreraRes.reason);
      }

      const surveyData = normalizeData({ dashboard, filtros, dimensiones, sentimiento, npsCarrera, csatCarrera, npsCicloCarrera, csatCicloCarrera });

      SURVEY_DATA_CACHE[cacheKey] = surveyData;
      return surveyData;
    } catch (e) {
      console.error('[portal] Error cargando datos de encuestas para ' + cacheKey + ':', e);
      return null;
    }
  }

  // ── Datos de graduados (fase 1.2) ──
  async function loadGraduateData() {
    const periodo = getPeriodoDeFase('1.2');
    if (!periodo) {
      GRADUATE_DATA = null;
      return;
    }
    try {
      const res = await fetch('./students/graduate/' + periodo + '/json/dashboard_data.json', { cache: 'no-store' });
      if (!res.ok) {
        GRADUATE_DATA = null;
        console.warn('[portal] dashboard_data.json de graduados no disponible (' + res.status + ')');
        return;
      }
      const dashboard = await res.json();
      GRADUATE_DATA = { resumen: (dashboard.resumen || {}) };
    } catch (e) {
      GRADUATE_DATA = null;
      console.warn('[portal] Error cargando datos de graduados:', e);
    }
  }

  // ── Normaliza los JSONs crudos del ETL a la forma interna de SURVEY_DATA ──
  function normalizeData(raw) {
    const dashboard = raw.dashboard || {};
    const filtros = raw.filtros || {};
    const dimensiones = Array.isArray(raw.dimensiones) ? raw.dimensiones : [];
    const sentimiento = raw.sentimiento || null;
    const csatCarrera = Array.isArray(raw.csatCarrera) ? raw.csatCarrera : [];
    const npsCarrera = Array.isArray(raw.npsCarrera) ? raw.npsCarrera : [];
    const csatCicloCarrera = Array.isArray(raw.csatCicloCarrera) ? raw.csatCicloCarrera : [];
    const npsCicloCarrera = Array.isArray(raw.npsCicloCarrera) ? raw.npsCicloCarrera : [];

    const weight = (sum, total) => total ? sum / total : 0;

    function aggCats(rows) {
      const m = new Map();
      rows.forEach(row => {
        const acc = m.get(row.categoria) || { categoria: row.categoria, t3b_pct: 0, total: 0 };
        acc.total += row.total;
        acc.t3b_pct += (row.t3b_pct || 0) * row.total;
        m.set(row.categoria, acc);
      });
      return [...m.values()]
        .map(c => ({ categoria: c.categoria, total: c.total, t3b_pct: weight(c.t3b_pct, c.total) }))
        .sort((a, b) => b.t3b_pct - a.t3b_pct);
    }

    function groupDims(rows) {
      const m = new Map();
      rows.forEach(row => {
        const key = row.dimension + '\u0000' + row.categoria;
        const acc = m.get(key) || { dimension: row.dimension, categoria: row.categoria, t3b_pct: 0, total: 0 };
        acc.total += row.total;
        acc.t3b_pct += (row.t3b_pct || 0) * row.total;
        m.set(key, acc);
      });
      return [...m.values()]
        .map(d => ({ dimension: d.dimension, categoria: d.categoria, total: d.total, t3b_pct: weight(d.t3b_pct, d.total) }))
        .sort((a, b) => b.t3b_pct - a.t3b_pct);
    }

    function buildUnidades(campo) {
      const byKey = {};
      dimensiones.forEach(row => {
        (byKey[row[campo]] = byKey[row[campo]] || []).push(row);
      });
      return Object.keys(byKey)
        .map(nombre => {
          const rows = byKey[nombre];
          const total = rows.reduce((s, r) => s + r.total, 0);
          if (!total) return null;
          const sumPct = rows.reduce((s, r) => s + (r.t3b_pct || 0) * r.total, 0);
          return { nombre, total, t3b_pct: weight(sumPct, total), cats: aggCats(rows) };
        })
        .filter(Boolean)
        .sort((a, b) => b.t3b_pct - a.t3b_pct);
    }

    function groupByCampo(campo, rowsByCampo) {
      const out = {};
      Object.keys(rowsByCampo).forEach(nombre => {
        if (rowsByCampo[nombre].some(r => r.total > 0)) out[nombre] = groupDims(rowsByCampo[nombre]);
      });
      return out;
    }

    const byFac = {};
    const byCar = {};
    dimensiones.forEach(row => {
      (byFac[row.facultad] = byFac[row.facultad] || []).push(row);
      (byCar[row.carrera] = byCar[row.carrera] || []).push(row);
    });

    const surveyData = {
      resumen: dashboard.resumen,
      _export: dashboard._export || null,
      csat_dist: dashboard.csat,
      nps_dist: {
        promotores: (dashboard.nps || {}).promotores,
        pasivos: (dashboard.nps || {}).pasivos,
        detractores: (dashboard.nps || {}).detractores,
        score: (dashboard.nps || {}).score
      },
      hallazgos: dashboard.hallazgos,
      filtros: filtros,
      csat_carrera: csatCarrera,
      nps_carrera: npsCarrera,
      csat_ciclo_carrera: csatCicloCarrera,
      nps_ciclo_carrera: npsCicloCarrera,
      dimensiones_raw: dimensiones,
      dims: groupDims(dimensiones),
      cats: aggCats(dimensiones),
      facultades_data: buildUnidades('facultad'),
      carreras_data: buildUnidades('carrera'),
      dims_by_fac: groupByCampo('facultad', byFac),
      dims_by_car: groupByCampo('carrera', byCar),
      sent: dashboard.sent || null,
      sentimiento: sentimiento
    };
    return surveyData;
  }

  // ── Inicializa SURVEY_DATA global ──
  async function initSurveyData(nivel, periodo) {
    if (periodo == null) {
      periodo = nivel;
      nivel = DEFAULT_NIVEL;
    }
    SURVEY_DATA = await loadSurveyData(nivel, periodo);
    if (!SURVEY_DATA) {
      console.error('[portal] No se pudieron cargar los datos de encuestas (' + nivel + '/' + periodo + ')');
    }
  }

  // ── Helpers de filtrado / re-agregación (datos crudos) ──
  function getCarrerasForFiltro(facultad) {
    const F = SURVEY_DATA.filtros;
    if (!facultad || esEstudiosGen(facultad)) return (F.carreras || []).slice();
    return (F.facultad_carrera[facultad] || []).slice();
  }

  function getCiclosForFiltro(facultad, carrera) {
    const F = SURVEY_DATA.filtros;
    const ciclos = F.ciclos || [];
    if (esEstudiosGen(facultad)) return CICLOS_ESTUDIOS_GENERALES;
    if (!facultad && !carrera) return ciclos;
    const max = FACULTADES_12_CICLOS.indexOf(facultad) !== -1 || CARRERAS_12_CICLOS.indexOf(carrera) !== -1
      ? MAX_CICLOS_ESPECIALES : MAX_CICLOS_DEFAULT;
    return ciclos.filter(c => (parseInt(c, 10) || 0) <= max);
  }

  function filtrarDatos(datos, facultad, carrera, ciclo) {
    if (!datos) return [];
    const ciclos = Array.isArray(ciclo) ? ciclo : ciclo ? [ciclo] : null;
    return datos.filter(row => {
      if (esEstudiosGen(facultad)) {
        return CICLOS_ESTUDIOS_GENERALES.indexOf(row.ciclo) !== -1 &&
          (!carrera || row.carrera === carrera) &&
          (!ciclos || ciclos.indexOf(row.ciclo) !== -1);
      }
      return (!facultad || row.facultad === facultad) &&
        (!carrera || row.carrera === carrera) &&
        (!ciclos || ciclos.indexOf(row.ciclo) !== -1);
    });
  }

  function groupDimsRows(rows) {
    const weight = (sum, total) => total ? sum / total : 0;
    const m = new Map();
    rows.forEach(row => {
      const key = row.dimension + '\u0000' + row.categoria;
      const acc = m.get(key) || { dimension: row.dimension, categoria: row.categoria, t3b_pct: 0, total: 0 };
      acc.total += row.total;
      acc.t3b_pct += (row.t3b_pct || 0) * row.total;
      m.set(key, acc);
    });
    return [...m.values()]
      .map(d => ({ dimension: d.dimension, categoria: d.categoria, total: d.total, t3b_pct: weight(d.t3b_pct, d.total) }))
      .sort((a, b) => b.t3b_pct - a.t3b_pct);
  }

  function aggCatsRows(rows) {
    const weight = (sum, total) => total ? sum / total : 0;
    const m = new Map();
    rows.forEach(row => {
      const acc = m.get(row.categoria) || { categoria: row.categoria, t3b_pct: 0, total: 0 };
      acc.total += row.total;
      acc.t3b_pct += (row.t3b_pct || 0) * row.total;
      m.set(row.categoria, acc);
    });
    return [...m.values()]
      .map(c => ({ categoria: c.categoria, total: c.total, t3b_pct: weight(c.t3b_pct, c.total) }))
      .sort((a, b) => b.t3b_pct - a.t3b_pct);
  }

  function getDimsTop3() {
    const g = window.__surveyFilter ? window.__surveyFilter.top3 : null;
    const raw = SURVEY_DATA.dimensiones_raw || [];
    if (!raw.length) {
      if (g && g.car && SURVEY_DATA.dims_by_car && SURVEY_DATA.dims_by_car[g.car]) return SURVEY_DATA.dims_by_car[g.car];
      if (g && g.fac && SURVEY_DATA.dims_by_fac && SURVEY_DATA.dims_by_fac[g.fac]) return SURVEY_DATA.dims_by_fac[g.fac];
      return SURVEY_DATA.dims;
    }
    if (!g || (!g.fac && !g.car && (!g.ciclos || !g.ciclos.length))) return SURVEY_DATA.dims;
    const rows = filtrarDatos(raw, g.fac, g.car, g.ciclos);
    if (!rows.length) return SURVEY_DATA.dims;
    return groupDimsRows(rows);
  }

  // ── Detalle por Carrera (réplica index.html renderDetalleCarreras) ──
  // Devuelve { rows, csatRef, npsRef }: rows = filas por carrera con CSAT
  // (Top 3 Box), NPS y diferencia vs promedio del conjunto filtrado.
  function getDetalleData() {
    const g = window.__surveyFilter ? window.__surveyFilter.detalle : null;
    const fac = g ? g.fac : '';
    const rawCic = g ? g.ciclos : [];
    const ciclos = (Array.isArray(rawCic) && rawCic.length) ? rawCic : '';
    const csatRows = SURVEY_DATA.csat_ciclo_carrera || [];
    const npsRows = SURVEY_DATA.nps_ciclo_carrera || [];
    const hasCiclo = !!csatRows.length;

    let csatMap, npsMap;
    if (!hasCiclo) {
      csatMap = new Map();
      (SURVEY_DATA.csat_carrera || [])
        .filter(c => !fac || c.facultad === fac)
        .forEach(c => {
          const t3b = (c['Totalmente satisfecho'] || 0) + (c['Muy satisfecho'] || 0) + (c['Satisfecho'] || 0);
          const total = t3b + (c['Insatisfecho'] || 0) + (c['Totalmente insatisfecho'] || 0);
          csatMap.set(c.carrera, { carrera: c.carrera, facultad: c.facultad, t3b, total });
        });
      npsMap = new Map();
      (SURVEY_DATA.nps_carrera || [])
        .filter(n => !fac || n.facultad === fac)
        .forEach(n => {
          npsMap.set(n.carrera, {
            promotores: n.promotores || 0,
            pasivos: n.pasivos || 0,
            detractores: n.detractores || 0
          });
        });
    } else {
      const filteredCsat = filtrarDatos(csatRows, fac, null, ciclos);
      const filteredNps = filtrarDatos(npsRows, fac, null, ciclos);

      csatMap = new Map();
      filteredCsat.forEach(r => {
        const acc = csatMap.get(r.carrera) || {
          carrera: r.carrera, facultad: r.facultad, t3b: 0, total: 0
        };
        acc.t3b += (r['Totalmente satisfecho'] || 0) + (r['Muy satisfecho'] || 0) + (r['Satisfecho'] || 0);
        acc.total += (r['Totalmente satisfecho'] || 0) + (r['Muy satisfecho'] || 0) + (r['Satisfecho'] || 0) + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
        csatMap.set(r.carrera, acc);
      });

      npsMap = new Map();
      filteredNps.forEach(r => {
        const acc = npsMap.get(r.carrera) || { promotores: 0, pasivos: 0, detractores: 0 };
        acc.promotores += r.promotores || 0;
        acc.pasivos += r.pasivos || 0;
        acc.detractores += r.detractores || 0;
        npsMap.set(r.carrera, acc);
      });
    }

    // Promedios del conjunto filtrado (igual que dashboard.js L962-983)
    let promT = 0, pasT = 0, detT = 0;
    npsMap.forEach(v => { promT += v.promotores; pasT += v.pasivos; detT += v.detractores; });
    const npsTotal = promT + pasT + detT;
    const npsRef = npsTotal > 0 ? ((promT - detT) / npsTotal) * 100 : 0;
    let tt = 0, tr = 0;
    csatMap.forEach(v => { tt += v.t3b; tr += v.total; });
    const csatRef = tr > 0 ? (tt / tr) * 100 : ((SURVEY_DATA.resumen || {}).csat || {}).score || 0;

    const rows = [...csatMap.values()].map(c => {
      const n = npsMap.get(c.carrera) || {};
      const nT = (n.promotores || 0) + (n.pasivos || 0) + (n.detractores || 0);
      const npsScore = nT > 0 ? (((n.promotores || 0) - (n.detractores || 0)) / nT) * 100 : 0;
      const csatScore = c.total > 0 ? (c.t3b / c.total) * 100 : 0;
      return {
        carrera: c.carrera,
        facultad: c.facultad,
        encuestas: c.total,
        csat_score: csatScore,
        nps_score: npsScore,
        promotores: n.promotores || 0,
        detractores: n.detractores || 0,
        vsPromCsat: csatScore - csatRef,
        vsPromNps: npsScore - npsRef
      };
    }).sort((a, b) => a.carrera.localeCompare(b.carrera));

    return { rows, csatRef, npsRef };
  }

  // Compat: tabla de carreras como array simple (fase previa).
  function getCarrerasTabla() {
    return getDetalleData().rows;
  }

  // ── Exposición pública ──
  window.SurveyPortalCore = {
    esc: esc,
    fmtNum: fmtNum,
    formatCicloText: formatCicloText,
    satColorPortal: satColorPortal,
    esEstudiosGen: esEstudiosGen,
    periodosReales: periodosReales,
    faseConDatos: faseConDatos,
    nivelDeFase: nivelDeFase,
    periodosDeFase: periodosDeFase,
    NIVELES_FASE: NIVELES_FASE
  };

  window.SurveyPortalData = {
    loadPeriodos: loadPeriodos,
    loadSurveyData: loadSurveyData,
    loadGraduatePeriodos: loadGraduatePeriodos,
    loadGraduateData: loadGraduateData,
    normalizeData: normalizeData,
    initSurveyData: initSurveyData,
    filtrarDatos: filtrarDatos,
    groupDimsRows: groupDimsRows,
    aggCatsRows: aggCatsRows,
    getDimsTop3: getDimsTop3,
    getCarrerasTabla: getCarrerasTabla,
    getDetalleData: getDetalleData,
    esEstudiosGen: esEstudiosGen,
    getCarrerasForFiltro: getCarrerasForFiltro,
    getCiclosForFiltro: getCiclosForFiltro,
    PROGRAMA_ESTUDIOS_GENERALES: PROGRAMA_ESTUDIOS_GENERALES,
    CICLOS_ESTUDIOS_GENERALES: CICLOS_ESTUDIOS_GENERALES,
    CARRERAS_12_CICLOS: CARRERAS_12_CICLOS,
    FACULTADES_12_CICLOS: FACULTADES_12_CICLOS,
    MAX_CICLOS_DEFAULT: MAX_CICLOS_DEFAULT,
    MAX_CICLOS_ESPECIALES: MAX_CICLOS_ESPECIALES,
    getSurveyData: function () { return SURVEY_DATA; },
    getSurveyDataCache: function () { return SURVEY_DATA_CACHE; },
    setSurveyData: function (d) { SURVEY_DATA = d; },
    getGraduateData: function () { return GRADUATE_DATA; },
    // ── Acceso genérico por ítem ──
    loadPeriodosDeNiveles: loadPeriodosDeNiveles,
    getPeriodosDeFase: function (phaseId) { return periodosDeFase(phaseId); },
    getPeriodoDeFase: getPeriodoDeFase,
    tieneDatosDeFase: tieneDatosDeFase,
    nivelDeFase: nivelDeFase,
    // ── Alias temporales (se eliminan al migrar todos los consumidores) ──
    getDefaultNivel: function () { return nivelDeFase('1.0'); },
    getDefaultPeriodo: function () { return getPeriodoDeFase('1.0'); },
    getPeriodosList: function () { return periodosDeFase('1.0'); },
    getGraduatePeriodo: function () { return getPeriodoDeFase('1.2'); },
    getGraduatePeriodosList: function () { return periodosDeFase('1.2'); }
  };
})();
