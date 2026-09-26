/**
 * SURVEY SENTIMENT VIEW — Renderizador del análisis cualitativo y semántico.
 *
 * Muestra KPIs de comentarios, chips de temas semánticos principales,
 * tarjetas de insights cualitativos (insatisfacción/mejora/fortalezas) con frases reales,
 * y la tabla detallada de comentarios agrupados por carrera.
 *
 * Dependencias: SurveyFormatters, SurveyDOMHelpers, SurveySanitizer (globales)
 *
 * @module components/sentiment-view
 * @version 3.0.0
 */
window.SurveySentimentView = (() => {
  'use strict';

  const _fmt = window.SurveyFormatters;
  const _dh = window.SurveyDOMHelpers;
  const _san = window.SurveySanitizer;
  const _ttp = window.SurveyTooltip;

  const C = window.SURVEY_CONFIG || {};
  const CICLOS_ESTUDIOS_GENERALES = C.CICLOS_ESTUDIOS_GENERALES;

  const esEstudiosGen = _dh.esEstudiosGen;
  const $ = _dh.$;

  // State for the Paginated Comment Explorador
  const state = {
    originalComments: [],
    filteredComments: [],
    currentPage: 0,
    pageSize: 7,
    sentimentCache: null
  };

  function colorPorTipo(tipo) {
    if (tipo === 'negativo') {
      return { border: 'var(--ulima-red)', bg: 'var(--sentiment-neg-bg, var(--danger-pastel))', label: 'Insatisfacción' };
    }
    if (tipo === 'positivo') {
      return { border: 'var(--success-text)', bg: 'var(--sentiment-pos-bg, var(--success-pastel))', label: 'Fortaleza reconocida' };
    }
    return { border: 'var(--ulima-orange)', bg: 'var(--sentiment-neu-bg, var(--warning-pastel))', label: 'Oportunidad de mejora' };
  }

  function drawSentimentBars(stats) {
    const container = $('sentimiento-bar-chart');
    if (!container) return;
    container.innerHTML = '';
    // Set fixed height to match Ideas por segmento NPS
    container.className = 'seg-nps-barras';

    const pos = stats.pos.total;
    const neu = stats.neu.total;
    const neg = stats.neg.total;
    const total = pos + neu + neg;
    if (total === 0) return;

    const data = [
      { label: 'Positivo', value: pos, color: 'var(--success-text)', breakdown: stats.pos },
      { label: 'Neutro', value: neu, color: 'var(--gray-400)', breakdown: stats.neu },
      { label: 'Negativo', value: neg, color: 'var(--ulima-red)', breakdown: stats.neg }
    ];

    const fragment = document.createDocumentFragment();
    data.forEach((item, index) => {
      if (item.value === 0) return;
      
      const pct = Math.round((item.value / total) * 100);
      const barValueOutside = pct < 20;

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label bar-label-fija">${item.label}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="--w:${pct}%; --c:${item.color}; --delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${_fmt.formatPctSimple(item.value, total)}</span>
          </div>
        </div>
      `;

      // Tooltip events
      barItem.addEventListener('mouseenter', (e) => {
        const b = item.breakdown;
        let html = '<table class="tooltip-table">';
        html += `<tr><td>Promotores</td><td class="tooltip-num">${_fmt.formatInteger(b.prom)}</td></tr>`;
        html += `<tr><td>Pasivos</td><td class="tooltip-num">${_fmt.formatInteger(b.pas)}</td></tr>`;
        html += `<tr><td>Detractores</td><td class="tooltip-num">${_fmt.formatInteger(b.det)}</td></tr>`;
        html += `<tr><td colspan="2" class="tooltip-sep"></td></tr>`;
        html += `<tr><td><strong>${item.label}</strong></td><td class="tooltip-num">${_fmt.formatInteger(item.value)} ideas (${_fmt.formatPctSimple(item.value, total)})</td></tr>`;
        html += '</table>';
        // raw=true justificado en todos los tooltips de este modulo:
        // los valores interpolados son numericos (formatInteger/formatPctSimple)
        // o ya escapados con _san.escapeHTML(). No hay input de usuario sin escapar.
        _ttp.show(e, html, true);
      });
      barItem.addEventListener('mousemove', (e) => {
        _ttp.move(e);
      });
      barItem.addEventListener('mouseleave', () => {
        _ttp.hide();
      });

      fragment.appendChild(barItem);
    });

    container.appendChild(fragment);
  }

  function renderMetricCards(comments, cache, totalRespuestasGlobal, npsData) {
    const kpiGrid = $('sentiment-kpis');
    if (!kpiGrid) return;
    
    // totalRespuestasGlobal es el valor exacto de dashboard_data.json.resumen.encuestas
    // pasado por dashboard.js. Fallback a comments.length si no está disponible.
    const totalGlobal = totalRespuestasGlobal || comments.length;
    const totalRespuestas = totalGlobal;
    
    let textAbierto = 0, ideas = 0, neg = 0, pos = 0, neu = 0, sumInt = 0;
    
    comments.forEach(c => {
      if (c.es_valido) {
        ideas++;
        if (c.sentimiento === 'positivo') pos++;
        else if (c.sentimiento === 'negativo') neg++;
        else neu++;
        sumInt += (c.intensidad || 0);
      }
    });

    const uniqueIds = new Set(comments.map(c => c.id_encuesta || c.comentario_id_original));
    textAbierto = uniqueIds.size;

  // NPS promotores/pasivos/detractores entregados explícitamente por dashboard.js / portal
  // (desacoplado del DOM #nps-legend; ver SentimentView.init npsData). CAL-04 mantenido
  // como fallback si no se provee npsData.
  let promotores = 0, pasivos = 0, detractores = 0;
  if (npsData && (npsData.promotores != null || npsData.pasivos != null || npsData.detractores != null)) {
    promotores = Number(npsData.promotores) || 0;
    pasivos = Number(npsData.pasivos) || 0;
    detractores = Number(npsData.detractores) || 0;
  } else {
    // CAL-04: fallback legacy (periodos generados antes del fix) leyendo #nps-legend
    const npsLegend = document.getElementById('nps-legend');
    if (npsLegend) {
      const dp = npsLegend.getAttribute('data-promotores');
      const dpa = npsLegend.getAttribute('data-pasivos');
      const dd = npsLegend.getAttribute('data-detractores');
      if (dp !== null) promotores = parseInt(dp, 10) || 0;
      else if (dp === null && npsLegend.textContent) {
        const matchProm = npsLegend.textContent.match(/Promotores:\s*([\d,]+)/);
        if (matchProm) promotores = parseInt(matchProm[1].replace(/,/g, ''), 10);
      }
      if (dpa !== null) pasivos = parseInt(dpa, 10) || 0;
      else if (dpa === null && npsLegend.textContent) {
        const matchPas = npsLegend.textContent.match(/Pasivos:\s*([\d,]+)/);
        if (matchPas) pasivos = parseInt(matchPas[1].replace(/,/g, ''), 10);
      }
      if (dd !== null) detractores = parseInt(dd, 10) || 0;
      else if (dd === null && npsLegend.textContent) {
        const matchDet = npsLegend.textContent.match(/Detractores:\s*([\d,]+)/);
        if (matchDet) detractores = parseInt(matchDet[1].replace(/,/g, ''), 10);
      }
    }
  }

    const intensidadProm = ideas > 0 ? (sumInt / ideas) : 0; 

    const pctPos = ideas > 0 ? Math.round((pos/ideas)*100) : 0;
    const pctNeu = ideas > 0 ? Math.round((neu/ideas)*100) : 0;
    const pctNeg = ideas > 0 ? Math.round((neg/ideas)*100) : 0;

    const esPortal = !!(window.SurveyPortalData && window.svg);

        const createKpiCard = (label, value, color, icon) => {
          if (esPortal) {
            return (
              '<div class="survey-kpi" style="--kpi-color:' + color + ';">' +
                '<div class="survey-kpi-bar-top"></div>' +
                '<div class="survey-kpi-body">' +
                  '<p class="survey-kpi-value">' + value + '</p>' +
                  '<p class="survey-kpi-label">' + label + '</p>' +
                '</div>' +
                '<div class="survey-kpi-icon">' + window.svg(icon) + '</div>' +
              '</div>'
            );
          }
          return (
            `<div class="kpi-card">
              <div class="kpi-value ${color}">${value}</div>
              <div class="kpi-label ${color}">${label}</div>
            </div>`
          );
        };

        // Row 1: Total encuestados, Promotores, Pasivos, Detractores, Con texto abierto
        // Row 2: Intensidad prom., Positivas, Neutras, Negativas, Ideas analizadas
        if (esPortal) {
          kpiGrid.className = 'survey-kpi-grid';
          kpiGrid.innerHTML = [
            createKpiCard('Total encuestados', totalRespuestas, 'var(--amber)', 'users'),
                        createKpiCard('Promotores', promotores, 'var(--emerald)', 'trending-up'),
                        createKpiCard('Pasivos', pasivos, 'var(--kpi-neutro)', 'circle-dot'),
                        createKpiCard('Detractores', detractores, 'var(--ulima-orange)', 'alert-triangle'),
                        createKpiCard('Con texto abierto', textAbierto, 'var(--kpi-azul)', 'file-text'),
                        createKpiCard('Intensidad prom.', _fmt.formatDecimal(intensidadProm, 2), 'var(--amber)', 'gauge'),
            createKpiCard('Positivas', pos, 'var(--emerald)', 'check-circle'),
            createKpiCard('Neutras', neu, 'var(--kpi-neutro)', 'circle'),
            createKpiCard('Negativas', neg, 'var(--ulima-orange)', 'alert-circle'),
            createKpiCard('Ideas analizadas', ideas, 'var(--kpi-azul)', 'clipboard-list')
          ].join('');
        } else {
          kpiGrid.className = 'kpi-cards-bloque';
          kpiGrid.innerHTML = `
            <div class="kpi-cards-row">
              ${createKpiCard('Total encuestados', totalRespuestas, 'color-emplea')}
              ${createKpiCard('Promotores', promotores, 'color-csat')}
              ${createKpiCard('Pasivos', pasivos, 'color-emplea')}
              ${createKpiCard('Detractores', detractores, 'color-negative')}
              ${createKpiCard('Con texto abierto', textAbierto, 'color-emplea')}
            </div>
            <div class="kpi-cards-row">
              ${createKpiCard('Intensidad prom.', _fmt.formatDecimal(intensidadProm, 2), 'color-emplea')}
              ${createKpiCard('Positivas', pos, 'color-csat')}
              ${createKpiCard('Neutras', neu, 'color-emplea')}
              ${createKpiCard('Negativas', neg, 'color-negative')}
              ${createKpiCard('Ideas analizadas', ideas, 'color-emplea')}
            </div>
          `;
        }
  }

  function renderSentimentDistribution(comments) {
    const stats = {
      pos: { total: 0, prom: 0, pas: 0, det: 0 },
      neu: { total: 0, prom: 0, pas: 0, det: 0 },
      neg: { total: 0, prom: 0, pas: 0, det: 0 }
    };
    
    comments.forEach(c => {
      if (!c.es_valido) return;
      
      const nps = Number(c.nps_score);
      let npsKey = 'det';
      if (nps >= 9) npsKey = 'prom';
      else if (nps >= 7) npsKey = 'pas';

      let sentKey = 'neu';
      if (c.sentimiento === 'positivo') sentKey = 'pos';
      else if (c.sentimiento === 'negativo') sentKey = 'neg';
      
      stats[sentKey].total++;
      stats[sentKey][npsKey]++;
    });

    drawSentimentBars(stats);
  }

  // Draw Top categorías — menciones totales (Vertical Bars)
  function renderTopCategoriesBars(comments) {
    const container = $('categorias-barras-container');
    if (!container) return;

    container.innerHTML = '';
    // Horizontal flex row with bottom alignment for the columns
    container.className = 'cat-barras';
    
    const stats = {};

    comments.forEach(c => {
      if (!c.es_valido) return;
      const cat = c.categoria_padre || c.categoria || 'Otros';
      if (!stats[cat]) stats[cat] = { total: 0 };
      stats[cat][c.sentimiento] = (stats[cat][c.sentimiento] || 0) + 1;
      stats[cat].total++;
    });

    const sortedCats = Object.keys(stats).sort((a, b) => stats[b].total - stats[a].total);

    if (sortedCats.length === 0) {
      container.className = 'cat-barras esta-vacio';
      container.innerHTML = '<p class="sin-datos">No hay menciones registradas.</p>';
      return;
    }

    const maxTotal = stats[sortedCats[0]].total;

    sortedCats.forEach(cat => {
      const s = stats[cat];
      const heightPct = Math.max(10, (s.total / maxTotal) * 100);
      
      const posCount = s['positivo'] || 0;
      const neuCount = s['neutro'] || 0;
      const negCount = s['negativo'] || 0;

      const pPct = (posCount / s.total) * 100;
      const nPct = (neuCount / s.total) * 100;
      const negPct = (negCount / s.total) * 100;

      const col = document.createElement('div');
      col.className = 'cat-col';
      col.innerHTML = `
        <div class="cat-total">${_fmt.formatInteger(s.total)}</div>
        <div class="cat-bar" style="--cat-h:${heightPct}%">
          <div class="cat-pos" style="--cat-pct:${pPct}%"></div>
          <div class="cat-neu" style="--cat-pct:${nPct}%"></div>
          <div class="cat-neg" style="--cat-pct:${negPct}%"></div>
        </div>
        <div class="cat-name">${_san.escapeHTML(cat)}</div>
      `;

      // Tooltip enriquecido con conteos + porcentajes (2 decimales), consistente
      // con el resto de la app. Reemplaza al title HTML nativo.
      let tooltipHtml = '<table class="tooltip-table">';
      tooltipHtml += `<tr><td>Positivos</td><td class="tooltip-num">${_fmt.formatInteger(posCount)} (${_fmt.formatPctSimple(posCount, s.total)})</td></tr>`;
      tooltipHtml += `<tr><td>Neutros</td><td class="tooltip-num">${_fmt.formatInteger(neuCount)} (${_fmt.formatPctSimple(neuCount, s.total)})</td></tr>`;
      tooltipHtml += `<tr><td>Negativos</td><td class="tooltip-num">${_fmt.formatInteger(negCount)} (${_fmt.formatPctSimple(negCount, s.total)})</td></tr>`;
      tooltipHtml += `<tr><td colspan="2" class="tooltip-sep"></td></tr>`;
      tooltipHtml += `<tr><td><strong>${_san.escapeHTML(cat)}</strong></td><td class="tooltip-num">${_fmt.formatInteger(s.total)} menciones</td></tr>`;
      tooltipHtml += '</table>';
      col.addEventListener('mouseenter', (e) => { if (_ttp) _ttp.show(e, tooltipHtml, true); });
      col.addEventListener('mousemove', (e) => { if (_ttp) _ttp.move(e); });
      col.addEventListener('mouseleave', () => { if (_ttp) _ttp.hide(); });

      container.appendChild(col);
    });
  }

  function renderNPSSegmentBars(comments) {
    const container = $('seg-nps-container');
    if (!container) return;
    container.innerHTML = '';
    container.className = 'seg-nps-barras';

    const stats = {
      'Promotor': { total: 0, pos: 0, neu: 0, neg: 0 },
      'Pasivo': { total: 0, pos: 0, neu: 0, neg: 0 },
      'Detractor': { total: 0, pos: 0, neu: 0, neg: 0 }
    };

    let totalIdeas = 0;
    comments.forEach(c => {
      if (!c.es_valido) return;
      const nps = Number(c.nps_score);
      let seg = '';
      if (nps >= 9) seg = 'Promotor';
      else if (nps >= 7) seg = 'Pasivo';
      else seg = 'Detractor';
      c.segmento_nps = seg;
      
      stats[seg].total++;
      if (c.sentimiento === 'positivo') stats[seg].pos++;
      else if (c.sentimiento === 'negativo') stats[seg].neg++;
      else stats[seg].neu++;
      
      totalIdeas++;
    });

    if (totalIdeas === 0) return;

    const data = [
      { label: 'Promotores', value: stats['Promotor'].total, color: 'var(--success-text)', breakdown: stats['Promotor'] },
      { label: 'Pasivos', value: stats['Pasivo'].total, color: 'var(--gray-400)', breakdown: stats['Pasivo'] },
      { label: 'Detractores', value: stats['Detractor'].total, color: 'var(--ulima-red)', breakdown: stats['Detractor'] }
    ];

    const fragment = document.createDocumentFragment();
    data.forEach((item, index) => {
      if (item.value === 0) return;
      
      const pct = Math.round((item.value / totalIdeas) * 100);
      const barValueOutside = pct < 20;

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label bar-label-fija">${item.label}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="--w:${pct}%; --c:${item.color}; --delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${_fmt.formatPctSimple(item.value, totalIdeas)}</span>
          </div>
        </div>
      `;

      // Tooltip events
      barItem.addEventListener('mouseenter', (e) => {
        const b = item.breakdown;
        let html = '<table class="tooltip-table">';
        html += `<tr><td>Positivos</td><td class="tooltip-num">${_fmt.formatInteger(b.pos)}</td></tr>`;
        html += `<tr><td>Neutros</td><td class="tooltip-num">${_fmt.formatInteger(b.neu)}</td></tr>`;
        html += `<tr><td>Negativos</td><td class="tooltip-num">${_fmt.formatInteger(b.neg)}</td></tr>`;
        html += `<tr><td colspan="2" class="tooltip-sep"></td></tr>`;
        html += `<tr><td><strong>${item.label}</strong></td><td class="tooltip-num">${_fmt.formatInteger(item.value)} ideas (${_fmt.formatPctSimple(item.value, totalIdeas)})</td></tr>`;
        html += '</table>';
        _ttp.show(e, html, true);
      });
      barItem.addEventListener('mousemove', (e) => {
        _ttp.move(e);
      });
      barItem.addEventListener('mouseleave', () => {
        _ttp.hide();
      });

      fragment.appendChild(barItem);
    });

    container.appendChild(fragment);
  }

  // Generic Aspects & Intensity lists rendering
  function _renderList(containerId, data, isIntensity, isPos) {
    const container = $(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (data.length === 0) {
      container.innerHTML = '<span class="msj-corto">Data insuficiente</span>';
      return;
    }
    
    const maxVal = Math.max(...data.map(d => d.val));
    const fragment = document.createDocumentFragment();

    data.forEach((item, index) => {
      let pct = 0;
      let displayVal = '';
      if (isIntensity) {
        pct = (item.val / 5) * 100;
        displayVal = _fmt.formatDecimal(item.val, 2);
      } else {
        pct = maxVal > 0 ? (item.val / maxVal) * 100 : 0;
        displayVal = _fmt.formatInteger(item.val);
      }
      pct = Math.round(pct);
      const barValueOutside = pct < 20;
      const color = isPos ? 'var(--success-text)' : 'var(--ulima-red)';

      const barItem = document.createElement('div');
      barItem.className = 'bar-item';
      barItem.innerHTML = `
        <div class="bar-label">${_san.escapeHTML(item.name)}</div>
        <div class="bar-container">
          <div class="bar-fill animated" style="--w:${pct}%; --c:${color}; --delay:${index * 0.08}s">
            <span class="bar-value${barValueOutside ? ' bar-value-outside' : ''}">${displayVal}</span>
          </div>
        </div>
      `;

      const tooltipText = isIntensity ? 
        `<table class="tooltip-table"><tr><td class="tooltip-fila"><strong>${_san.escapeHTML(item.name)}</strong></td><td class="tooltip-num tooltip-fila">Intensidad promedio ${displayVal}</td></tr></table>` : 
        `<table class="tooltip-table"><tr><td class="tooltip-fila"><strong>${_san.escapeHTML(item.name)}</strong></td><td class="tooltip-num tooltip-fila">${_fmt.formatInteger(item.val)} menciones</td></tr></table>`;
        
      barItem.addEventListener('mouseenter', (e) => {
        _ttp.show(e, tooltipText, true);
      });
      barItem.addEventListener('mousemove', (e) => _ttp.move(e));
      barItem.addEventListener('mouseleave', () => _ttp.hide());

      fragment.appendChild(barItem);
    });
    container.appendChild(fragment);
  }

  function getAspectData(comments, filterSentimiento, isIntensity) {
    let total = 0;
    const aspStats = {};
    comments.forEach(c => {
      if (!c.es_valido) return;
      if (c.sentimiento !== filterSentimiento) return;
      total++;
      const aspect = c.aspecto_normalizado || c.categoria || 'Otros';
      if (!aspStats[aspect]) aspStats[aspect] = { count: 0, intSum: 0 };
      aspStats[aspect].count++;
      aspStats[aspect].intSum += (c.intensidad || 0);
    });
    
    const aspects = Object.keys(aspStats);
    let result = [];
    if (isIntensity) {
      result = aspects.map(a => ({ name: a, val: aspStats[a].count > 0 ? (aspStats[a].intSum / aspStats[a].count) : 0, count: aspStats[a].count }))
        .filter(a => a.count > 0)
        .sort((a, b) => b.val - a.val).slice(0, 5);
    } else {
      result = aspects.map(a => ({ name: a, val: aspStats[a].count }))
        .filter(a => a.val > 0)
        .sort((a, b) => b.val - a.val).slice(0, 5);
    }
    return { data: result, total };
  }

  function renderPositiveAspects(comments) {
    const res = getAspectData(comments, 'positivo', false);
    _renderList('aspectos-positivos-container', res.data, false, true);
  }

  function renderNegativeAspects(comments) {
    const res = getAspectData(comments, 'negativo', false);
    _renderList('aspectos-negativos-container', res.data, false, false);
  }

  function renderPositiveIntensity(comments) {
    const res = getAspectData(comments, 'positivo', true);
    _renderList('intensidad-positivos-container', res.data, true, true);
  }

  function renderNegativeIntensity(comments) {
    const res = getAspectData(comments, 'negativo', true);
    _renderList('intensidad-negativos-container', res.data, true, false);
  }

  function renderCareerNPSTable(comments) {
    const tbody = $('tbody-nps-carrera');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const carStats = {};
    comments.forEach(c => {
      const car = c.carrera || 'No Definida';
      if (!carStats[car]) {
        carStats[car] = {
          totalIdeas: 0,
          uniqueComments: new Set(),
          prom: 0,
          pas: 0,
          det: 0
        };
      }
      carStats[car].totalIdeas++;
      const commentId = c.comentario_id_original || c.id || c.comentario_original;
      if (commentId) {
        if (!carStats[car].uniqueComments.has(commentId)) {
          carStats[car].uniqueComments.add(commentId);
          if (c.nps_score >= 9) carStats[car].prom++;
          else if (c.nps_score >= 7) carStats[car].pas++;
          else carStats[car].det++;
        }
      } else {
        if (c.nps_score >= 9) carStats[car].prom++;
        else if (c.nps_score >= 7) carStats[car].pas++;
        else carStats[car].det++;
      }
    });

    const sortedCars = Object.keys(carStats).sort((a, b) => 
      (carStats[b].uniqueComments.size - carStats[a].uniqueComments.size) || 
      (carStats[b].totalIdeas - carStats[a].totalIdeas)
    );
    
    sortedCars.forEach(car => {
      const s = carStats[car];
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="celda-carrera">${_san.escapeHTML(car)}</td>
        <td class="text-center">${s.uniqueComments.size}</td>
        <td class="text-center">${s.totalIdeas}</td>
        <td class="text-center celda-prom">${s.prom}</td>
        <td class="text-center celda-destacada">${s.pas}</td>
        <td class="text-center celda-det">${s.det}</td>
      `;
      tbody.appendChild(tr);
    });
  }


  // Populate dynamic category selector
  function populateExploradorTopicsDropdown(comentarios) {
    const select = $('explorador-categoria');
    if (!select) return;

    const currentVal = select.value;
    const categories = [...new Set(comentarios.filter(c => c.es_valido).map(c => c.categoria_padre || c.categoria))].filter(Boolean).sort();

    select.innerHTML = '<option value="">Todos los temas</option>';
    categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      select.appendChild(opt);
    });

    if (categories.includes(currentVal)) {
      select.value = currentVal;
    }

    if (select.__custom) {
      select.__custom.update();
    }
  }

  function resetExploradorFilters() {
    const searchInput = $('explorador-search');
    if (searchInput) searchInput.value = '';
    
    const catSelect = $('explorador-categoria');
    if (catSelect) {
      catSelect.value = '';
      if (catSelect.__custom) catSelect.__custom.update();
    }
    
    const sentSelect = $('explorador-sentimiento');
    if (sentSelect) {
      sentSelect.value = '';
      if (sentSelect.__custom) sentSelect.__custom.update();
    }
    
    applyExploradorFilters();
  }

  // Filter comments for the paginated list
  function applyExploradorFilters() {
    const searchVal = $('explorador-search')?.value.toLowerCase() || '';
    const catVal = $('explorador-categoria')?.value || '';
    const sentVal = $('explorador-sentimiento')?.value || '';

    // First, apply the independent business filters for this specific block
    const baseComments = getFilteredSubset('sent');

    // Then, apply the explorador specific filters
    state.filteredComments = baseComments.filter(c => {
      const itemParent = c.categoria_padre || c.categoria;
      if (catVal && itemParent !== catVal) return false;
      if (sentVal && c.sentimiento !== sentVal) return false;

      if (searchVal) {
        const inOrig = c.fragmento_original?.toLowerCase().includes(searchVal);
        const inCorregido = c.fragmento_mostrar?.toLowerCase().includes(searchVal);
        const inCarrera = c.carrera?.toLowerCase().includes(searchVal);
        const inCat = itemParent?.toLowerCase().includes(searchVal);
        if (!inOrig && !inCorregido && !inCarrera && !inCat) return false;
      }

      return true;
    });

    state.currentPage = 0;
    renderExplorerTable();
    updateExploradorPagination();
  }

  // Render rows in the comments table
  function renderExplorerTable() {
    const tbody = $('tbody-explorador-comentarios');
    if (!tbody) return;

    tbody.innerHTML = '';
    const start = state.currentPage * state.pageSize;
    const end = Math.min(start + state.pageSize, state.filteredComments.length);
    const pageComments = state.filteredComments.slice(start, end);

    if (pageComments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center celda-vacia">No se encontraron comentarios con los filtros actuales.</td></tr>';
      return;
    }

    const fragment = document.createDocumentFragment();
    pageComments.forEach(c => {
      const tr = document.createElement('tr');

      let sentBadge = '';
      if (!c.es_valido) {
        const motivoLabel = c.motivo_invalidez === 'spam_o_ruido' ? 'Ruido' : 'Sin opinión';
        sentBadge = `<span class="insignia insignia-ruido">${motivoLabel}</span>`;
      } else {
        let estado = 'neutro', label = 'Neutro';
        if (c.sentimiento === 'positivo') {
          estado = 'positivo';
          label = 'Positivo';
        } else if (c.sentimiento === 'negativo') {
          estado = 'negativo';
          label = 'Negativo';
        }
        sentBadge = `<span class="insignia insignia-${estado}">${label}</span>`;
      }

      let nivelNps = 'det';
      if (c.nps_score >= 9) nivelNps = 'prom';
      else if (c.nps_score >= 7) nivelNps = 'pas';
      const npsBadge = `<span class="insignia-nps insignia-nps-${nivelNps}">${c.nps_score}</span>`;

      let safeCiclo = '-';
      if (c.ciclo) {
        safeCiclo = _fmt.formatCicloText(c.ciclo).replace(/\s*ciclo\s*/i, '');
      }

      const textoAbiertoText = c.comentario_original || c.fragmento_original;
      const textoAbierto = _san.escapeHTML(textoAbiertoText);

      const ideaAnalizadaText = c.fragmento_mostrar || c.fragmento_original;
      const displayIdeaAnalizada = c.es_valido
        ? _san.escapeHTML(ideaAnalizadaText)
        : `<span class="texto-invalidado">[Invalidado: ${_san.escapeHTML(c.motivo_invalidez)}]</span> "${_san.escapeHTML(ideaAnalizadaText)}"`;

      tr.innerHTML = `
        <td class="celda-carrera-izq">${_san.escapeHTML(c.carrera)}</td>
        <td class="text-center celda-suave">${safeCiclo}</td>
        <td class="text-center">${npsBadge}</td>
        <td class="celda-texto">${textoAbierto}</td>
        <td class="celda-texto">${displayIdeaAnalizada}</td>
        <td class="celda-suave">${_san.escapeHTML(c.categoria || '-')}</td>
        <td class="text-center">${sentBadge}</td>
        <td class="text-center celda-destacada">${c.intensidad ? Math.round(Number(c.intensidad)) : '-'}</td>
      `;
      fragment.appendChild(tr);
    });
    tbody.appendChild(fragment);
  }

  function updateExploradorPagination() {
    const total = state.filteredComments.length;
    const prevBtn = $('explorador-btn-prev');
    const nextBtn = $('explorador-btn-next');
    const info = $('explorador-pagination-info');

    if (!prevBtn || !nextBtn || !info) return;

    const start = state.currentPage * state.pageSize;
    const end = Math.min(start + state.pageSize, total);

    prevBtn.disabled = state.currentPage === 0;
    nextBtn.disabled = end >= total;

    if (total === 0) {
      info.textContent = 'Mostrando 0-0 de 0 comentarios';
    } else {
      info.textContent = `Mostrando ${start + 1}-${end} de ${total} comentarios`;
    }
  }

  // Export: descarga el ZIP pre-generado por el ETL.
  // Los ZIPs se guardan en ./exports/ (no en ./json/) para evitar
  // que se desplieguen en GitHub Pages. Si el ZIP no está disponible,
  // se muestra un modal estilizado en lugar de alert() nativo.
  function exportCSV() {
    const exp = state.exportConfig;
    if (!exp || !exp.nombre_encuesta || !exp.fecha_generacion) {
      _showExportModal('La exportación ZIP no está disponible para este período.');
      return;
    }
    const zipName = `data_${exp.nombre_encuesta}_${exp.fecha_generacion}.zip`;
    const zipUrl = `./exports/${zipName}`;
    // Verificar disponibilidad del ZIP antes de iniciar descarga.
    // Si el ZIP no se despliega en GitHub Pages, mostrar modal informativo.
    fetch(zipUrl, { method: 'HEAD' })
      .then(resp => {
        if (resp.ok) {
          const link = document.createElement('a');
          link.setAttribute('href', zipUrl);
          link.setAttribute('download', zipName);
          link.className = 'descarga-oculta';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } else {
          _showExportModal('La exportación ZIP no está disponible para este período.');
        }
      })
      .catch(() => {
        _showExportModal('La exportación ZIP no está disponible para este período.');
      });
  }

  // Modal estilizado para mensajes de exportación (reemplaza alert() nativo).
  // Cumple la regla ESLint no-alert y mejora la UX.
  function _showExportModal(message) {
    // Reutilizar overlay existente si ya está en el DOM
    let overlay = document.getElementById('export-modal-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'export-modal-overlay';
      overlay.setAttribute('role', 'dialog');
      overlay.setAttribute('aria-modal', 'true');
      overlay.setAttribute('aria-labelledby', 'export-modal-title');
      overlay.className = 'modal-overlay';
      const modal = document.createElement('div');
      modal.className = 'modal-caja';
      const title = document.createElement('h3');
      title.id = 'export-modal-title';
      title.textContent = 'Exportación no disponible';

      const body = document.createElement('p');
      body.textContent = message;

      const closeBtn = document.createElement('button');
      closeBtn.textContent = 'Cerrar';
      closeBtn.setAttribute('type', 'button');

      closeBtn.addEventListener('click', () => overlay.remove());
      overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
      modal.appendChild(title);
      modal.appendChild(body);
      modal.appendChild(closeBtn);
      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      // Focus inicial en el boton para accesibilidad por teclado
      closeBtn.focus();
    }
  }

  // Set up event listeners
  function setupExploradorListeners() {
    const searchInput = $('explorador-search');
    if (searchInput && !searchInput.dataset.listener) {
      searchInput.addEventListener('input', () => {
        applyExploradorFilters();
      });
      searchInput.dataset.listener = 'true';
    }

    const _cs = window.SurveyCustomSelect;

    const catSelect = $('explorador-categoria');
    if (catSelect && !catSelect.__custom && _cs) {
      catSelect.__custom = _cs.create(catSelect, () => {
        applyExploradorFilters();
      });
    }

    const sentSelect = $('explorador-sentimiento');
    if (sentSelect && !sentSelect.__custom && _cs) {
      sentSelect.__custom = _cs.create(sentSelect, () => {
        applyExploradorFilters();
      });
    }



    const exportBtn = $('explorador-export-csv');
    if (exportBtn && !exportBtn.dataset.listener) {
      exportBtn.addEventListener('click', () => {
        exportCSV();
      });
      exportBtn.dataset.listener = 'true';
    }

    const resetBtn = $('explorador-reset');
    if (resetBtn && !resetBtn.dataset.listener) {
      resetBtn.addEventListener('click', () => {
        resetExploradorFilters();
      });
      resetBtn.dataset.listener = 'true';
    }

    const prevBtn = $('explorador-btn-prev');
    if (prevBtn && !prevBtn.dataset.listener) {
      prevBtn.addEventListener('click', () => {
        if (state.currentPage > 0) {
          state.currentPage--;
          renderExplorerTable();
          updateExploradorPagination();
        }
      });
      prevBtn.dataset.listener = 'true';
    }

    const nextBtn = $('explorador-btn-next');
    if (nextBtn && !nextBtn.dataset.listener) {
      nextBtn.addEventListener('click', () => {
        const total = state.filteredComments.length;
        if ((state.currentPage + 1) * state.pageSize < total) {
          state.currentPage++;
          renderExplorerTable();
          updateExploradorPagination();
        }
      });
      nextBtn.dataset.listener = 'true';
    }
  }

  function getFilteredSubset(prefix) {
    if (!state.originalComments) return [];
    let filtroFac = $(`filter-facultad-${prefix}`)?.value || '';
    let filtroCar = $(`filter-carrera-${prefix}`)?.value || '';
    const filtroCiclo = _dh.getSelectedValues($(`filter-ciclo-${prefix}`)) || '';
    
    // Defensa extra contra valores residuales del select original (placeholders sin value vacío)
    if (filtroFac.toLowerCase().includes('todas')) filtroFac = '';
    if (filtroCar.toLowerCase().includes('todas')) filtroCar = '';

    return state.originalComments.filter(c => {
      if (filtroCar && c.carrera !== filtroCar) return false;
      if (filtroFac) {
        if (esEstudiosGen(filtroFac)) {
          const cycles = filtroCiclo ? (Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo]) : CICLOS_ESTUDIOS_GENERALES;
          if (!cycles.includes(c.ciclo)) return false;
        } else if (c.facultad !== filtroFac) {
          return false;
        }
      } else if (filtroCiclo) {
        const selectedCycles = Array.isArray(filtroCiclo) ? filtroCiclo : [filtroCiclo];
        if (selectedCycles.length > 0 && !selectedCycles.includes(c.ciclo)) return false;
      }
      return true;
    });
  }

  function init(sentimientoData, totalRespuestasGlobal, exportConfig, npsData) {
    if (!sentimientoData) return;

    // Cargar comentarios directamente desde la raíz del JSON
    state.originalComments = sentimientoData.comentarios || [];
    state.sentimentCache = sentimientoData;
    state.totalRespuestasGlobal = totalRespuestasGlobal;
    state.exportConfig = exportConfig || null;
  state.npsData = npsData || null;

    const kpiGrid = $('sentiment-kpis');
    if (kpiGrid && (!sentimientoData.topicos || !sentimientoData.topicos.length)) {
      kpiGrid.innerHTML = `<p class="sin-datos sin-datos-lg">
        No hay datos de análisis semántico disponibles para este período.</p>`;
    }

    // Renderizar insights IA (Fase 8)
    renderInsightsIA(sentimientoData);
  }

  function updateMacro() {
    const subset = getFilteredSubset('sent');
    renderMetricCards(subset, state.sentimentCache, state.totalRespuestasGlobal, state.npsData);
    renderSentimentDistribution(subset);
    renderNPSSegmentBars(subset);
    renderTopCategoriesBars(subset);
  }

  function updateAspectos() {
    const subset = getFilteredSubset('sent');
    renderPositiveAspects(subset);
    renderNegativeAspects(subset);
    renderPositiveIntensity(subset);
    renderNegativeIntensity(subset);
  }

  function updateNpsCarrera() {
    const subset = getFilteredSubset('sent');
    renderCareerNPSTable(subset);
  }

  function updateDetalle() {
    const subset = getFilteredSubset('sent');
    populateExploradorTopicsDropdown(subset);
    setupExploradorListeners();
    applyExploradorFilters();
  }

  /**
   * Renderiza los insights IA (global + por categoría padre) en el div huérfano
   * #insight-cualitativo y #insight-cualitativo-categorias.
   * Fase 8: conecta el campo insights_ia del JSON (generado por insights_generator.py)
   * con el frontend que antes estaba desconectado.
   */
  function renderInsightsIA(sentimientoData) {
    const insights = sentimientoData && sentimientoData.insights_ia;
    const divGlobal = $('insight-cualitativo');
    const divCategorias = $('insight-cualitativo-categorias');

    // Fallback: si no hay insights o no hay div, mostrar mensaje
    if (!divGlobal) return;

    if (!insights || (!insights.global && !insights.por_categoria_padre)) {
      divGlobal.textContent = 'No hay análisis cualitativo disponible para este período.';
      if (divCategorias) divCategorias.innerHTML = '';
      return;
    }

    // Renderizar insight global (escape por seguridad)
    divGlobal.textContent = insights.global || 'Análisis no disponible.';

    // Renderizar insights por categoría padre
    if (!divCategorias) return;
    divCategorias.innerHTML = '';

    const porCat = insights.por_categoria_padre || {};
    const categorias = Object.keys(porCat);

    if (categorias.length === 0) {
      return;
    }

    categorias.forEach((cat) => {
      const texto = porCat[cat];
      if (!texto) return;

      const item = document.createElement('div');
      item.className = 'insight-cat';

      const titulo = document.createElement('div');
      titulo.className = 'insight-cat-titulo';
      titulo.textContent = cat;

      const desc = document.createElement('div');
      desc.className = 'insight-cat-texto';
      desc.textContent = texto;

      item.appendChild(titulo);
      item.appendChild(desc);
      divCategorias.appendChild(item);
    });
  }

  return {
    init,
    updateMacro,
    updateAspectos,
    updateNpsCarrera,
    updateDetalle,
    applyExploradorFilters,
    renderInsightsIA
  };
})();
