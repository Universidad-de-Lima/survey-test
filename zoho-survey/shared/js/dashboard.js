const SurveyDashboard = (() => {
  'use strict';

  // Flag de versión para el módulo de análisis cualitativo - Consolidado en v3.0.2

  // ── Constantes y Configuración de Negocio ──
  const config = window.SURVEY_CONFIG || {};
  const BASE_URL = './json';
  const META_NPS = config.META_NPS ?? 50;
  const META_CSAT = config.META_CSAT ?? 93;
  const META_T2B = config.META_T2B ?? 70;
  const META_PONDERADO = config.META_PONDERADO ?? 80;
  const META_EMPLEABILIDAD = config.META_EMPLEABILIDAD ?? 85;
  const CARRERAS_12_CICLOS = config.CARRERAS_12_CICLOS;
  const FACULTADES_12_CICLOS = config.FACULTADES_12_CICLOS;
  const PROGRAMA_ESTUDIOS_GENERALES = config.PROGRAMA_ESTUDIOS_GENERALES;
  const CICLOS_ESTUDIOS_GENERALES = config.CICLOS_ESTUDIOS_GENERALES;
  const FACULTAD_PLACEHOLDER = config.FACULTAD_PLACEHOLDER;
  const FACULTAD_PLACEHOLDER_PROG = config.FACULTAD_PLACEHOLDER_PROG;
  const SAT_KEYS = config.SAT_KEYS;
  const SAT_TOP3_KEYS = config.SAT_KEYS.slice(0, 3);
  const SAT_TOP2_KEYS = config.SAT_TOP2_KEYS;

  // ── Módulos Externos Reutilizables ──
  const _fmt = window.SurveyFormatters;
  const _mt = window.SurveyMetrics;
  const _san = window.SurveySanitizer;
  const _dh = window.SurveyDOMHelpers;
  const _ttp = window.SurveyTooltip;
  const _pb = window.SurveyProgressBar;
  const _fc = window.SurveyFilterController;
  const _rc = window.SurveyRadarChart;
  const _sv = window.SurveySentimentView;

  // Cache Central de Datos
  const cache = {
    dashboard: null,
    dimensiones: null,
    ids: null,
    npsCicloCarrera: null,
    csatCicloCarrera: null,
    npsCarrera: null,
    csatCarrera: null,
    filtros: null,
    sentimiento: null,
  };

  // Referencias a Elementos DOM Clave
  const DOM = {
    tooltip: document.getElementById('tooltip'),
    footerAnio: document.getElementById('footer-anio'),
    footerPeriodo: document.getElementById('footer-periodo'),
    footerFuenteTexto: document.getElementById('footer-fuente-texto'),
    kpiNpsValue: document.getElementById('kpi-nps-value'),
    kpiNpsBar: document.getElementById('kpi-nps-bar'),
    kpiNpsMeta: document.getElementById('kpi-nps-meta'),
    kpiCsatValue: document.getElementById('kpi-csat-value'),
    kpiCsatBar: document.getElementById('kpi-csat-bar'),
    kpiCsatMeta: document.getElementById('kpi-csat-meta'),
    kpiT2bValue: document.getElementById('kpi-t2b-value'),
    kpiT2bBar: document.getElementById('kpi-t2b-bar'),
    kpiT2bMeta: document.getElementById('kpi-t2b-meta'),
    kpiPonderadoValue: document.getElementById('kpi-ponderado-value'),
    kpiPonderadoBar: document.getElementById('kpi-ponderado-bar'),
    kpiPonderadoMeta: document.getElementById('kpi-ponderado-meta'),
    kpiEmpleaValue: document.getElementById('kpi-emplea-value'),
    kpiEmpleaBar: document.getElementById('kpi-emplea-bar'),
    kpiEmpleaMeta: document.getElementById('kpi-emplea-meta'),
    kpiEmpleaCard: document.getElementById('kpi-emplea-card'),
    npsBar: document.getElementById('nps-bar'),
    npsLegend: document.getElementById('nps-legend'),
    csatBar: document.getElementById('csat-bar'),
    csatLegend: document.getElementById('csat-legend'),
    insightHallazgos: document.getElementById('insight-hallazgos'),
    insightFortaleza: document.getElementById('insight-fortaleza'),
    insightAtencion: document.getElementById('insight-atencion'),
    radarChart: document.getElementById('radar-chart'),
    detallePromedioRef: document.getElementById('detalle-promedio-ref'),
    detallePromedioNpsRef: document.getElementById('detalle-promedio-nps-ref'),
    progressFill: document.getElementById('progress-fill'),
  };

  let csatScoreGlobal = 0;

  // Helpers compartidos: se delega a SurveyDOMHelpers para evitar duplicación.
  // Las variables locales mantienen compatibilidad con el código existente.
  const $ = _dh.$;
  const esEstudiosGen = _dh.esEstudiosGen;
  const sumKeys = _dh.sumKeys;
  const pct = (value, total) => (total > 0 ? (value / total) * 100 : 0);

  /**
   * Muestra un banner de error en la parte superior del dashboard.
   * @param {string} message - Mensaje descriptivo del error
   */
  function showError(message) {
    const banner = document.getElementById('error-banner');
    if (!banner) return;
    banner.textContent = message;
    banner.classList.add('visible');
    banner.setAttribute('role', 'alert');
  }

  /**
   * Oculta el banner de error.
   */
  function hideError() {
    const banner = document.getElementById('error-banner');
    if (!banner) return;
    banner.classList.remove('visible');
    banner.removeAttribute('role');
  }

  /**
   * Carga asíncrona de datos con resiliencia y degradación gradual.
   */
  async function loadAllData() {
    const criticalEndpoints = {
      dashboard: 'dashboard_data',
      filtros: 'filtros',
      dimensiones: 'dimensiones',
    };
    const optionalEndpoints = {
      ids: 'ids',
      npsCicloCarrera: 'nps_ciclo_carrera',
      csatCicloCarrera: 'csat_ciclo_carrera',
      npsCarrera: 'nps_carrera',
      csatCarrera: 'csat_carrera',
      sentimiento: 'sentimiento',
    };

    try {
      hideError();

      // 1. Cargar endpoints críticos (fallan globalmente ante error)
      const criticalKeys = Object.keys(criticalEndpoints);
      const criticalPromises = criticalKeys.map((key) =>
        fetch(`${BASE_URL}/${criticalEndpoints[key]}.json`, { cache: 'no-store' }).then((r) => {
          if (!r.ok) throw new Error(`Archivo crítico no disponible: ${criticalEndpoints[key]}`);
          return r.json();
        })
      );
      const criticalResults = await Promise.all(criticalPromises);
      criticalKeys.forEach((key, index) => {
        cache[key] = criticalResults[index];
      });

      // 2. Cargar endpoints opcionales de forma segura (tolerante a fallos de red/períodos vacíos)
      const optionalKeys = Object.keys(optionalEndpoints);
      const optionalPromises = optionalKeys.map((key) =>
        fetch(`${BASE_URL}/${optionalEndpoints[key]}.json`, { cache: 'no-store' })
          .then((r) => (r.ok ? r.json() : null))
          .catch((err) => {
            console.warn(`JSON opcional no cargado [${optionalEndpoints[key]}]:`, err);
            return null;
          })
      );
      const optionalResults = await Promise.all(optionalPromises);
      optionalKeys.forEach((key, index) => {
        cache[key] = optionalResults[index];
      });

      csatScoreGlobal = cache.dashboard.resumen.csat.score;
      return true;
    } catch (error) {
      const msg = error.message || 'Error desconocido al cargar datos.';
      console.error('Fallo grave al cargar los datos esenciales del dashboard:', msg);
      showError(`No se pudieron cargar los datos del dashboard: ${msg}. Verifica que los archivos JSON estén generados correctamente.`);
      return false;
    }
  }

  /**
   * Filtra los datos de Zoho Survey aplicando los filtros activos de Facultad, Carrera y Ciclo.
   */
  function filtrarDatos(datos, facultad, carrera, ciclo) {
    if (!datos) return [];
    const ciclos = Array.isArray(ciclo) ? ciclo : ciclo ? [ciclo] : null;
    return datos.filter((row) => {
      if (esEstudiosGen(facultad)) {
        return (
          CICLOS_ESTUDIOS_GENERALES.includes(row.ciclo) &&
          (!carrera || row.carrera === carrera) &&
          (!ciclos || ciclos.includes(row.ciclo))
        );
      }
      return (
        (!facultad || row.facultad === facultad) &&
        (!carrera || row.carrera === carrera) &&
        (!ciclos || ciclos.includes(row.ciclo))
      );
    });
  }

  /**
   * Renderiza el encabezado, KPIs globales del negocio y el bloque de texto con insights.
   */
  function renderEjecutivo() {
    const { resumen, hallazgos, nps, csat } = cache.dashboard;
    if (DOM.footerAnio) DOM.footerAnio.textContent = resumen.año ?? resumen.ano;
    if (DOM.footerPeriodo) {
      DOM.footerPeriodo.textContent = `Periodo: ${_fmt.formatDate(resumen.fecha_inicio)} - ${_fmt.formatDate(resumen.fecha_fin)} · Dirección de Planificación y Acreditación`;
    }
    if (DOM.footerFuenteTexto) {
      const nivel = resumen.empleabilidad ? 'GRADUADOS - PREGRADO' : 'ESTUDIANTIL- PREGRADO';
      const periodo = resumen.periodo || (resumen.año ?? resumen.ano);
      DOM.footerFuenteTexto.textContent = `ENCUESTA DE SATISFACCIÓN ${nivel} - ${periodo}`;
    }

    DOM.kpiNpsValue.textContent = _fmt.formatDecimal(resumen.nps.score);
    DOM.kpiNpsBar.style.width = `${Math.min(100, Math.max(0, resumen.nps.score))}%`;
    DOM.kpiNpsMeta.textContent = `Meta ${_fmt.formatInteger(META_NPS)}`;

    DOM.kpiCsatValue.textContent = _fmt.formatPercent(resumen.csat.score);
    DOM.kpiCsatBar.style.width = `${resumen.csat.score}%`;
    DOM.kpiCsatMeta.textContent = `Meta ${_fmt.formatInteger(META_CSAT)} %`;

    // T2B y Promedio Ponderado: se leen precomputados del JSON y, como fallback
    // para periodos generados antes de su incorporación, se derivan de la
    // distribución CSAT top-level mediante el gemelo JS (SurveyMetrics).
    const t2bPct = resumen.csat.t2b_pct ?? (_mt ? _mt.deriveT2B(csat, SAT_TOP2_KEYS) : 0);
    const ponderadoPct = resumen.csat.ponderado ?? (_mt ? _mt.derivePonderado(csat) : 0);

    if (DOM.kpiT2bValue) {
      DOM.kpiT2bValue.textContent = _fmt.formatScore(t2bPct);
      DOM.kpiT2bBar.style.width = `${Math.min(100, Math.max(0, t2bPct))}%`;
      DOM.kpiT2bMeta.textContent = `Meta ${_fmt.formatInteger(META_T2B)} %`;
    }
    if (DOM.kpiPonderadoValue) {
      DOM.kpiPonderadoValue.textContent = _fmt.formatScore(ponderadoPct);
      DOM.kpiPonderadoBar.style.width = `${Math.min(100, Math.max(0, ponderadoPct))}%`;
      DOM.kpiPonderadoMeta.textContent = `Meta ${_fmt.formatInteger(META_PONDERADO)} %`;
    }

    if (DOM.kpiEmpleaCard && resumen.empleabilidad) {
      DOM.kpiEmpleaCard.style.display = '';
      DOM.kpiEmpleaValue.textContent = _fmt.formatPercent(resumen.empleabilidad.score);
      DOM.kpiEmpleaBar.style.width = `${resumen.empleabilidad.score}%`;
      DOM.kpiEmpleaMeta.textContent = `Meta ${META_EMPLEABILIDAD} %`;
    } else if (DOM.kpiEmpleaCard) {
      DOM.kpiEmpleaCard.style.display = 'none';
    }

    renderNPSBar(nps);
    renderCSATBar(csat);

    const { nps_etapas: etapas } = hallazgos;
    const empleaPct = resumen.empleabilidad ? _fmt.formatInteger(Math.round(resumen.empleabilidad.score)) : '';
    DOM.insightHallazgos.innerHTML = resumen.empleabilidad
      ? _san.sanitizeHTML(`
      Actualmente, <strong>+${_fmt.formatInteger(hallazgos.csat_pct)} %</strong> de graduados están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos, que es de <strong>+${_fmt.formatInteger(hallazgos.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${hallazgos.nps_tipo}</strong>" a nivel global.
      La empleabilidad es de <strong>+${empleaPct}%</strong> respecto a la meta trazada para este año.
    `)
      : _san.sanitizeHTML(`
      Actualmente, <strong>+${_fmt.formatInteger(hallazgos.csat_pct)} %</strong> de estudiantes están satisfechos con la Universidad de Lima.
      El Índice de Promotores Netos, que es de <strong>+${_fmt.formatInteger(hallazgos.nps_score)}</strong>, posiciona a la institución en el rango
      "<strong>${hallazgos.nps_tipo}</strong>" a nivel global,
      pero <strong>${hallazgos.tendencia}</strong> conforme avanza la carrera:
      <strong>Inicial (${_fmt.formatDecimal(etapas.Inicial || 0)})</strong> →
      <strong>Intermedio (${_fmt.formatDecimal(etapas.Intermedio || 0)})</strong> →
      <strong>Avanzado (${_fmt.formatDecimal(etapas.Avanzado || 0)})</strong>.
      Teniendo una diferencia de <strong>-${_fmt.formatInteger(hallazgos.delta)}</strong> puntos en el ciclo de vida estudiantil.
    `);
  }

  function renderNPSBar(nps) {
    const prom = nps.Promotores ?? nps.promotores ?? 0;
    const pas = nps.Pasivos ?? nps.pasivos ?? 0;
    const det = nps.Detractores ?? nps.detractores ?? 0;
    const total = prom + pas + det;
    DOM.npsBar.innerHTML = `<div class="csat-bar-row">`
      + `<div class="csat-segment" style="width:${pct(prom, total)}%; background:var(--gray-700);"
           data-label="Promotores (9-10)" data-value="${_fmt.formatInteger(prom)} (${_fmt.formatPctDecimal(prom, total)})"><span class="csat-label">${_fmt.formatPctSimple(prom, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(pas, total)}%; background:var(--gray-400);"
           data-label="Pasivos (7-8)" data-value="${_fmt.formatInteger(pas)} (${_fmt.formatPctDecimal(pas, total)})"><span class="csat-label">${_fmt.formatPctSimple(pas, total)}</span></div>`
      + `<div class="csat-segment" style="width:${pct(det, total)}%; background:var(--ulima-orange);"
           data-label="Detractores (0-6)" data-value="${_fmt.formatInteger(det)} (${_fmt.formatPctDecimal(det, total)})"><span class="csat-label">${_fmt.formatPctSimple(det, total)}</span></div>`
      + `</div>`;
    DOM.npsLegend.innerHTML = `
      <div class="legend-item" data-label="Promotores (9-10)"><div class="legend-dot" style="background:var(--gray-700);"></div>Promotores: ${_fmt.formatInteger(prom)}</div>
      <div class="legend-item" data-label="Pasivos (7-8)"><div class="legend-dot" style="background:var(--gray-400);"></div>Pasivos: ${_fmt.formatInteger(pas)}</div>
      <div class="legend-item" data-label="Detractores (0-6)"><div class="legend-dot" style="background:var(--ulima-orange);"></div>Detractores: ${_fmt.formatInteger(det)}</div>
    `;
    // Data attributes para acceso programatico sin parseo regex (CAL-04)
    DOM.npsLegend.setAttribute('data-promotores', prom);
    DOM.npsLegend.setAttribute('data-pasivos', pas);
    DOM.npsLegend.setAttribute('data-detractores', det);
    adjustSegmentLabels('#nps-bar');
    // Hover highlight: agranda la leyenda al pasar sobre un segmento
    document.querySelectorAll('#nps-bar .csat-segment').forEach(function(seg) {
      seg.addEventListener('mouseenter', function() {
        document.querySelectorAll('#nps-legend .legend-item.highlight').forEach(function(el) { el.classList.remove('highlight'); });
        var item = document.querySelector('#nps-legend .legend-item[data-label="' + seg.getAttribute('data-label') + '"]');
        if (item) item.classList.add('highlight');
      });
      seg.addEventListener('mouseleave', function() {
        document.querySelectorAll('#nps-legend .legend-item.highlight').forEach(function(el) { el.classList.remove('highlight'); });
      });
    });
  }

  function renderCSATBar(csat) {
    const labels = [
      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' },
      { key: 'Muy satisfecho', color: 'var(--gray-600)' },
      { key: 'Satisfecho', color: 'var(--gray-400)' },
      { key: 'Insatisfecho', color: 'var(--ulima-orange)' },
      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' },
    ];
    const total = labels.reduce((accSum, item) => accSum + (csat[item.key] || 0), 0);
    const visibleLabels = labels.filter((item) => csat[item.key] > 0);
    DOM.csatBar.innerHTML = `<div class="csat-bar-row">`
      + visibleLabels
        .map((item) => {
          const p = pct(csat[item.key], total);
          return `<div class="csat-segment" style="width:${p}%; background:${item.color};"
                data-label="${item.key}" data-value="${_fmt.formatInteger(csat[item.key])} (${_fmt.formatPctDecimal(csat[item.key], total)})"><span class="csat-label">${_fmt.formatPctSimple(csat[item.key], total)}</span></div>`;
        })
        .join('')
      + `</div>`;
    DOM.csatLegend.innerHTML = visibleLabels
      .map((item) =>
        `<div class="legend-item" data-label="${item.key}"><div class="legend-dot" style="background:${item.color};"></div>${item.key}: ${_fmt.formatInteger(csat[item.key])}</div>`
      )
      .join('');
    adjustSegmentLabels('#csat-bar');
    // Hover highlight: agranda la leyenda al pasar sobre un segmento
    document.querySelectorAll('#csat-bar .csat-segment').forEach(function(seg) {
      seg.addEventListener('mouseenter', function() {
        document.querySelectorAll('#csat-legend .legend-item.highlight').forEach(function(el) { el.classList.remove('highlight'); });
        var item = document.querySelector('#csat-legend .legend-item[data-label="' + seg.getAttribute('data-label') + '"]');
        if (item) item.classList.add('highlight');
      });
      seg.addEventListener('mouseleave', function() {
        document.querySelectorAll('#csat-legend .legend-item.highlight').forEach(function(el) { el.classList.remove('highlight'); });
      });
    });
  }

  /**
   * Mide y ajusta de forma responsiva las etiquetas de segmentos de distribución.
   * Si la barra no cabe, renderiza etiquetas con líneas callout hacia arriba o abajo.
   */
  function adjustSegmentLabels(target) {
    let container, barRow;
    if (typeof target === 'string') {
      container = document.querySelector(target);
      if (!container) return;
      barRow = container.querySelector('.csat-bar-row');
    } else {
      barRow = target;
      container = barRow.parentElement;
    }
    if (!barRow || !container) return;

    const isDistBar = barRow.classList.contains('distribution-bar') || barRow.classList.contains('visibility-bar');
    const segSelector = isDistBar ? '.distribution-segment, .visibility-segment' : '.csat-segment';

    // Limpiar elementos de ejecuciones anteriores
    container.querySelectorAll('.csat-labels-above, .csat-labels-below').forEach((el) => el.remove());

    barRow.querySelectorAll(isDistBar ? '.dist-label' : '.csat-label').forEach((lbl) => {
      lbl.style.visibility = '';
    });

    const SAFETY_MARGIN = 16;
    const barWidth = barRow.offsetWidth;

    if (!barWidth) {
      barRow.addEventListener('animationend', function onEnd() {
        barRow.removeEventListener('animationend', onEnd);
        requestAnimationFrame(() => adjustSegmentLabels(target));
      }, { once: true });
      setTimeout(() => requestAnimationFrame(() => adjustSegmentLabels(target)), config.ANIMATION_FALLBACK_MS ?? 1200);
      if (!container.dataset._visListener) {
        container.dataset._visListener = '1';
        document.addEventListener('visibilitychange', function visHandler() {
          if (!document.hidden) {
            document.removeEventListener('visibilitychange', visHandler);
            delete container.dataset._visListener;
            adjustSegmentLabels(target);
          }
        });
      }
      return;
    }

    const smallSegs = [];
    barRow.querySelectorAll(segSelector).forEach((seg) => {
      const segPct = isDistBar
        ? (parseFloat(seg.style.width) || 0) / 100
        : seg.offsetWidth / barWidth;
      const tooNarrow = isDistBar
        ? segPct < 0.015
        : seg.offsetWidth < (config.MIN_SEGMENT_WIDTH ?? 30);
      const tooSmall = segPct < (config.SEGMENT_EXTERNAL_LABEL_PCT ?? 0.02);
      const textContent = (seg.textContent || '').trim();
      const textOverflows = isDistBar
        ? (textContent.length * 8 + SAFETY_MARGIN > seg.offsetWidth)
        : (() => { const lbl = seg.querySelector('.csat-label'); return lbl ? lbl.scrollWidth + SAFETY_MARGIN > seg.offsetWidth : false; })();
      const selected = textOverflows || tooNarrow || tooSmall;
      const isZero = isDistBar ? (parseFloat(seg.style.width) || 0) === 0 : segPct < (config.SEGMENT_LABEL_HIDE_PCT ?? 0.005);
      if (isZero || parseFloat(textContent.replace(',', '.')) === 0) {
        const lbl = isDistBar ? seg.querySelector('.dist-label') : seg.querySelector('.csat-label');
        if (lbl) lbl.style.visibility = 'hidden';
        return;
      }
      if (selected) smallSegs.push(seg);
    });

    if (!smallSegs.length) {
      if (isDistBar) {
        const ROW_H = 6;
        const wa = document.createElement('div');
        wa.className = 'csat-labels-above';
        wa.style.height = (ROW_H + 4) + 'px';
        container.insertBefore(wa, barRow);
        const wb = document.createElement('div');
        wb.className = 'csat-labels-below';
        wb.style.height = (ROW_H + 4) + 'px';
        container.appendChild(wb);
      }
      return;
    }

    smallSegs.sort((a, b) => a.offsetWidth - b.offsetWidth);
    const aboveSegs = [];
    const belowSegs = [];
    smallSegs.forEach((seg, i) => {
      if (i % 2 === 0) aboveSegs.push(seg);
      else belowSegs.push(seg);
    });

    const ROW_H = 6;

    function createLabelWrap(className) {
      const w = document.createElement('div');
      w.className = className;
      return w;
    }

    const wrapAbove = createLabelWrap('csat-labels-above');
    container.insertBefore(wrapAbove, barRow);

    const wrapBelow = createLabelWrap('csat-labels-below');
    container.appendChild(wrapBelow);

    let distCumulativePct = 0;
    const distSegOffsets = [];
    if (isDistBar) {
      barRow.querySelectorAll(segSelector).forEach((seg) => {
        const pctWidth = parseFloat(seg.style.width) || 0;
        distSegOffsets.push({ seg, leftPct: distCumulativePct, pct: pctWidth });
        distCumulativePct += pctWidth;
      });
    }

    function renderLabelGroup(segs, wrap, isBelow) {
      if (!segs.length) return;
      const rows = [];
      const assignments = [];
      const wrapLeft = wrap.getBoundingClientRect().left;

      segs.forEach((seg) => {
        let cx;
        if (isDistBar) {
          const info = distSegOffsets.find((d) => d.seg === seg);
          cx = info ? ((info.leftPct + info.pct / 2) / 100) * barWidth : 0;
        } else {
          cx = (seg.getBoundingClientRect().left - wrapLeft) + seg.getBoundingClientRect().width / 2;
        }
        const txt = isDistBar ? (seg.textContent || '').trim() : (seg.querySelector('.csat-label')?.textContent || '');
        const temp = document.createElement('div');
        temp.className = 'csat-label-above';
        temp.textContent = txt;
        temp.style.cssText = 'position:absolute;left:-9999px';
        document.body.appendChild(temp);
        const labelW = temp.scrollWidth || 30;
        document.body.removeChild(temp);

        const labelL = cx - labelW / 2;
        let row = 0;
        for (let r = 0; r <= rows.length; r++) {
          if (!rows[r] || labelL >= rows[r] + 10) { row = r; rows[r] = cx + labelW / 2; break; }
        }
        assignments.push({ seg, cx, labelW, row, txt });
      });

      const totalRows = rows.length || 1;

      assignments.forEach(({ seg, cx, row, txt }) => {
        const lbl = isDistBar ? seg.querySelector('.dist-label') : seg.querySelector('.csat-label');
        if (lbl) lbl.style.visibility = 'hidden';

        const segColor = getComputedStyle(seg).backgroundColor;
        const el = document.createElement('div');
        el.className = 'csat-label-above';
        el.textContent = txt;
        el.style.color = segColor;
        wrap.appendChild(el);
        el.style.left = cx + 'px';

        if (isBelow) {
          el.style.top = (row * ROW_H + 4) + 'px';
        } else {
          el.style.top = ((totalRows - row) * ROW_H - 12) + 'px';
        }

        const line = document.createElement('span');
        line.className = 'callout-line';
        line.style.background = segColor;
        if (isBelow) {
          line.style.top = 'auto';
          line.style.bottom = '100%';
          line.style.height = Math.max(4, (row * ROW_H + 4)) + 'px';
        } else {
          line.style.height = Math.max(4, (totalRows * ROW_H + 4) - el.offsetTop - el.offsetHeight) + 'px';
        }
        el.appendChild(line);

        const arm = document.createElement('span');
        arm.className = 'callout-arm';
        arm.style.background = segColor;
        line.appendChild(arm);

        const dot = document.createElement('span');
        dot.className = 'callout-dot';
        dot.style.background = segColor;
        el.appendChild(dot);
      });

      wrap.style.height = (totalRows * ROW_H + 4) + 'px';
    }

    renderLabelGroup(aboveSegs, wrapAbove, false);
    renderLabelGroup(belowSegs, wrapBelow, true);

    const hAbove = parseFloat(wrapAbove.style.height) || 0;
    const hBelow = parseFloat(wrapBelow.style.height) || 0;
    const maxH = Math.max(hAbove, hBelow);
    if (maxH > 0) {
      wrapAbove.style.height = maxH + 'px';
      wrapBelow.style.height = maxH + 'px';
    }
  }

  // ==================== SECCIÓN OPERATIVO ====================
  function renderTop3Bars(containerId, data) {
    const container = $(containerId);
    if (!container) return;
    const fragment = document.createDocumentFragment();
  function buildSatisfactionPieSvg(counts, satKeys, total) {
    let html = '';
// ——— Left column: exploded pie chart SVG ———
        const satShort = ['Tot.Sat.', 'Muy.Sat.', 'Satisfe.', 'Insatis.', 'Tot.Ins.'];
        const segmentColors = ['#9CA3AF', '#D1D5DB', '#E5E7EB', '#F3F4F6', '#ffffff']; // gray-400, gray-300, gray-200, gray-100, white
        // Find largest segment
        let maxIdx = 0, maxVal = 0;
        const values = satKeys.map((k, i) => {
          const v = counts[k] || 0;
          if (v > maxVal) { maxVal = v; maxIdx = i; }
          return v;
        });
        const cx = 90, cy = 90, r = 70;
        let svgParts = [];
        const externalLabels = [];
        let angle = -Math.PI / 2;
        values.forEach((val, i) => {
          if (val === 0) return;
          const pct = val / total;
          const a = pct * 2 * Math.PI;
          const midAngle = angle + a / 2;
          const expl = 0; // sin separación entre segmentos
          const dx = expl * Math.cos(midAngle);
          const dy = expl * Math.sin(midAngle);
          const x1 = cx + dx + r * Math.cos(angle);
          const y1 = cy + dy + r * Math.sin(angle);
          const x2 = cx + dx + r * Math.cos(angle + a);
          const y2 = cy + dy + r * Math.sin(angle + a);
          const large = a > Math.PI ? 1 : 0;
          const path = `M${cx + dx} ${cy + dy} L${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
          svgParts.push(`<path d="${path}" fill="${segmentColors[i]}"/>`);
          const pctText = _fmt.formatDecimal(pct * 100, 1);
          const isSmall = pct < 0.12;
          if (isSmall) {
            const outR = r * 1.35;
            const ox = cx + dx + outR * Math.cos(midAngle);
            const oy = cy + dy + outR * Math.sin(midAngle);
            const edgeX = cx + dx + r * Math.cos(midAngle);
            const edgeY = cy + dy + r * Math.sin(midAngle);
            const countText = _fmt.formatInteger(val);
            externalLabels.push({ ox, oy, edgeX, edgeY, midAngle, shortName: satShort[i], countText, cx, cy, dx, dy });
          } else {
            const labelR = r * 0.62;
            const lx = cx + dx + labelR * Math.cos(midAngle);
            const ly = cy + dy + labelR * Math.sin(midAngle);
            svgParts.push(`<text x="${lx}" y="${ly - 5}" text-anchor="middle" fill="#111827" font-size="10" font-weight="600">${satShort[i]}</text>`);
            svgParts.push(`<text x="${lx}" y="${ly + 8}" text-anchor="middle" fill="#111827" font-size="10" font-weight="700">${_fmt.formatInteger(val)}</text>`);
          }
          angle += a;
        });
        // External labels: alternate sides for adjacent labels to avoid stacking
        const angleThreshold = 0.4;
        externalLabels.sort((a, b) => a.midAngle - b.midAngle);
        externalLabels.forEach((l, idx) => {
          if (idx > 0 && Math.abs(l.midAngle - externalLabels[idx - 1].midAngle) < angleThreshold) {
            l._side = idx % 2 === 0 ? 'left' : 'right';
          } else {
            l._side = Math.cos(l.midAngle) >= 0 ? 'right' : 'left';
          }
        });
        externalLabels.forEach((l) => {
          const naturalSide = Math.cos(l.midAngle) >= 0 ? 'right' : 'left';
          if (l._side !== naturalSide) {
            const outR = r * 1.35;
            const flippedCos = -Math.abs(Math.cos(l.midAngle)) * (l._side === 'left' ? -1 : 1);
            const rawSin = Math.sin(l.midAngle);
            const norm = Math.sqrt(flippedCos * flippedCos + rawSin * rawSin);
            const newCos = flippedCos / norm;
            const newSin = rawSin / norm;
            l.ox = l.cx + l.dx + outR * newCos;
            l.oy = l.cy + l.dy + outR * newSin;
            l.edgeX = l.cx + l.dx + r * newCos;
            l.edgeY = l.cy + l.dy + r * newSin;
          }
        });
        // Vertical collision avoidance within each side group
        const leftG = externalLabels.filter(l => l._side === 'left').sort((a, b) => a.oy - b.oy);
        const rightG = externalLabels.filter(l => l._side === 'right').sort((a, b) => a.oy - b.oy);
        [leftG, rightG].forEach((group) => {
          const minGap = 22;
          for (let i = 1; i < group.length; i++) {
            if (group[i].oy < group[i - 1].oy + minGap) {
              group[i].oy = group[i - 1].oy + minGap;
            }
          }
          for (let i = group.length - 2; i >= 0; i--) {
            if (group[i].oy > group[i + 1].oy - minGap) {
              group[i].oy = group[i + 1].oy - minGap;
            }
          }
        });
        externalLabels.forEach((l) => {
          const anchor = l._side === 'right' ? 'start' : 'end';
          const xOff = l._side === 'right' ? 3 : -3;
          const midX = (l.edgeX + l.ox) / 2;
          const midY = (l.edgeY + l.oy) / 2 - 4;
          svgParts.push(`<polyline points="${l.edgeX},${l.edgeY} ${midX},${midY} ${l.ox},${l.oy}" fill="none" stroke="#9CA3AF" stroke-width="0.5"/>`);
          svgParts.push(`<text x="${l.ox + xOff}" y="${l.oy - 5}" text-anchor="${anchor}" fill="#fff" font-size="10" font-weight="500">${l.shortName}</text>`);
          svgParts.push(`<text x="${l.ox + xOff}" y="${l.oy + 8}" text-anchor="${anchor}" fill="#fff" font-size="10" font-weight="600">${l.countText}</text>`);
        });
        html += '<div style="display:flex;flex-direction:column;align-items:center;">';
          html += `<svg width="200" height="170" viewBox="-25 -30 230 200">${svgParts.join('')}</svg>`;
          html += '<div style="text-align:center;color:#fff;font-size: var(--text-md);font-weight: var(--font-medium);">Escala de Satisfacción</div>';
        html += '</div>';

            return html;
  }

    data.forEach((item, index) => {
      const barClass = item.pct >= META_CSAT ? 'high' : item.pct >= 80 ? 'medium' : 'low';
      const barValueOutside = item.pct < 12;
      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label">${_fmt.formatDimensionName(item.dim)}</div>
        <div class="bar-container">
          <div class="bar-fill animated ${barClass}" style="width:${item.pct}%; animation-delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${_fmt.formatPercent(item.pct, 2)}</span>
          </div>
        </div>
      `;
      barItem.querySelector('.bar-container').addEventListener('mousemove', (e) => {
        const fac = $('filter-facultad-top3').value;
        const car = $('filter-carrera-top3').value;
        const cic = _dh.getSelectedValues($('filter-ciclo-top3'));
        const rows = filtrarDatos(cache.dimensiones, fac, car, cic).filter((r) => r.dimension === item.dim);
        const counts = {
          'Totalmente satisfecho': 0,
          'Muy satisfecho': 0,
          Satisfecho: 0,
          Insatisfecho: 0,
          'Totalmente insatisfecho': 0,
          'No utilizo': 0,
          'No conozco': 0,
        };
        rows.forEach((r) => {
          Object.keys(counts).forEach((key) => {
            counts[key] += r[key] || 0;
          });
        });
        const satKeys = ['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho', 'Insatisfecho', 'Totalmente insatisfecho'];
        const total = satKeys.reduce((s, k) => s + counts[k], 0);
        const t3bVal = total > 0 ? (counts['Totalmente satisfecho'] + counts['Muy satisfecho'] + counts['Satisfecho']) / total * 100 : 0;
        const t2bVal = total > 0 ? (counts['Totalmente satisfecho'] + counts['Muy satisfecho']) / total * 100 : 0;
        const pondVal = total > 0 ? ((5 * counts['Totalmente satisfecho'] + 4 * counts['Muy satisfecho'] + 3 * counts['Satisfecho'] + 2 * counts['Insatisfecho'] + 1 * counts['Totalmente insatisfecho']) / total) / 5 * 100 : 0;
        let html = '<div style="display:flex;gap:12px;white-space:nowrap;">';

            // Pie SVG (extraido a buildSatisfactionPieSvg)
    html += buildSatisfactionPieSvg(counts, satKeys, total);

// ——— Right column: horizontal bars for T3B, T2B, Ponderado ———
        html += '<div style="display:flex;flex-direction:column;gap:6px;min-width:200px;border-left:1px solid rgba(255,255,255,0.2);padding:0 8px;">';
        html += '<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:6px;">';
        const barItems = [
          { label: 'T3B', value: t3bVal },
          { label: 'T2B', value: t2bVal },
          { label: 'Ponderado', value: pondVal }
        ];
        barItems.forEach((item) => {
          const cssVal = item.value.toFixed(2);
          const p = item.value;
          const outside = p < 12;
          html += '<div style="display:flex;align-items:center;gap:8px;">';
          html += `<span style="color:#fff;font-size: var(--text-xs);font-weight: var(--font-semibold);width:60px;text-align:right;flex-shrink:0;">${item.label}</span>`;
          html += '<div style="flex:1;height:18px;background:rgba(255,255,255,0.12);border-radius:4px;overflow:visible;position:relative;">';
          html += `<div style="height:100%;width:${cssVal}%;background:#fff;border-radius:4px;display:flex;align-items:center;justify-content:flex-end;padding-right:4px;transition:width 0.3s;min-width:0;">`;
          if (!outside) {
            html += `<span style="color:#111827;font-size: var(--text-xs);font-weight: var(--font-bold);line-height:1;">${_fmt.formatDecimal(p, 2)} %</span>`;
          }
          html += '</div>';
          if (outside) {
            html += `<span style="position:absolute;left:100%;top:50%;transform:translateY(-50%);margin-left:4px;color:#fff;font-size: var(--text-xs);font-weight: var(--font-bold);white-space:nowrap;">${_fmt.formatDecimal(p, 2)} %</span>`;
          }
          html += '</div>';
          html += '</div>';
        });
        html += '</div>'; // close bars centering container
        html += '<div style="color:#fff;font-size: var(--text-md);font-weight: var(--font-medium);text-align:center;">Top Box y Ponderado</div>';
        html += '</div>'; // close right column
        html += '</div>'; // close flex container
        // raw=true justificado: html se construye con valores numericos (formatInteger/formatPctSimple)
        // y labels hardcodeados. Sin interpolacion de input de usuario sin escapar.
        if (_ttp) _ttp.show(e, html, true);
      });
      barItem.querySelector('.bar-container').addEventListener('mouseleave', () => _ttp?.hide());
      fragment.appendChild(barItem);
    });
    container.innerHTML = '';
    container.appendChild(fragment);
  }

  function updateTop3Filters() {
    const fac = $('filter-facultad-top3').value;
    const car = $('filter-carrera-top3').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-top3'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const categories = {
      academico: 'Académico',
      infraestructura: 'Infraestructura',
      tecnologia: 'Tecnología',
      adminBienestar: 'Administrativo y Bienestar',
      docencia: 'Docencia',
      desarrollo: 'Desarrollo Profesional',
    };
    const top3Data = {};
    Object.entries(categories).forEach(([key, nombre]) => {
      const dims = {};
      filtered
        .filter((r) => r.categoria === nombre)
        .forEach((r) => {
          if (!_rc.dimensionAplica(filtered, r.dimension)) return;
          if (!dims[r.dimension]) dims[r.dimension] = { total: 0, top3: 0 };
          dims[r.dimension].total += sumKeys(r, SAT_KEYS);
          dims[r.dimension].top3 += sumKeys(r, SAT_TOP3_KEYS);
        });
      top3Data[key] = Object.entries(dims)
        .map(([dim, val]) => ({ dim, pct: val.total ? (val.top3 / val.total) * 100 : 0 }))
        .sort((a, b) => b.pct - a.pct);
    });

    renderTop3Bars('chart-academico', top3Data.academico);
    renderTop3Bars('chart-infraestructura', top3Data.infraestructura);
    renderTop3Bars('chart-tecnologia', top3Data.tecnologia);
    renderTop3Bars('chart-admin-bienestar', top3Data.adminBienestar);
    renderTop3Bars('chart-docencia', top3Data.docencia);
    renderTop3Bars('chart-desarrollo', top3Data.desarrollo);

    ['chart-docencia', 'chart-desarrollo'].forEach((id) => {
      const chart = $(id);
      if (chart && chart.children.length === 0) {
        const card = chart.closest('.card');
        if (card) card.style.display = 'none';
      } else if (chart) {
        const card = chart.closest('.card');
        if (card) card.style.display = '';
      }
    });
  }

  function renderRadarIndependiente() {
    const fac = $('filter-facultad-radar').value;
    const car = $('filter-carrera-radar').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-radar'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);

    if (_rc) {
      _rc.render({
        svgId: 'radar-chart',
        filteredDimensions: filtered,
        rawDimensions: cache.dimensiones,
        fac,
        car,
        cic,
      });
    }
  }

  // ==================== SECCIÓN DETALLADO ====================
  function renderPreguntas() {
    const fac = $('filter-facultad-preguntas').value;
    const car = $('filter-carrera-preguntas').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-preguntas'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) {
        dimMap[r.dimension] = {
          categoria: r.categoria,
          totSat: 0,
          muySat: 0,
          sat: 0,
          insat: 0,
          totInsat: 0,
        };
      }
      dimMap[r.dimension].totSat += r['Totalmente satisfecho'] || 0;
      dimMap[r.dimension].muySat += r['Muy satisfecho'] || 0;
      dimMap[r.dimension].sat += r['Satisfecho'] || 0;
      dimMap[r.dimension].insat += r['Insatisfecho'] || 0;
      dimMap[r.dimension].totInsat += r['Totalmente insatisfecho'] || 0;
      dimMap[r.dimension].encuestas = (dimMap[r.dimension].encuestas || 0) + (r.total ?? r.count ?? 1);
    });

    const data = Object.entries(dimMap)
      .map(([dim, val]) => {
        const total = val.totSat + val.muySat + val.sat + val.insat + val.totInsat;
        const top3 = val.totSat + val.muySat + val.sat;
        // Anchos en decimal directo para que todos los segmentos se rendericen
        // (un valor de 0.33% no desaparezca a 0% por Math.round). La suma de
        // los 5 anchos es siempre 100% porque total = suma de los 5 conteos.
        const p1 = total > 0 ? (val.totSat / total) * 100 : 0;
        const p2 = total > 0 ? (val.muySat / total) * 100 : 0;
        const p3 = total > 0 ? (val.sat / total) * 100 : 0;
        const p4 = total > 0 ? (val.insat / total) * 100 : 0;
        const p5 = total > 0 ? (val.totInsat / total) * 100 : 0;
        return {
          dimension: dim,
          categoria: val.categoria,
          encuestas: val.encuestas || val.totSat + val.muySat + val.sat + val.insat + val.totInsat,
          top3box: total > 0 ? ((top3 / total) * 100).toFixed(2) : '0.00',
          top2box: total > 0 ? (((val.totSat + val.muySat) / total) * 100).toFixed(2) : '0.00',
          ponderado: total > 0 ? (
            ((5 * val.totSat + 4 * val.muySat + 3 * val.sat + 2 * val.insat + 1 * val.totInsat) / total) / 5 * 100
          ).toFixed(2) : '0.00',
          totSat: val.totSat,
          muySat: val.muySat,
          sat: val.sat,
          insat: val.insat,
          totInsat: val.totInsat,
          total,
          pctTotSat: p1,
          pctMuySat: p2,
          pctSat: p3,
          pctInsat: p4,
          pctTotInsat: p5,
        };
      })
      .filter((item) => parseFloat(item.top3box) > 0)
      .sort((a, b) => parseFloat(b.top3box) - parseFloat(a.top3box));

    const tbody = $('tbody-preguntas');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const catCorta =
        item.categoria === 'Administrativo y Bienestar' ? 'Servicios' :
        item.categoria === 'Desarrollo Profesional' ? 'Desarrollo' :
        item.categoria;
      const heatClass =
        parseFloat(item.top3box) >= META_CSAT ? 'heat-high' :
        parseFloat(item.top3box) >= 80 ? 'heat-medium' : 'heat-low';
      const heatClassT2 =
        parseFloat(item.top2box) >= META_CSAT ? 'heat-high' :
        parseFloat(item.top2box) >= 80 ? 'heat-medium' : 'heat-low';

      tr.innerHTML = `
        <td>${_fmt.formatDimensionName(item.dimension)}</td>
        <td class="text-center">${_fmt.formatInteger(item.encuestas)}</td>
        <td class="text-center"><span class="heatmap-cell ${heatClass}">${_fmt.formatPercent(parseFloat(item.top3box), 2)}</span></td>
        <td class="text-center" style="font-weight:var(--font-bold)">${_fmt.formatScore(parseFloat(item.top2box), 2)}</td>
        <td class="text-center" style="font-weight:var(--font-bold)">${_fmt.formatScore(parseFloat(item.ponderado), 2)}</td>
        <td class="text-center">${_san.escapeHTML(catCorta)}</td>
        <td>
          <div class="distribution-bar animated">
            <div class="distribution-segment" style="width:${item.pctTotSat}%;background:var(--gray-800);" data-label="Totalmente satisfecho" data-value="${_fmt.formatInteger(item.totSat)} (${_fmt.formatPctDecimal(item.totSat, item.total)})"></div>
            <div class="distribution-segment" style="width:${item.pctMuySat}%;background:var(--gray-500);" data-label="Muy satisfecho" data-value="${_fmt.formatInteger(item.muySat)} (${_fmt.formatPctDecimal(item.muySat, item.total)})"></div>
            <div class="distribution-segment" style="width:${item.pctSat}%;background:var(--gray-300);color:var(--gray-700);" data-label="Satisfecho" data-value="${_fmt.formatInteger(item.sat)} (${_fmt.formatPctDecimal(item.sat, item.total)})"></div>
            <div class="distribution-segment" style="width:${item.pctInsat}%;background:var(--ulima-orange);" data-label="Insatisfecho" data-value="${_fmt.formatInteger(item.insat)} (${_fmt.formatPctDecimal(item.insat, item.total)})"></div>
            <div class="distribution-segment" style="width:${item.pctTotInsat}%;background:var(--ulima-red);" data-label="Totalmente insatisfecho" data-value="${_fmt.formatInteger(item.totInsat)} (${_fmt.formatPctDecimal(item.totInsat, item.total)})"></div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.distribution-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          if (_ttp) _ttp.show(e, `<table style="border-collapse:collapse;font-size: var(--text-sm);"><tr><th style="text-align:left;padding:2px 6px;border-bottom:1px solid #ccc;">Escala de Satisfacción</th><th style="text-align:right;padding:2px 6px;border-bottom:1px solid #ccc;">Respuestas</th></tr><tr><td style="padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${seg.dataset.label}</td><td style="text-align:right;padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${seg.dataset.value}</td></tr></table>`, true);
        });
        seg.addEventListener('mouseleave', () => _ttp?.hide());
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  function renderDetalleCarreras() {
    const fac = $('filter-facultad-detalle').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-detalle'));
    const filteredIds = filtrarDatos(cache.ids, fac, null, cic);
    const countsMap = {};
    filteredIds.forEach((r) => {
      countsMap[r.carrera] = (countsMap[r.carrera] || 0) + (r.total ?? r.count);
    });

    const hasCiclo = cache.npsCicloCarrera?.length > 0;
    const npsSource = hasCiclo ? cache.npsCicloCarrera : cache.npsCarrera;
    const csatSource = hasCiclo ? cache.csatCicloCarrera : cache.csatCarrera;

    const npsMap = {};
    const filteredNps = filtrarDatos(npsSource || [], fac, null, cic);
    filteredNps.forEach((r) => {
      if (!npsMap[r.carrera]) npsMap[r.carrera] = { prom: 0, pas: 0, det: 0 };
      npsMap[r.carrera].prom += r.Promotores ?? r.promotores ?? 0;
      npsMap[r.carrera].pas += r.Pasivos ?? r.pasivos ?? 0;
      npsMap[r.carrera].det += r.Detractores ?? r.detractores ?? 0;
    });

    const csatMap = {};
    const filteredCsat = filtrarDatos(csatSource || [], fac, null, cic);
    filteredCsat.forEach((r) => {
      if (!csatMap[r.carrera]) csatMap[r.carrera] = { t3b: 0, total: 0 };
      const t3b = sumKeys(r, SAT_TOP3_KEYS);
      const total = t3b + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
      csatMap[r.carrera].t3b += t3b;
      csatMap[r.carrera].total += total;
    });

    let npsRef = 0;
    let csatRef = 0;
    {
      let prom = 0, pas = 0, det = 0;
      Object.values(npsMap).forEach((val) => {
        prom += val.prom;
        pas += val.pas;
        det += val.det;
      });
      const total = prom + pas + det;
      npsRef = total > 0 ? ((prom - det) / total) * 100 : 0;
    }
    {
      let tt = 0, tr = 0;
      Object.values(csatMap).forEach((val) => {
        tt += val.t3b;
        tr += val.total;
      });
      csatRef = tr > 0 ? (tt / tr) * 100 : csatScoreGlobal;
    }
    DOM.detallePromedioRef.textContent = `(${_fmt.formatDecimal(csatRef, 2)} %)`;
    DOM.detallePromedioNpsRef.textContent = `(${_fmt.formatDecimal(npsRef, 2)})`;

    const data = Object.entries(countsMap)
      .map(([carrera, encuestas]) => {
        const npsVal = npsMap[carrera];
        const csatVal = csatMap[carrera];
        const npsT = npsVal ? npsVal.prom + npsVal.pas + npsVal.det : 0;
        const npsS = npsT > 0 ? ((npsVal.prom - npsVal.det) / npsT) * 100 : 0;
        const csatS = csatVal?.total > 0 ? (csatVal.t3b / csatVal.total) * 100 : 0;
        return {
          carrera,
          encuestas,
          nps: npsS,
          csat: csatS,
          vsPromCsat: csatS - csatRef,
          vsPromNps: npsS - npsRef,
        };
      })
      .sort((a, b) => a.carrera.localeCompare(b.carrera));

    const tbody = $('tbody-detalle');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const vsCsatTxt =
        item.vsPromCsat >= 0
          ? `<span style="color:var(--success-text);font-weight: var(--font-semibold);">+${_fmt.formatInteger(Math.round(item.vsPromCsat))}</span>`
          : `<span style="color:var(--ulima-red);font-weight: var(--font-semibold);">${_fmt.formatInteger(Math.round(item.vsPromCsat))}</span>`;

      const vsNpsTxt =
        item.vsPromNps >= 0
          ? `<span style="color:var(--success-text);font-weight: var(--font-semibold);">+${_fmt.formatInteger(Math.round(item.vsPromNps))}</span>`
          : `<span style="color:var(--ulima-red);font-weight: var(--font-semibold);">${_fmt.formatInteger(Math.round(item.vsPromNps))}</span>`;

      tr.innerHTML = `
        <td>${_san.escapeHTML(item.carrera)}</td>
        <td class="text-center">${_fmt.formatInteger(item.encuestas)}</td>
        <td class="text-center" style="font-weight: var(--font-bold);">${_fmt.formatPercent(item.csat, 2)}</td>
        <td class="text-center">${vsCsatTxt}</td>
        <td class="text-center" style="font-weight: var(--font-bold);">${_fmt.formatDecimal(item.nps, 2)}</td>
        <td class="text-center">${vsNpsTxt}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  function renderVisibilidad() {
    const fac = $('filter-facultad-visibilidad').value;
    const car = $('filter-carrera-visibilidad').value;
    const cic = _dh.getSelectedValues($('filter-ciclo-visibilidad'));
    const filtered = filtrarDatos(cache.dimensiones, fac, car, cic);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) dimMap[r.dimension] = { noConozco: 0, noUtilizo: 0, conoce: 0, encuestas: 0 };
      dimMap[r.dimension].noConozco += r['No conozco'] || 0;
      dimMap[r.dimension].noUtilizo += r['No utilizo'] || 0;
      dimMap[r.dimension].conoce += sumKeys(r, SAT_KEYS);
      dimMap[r.dimension].encuestas += (r.total ?? r.count ?? 0);
    });
    const data = Object.entries(dimMap)
      .filter(([, val]) => val.noConozco > 0 || val.noUtilizo > 0)
      .map(([dim, val]) => {
        const total = val.noConozco + val.noUtilizo + val.conoce;
        return {
          dimension: dim,
          encuestas: val.encuestas || val.noConozco + val.noUtilizo + val.conoce,
          noConozco: val.noConozco,
          noUtilizo: val.noUtilizo,
          conoce: val.conoce,
          pctNoConozco: total > 0 ? (val.noConozco / total) * 100 : 0,
          pctNoUtilizo: total > 0 ? (val.noUtilizo / total) * 100 : 0,
          pctConoce: total > 0 ? (val.conoce / total) * 100 : 0,
          total,
        };
      })
      .sort((a, b) => a.pctNoConozco + a.pctNoUtilizo - (b.pctNoConozco + b.pctNoUtilizo));

    const tbody = $('tbody-visibilidad');
    if (!tbody) return;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${_fmt.formatDimensionName(item.dimension)}</td>
        <td class="text-center">${_fmt.formatInteger(item.encuestas)}</td>
        <td class="text-center">${_fmt.formatInteger(item.noConozco)} (${_fmt.formatDecimal(item.pctNoConozco, 2)} %)</td>
        <td class="text-center">${_fmt.formatInteger(item.noUtilizo)} (${_fmt.formatDecimal(item.pctNoUtilizo, 2)} %)</td>
        <td>
          <div class="visibility-bar animated">
            <div class="visibility-segment no-conozco" style="width:${item.pctNoConozco}%;" data-label="No conozco" data-value="${_fmt.formatInteger(item.noConozco)} (${_fmt.formatPctDecimal(item.noConozco, item.total)})"></div>
            <div class="visibility-segment no-utilizo" style="width:${item.pctNoUtilizo}%;" data-label="No utilizo" data-value="${_fmt.formatInteger(item.noUtilizo)} (${_fmt.formatPctDecimal(item.noUtilizo, item.total)})"></div>
            <div class="visibility-segment conocido"   style="width:${item.pctConoce}%;"    data-label="Conozco/Utilizo" data-value="${_fmt.formatInteger(item.conoce)} (${_fmt.formatPctDecimal(item.conoce, item.total)})"></div>
          </div>
        </td>
      `;
      tr.querySelectorAll('.visibility-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          if (_ttp) _ttp.show(e, `<table style="border-collapse:collapse;font-size: var(--text-sm);"><tr><th style="text-align:left;padding:2px 6px;border-bottom:1px solid #ccc;">Opción</th><th style="text-align:right;padding:2px 6px;border-bottom:1px solid #ccc;">Respuestas</th></tr><tr><td style="padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${seg.dataset.label}</td><td style="text-align:right;padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">${seg.dataset.value}</td></tr></table>`, true);
        });
        seg.addEventListener('mouseleave', () => _ttp?.hide());
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    updateInsightAtencion(data, fac, car, cic);
  }

  function updateInsightAtencion(data, fac, car, cic) {
    if (!DOM.insightAtencion || !data.length) {
      if (DOM.insightAtencion) DOM.insightAtencion.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const sorted = [...data].sort((a, b) => b.pctNoConozco + b.pctNoUtilizo - (a.pctNoConozco + a.pctNoUtilizo));
    const criticos = sorted.filter((d) => d.pctNoConozco + d.pctNoUtilizo >= 50);
    const moderados = sorted.filter((d) => {
      const sumVal = d.pctNoConozco + d.pctNoUtilizo;
      return sumVal >= 25 && sumVal < 50;
    });
    const hayFiltro = fac || car || (Array.isArray(cic) ? cic.length > 0 : cic);
    const contexto = hayFiltro ? [fac, car, Array.isArray(cic) ? cic.join(', ') : cic].filter(Boolean).join(' · ') : '';
    const cleanContexto = _san.escapeHTML(contexto);
    const fmtP = (v) => _fmt.formatDecimal(v, 2) + ' %';
    const fmtD = (d) => _san.escapeHTML(_fmt.formatDimensionName(d));
    let txt = '';

    if (hayFiltro) {
      txt += `<strong style="font-size: var(--text-sm);text-transform:uppercase;letter-spacing:1px;">${cleanContexto}</strong><br>`;
      if (criticos.length) {
        txt += `${criticos.length === 1 ? 'El servicio con <strong>menor visibilidad</strong> es' : 'Los servicios con <strong>menor visibilidad</strong> son'} `;
        txt += criticos
          .slice(0, 3)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(', ');
        txt += `. En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones tienen más del 50 % de desconocimiento o no uso.`;
      } else if (moderados.length) {
        txt += `No hay servicios con desconocimiento crítico (>50 %). Las dimensiones con mayor oportunidad son `;
        txt += moderados
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(' y ');
        txt += `.`;
      } else {
        txt += `Los servicios presentan niveles aceptables de visibilidad. Las dimensiones con mayor margen de mejora son `;
        txt += sorted
          .slice(0, 2)
          .map((d) => `<strong>${fmtD(d.dimension)}</strong> (${fmtP(d.pctNoConozco)} · No conozco + ${fmtP(d.pctNoUtilizo)} · No utilizo)`)
          .join(' y ');
        txt += `.`;
      }
    } else {
      if (sorted.length >= 2) {
        const [first, second] = sorted;
        txt += `<strong>${fmtD(first.dimension)}</strong> (${fmtP(first.pctNoConozco)} · No conozco + ${fmtP(first.pctNoUtilizo)} · No utilizo) y `;
        txt += `<strong>${fmtD(second.dimension)}</strong> (${fmtP(second.pctNoConozco)} · No conozco + ${fmtP(second.pctNoUtilizo)} · No utilizo) `;
        txt += `son las que presentan <strong>menor visibilidad</strong>.`;
        if (criticos.length) {
          txt += ` En total, <strong>${criticos.length}</strong> de ${data.length} dimensiones superan el 50 % de desconocimiento o no uso.`;
        }
      } else if (sorted.length === 1) {
        const [first] = sorted;
        txt += `<strong>${fmtD(first.dimension)}</strong> (${fmtP(first.pctNoConozco)} · No conozco + ${fmtP(first.pctNoUtilizo)} · No utilizo) es la que presenta <strong>menor visibilidad</strong>.`;
      }
    }
    DOM.insightAtencion.innerHTML = txt;
  }


  function setupSentimientoFilters() {
    if (_fc && _sv) {
      _sv.init(cache.sentimiento, cache.dashboard?.resumen?.encuestas, cache.dashboard?._export, cache.dashboard?.nps);
      // Se eliminaron todos los filtros de análisis cualitativo, así que llamamos directamente a la renderización
      _sv.updateMacro();
      _sv.updateAspectos();
      _sv.updateNpsCarrera();
      _sv.updateDetalle();
    }
  }

  // ==================== BARRA DE PROGRESO ====================
  function setupProgressBar() {
    if (_pb) _pb.init();
  }

  // ==================== INICIALIZACIÓN ====================
  async function init() {
    // Mostrar estado de carga en los insights mientras se cargan los datos
    const loadingEls = document.querySelectorAll('.insight-text');
    loadingEls.forEach((el) => {
      if (el.textContent === 'Cargando...') el.textContent = 'Cargando...';
    });

    if (!(await loadAllData())) {
      console.error('No se pudieron cargar los datos del dashboard.');
      // Los insights se quedan con el texto de carga y el banner muestra el error
      DOM.insightHallazgos.textContent = 'Error al cargar los datos. Verifica la conexión o contacta al administrador.';
      if (DOM.insightFortaleza) DOM.insightFortaleza.textContent = 'Datos no disponibles.';
      if (DOM.insightAtencion) DOM.insightAtencion.textContent = 'Datos no disponibles.';
      return;
    }

    const tieneDatosCualitativos =
      cache.sentimiento &&
      cache.sentimiento.resumen &&
      cache.sentimiento.resumen.total_con_comentario > 0 &&
      cache.sentimiento.topicos &&
      cache.sentimiento.topicos.length > 0;

    // Ocultar ciclo si el período no lo contiene
    if (cache.filtros && !cache.filtros.has_ciclo) {
      document.querySelectorAll('.filter-ciclo-actions').forEach((el) => {
        el.style.display = 'none';
      });
      // Y la columna "Ciclo" del explorador de comentarios
      const tablaExplorador = document.getElementById('tabla-explorador-comentarios');
      if (tablaExplorador) tablaExplorador.classList.add('sin-ciclo');
    }

    if (!tieneDatosCualitativos) {
      const secSentimiento = document.getElementById('cualitativo');
      if (secSentimiento) secSentimiento.style.display = 'none';

      const navLinkSentimiento = document.querySelector('.nav-links a[href="#cualitativo"]');
      if (navLinkSentimiento) {
        const liSentimiento = navLinkSentimiento.closest('li');
        if (liSentimiento) liSentimiento.style.display = 'none';
        else navLinkSentimiento.style.display = 'none';
      }
    }

    renderEjecutivo();

    // Enlazar los controladores de filtros usando el módulo FilterController
    if (_fc) {
      _fc.setup('top3', cache.filtros, updateTop3Filters);
      _fc.setup('radar', cache.filtros, renderRadarIndependiente);
      _fc.setup('preguntas', cache.filtros, renderPreguntas);
      _fc.setup('detalle', cache.filtros, renderDetalleCarreras);
      _fc.setup('visibilidad', cache.filtros, renderVisibilidad);
    }

    if (tieneDatosCualitativos) {
      setupSentimientoFilters();
    }

    setupProgressBar();

    // Redimensionamiento Responsivo
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        adjustSegmentLabels('#nps-bar');
        adjustSegmentLabels('#csat-bar');
      }, 250);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ── Public API ─────────────────────────────────────────────
  return {
    init,
    reload: loadAllData,
    cache,
    DOM,
    filtrarDatos,
    renderEjecutivo,
    renderNPSBar,
    renderCSATBar,
    updateTop3Filters,
    renderRadarIndependiente,
    renderPreguntas,
    renderDetalleCarreras,
    renderVisibilidad,
    updateInsightAtencion,
    showError,
    hideError,
  };
})();

window.SurveyDashboard = SurveyDashboard;
