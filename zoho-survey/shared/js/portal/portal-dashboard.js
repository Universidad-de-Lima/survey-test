/* ============================================================
   SURVEY PORTAL DASHBOARD — Vista "Dashboard" del portal v5.0:
   tarjetas de satisfacción por fase + barra de NPS.
   Expone window.SurveyPortalDashboard.
   Depende de SurveyPortalCore (fmtNum/svg vía window) y
   SurveyPortalData (datos de encuesta y graduados).
   ============================================================ */
(function () {
  'use strict';

  var _core = window.SurveyPortalCore;
  var _data = window.SurveyPortalData;
  var fmtNum = _core.fmtNum;
  var $ = window.SurveyDOMHelpers.$;

  // Umbrales de color (desde constants.js, fuente canónica)
  const META_CSAT = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_CSAT) ?? 93;
  const META_PONDERADO = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_PONDERADO) ?? 80;
  const META_NPS = (window.SURVEY_CONFIG && window.SURVEY_CONFIG.META_NPS) ?? 50;
  const META_NPS_MEDIO = 20; // no hay en constants, mantener como visual

  // Subtítulo de cada tarjeta: el periodo publicado o, si todavía no hay
  // datos, el mismo texto que las fases sin dashboard.
  const SIN_DATOS = 'Página en construcción';

  function satRole(phase) {
    return _data.getPeriodoDeFase(phase.id) || SIN_DATOS;
  }

  // ── Anillos: la última medición de cada encuesta ──
  // Un anillo por encuesta con su periodo más reciente. El anillo se llena
  // sobre la escala real del NPS (-100 a +100: medio anillo es cero) y el
  // color sigue las metas del proyecto.
  const GRUPOS_ANILLOS = ['Estudiantes', 'Graduados y egresados', 'Colaboradores y empleadores'];

  function colorDeNps(valor) {
    if (valor == null) return 'var(--muted)';
    if (valor >= META_NPS) return 'var(--emerald)';
    return valor >= META_NPS_MEDIO ? 'var(--amber)' : 'var(--rose)';
  }

  // Posición en el anillo: -100 → 0 %, 0 → 50 %, +100 → 100 %.
  function llenadoDeNps(valor) {
    if (valor == null) return '0.00';
    const pct = (Number(valor) + 100) / 2;
    return Math.max(0, Math.min(100, pct)).toFixed(2);
  }

  function tendenciaDe(medicion) {
    if (!medicion || medicion.nps == null) return '<span class="ring-tend pendiente">sin datos</span>';
    if (medicion.delta == null) return '<span class="ring-tend pendiente">primera medición</span>';
    const sube = medicion.delta > 0;
    const clase = sube ? 'sube' : 'baja';
    const signo = sube ? '▲ +' : '▼ ';
    return '<span class="ring-tend ' + clase + '">' + signo + fmtNum(medicion.delta, 2) +
      ' vs ' + _core.esc(medicion.anterior || '') + '</span>';
  }

  function anilloDeEncuesta(phase, medicion) {
    const esc2 = _core.esc;
    const hayDatos = !!(medicion && medicion.nps != null);
    if (!hayDatos) {
      return '<div class="ring pendiente">' +
        '<div class="ring-aro" style="background:conic-gradient(var(--ring-track) 0 100%)">' +
          '<div class="ring-centro"><b class="sin-dato">—</b><i>NPS</i></div>' +
        '</div>' +
        '<span class="ring-nom">' + esc2(phase.name) + '</span>' +
        '<span class="ring-per">próximamente</span>' +
        '<span class="ring-satisf"><span class="ring-barra"><i style="width:0%"></i></span>' +
          '<span class="sin-dato">—</span></span>' +
        tendenciaDe(medicion) +
      '</div>';
    }

    const color = colorDeNps(medicion.nps);
    const signo = medicion.nps > 0 ? '+' : '';
    const csatPct = medicion.csat == null ? '0.00' : medicion.csat.toFixed(2);
    const csatTexto = medicion.csat == null ? '—' : fmtNum(medicion.csat, 2) + ' %';
    const colorCsat = medicion.csat == null ? 'var(--muted)'
      : (medicion.csat >= META_CSAT ? 'var(--emerald)'
        : medicion.csat >= META_PONDERADO ? 'var(--amber)' : 'var(--rose)');
    const detalle = esc2(medicion.periodo || '') +
      (medicion.respuestas != null ? ' · ' + fmtNum(medicion.respuestas, 0) + ' respuestas' : '');

    return '<div class="ring">' +
      '<div class="ring-aro" style="background:conic-gradient(' + color + ' 0 ' + llenadoDeNps(medicion.nps) +
        '%, var(--ring-track) 0)">' +
        '<div class="ring-centro"><b style="color:' + color + '">' + signo + fmtNum(medicion.nps, 2) + '</b><i>NPS</i></div>' +
      '</div>' +
      '<span class="ring-nom">' + esc2(phase.name) + '</span>' +
      '<span class="ring-per">' + detalle + '</span>' +
      '<span class="ring-satisf"><span class="ring-barra"><i style="width:' + csatPct + '%; background:' + colorCsat +
        '"></i></span><span style="color:' + colorCsat + '">' + csatTexto + '</span></span>' +
      tendenciaDe(medicion) +
    '</div>';
  }

  function renderAnillos(mediciones, fases) {
    const porFase = {};
    (mediciones || []).forEach(function (m) { porFase[m.faseId] = m; });

    const secciones = GRUPOS_ANILLOS.map(function (grupo) {
      const delGrupo = (fases || []).filter(function (p) { return !p.optional && p.grupo === grupo; });
      if (!delGrupo.length) return '';
      return '<div class="ring-grupo">' + _core.esc(grupo) + '</div>' +
        '<div class="ring-grid">' + delGrupo.map(function (p) {
          return anilloDeEncuesta(p, porFase[p.id]);
        }).join('') + '</div>';
    }).join('');

    return '<section class="section">' +
      '<div class="repo-card">' +
        '<div class="repo-card-inner" style="flex-direction:column; align-items:stretch;">' +
          '<h2 class="repo-card-title">' + window.svg('gauge', 16) + 'Última encuesta de cada grupo</h2>' +
          '<p class="repo-card-desc">Cada anillo muestra la medición más reciente de una encuesta: el número del centro es su ' +
            '<strong>índice de promotores netos</strong>, el anillo se llena sobre la escala −100 a +100 (medio anillo es cero) ' +
            'y abajo va el <strong>nivel de satisfacción</strong>.</p>' +
          '<div class="ring-leyenda">' +
            '<span><i style="background:var(--emerald)"></i>NPS de ' + META_NPS + ' o más</span>' +
            '<span><i style="background:var(--amber)"></i>entre ' + META_NPS_MEDIO + ' y ' + META_NPS + '</span>' +
            '<span><i style="background:var(--rose)"></i>debajo de ' + META_NPS_MEDIO + '</span>' +
            '<span><i style="background:var(--ring-track)"></i>todavía sin datos</span>' +
          '</div>' +
          secciones +
        '</div>' +
      '</div>' +
    '</section>';
  }

  let _renderToken = 0;

  async function renderDashboard() {
    // Las mediciones llegan por red; si mientras cargaba se pidió otro render,
    // este se descarta para no pisar el más reciente.
    const token = ++_renderToken;
    const mediciones = await _data.loadMedicionesDeEncuestas();
    if (token !== _renderToken) return;

    var REPO_TARGET = window.REPO_TARGET;
    var PORTAL_PHASES = window.PORTAL_PHASES;
    var svg = window.svg;

    const dashData = _data.getSurveyDataCache()[_data.nivelDeFase('1.0') + '/' + _data.getPeriodoDeFase('1.0')] || _data.getSurveyData();

    const html =
      '<div class="main-inner">' +
        renderAnillos(mediciones, PORTAL_PHASES) +
        '<section class="section">' +
          '<div class="repo-card">' +
            '<div class="repo-card-inner">' +
              '<div style="min-width:0; flex:1 1 300px; display:flex; flex-direction:column; justify-content:center;">' +
                '<h2 class="repo-card-title">' + svg('gauge', 16) + 'Nivel de Satisfacción</h2>' +
                '<p class="repo-card-desc">' + REPO_TARGET.summary + '</p>' +
                '<div class="satisfaction-bars" style="margin-top:16px;">' +
                  PORTAL_PHASES.filter(p => !p.optional).map(phase => {
                    const realScore = phase.id === '1.0' ? (dashData && dashData.resumen ? dashData.resumen.csat.score : null)
                      : phase.id === '1.2' ? (_data.getGraduateData() && _data.getGraduateData().resumen ? _data.getGraduateData().resumen.csat.score : null)
                      : null;
                    const pctCss = realScore == null ? '0.00' : realScore.toFixed(2);  // para width (CSS: punto)
                    const pct = fmtNum(realScore, 2);                                 // para texto visible (coma)
                    const pNum = parseFloat(pctCss);
                    const color = realScore == null ? 'var(--muted)' : (pNum >= META_CSAT ? 'var(--emerald)' : pNum >= META_PONDERADO ? 'var(--amber)' : 'var(--rose)');
                    return '<div class="sat-row' + (realScore == null ? ' sat-row-locked' : '') + '">' +
                      '<div class="sat-info">' +
                        '<span class="sat-icon" style="color: var(--muted-foreground);">' + svg(phase.icon, 16) + '</span>' +
                        '<span style="display:flex;flex-direction:column;min-width:0;">' +
                          '<span class="sat-name">' + phase.name + '</span>' +
                          '<span class="sat-role">' + satRole(phase) + '</span>' +
                        '</span>' +
                      '</div>' +
                      '<div class="sat-bar-wrap">' +
                        '<div class="sat-bar" style="width:' + pctCss + '%; background:' + color + ';"></div>' +
                      '</div>' +
                      '<span class="sat-pct" style="color:' + color + ';">' + pct + '%</span>' +
                    '</div>';
                  }).join('') +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</section>' +

        '<section class="section">' +
          '<div class="repo-card">' +
            '<div class="repo-card-inner">' +
              '<div style="min-width:0; flex:1 1 300px; display:flex; flex-direction:column; justify-content:center;">' +
                '<h2 class="repo-card-title">' + svg('gauge', 16) + 'Índice de Promotores Netos</h2>' +
                '<p class="repo-card-desc">El índice de promotores netos se obtiene a partir de la pregunta <strong>¿Qué tan probable es que recomiendes a la Universidad de Lima?</strong>. Se calcula restando el porcentaje de respuestas <strong>detractoras</strong> (valores de 0 a 6) del porcentaje de respuestas <strong>promotoras</strong> (valores de 9 y 10) sobre el total de respuestas de la escala de percepción de 10 puntos y excluyendo las <strong>respuestas vacías</strong>.</p>' +
                '<div class="satisfaction-bars" style="margin-top:16px;">' +
                  PORTAL_PHASES.filter(p => !p.optional).map(phase => {
                    const realScore = phase.id === '1.0' ? (dashData && dashData.resumen ? dashData.resumen.nps.score : null)
                      : phase.id === '1.2' ? (_data.getGraduateData() && _data.getGraduateData().resumen ? _data.getGraduateData().resumen.nps.score : null)
                      : null;
                    const npsCss = realScore == null ? '0.00' : realScore.toFixed(2);  // para width (CSS: punto)
                    const nps = fmtNum(realScore, 2);                                 // para texto visible (coma)
                    const nNum = parseFloat(npsCss);
                    const color = realScore == null ? 'var(--muted)' : (nNum >= META_NPS ? 'var(--emerald)' : nNum >= META_NPS_MEDIO ? 'var(--amber)' : 'var(--rose)');
                    return '<div class="sat-row' + (realScore == null ? ' sat-row-locked' : '') + '">' +
                      '<div class="sat-info">' +
                        '<span class="sat-icon" style="color: var(--muted-foreground);">' + svg(phase.icon, 16) + '</span>' +
                        '<span style="display:flex;flex-direction:column;min-width:0;">' +
                          '<span class="sat-name">' + phase.name + '</span>' +
                          '<span class="sat-role">' + satRole(phase) + '</span>' +
                        '</span>' +
                      '</div>' +
                      '<div class="sat-bar-wrap">' +
                        '<div class="sat-bar" style="width:' + npsCss + '%; background:' + color + ';"></div>' +
                      '</div>' +
                      '<span class="sat-pct" style="color:' + color + ';">' + nps + '</span>' +
                    '</div>';
                  }).join('') +
                '</div>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</section>' +

      '</div>';

    $('mainContent').innerHTML = html;
  }

  // Tarjeta de metadatos del archivo (estilo web de referencia)
  // filename = periodo (ej. "2026-1"), nivel = "students/undergraduate" | "students/graduate"
  async function renderMetaCard(filename, nivel) {
    const svg = window.svg;
    const D = _data.getSurveyData() || {};
    const resumen = D.resumen || {};

    const encuestados = resumen.encuestas != null ? fmtNum(resumen.encuestas, 0) + ' encuestados' : '';
    const carreras = resumen.carreras != null ? fmtNum(resumen.carreras, 0) + ' carreras' : '';
    const facultades = resumen.facultades != null ? fmtNum(resumen.facultades, 0) + ' facultades' : '';

    // Fecha del JSON del periodo (resumen.fecha_fin); sin fallback hardcodeado
    let fechaItem = '';
    const fechaFin = resumen && resumen.fecha_fin;
    if (fechaFin) {
      const d = new Date(fechaFin + 'T00:00:00');
      if (!isNaN(d.getTime())) {
        fechaItem = '<span class="item">' + svg('clock', 12) +
          d.toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' }) +
        '</span>';
      }
    }

    // Construir nombre del ZIP según nivel y periodo (patrón del ETL csv_exporter.py)
    // _sanitizar_nombre_csv: lower + [^a-z0-9áéíóúñü]→_ + colapsar _ + strip _
    // CSV pregrado: "ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - {periodo}.csv"
    // CSV graduados: "ENCUESTA DE SATISFACCIÓN GRADUADOS - PREGRADO - {periodo}.csv"
    function zipFilename(nivel, periodo) {
      const p = periodo.replace('-', '_');
      if (nivel === 'students/graduate') {
        // base = encuesta_de_satisfacción_graduados_pregrado_{p}
        return 'data_encuesta_de_satisfacción_graduados_pregrado_' + p + '.zip';
      }
      // base = encuesta_de_satisfacción_estudiantil_pregrado_{p}
      return 'data_encuesta_de_satisfacción_estudiantil_pregrado_' + p + '.zip';
    }

    const zipName = zipFilename(nivel, filename);
    const zipUrl = './' + nivel + '/' + filename + '/exports/' + encodeURIComponent(zipName);

    // Tamaño real del archivo descargable (HEAD); si no existe, no se muestra
    let sizeItem = '';
    try {
      const head = await fetch(zipUrl, { method: 'HEAD', cache: 'no-store' });
      const bytes = head.ok ? parseInt(head.headers.get('content-length') || '0', 10) : 0;
      if (bytes > 0) {
        const kb = (bytes / 1024).toFixed(1).replace('.', ',');
        sizeItem = '<span class="item"><span class="dot"></span>' + kb + ' KB</span>';
      }
    } catch (e) { /* sin red: omitir tamaño */ }

    return '<div class="file-meta-bar" style="margin-top:-8px;">' +
      '<span class="item filename" style="color:var(--primary);">' +
        svg('calendar', 14) +
        filename +
      '</span>' +
      (encuestados ? '<span class="item">' + svg('users', 12) + encuestados + '</span>' : '') +
      (carreras ? '<span class="item">' + svg('graduation-cap', 12) + carreras + '</span>' : '') +
      (facultades ? '<span class="item">' + svg('landmark', 12) + facultades + '</span>' : '') +
      sizeItem +
      fechaItem +
      '<a href="' + zipUrl + '" download="' + zipName + '" class="btn-download" style="text-decoration:none;">' +
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3"></path><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m7 10 5 5 5-5"></path></svg>Descargar' +
      '</a>' +
    '</div>';
  }

  window.SurveyPortalDashboard = {
    renderDashboard: renderDashboard,
    renderMetaCard: renderMetaCard,
    satRole: satRole
  };
})();
