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

  function renderDashboard() {
    var REPO_TARGET = window.REPO_TARGET;
    var PORTAL_PHASES = window.PORTAL_PHASES;
    var svg = window.svg;

    const dashData = _data.getSurveyDataCache()[_data.nivelDeFase('1.0') + '/' + _data.getPeriodoDeFase('1.0')] || _data.getSurveyData();

    const html =
      '<div class="main-inner">' +
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
