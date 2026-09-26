/* ============================================================
   SURVEY PORTAL SURVEY — Vista 1.0 (Estudiantes Pregrado) del
   portal v5.0: KPIs, distribuciones CSAT/NPS, hallazgos,
   top3 por categoría, radar y tabla detalle.
   Expone window.SurveyPortalSurvey.
   Depende de SurveyPortalCore, SurveyPortalData,
   SurveyPortalFilters, SurveyPortalDashboard y SurveyPortalRadar.
   NOTA: showBarTooltip/hideBarTooltip usan un tooltip propio
   (#barTooltip.bar-tooltip) porque SurveyTooltip externo usa
   #tooltip.tooltip con estilos que no están en el portal.
   ============================================================ */
(function () {
  'use strict';

  var _core = window.SurveyPortalCore;
  var _data = window.SurveyPortalData;
  var _filters = window.SurveyPortalFilters;
  var _dashboard = window.SurveyPortalDashboard;
  var _dh = window.SurveyDOMHelpers;
  var esc = _core.esc;
  var fmtNum = _core.fmtNum;
  var $ = _dh.$;

  // Meta de satisfacción (desde constants.js, fuente canónica)
  const META_CSAT = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_CSAT) ?? 93;
  const META_PONDERADO = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_PONDERADO) ?? 80;

  // ── Top 3 por categoría (réplica index.html) ──
  const top3Config = [
    { titulo: 'Académico', id: 'chart-academico', categoria: 'Académico' },
    { titulo: 'Servicios al Estudiante', id: 'chart-admin-bienestar', categoria: 'Administrativo y Bienestar' },
    { titulo: 'Docencia', id: 'chart-docencia', categoria: 'Docencia' },
    { titulo: 'Tecnología', id: 'chart-tecnologia', categoria: 'Tecnología' },
    { titulo: 'Desarrollo Profesional', id: 'chart-desarrollo', categoria: 'Desarrollo Profesional' },
    { titulo: 'Infraestructura', id: 'chart-infraestructura', categoria: 'Infraestructura' }
  ];

  function showBarTooltip(e, text) {
    let tip = document.getElementById('barTooltip');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'barTooltip';
      tip.className = 'bar-tooltip';
      document.body.appendChild(tip);
    }
    tip.textContent = text;
    tip.style.display = 'block';
    const x = e.clientX + 12;
    const y = e.clientY + 12;
    tip.style.left = (x + tip.offsetWidth > window.innerWidth ? e.clientX - tip.offsetWidth - 12 : x) + 'px';
    tip.style.top = (y + tip.offsetHeight > window.innerHeight ? e.clientY - tip.offsetHeight - 12 : y) + 'px';
  }

  function hideBarTooltip() {
    const tip = document.getElementById('barTooltip');
    if (tip) tip.style.display = 'none';
  }

  function initBarLabelTooltips(container) {
    const labels = container.querySelectorAll('.bar-label');
    labels.forEach(function (label) {
      label.dataset.full = label.textContent;
      const updateClipped = function () {
        const span = label.querySelector('.bar-label-text') || label;
        label._barClipped = span.scrollWidth > span.clientWidth + 1;
      };
      updateClipped();
      label.addEventListener('mousemove', function (e) {
        if (!label._barClipped) return;
        showBarTooltip(e, label.dataset.full);
      });
      label.addEventListener('mouseleave', hideBarTooltip);
      if (!window.__barTooltipResizeBound) {
        window.__barTooltipResizeBound = true;
        let t;
        window.addEventListener('resize', function () {
          clearTimeout(t);
          t = setTimeout(function () {
            document.querySelectorAll('.bar-item .bar-label').forEach(function (l) {
              const span = l.querySelector('.bar-label-text') || l;
              l._barClipped = span.scrollWidth > span.clientWidth + 1;
            });
          }, 150);
        });
      }
    });
  }

  function renderTop3Bars(containerId, data) {
    const container = $(containerId);
    if (!container) return;
    const visible = (data || []).filter(function (item) { return item && item.t3b_pct !== 0 && item.t3b_pct !== null && item.t3b_pct !== undefined; });
    container.innerHTML = visible.map(function (item, index) {
      const pct = item.t3b_pct;
      const barClass = pct >= META_CSAT ? 'high' : pct >= META_PONDERADO ? 'medium' : 'low';
      return '<div class="bar-item">' +
        '<div class="bar-label"><span class="bar-label-text">' + window.SurveyFormatters.formatDimensionName(item.dimension) + '</span></div>' +
        '<div class="bar-container">' +
          '<div class="bar-fill animated ' + barClass + '" style="width:' + pct + '%;animation-delay:' + (index * 0.08) + 's">' +
            '<span class="bar-value">' + fmtNum(pct, 2) + ' %</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('');
    initBarLabelTooltips(container);
  }

  function renderTop3Cards(dims) {
    const source = dims || (_data.getSurveyData() && _data.getSurveyData().dims) || [];
    top3Config.forEach(function (c) {
      const chartEl = $(c.id);
      if (!chartEl) return;
      const data = source
        .filter(function (d) { return d.categoria === c.categoria; })
        .sort(function (a, b) { return b.t3b_pct - a.t3b_pct; });
      renderTop3Bars(c.id, data);
      const card = chartEl.closest('.card');
      if (card) card.style.display = data.length ? '' : 'none';
    });
  }

  function tablaFilaHtml(item) {
    const fmt = window.SurveyFormatters || {};
    const vsCsatTxt = item.vsPromCsat >= 0
      ? '<span style="color:var(--success-text);font-weight: var(--font-semibold);">+' + fmt.formatInteger(Math.round(item.vsPromCsat)) + '</span>'
      : '<span style="color:var(--ulima-red);font-weight: var(--font-semibold);">' + fmt.formatInteger(Math.round(item.vsPromCsat)) + '</span>';
    const vsNpsTxt = item.vsPromNps >= 0
      ? '<span style="color:var(--success-text);font-weight: var(--font-semibold);">+' + fmt.formatInteger(Math.round(item.vsPromNps)) + '</span>'
      : '<span style="color:var(--ulima-red);font-weight: var(--font-semibold);">' + fmt.formatInteger(Math.round(item.vsPromNps)) + '</span>';
    return '<tr>' +
      '<td>' + esc(item.carrera) + '</td>' +
      '<td class="text-center">' + fmt.formatInteger(item.encuestas) + '</td>' +
      '<td class="text-center" style="font-weight: var(--font-bold);">' + fmt.formatPercent(item.csat_score, 2) + '</td>' +
      '<td class="text-center">' + vsCsatTxt + '</td>' +
      '<td class="text-center" style="font-weight: var(--font-bold);">' + fmt.formatDecimal(item.nps_score, 2) + '</td>' +
      '<td class="text-center">' + vsNpsTxt + '</td>' +
    '</tr>';
  }

  function renderTablaDetalle() {
    const tbody = $('tbody-detalle');
    if (!tbody) return;
    const det = _data.getDetalleData();
    const fmt = window.SurveyFormatters || {};
    const refCsatEl = $('detalle-promedio-ref');
    if (refCsatEl) refCsatEl.textContent = '(' + fmt.formatDecimal(det.csatRef, 2) + ' %)';
    const refNpsEl = $('detalle-promedio-nps-ref');
    if (refNpsEl) refNpsEl.textContent = '(' + fmt.formatDecimal(det.npsRef, 2) + ')';
    tbody.innerHTML = det.rows.map(tablaFilaHtml).join('');
  }

  // ── Nivel de satisfacción detallado (tabla por dimensión con distribución) ──
  // Réplica fiel de index (dashboard.js renderPreguntas): agrupa dimensiones.json
  // por dimensión, calcula Top 3 Box / Top 2 Box / Ponderado y pinta segmentos.
  function renderPreguntas() {
    const tbody = $('tbody-preguntas');
    if (!tbody) return;
    const g = window.__surveyFilter.preguntas || { fac: '', car: '', ciclos: '' };
    const rawCic = g.ciclos;
    // Normalizar array vacío a '' (igual que __applyFilter): un array vacío
    // en filtrarDatos filtra TODO (truthy en JS); '' o null = sin restricción.
    const ciclos = (Array.isArray(rawCic) && rawCic.length) ? rawCic : '';
    const raw = _data.getSurveyData().dimensiones_raw || [];
    const filtered = _data.filtrarDatos(raw, g.fac, g.car, ciclos);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) {
        dimMap[r.dimension] = {
          categoria: r.categoria, totSat: 0, muySat: 0, sat: 0, insat: 0, totInsat: 0,
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
        const p1 = total > 0 ? (val.totSat / total) * 100 : 0;
        const p2 = total > 0 ? (val.muySat / total) * 100 : 0;
        const p3 = total > 0 ? (val.sat / total) * 100 : 0;
        const p4 = total > 0 ? (val.insat / total) * 100 : 0;
        const p5 = total > 0 ? (val.totInsat / total) * 100 : 0;
        return {
          dimension: dim,
          categoria: val.categoria,
          encuestas: val.encuestas || total,
          top3box: total > 0 ? ((top3 / total) * 100).toFixed(2) : '0.00',
          top2box: total > 0 ? (((val.totSat + val.muySat) / total) * 100).toFixed(2) : '0.00',
          ponderado: total > 0 ? (((5 * val.totSat + 4 * val.muySat + 3 * val.sat + 2 * val.insat + 1 * val.totInsat) / total) / 5 * 100).toFixed(2) : '0.00',
          totSat: val.totSat, muySat: val.muySat, sat: val.sat, insat: val.insat, totInsat: val.totInsat,
          total,
          pctTotSat: p1, pctMuySat: p2, pctSat: p3, pctInsat: p4, pctTotInsat: p5,
        };
      })
      .filter((item) => parseFloat(item.top3box) > 0)
      .sort((a, b) => parseFloat(b.top3box) - parseFloat(a.top3box));

    const fmt = window.SurveyFormatters || {};
    const esc = _core.esc;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      const catCorta =
        item.categoria === 'Administrativo y Bienestar' ? 'Servicios' :
        item.categoria === 'Desarrollo Profesional' ? 'Desarrollo' :
        item.categoria;
      const heatClass =
        parseFloat(item.top3box) >= META_CSAT ? 'heat-high' :
        parseFloat(item.top3box) >= META_PONDERADO ? 'heat-medium' : 'heat-low';
      const heatClassT2 =
        parseFloat(item.top2box) >= META_CSAT ? 'heat-high' :
        parseFloat(item.top2box) >= META_PONDERADO ? 'heat-medium' : 'heat-low';

      tr.innerHTML =
        '<td>' + (fmt.formatDimensionName ? fmt.formatDimensionName(item.dimension) : esc(item.dimension)) + '</td>' +
        '<td class="text-center">' + (fmt.formatInteger ? fmt.formatInteger(item.encuestas) : item.encuestas) + '</td>' +
        '<td class="text-center"><span class="heatmap-cell ' + heatClass + '">' + (fmt.formatPercent ? fmt.formatPercent(parseFloat(item.top3box), 2) : item.top3box + ' %') + '</span></td>' +
        '<td class="text-center" style="font-weight:var(--font-bold);">' + (fmt.formatScore ? fmt.formatScore(parseFloat(item.top2box), 2) : item.top2box + ' %') + '</td>' +
        '<td class="text-center" style="font-weight:var(--font-bold);">' + (fmt.formatScore ? fmt.formatScore(parseFloat(item.ponderado), 2) : item.ponderado + ' %') + '</td>' +
        '<td class="text-center">' + esc(catCorta) + '</td>' +
        '<td><div class="distribution-bar animated">' +
          '<div class="distribution-segment" style="width:' + item.pctTotSat + '%;background:var(--gray-800);" data-label="Totalmente satisfecho" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.totSat) : item.totSat) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.totSat, item.total) : '') + ')"></div>' +
          '<div class="distribution-segment" style="width:' + item.pctMuySat + '%;background:var(--gray-500);" data-label="Muy satisfecho" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.muySat) : item.muySat) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.muySat, item.total) : '') + ')"></div>' +
          '<div class="distribution-segment" style="width:' + item.pctSat + '%;background:var(--gray-300);color:var(--gray-700);" data-label="Satisfecho" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.sat) : item.sat) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.sat, item.total) : '') + ')"></div>' +
          '<div class="distribution-segment" style="width:' + item.pctInsat + '%;background:var(--ulima-orange);" data-label="Insatisfecho" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.insat) : item.insat) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.insat, item.total) : '') + ')"></div>' +
          '<div class="distribution-segment" style="width:' + item.pctTotInsat + '%;background:var(--ulima-red);" data-label="Totalmente insatisfecho" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.totInsat) : item.totInsat) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.totInsat, item.total) : '') + ')"></div>' +
        '</div></td>';
      tr.querySelectorAll('.distribution-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          const ttp = window.SurveyTooltip;
          if (ttp && ttp.show) ttp.show(e, '<table style="border-collapse:collapse;font-size: var(--text-sm);"><tr><th style="text-align:left;padding:2px 6px;border-bottom:1px solid #ccc;">Escala de Satisfacción</th><th style="text-align:right;padding:2px 6px;border-bottom:1px solid #ccc;">Respuestas</th></tr><tr><td style="padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">' + esc(seg.dataset.label) + '</td><td style="text-align:right;padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">' + seg.dataset.value + '</td></tr></table>', true);
        });
        seg.addEventListener('mouseleave', () => {
          const ttp = window.SurveyTooltip;
          if (ttp && ttp.hide) ttp.hide();
        });
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  }

  // ── Visibilidad de Servicios (réplica index.html renderVisibilidad) ──
  function renderVisibilidad() {
    const g = window.__surveyFilter.visibilidad || { fac: '', car: '', ciclos: '' };
    const rawCic = g.ciclos;
    const ciclos = (Array.isArray(rawCic) && rawCic.length) ? rawCic : '';
    const raw = _data.getSurveyData().dimensiones_raw || [];
    const filtered = _data.filtrarDatos(raw, g.fac, g.car, ciclos);
    const dimMap = {};
    filtered.forEach((r) => {
      if (!dimMap[r.dimension]) dimMap[r.dimension] = { noConozco: 0, noUtilizo: 0, conoce: 0, encuestas: 0 };
      dimMap[r.dimension].noConozco += r['No conozco'] || 0;
      dimMap[r.dimension].noUtilizo += r['No utilizo'] || 0;
      dimMap[r.dimension].conoce += (r['Totalmente satisfecho'] || 0) + (r['Muy satisfecho'] || 0) + (r['Satisfecho'] || 0) + (r['Insatisfecho'] || 0) + (r['Totalmente insatisfecho'] || 0);
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
    const fmt = window.SurveyFormatters || {};
    const esc = _core.esc;
    const fragment = document.createDocumentFragment();
    data.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + (fmt.formatDimensionName ? fmt.formatDimensionName(item.dimension) : esc(item.dimension)) + '</td>' +
        '<td class="text-center">' + (fmt.formatInteger ? fmt.formatInteger(item.encuestas) : item.encuestas) + '</td>' +
        '<td class="text-center">' + (fmt.formatInteger ? fmt.formatInteger(item.noConozco) : item.noConozco) + ' (' + (fmt.formatDecimal ? fmt.formatDecimal(item.pctNoConozco, 2) : item.pctNoConozco) + ' %)</td>' +
        '<td class="text-center">' + (fmt.formatInteger ? fmt.formatInteger(item.noUtilizo) : item.noUtilizo) + ' (' + (fmt.formatDecimal ? fmt.formatDecimal(item.pctNoUtilizo, 2) : item.pctNoUtilizo) + ' %)</td>' +
        '<td>' +
          '<div class="visibility-bar animated">' +
            '<div class="visibility-segment no-conozco" style="width:' + item.pctNoConozco + '%;" data-label="No conozco" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.noConozco) : item.noConozco) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.noConozco, item.total) : '') + ')"></div>' +
            '<div class="visibility-segment no-utilizo" style="width:' + item.pctNoUtilizo + '%;" data-label="No utilizo" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.noUtilizo) : item.noUtilizo) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.noUtilizo, item.total) : '') + ')"></div>' +
            '<div class="visibility-segment conocido" style="width:' + item.pctConoce + '%;" data-label="Conozco/Utilizo" data-value="' + (fmt.formatInteger ? fmt.formatInteger(item.conoce) : item.conoce) + ' (' + (fmt.formatPctDecimal ? fmt.formatPctDecimal(item.conoce, item.total) : '') + ')"></div>' +
          '</div>' +
        '</td>';
      tr.querySelectorAll('.visibility-segment').forEach((seg) => {
        seg.addEventListener('mousemove', (e) => {
          const ttp = window.SurveyTooltip;
          if (ttp && ttp.show) ttp.show(e, '<table style="border-collapse:collapse;font-size: var(--text-sm);"><tr><th style="text-align:left;padding:2px 6px;border-bottom:1px solid #ccc;">Opción</th><th style="text-align:right;padding:2px 6px;border-bottom:1px solid #ccc;">Respuestas</th></tr><tr><td style="padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">' + esc(seg.dataset.label) + '</td><td style="text-align:right;padding:2px 6px;border-bottom:1px solid #eee;vertical-align:middle;">' + seg.dataset.value + '</td></tr></table>', true);
        });
        seg.addEventListener('mouseleave', () => {
          const ttp = window.SurveyTooltip;
          if (ttp && ttp.hide) ttp.hide();
        });
      });
      fragment.appendChild(tr);
    });
    tbody.innerHTML = '';
    tbody.appendChild(fragment);

    updateInsightAtencion(data);
  }

  // ── Insight "Oportunidad de mejora" (réplica index.html updateInsightAtencion) ──
  function updateInsightAtencion(data) {
    const insight = $('insight-atencion');
    if (!insight || !data.length) {
      if (insight) insight.innerHTML = 'Sin datos suficientes para el análisis.';
      return;
    }
    const g = window.__surveyFilter.visibilidad || {};
    const fac = g.fac, car = g.car, cic = g.ciclos;
    const sorted = [...data].sort((a, b) => b.pctNoConozco + b.pctNoUtilizo - (a.pctNoConozco + a.pctNoUtilizo));
    const criticos = sorted.filter((d) => d.pctNoConozco + d.pctNoUtilizo >= 50);
    const moderados = sorted.filter((d) => {
      const sumVal = d.pctNoConozco + d.pctNoUtilizo;
      return sumVal >= 25 && sumVal < 50;
    });
    const hayFiltro = fac || car || (Array.isArray(cic) ? cic.length > 0 : cic);
    const contexto = hayFiltro ? [fac, car, Array.isArray(cic) ? cic.join(', ') : cic].filter(Boolean).join(' · ') : '';
    const esc = _core.esc;
    const fmt = window.SurveyFormatters || {};
    const fmtP = (v) => fmt.formatDecimal(v, 2) + ' %';
    const fmtD = (d) => esc(fmt.formatDimensionName ? fmt.formatDimensionName(d) : d);
    let txt = '';
    if (hayFiltro) {
      txt += '<strong style="font-size: var(--text-sm);text-transform:uppercase;letter-spacing:1px;">' + esc(contexto) + '</strong><br>';
      if (criticos.length) {
        txt += (criticos.length === 1 ? 'El servicio con <strong>menor visibilidad</strong> es' : 'Los servicios con <strong>menor visibilidad</strong> son') + ' ';
        txt += criticos
          .slice(0, 3)
          .map((d) => '<strong>' + fmtD(d.dimension) + '</strong> (' + fmtP(d.pctNoConozco) + ' · No conozco + ' + fmtP(d.pctNoUtilizo) + ' · No utilizo)')
          .join(', ');
        txt += '. En total, <strong>' + criticos.length + '</strong> de ' + data.length + ' dimensiones tienen más del 50 % de desconocimiento o no uso.';
      } else if (moderados.length) {
        txt += 'No hay servicios con desconocimiento crítico (>50 %). Las dimensiones con mayor oportunidad son ';
        txt += moderados
          .slice(0, 2)
          .map((d) => '<strong>' + fmtD(d.dimension) + '</strong> (' + fmtP(d.pctNoConozco) + ' · No conozco + ' + fmtP(d.pctNoUtilizo) + ' · No utilizo)')
          .join(' y ');
        txt += '.';
      } else {
        txt += 'Los servicios presentan niveles aceptables de visibilidad. Las dimensiones con mayor margen de mejora son ';
        txt += sorted
          .slice(0, 2)
          .map((d) => '<strong>' + fmtD(d.dimension) + '</strong> (' + fmtP(d.pctNoConozco) + ' · No conozco + ' + fmtP(d.pctNoUtilizo) + ' · No utilizo)')
          .join(' y ');
        txt += '.';
      }
    } else {
      if (sorted.length >= 2) {
        const [first, second] = sorted;
        txt += '<strong>' + fmtD(first.dimension) + '</strong> (' + fmtP(first.pctNoConozco) + ' · No conozco + ' + fmtP(first.pctNoUtilizo) + ' · No utilizo) y ';
        txt += '<strong>' + fmtD(second.dimension) + '</strong> (' + fmtP(second.pctNoConozco) + ' · No conozco + ' + fmtP(second.pctNoUtilizo) + ' · No utilizo) ';
        txt += 'son las que presentan <strong>menor visibilidad</strong>.';
        if (criticos.length) {
          txt += ' En total, <strong>' + criticos.length + '</strong> de ' + data.length + ' dimensiones superan el 50 % de desconocimiento o no uso.';
        }
      } else if (sorted.length === 1) {
        const [first] = sorted;
        txt += '<strong>' + fmtD(first.dimension) + '</strong> (' + fmtP(first.pctNoConozco) + ' · No conozco + ' + fmtP(first.pctNoUtilizo) + ' · No utilizo) es la que presenta <strong>menor visibilidad</strong>.';
      }
    }
    insight.innerHTML = txt;
  }

  async function renderSurveyView() {
    const svg = window.svg;
    const ICONS = window.ICONS;
    const D = _data.getSurveyData();
    if (!D || !D.resumen) {
      // Sin datos no se puede pintar el dashboard. Se registra el motivo y se
      // deja lo que ya haya en pantalla (portal.js muestra "en construccion"),
      // en lugar de lanzar una excepcion que congelaba el indicador de carga.
      console.error('[portal] renderSurveyView sin datos: no se renderiza el dashboard.');
      return;
    }
    const r = D.resumen;
    const nivel = _data.nivelDeFase(window.state.activePhaseId);
    const metaCardHtml = await _dashboard.renderMetaCard(window.state.activeFile, nivel);
    window.__surveyFilter = window.__surveyFilter || {
      top3: { fac: '', car: '', ciclos: [] },
      radar: { fac: '', car: '', ciclos: [], cats: [] },
      preguntas: { fac: '', car: '', ciclos: [] },
      detalle: { fac: '', ciclos: [] },
      visibilidad: { fac: '', car: '', ciclos: [] }
    };

    // KPIs ejecutivos (formato portal - tarjetas con barra superior + icono)
    const kpis = [
      { label: 'Nivel de Satisfacción', value: fmtNum(r.csat.score, 2) + ' %', color: 'var(--emerald)', icon: 'check-circle' },
      { label: 'Top 2 Box', value: fmtNum(r.csat.t2b_pct, 2) + ' %', color: '#666666', icon: 'trending-up' },
      { label: 'Promedio Ponderado', value: fmtNum(r.csat.ponderado, 2) + ' %', color: 'var(--amber)', icon: 'bar-chart' },
      { label: 'Índice de Promotores Netos', value: fmtNum(r.nps.score, 2), color: '#FF5117', icon: 'users' }
    ];
    if (r.empleabilidad && r.empleabilidad.score != null) {
      kpis.push({ label: 'Índice de Empleabilidad', value: fmtNum(r.empleabilidad.score, 2) + ' %', color: '#1A73E8', icon: 'graduation-cap' });
    }
    const kpiHtml = kpis.map(k =>
      '<div class="survey-kpi">' +
        '<div class="survey-kpi-bar-top" style="background:' + k.color + ';"></div>' +
        '<div class="survey-kpi-body">' +
          '<p class="survey-kpi-value" style="color:' + k.color + ';">' + k.value + '</p>' +
          '<p class="survey-kpi-label">' + k.label + '</p>' +
        '</div>' +
        '<div class="survey-kpi-icon" style="background:' + k.color + ';">' +
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:white;">' + ICONS[k.icon] + '</svg>' +
        '</div>' +
      '</div>'
    ).join('');

    // Filtros (3 grupos independientes + preguntas)
    const filtroTop3Html = _filters.buildFiltroHtml('top3');
    const filtroRadarHtml = _filters.buildFiltroHtml('radar');
    const filtroPreguntasHtml = _filters.buildFiltroHtml('preguntas');
    const filtroDetalleHtml = _filters.buildFiltroHtml('detalle');
    const filtroVisibilidadHtml = _filters.buildFiltroHtml('visibilidad');

    // ── DISTRIBUCIONES CSAT / NPS ──
    const distribucionesHtml =
        '<section class="survey-section">' +
          '<h3 class="survey-subsection-title">Distribución del Nivel de Satisfacción</h3>' +
          '<div class="csat-distribution">' +
            '<div class="csat-bar" id="csat-bar"></div>' +
            '<div class="legend" id="csat-legend"></div>' +
          '</div>' +
        '</section>' +
        '<section class="survey-section">' +
          '<h3 class="survey-subsection-title">Composición del Índice de Promotores Netos</h3>' +
          '<div class="csat-distribution">' +
            '<div class="csat-bar" id="nps-bar"></div>' +
            '<div class="legend" id="nps-legend"></div>' +
          '</div>' +
        '</section>';

    // ── Top 3 por categoría (réplica index.html) ──
    const top3CardsHtml = '<div class="grid-2" id="top3-cards">' +
      top3Config.map(c =>
        '<div class="card"><div class="card-title">' + esc(c.titulo) + '</div><div class="bar-chart" id="' + c.id + '"></div></div>'
      ).join('') +
      '</div>';

    const html = `
    ${metaCardHtml}

    <!-- ── EJECUTIVO ── -->
    <section class="survey-section">
      <h3 class="survey-section-title">${svg('bar-chart', 14)}Análisis Ejecutivo</h3>
      <div class="survey-kpi-grid">${kpiHtml}</div>
    </section>

    ${distribucionesHtml}

    <section class="survey-section">
      <div class="insight-box info">
        <div class="insight-title">Hallazgos</div>
        <p class="insight-text">Actualmente, <strong>+${fmtNum(D.hallazgos.csat_pct, 0)} %</strong> de estudiantes están satisfechos con la Universidad de Lima. El Índice de Promotores Netos, que es de <strong>+${fmtNum(D.hallazgos.nps_score, 0)}</strong>, posiciona a la institución en el rango "<strong>${esc(D.hallazgos.nps_tipo)}</strong>" a nivel global, pero <strong>${esc(D.hallazgos.tendencia)}</strong> conforme avanza la carrera: <strong>Inicial (${fmtNum(D.hallazgos.nps_etapas.Inicial, 2)})</strong> → <strong>Intermedio (${fmtNum(D.hallazgos.nps_etapas.Intermedio, 2)})</strong> → <strong>Avanzado (${fmtNum(D.hallazgos.nps_etapas.Avanzado, 2)})</strong>. Teniendo una diferencia de <strong>-${fmtNum(D.hallazgos.delta, 0)}</strong> puntos en el ciclo de vida estudiantil.
        </p>
      </div>
    </section>

    <!-- ── OPERATIVO ── -->
    <section class="survey-section">
      <h3 class="survey-section-title">${svg('gauge', 14)}Análisis Operativo</h3>
      <h3 class="survey-subsection-title">Nivel de Satisfacción</h3>
      ${filtroTop3Html}
      ${top3CardsHtml}
      <h3 class="survey-subsection-title">Radar General - Nivel de satisfacción</h3>
      ${filtroRadarHtml}
      <div class="card radar-container">
        <svg class="radar-svg" viewBox="-40 -40 600 600" preserveAspectRatio="xMidYMid meet" id="radar-chart" role="img" aria-label="Gráfico radar de satisfacción por dimensión"></svg>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:var(--gray-700);"></div>≥93 % (Fortaleza)</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--gray-400);"></div>80-92 % (Adecuado)</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--ulima-red);"></div><80 % (Atención)</div>
        </div>
      </div>
      <div class="insight-box success" aria-live="polite">
        <div class="insight-title">Fortalezas</div>
        <p class="insight-text" id="insight-fortaleza">Cargando...</p>
      </div>
    </section>

    <!-- ── DETALLADO ── -->
    <section class="survey-section">
      <h3 class="survey-section-title">${svg('table', 14)}Análisis Detallado</h3>
      <h3 class="survey-subsection-title">Nivel de satisfacción detallado</h3>
      ${filtroPreguntasHtml}
      <div class="survey-table-wrap">
        <table class="survey-table" id="tabla-preguntas">
          <thead><tr>
            <th style="width: 25%;">Dimensión</th>
            <th class="text-center" style="width: 12%;">Respuestas</th>
            <th class="text-center" style="width: 12%;">Top 3 Box</th>
            <th class="text-center" style="width: 12%;">Top 2 Box</th>
            <th class="text-center" style="width: 12%;">Ponderado</th>
            <th class="text-center" style="width: 12%;">Categoría</th>
            <th style="width: 15%;">Distribución</th>
          </tr></thead>
          <tbody id="tbody-preguntas"></tbody>
        </table>
      </div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-800);"></div> Totalmente satisfecho</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-500);"></div> Muy satisfecho</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-300);"></div> Satisfecho</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--ulima-orange);"></div> Insatisfecho</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--ulima-red);"></div> Totalmente insatisfecho</div>
      </div>
      <div class="insight-box warning">
        <div class="insight-title">Nota</div>
        <p class="insight-text">El <strong>Top 3 Box</strong> se calcula dividiendo la suma de las respuestas "<strong>Totalmente satisfecho</strong>", "<strong>Muy satisfecho</strong>" y "<strong>Satisfecho</strong>" entre el total de respuestas, excluyendo "<strong>No conozco</strong>", "<strong>No utilizo</strong>" y las respuestas <strong>vacías</strong>.</p>
      </div>
      <h3 class="survey-subsection-title">Detalle por Carrera</h3>
      ${filtroDetalleHtml}
      <div class="survey-table-wrap">
        <table class="survey-table" id="tabla-detalle" role="region" aria-label="NPS y CSAT por carrera">
          <caption class="sr-only">Detalle de NPS y CSAT por carrera</caption>
          <thead><tr>
            <th scope="col" style="width: 15%;">CARRERA</th>
            <th scope="col" class="text-center" style="width: 17%;">ENCUESTAS</th>
            <th scope="col" class="text-center" style="width: 17%;">Nivel de Satisfacción</th>
            <th scope="col" class="text-center" style="width: 17%;">VS PROMEDIO <span id="detalle-promedio-ref"></span></th>
            <th scope="col" class="text-center" style="width: 17%;">Índice de Promotores Netos</th>
            <th scope="col" class="text-center" style="width: 17%;">VS PROMEDIO <span id="detalle-promedio-nps-ref"></span></th>
          </tr></thead>
          <tbody id="tbody-detalle"></tbody>
        </table>
      </div>
    </section>

    <!-- ── VISIBILIDAD ── -->
    <section class="survey-section">
      <h3 class="survey-subsection-title">Visibilidad de Servicios (No conozco / No utilizo)</h3>
      ${filtroVisibilidadHtml}
      <div class="survey-table-wrap">
        <table class="survey-table" id="tabla-visibilidad" role="region" aria-label="Visibilidad de servicios">
          <caption class="sr-only">Visibilidad de servicios por carrera</caption>
          <thead><tr>
            <th scope="col" style="width: 35%;">DIMENSIÓN</th>
            <th scope="col" class="text-center" style="width: 15%;">RESPUESTAS</th>
            <th scope="col" class="text-center" style="width: 15%;">NO CONOZCO</th>
            <th scope="col" class="text-center" style="width: 15%;">NO UTILIZO</th>
            <th scope="col" class="text-center" style="width: 20%;">DISTRIBUCIÓN</th>
          </tr></thead>
          <tbody id="tbody-visibilidad"></tbody>
        </table>
      </div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-800);"></div> No conozco</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-500);"></div> No utilizo</div>
        <div class="legend-item"><div class="legend-dot" style="background: var(--gray-300);"></div> Conozco/Utilizo</div>
      </div>
      <div class="insight-box warning" aria-live="polite">
        <div class="insight-title">Oportunidad de mejora</div>
        <p class="insight-text" id="insight-atencion">Cargando...</p>
      </div>
    </section>

    <!-- ── CUALITATIVO ── -->
    <section class="survey-section" id="cualitativo-section">
      <h3 class="survey-section-title">${svg('message-square', 14)}ANÁLISIS CUALITATIVO</h3>
      <div class="kpi-grid" id="sentiment-kpis"></div>
      <h3 class="survey-subsection-title" style="margin-top: 32px;">Respuestas por sentimiento</h3>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Distribución de sentimientos</div>
          <div class="bar-chart" id="sentimiento-bar-chart"></div>
        </div>
        <div class="card">
          <div class="card-title">Ideas por segmento NPS</div>
          <div id="seg-nps-container"></div>
        </div>
      </div>
      <div class="grid-2" style="margin-top: 24px;">
        <div class="card" style="grid-column: 1 / -1;">
          <div class="card-title">Categorías — menciones totales</div>
          <div id="categorias-barras-container"></div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Aspectos más positivos</div>
          <div class="bar-chart" id="aspectos-positivos-container"></div>
        </div>
        <div class="card">
          <div class="card-title">Aspectos más negativos</div>
          <div class="bar-chart" id="aspectos-negativos-container"></div>
        </div>
        <div class="card">
          <div class="card-title">Intensidad en aspectos positivos</div>
          <div class="bar-chart" id="intensidad-positivos-container"></div>
        </div>
        <div class="card">
          <div class="card-title">Intensidad en aspectos negativos</div>
          <div class="bar-chart" id="intensidad-negativos-container"></div>
        </div>
      </div>
      <h3 class="survey-subsection-title" style="margin-top:32px;">Respuestas por carrera — distribución NPS completa</h3>
      <div class="table-scroll" style="margin-bottom: 24px;">
        <table class="survey-table" id="tabla-nps-carrera" role="region" aria-label="Distribucion NPS por carrera">
          <caption class="sr-only">Distribucion NPS completa por carrera</caption>
          <thead><tr>
            <th scope="col" style="width: 20%;">CARRERA</th>
            <th scope="col" class="text-center" style="width: 16%;">TEXTO ABIERTO</th>
            <th scope="col" class="text-center" style="width: 16%;">IDEAS ANALIZADAS</th>
            <th scope="col" class="text-center" style="width: 16%;">PROMOTORES</th>
            <th scope="col" class="text-center" style="width: 16%;">PASIVOS</th>
            <th scope="col" class="text-center" style="width: 16%;">DETRACTores</th>
          </tr></thead>
          <tbody id="tbody-nps-carrera"></tbody>
        </table>
      </div>
      <h3 class="survey-subsection-title" style="margin-top:32px;">Detalle de ideas</h3>
      <p style="color:var(--gray-500); font-size: var(--text-md); margin-bottom:12px; line-height:1.5;">
        Busque y filtre las respuestas textuales de los alumnos. La columna "Idea analizada" corrige faltas ortográficas y modismos comunes para facilitar su lectura rápida sin alterar su significado original.
      </p>
      <div class="filter-container" role="group" aria-label="Controles del explorador cualitativo" style="margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">
        <div class="filter-group" style="flex: 1; min-width: 200px;">
          <input type="text" id="explorador-search" class="filter-select" placeholder="Buscar palabras clave en comentarios..." style="width: 100%; padding: 6px 10px; border-radius: var(--radius-md); border: 1px solid var(--gray-300); font-size: var(--text-md); font-family: inherit; background-image: none; cursor: text;">
        </div>
        <div class="filter-group">
          <label class="filter-label" for="explorador-categoria">Tema Padre:</label>
          <select class="filter-select" id="explorador-categoria">
            <option value="">Todos los temas</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label" for="explorador-sentimiento">Sentimiento:</label>
          <select class="filter-select" id="explorador-sentimiento">
            <option value="">Todos</option>
            <option value="positivo">Positivo</option>
            <option value="neutro">Neutro</option>
            <option value="negativo">Negativo</option>
          </select>
        </div>
        <button class="filter-reset" id="explorador-reset" type="button" style="margin-left: auto;">Limpiar</button>
      </div>
      <div class="table-scroll" style="margin-bottom: 12px;">
        <table class="survey-table" id="tabla-explorador-comentarios" role="region" aria-label="Explorador de comentarios cualitativos">
          <caption class="sr-only">Explorador de comentarios con filtros de sentimiento y tema</caption>
          <thead><tr>
            <th scope="col" style="width: 16%; text-align: left;">Carrera</th>
            <th scope="col" style="width: 5%;" class="text-center">Ciclo</th>
            <th scope="col" style="width: 5%;" class="text-center">NPS</th>
            <th scope="col" style="width: 34%;">Texto abierto</th>
            <th scope="col" style="width: 18%;">Idea analizada</th>
            <th scope="col" style="width: 12%;">Tema</th>
            <th scope="col" style="width: 5%;" class="text-center">Sentimiento</th>
            <th scope="col" style="width: 5%;" class="text-center">Intensidad</th>
          </tr></thead>
          <tbody id="tbody-explorador-comentarios"></tbody>
        </table>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px;">
        <span id="explorador-pagination-info" style="font-size: var(--text-md); color: var(--text2); font-weight: var(--font-medium);">Mostrando 0-0 de 0 comentarios</span>
        <div style="display: flex; gap: 8px;">
          <button id="explorador-export-csv" class="filter-reset" style="padding: 4px 10px; font-size: var(--text-md);">Descargar</button>
          <button id="explorador-btn-prev" class="filter-reset" style="padding: 4px 10px; font-size: var(--text-md);" disabled>Anterior</button>
          <button id="explorador-btn-next" class="filter-reset" style="padding: 4px 10px; font-size: var(--text-md);" disabled>Siguiente</button>
        </div>
      </div>
      <div class="insight-box info" aria-live="polite" style="margin-top:20px;">
        <div class="insight-title">Análisis IA</div>
        <p class="insight-text" id="insight-cualitativo">Cargando análisis cualitativo...</p>
        <div id="insight-cualitativo-categorias" style="margin-top: 12px;"></div>
      </div>
      <div class="insight-box warning" style="margin-top: 20px;">
        <div class="insight-title">Nota</div>
        <p class="insight-text">Análisis semántico automatizado de los comentarios de alumnos. Los comentarios se agrupan en categorías temáticas y se analiza su sentimiento e intensidad mediante modelos de embeddings locales (offline).</p>
      </div>
    </section>
    `;

    $('artifactBody').innerHTML = html;
    renderDistributions();
    renderTop3Cards(_data.getDimsTop3());
    window.SurveyPortalRadar.renderRadarIndependiente();
    _filters.bindCustomSelect('srv-fac-top3', 'top3');
    _filters.bindCustomSelect('srv-car-top3', 'top3');
    _filters.bindMultiselect('srv-ciclo-top3', 'top3');
    _filters.bindMultiselect('srv-cat-radar', 'radar', 'Todas las categorías', 'categorías');
    _filters.bindCustomSelect('srv-fac-radar', 'radar');
    _filters.bindCustomSelect('srv-car-radar', 'radar');
    _filters.bindMultiselect('srv-ciclo-radar', 'radar');
    _filters.bindCustomSelect('srv-fac-preguntas', 'preguntas');
    _filters.bindCustomSelect('srv-car-preguntas', 'preguntas');
    _filters.bindMultiselect('srv-ciclo-preguntas', 'preguntas');
    _filters.bindCustomSelect('srv-fac-detalle', 'detalle');
    _filters.bindMultiselect('srv-ciclo-detalle', 'detalle');
    _filters.bindCustomSelect('srv-fac-visibilidad', 'visibilidad');
    _filters.bindCustomSelect('srv-car-visibilidad', 'visibilidad');
    _filters.bindMultiselect('srv-ciclo-visibilidad', 'visibilidad');
    // Poblar paneles de los multiselects (ciclo, categorías) y cascada en el
    // render inicial: SurveyMultiselect.create() no llama update()/renderOptions().
    _filters.refreshSelects('top3');
    _filters.refreshSelects('radar');
    _filters.refreshSelects('preguntas');
    _filters.refreshSelects('detalle');
    _filters.refreshSelects('visibilidad');
    renderPreguntas();
    renderTablaDetalle();
    renderVisibilidad();
    renderCualitativo();
  }

  // ── Análisis Cualitativo: delega a SurveySentimentView (módulo compartido) ──
    function renderCualitativo() {
      const Sv = window.SurveySentimentView;
      if (!Sv || typeof Sv.init !== 'function') return;
      const D = _data.getSurveyData() || {};
      const cache = { sentimiento: D.sentimiento || {}, dashboard: D.dashboard || {} };
      const totalRespuestas = (D.resumen && D.resumen.encuestas) || (D.sentimiento && D.sentimiento.comentarios ? D.sentimiento.comentarios.length : 0);
      Sv.init(cache.sentimiento, totalRespuestas, D._export || {}, D.nps_dist || null);
      Sv.updateMacro();
      Sv.updateAspectos();
      Sv.updateNpsCarrera();
      Sv.updateDetalle();
    }

    // ── Distribución CSAT / NPS (barras apiladas por periodo) ──
    function renderDistributions() {
    const D = _data.getSurveyData() || {};
    const csat = D.csat_dist || {};
    const nps = D.nps_dist || {};

    const pct = (value, total) => (total > 0 ? (value / total) * 100 : 0);
    const fmtDecimal = (n, digits) => Number(n).toFixed(digits).replace('.', ',');
    const fmtPctSimple = (v, t) => (t === 0 ? '0,00 %' : fmtDecimal((v / t) * 100, 2) + ' %');
    const fmtPctDecimal = (v, t) => (t === 0 ? '0,00 %' : fmtDecimal((v / t) * 100, 2) + ' %');
    const fmtInt = (n) => fmtNum(n || 0, 0);

    function bindHover(barId, legendId) {
      document.querySelectorAll('#' + barId + ' .csat-segment').forEach(function (seg) {
        seg.addEventListener('mouseenter', function () {
          document.querySelectorAll('#' + legendId + ' .legend-item.highlight').forEach(function (el) { el.classList.remove('highlight'); });
          const item = document.querySelector('#' + legendId + ' .legend-item[data-label="' + seg.getAttribute('data-label') + '"]');
          if (item) item.classList.add('highlight');
        });
        seg.addEventListener('mouseleave', function () {
          document.querySelectorAll('#' + legendId + ' .legend-item.highlight').forEach(function (el) { el.classList.remove('highlight'); });
        });
      });
    }

    // NPS
    const prom = nps.promotores || 0;
    const pas = nps.pasivos || 0;
    const det = nps.detractores || 0;
    const npsTotal = prom + pas + det;
    const npsBar = $('nps-bar');
    const npsLegend = $('nps-legend');
    if (npsBar) {
      npsBar.innerHTML =
        '<div class="csat-bar-row">' +
          '<div class="csat-segment" style="width:' + pct(prom, npsTotal) + '%; background:var(--gray-700);" data-label="Promotores (9-10)" data-value="' + fmtInt(prom) + ' (' + fmtPctDecimal(prom, npsTotal) + ')"><span class="csat-label">' + fmtPctSimple(prom, npsTotal) + '</span></div>' +
          '<div class="csat-segment" style="width:' + pct(pas, npsTotal) + '%; background:var(--gray-400);" data-label="Pasivos (7-8)" data-value="' + fmtInt(pas) + ' (' + fmtPctDecimal(pas, npsTotal) + ')"><span class="csat-label">' + fmtPctSimple(pas, npsTotal) + '</span></div>' +
          '<div class="csat-segment" style="width:' + pct(det, npsTotal) + '%; background:var(--ulima-orange);" data-label="Detractores (0-6)" data-value="' + fmtInt(det) + ' (' + fmtPctDecimal(det, npsTotal) + ')"><span class="csat-label">' + fmtPctSimple(det, npsTotal) + '</span></div>' +
        '</div>';
      if (npsLegend) {
        npsLegend.innerHTML =
          '<div class="legend-item" data-label="Promotores (9-10)"><div class="legend-dot" style="background:var(--gray-700);"></div>Promotores: ' + fmtInt(prom) + '</div>' +
          '<div class="legend-item" data-label="Pasivos (7-8)"><div class="legend-dot" style="background:var(--gray-400);"></div>Pasivos: ' + fmtInt(pas) + '</div>' +
          '<div class="legend-item" data-label="Detractores (0-6)"><div class="legend-dot" style="background:var(--ulima-orange);"></div>Detractores: ' + fmtInt(det) + '</div>';
        npsLegend.setAttribute('data-promotores', prom);
        npsLegend.setAttribute('data-pasivos', pas);
        npsLegend.setAttribute('data-detractores', det);
      }
      bindHover('nps-bar', 'nps-legend');
    }

    // CSAT
    const csatLabels = [
      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' },
      { key: 'Muy satisfecho', color: 'var(--gray-600)' },
      { key: 'Satisfecho', color: 'var(--gray-400)' },
      { key: 'Insatisfecho', color: 'var(--ulima-orange)' },
      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' }
    ];
    const csatTotal = csatLabels.reduce((s, item) => s + (csat[item.key] || 0), 0);
    const visibleLabels = csatLabels.filter((item) => (csat[item.key] || 0) > 0);
    const csatBar = $('csat-bar');
    const csatLegend = $('csat-legend');
    if (csatBar) {
      csatBar.innerHTML =
        '<div class="csat-bar-row">' +
          visibleLabels.map((item) => {
            const v = csat[item.key] || 0;
            return '<div class="csat-segment" style="width:' + pct(v, csatTotal) + '%; background:' + item.color + ';" data-label="' + item.key + '" data-value="' + fmtInt(v) + ' (' + fmtPctDecimal(v, csatTotal) + ')"><span class="csat-label">' + fmtPctSimple(v, csatTotal) + '</span></div>';
          }).join('') +
        '</div>';
      if (csatLegend) {
        csatLegend.innerHTML = visibleLabels
          .map((item) => {
            const v = csat[item.key] || 0;
            return '<div class="legend-item" data-label="' + item.key + '"><div class="legend-dot" style="background:' + item.color + ';"></div>' + item.key + ': ' + fmtInt(v) + '</div>';
          })
          .join('');
      }
      bindHover('csat-bar', 'csat-legend');
    }

    adjustSegmentLabels('#nps-bar');
    adjustSegmentLabels('#csat-bar');
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
      setTimeout(() => requestAnimationFrame(() => adjustSegmentLabels(target)), 1200);
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
        : seg.offsetWidth < 30;
      const tooSmall = segPct < 0.02;
      const textContent = (seg.textContent || '').trim();
      const textOverflows = isDistBar
        ? (textContent.length * 8 + SAFETY_MARGIN > seg.offsetWidth)
        : (() => { const lbl = seg.querySelector('.csat-label'); return lbl ? lbl.scrollWidth + SAFETY_MARGIN > seg.offsetWidth : false; })();
      const selected = textOverflows || tooNarrow || tooSmall;
      const isZero = isDistBar ? (parseFloat(seg.style.width) || 0) === 0 : segPct === 0;
      if (isZero || parseFloat(textContent.replace(',', '.')) === 0) {
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

  // Re-ajustar etiquetas externas al redimensionar la ventana (debounced)
  let resizeT;
  window.addEventListener('resize', function () {
    clearTimeout(resizeT);
    resizeT = setTimeout(function () {
      adjustSegmentLabels('#nps-bar');
      adjustSegmentLabels('#csat-bar');
    }, 150);
  });

  window.SurveyPortalSurvey = {
    renderSurveyView: renderSurveyView,
    renderDistributions: renderDistributions,
    renderTop3Cards: renderTop3Cards,
    renderTop3Bars: renderTop3Bars,
    renderTablaDetalle: renderTablaDetalle,
    renderPreguntas: renderPreguntas,
    renderVisibilidad: renderVisibilidad,
    formatDimensionName: window.SurveyFormatters.formatDimensionName,
    showBarTooltip: showBarTooltip,
    initBarLabelTooltips: initBarLabelTooltips,
    adjustSegmentLabels: adjustSegmentLabels
  };
})();
