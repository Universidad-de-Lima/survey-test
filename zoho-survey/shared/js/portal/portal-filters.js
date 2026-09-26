/* ============================================================
   SURVEY PORTAL FILTERS — Sistema de filtros en cascada de la
   vista 1.0 (grupos independientes: top3 / radar / detalle).
   Expone window.SurveyPortalFilters.
   NOTA: se reutilizan los componentes externos SurveyCustomSelect
   y SurveyMultiselect (window.SurveyCustomSelect/SurveyMultiselect)
   en bindCustomSelect/bindMultiselect. El SurveyFilterController
   externo NO se usa: su esquema de IDs (filter-facultad-*) y su
   reset centralizado son incompatibles con los grupos independientes
   de la vista 1.0 (srv-fac-*, reset por grupo, select de categorías
   en radar, y grupo detalle sin select de carrera).
   ============================================================ */
(function () {
  'use strict';

  var _core = window.SurveyPortalCore;
  var _data = window.SurveyPortalData;
  var _dh = window.SurveyDOMHelpers;
  var esc = _core.esc;
  var fmtNum = _core.fmtNum;
  var formatCicloText = _core.formatCicloText;
  var $ = _dh.$;

  // Reemplaza las <option> de un select conservando la selección previa
  // cuando el valor sigue existiendo en la nueva lista.
  function populateSelect(sel, placeholder, values, displayValues) {
    if (!sel) return;
    let prev;
    if (sel.multiple) {
      prev = Array.from(sel.selectedOptions).map(o => o.value).filter(Boolean);
    } else {
      prev = sel.value;
    }
    sel.innerHTML = '<option value="">' + esc(placeholder) + '</option>';
    (values || []).forEach((v, i) => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = (displayValues && displayValues[i]) || v;
      if (sel.multiple) {
        if (prev.indexOf(v) !== -1) opt.selected = true;
      } else if (prev === v) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
  }

  function getCatsOptions() {
    const cats = [];
    (_data.getSurveyData().dims || []).forEach(d => { if (d.categoria && cats.indexOf(d.categoria) === -1) cats.push(d.categoria); });
    cats.sort();
    return cats;
  }

  // Actualiza las opciones de carrera/ciclo (y categorías en radar) sin
  // re-renderizar la vista. No toca la selección de facultad.
  function refreshSelects(grupo) {
    const g = window.__surveyFilter ? window.__surveyFilter[grupo] : null;
    if (!g) return;

    const carSel = $('srv-car-' + grupo);
    if (carSel) {
      populateSelect(carSel, 'Todas las carreras', _data.getCarrerasForFiltro(g.fac).sort());
      if (carSel.__custom && carSel.__custom.update) carSel.__custom.update();
    }

    const cicSel = $('srv-ciclo-' + grupo);
    const ciclos = _data.getCiclosForFiltro(g.fac, g.car);
    if (cicSel) {
      populateSelect(cicSel, 'Todos los ciclos', ciclos, ciclos.map(formatCicloText));
      if (cicSel.__multiselect && cicSel.__multiselect.update) cicSel.__multiselect.update();
    }

    if (grupo === 'radar') {
      const catSel = $('srv-cat-radar');
      if (catSel) {
        populateSelect(catSel, 'Todas las categorías', getCatsOptions());
        if (catSel.__multiselect && catSel.__multiselect.update) catSel.__multiselect.update();
      }
    }
  }

  function buildFiltroHtml(grupo) {
    const sel = window.__surveyFilter[grupo];
    const isRadar = grupo === 'radar';
    const isDetalle = grupo === 'detalle';
    const F = _data.getSurveyData().filtros;

    function facOptionsHtml() {
      const hasCiclo = !!F.has_ciclo;
      const lista = (F.facultades || []).slice().filter(f => f !== _data.PROGRAMA_ESTUDIOS_GENERALES).sort();
      const items = hasCiclo ? [_data.PROGRAMA_ESTUDIOS_GENERALES].concat(lista) : lista;
      return '<option value="">Todas las unidades académicas</option>' +
        items.map(f => '<option value="' + esc(f) + '"' + (sel.fac === f ? ' selected' : '') + '>' + esc(f) + '</option>').join('');
    }
    function carOptionsHtml() {
      const cars = _data.getCarrerasForFiltro(sel.fac).sort();
      return '<option value="">Todas las carreras</option>' +
        cars.map(c => '<option value="' + esc(c) + '"' + (sel.car === c ? ' selected' : '') + '>' + esc(c) + '</option>').join('');
    }
    function cicloOptionsHtml() {
      const ciclos = _data.getCiclosForFiltro(sel.fac, sel.car);
      const selCic = Array.isArray(sel.ciclos) ? sel.ciclos : [];
      return '<option value="">Todos los ciclos</option>' +
        ciclos.map(c => '<option value="' + esc(c) + '"' + (selCic.indexOf(c) !== -1 ? ' selected' : '') + '>' + esc(formatCicloText(c)) + '</option>').join('');
    }
    function catOptionsHtml() {
      const cats = getCatsOptions();
      return '<option value="">Todas las categorías</option>' +
        cats.map(c => '<option value="' + esc(c) + '"' + (sel.cats.indexOf(c) !== -1 ? ' selected' : '') + '>' + esc(c) + '</option>').join('');
    }

    let html = '<div class="filter-container' + (isRadar ? ' filter-container-wrap' : '') + '" role="group" aria-label="Filtros de ' + grupo + '" class="espacio-arriba-16">';

    if (isRadar) {
      html += '<div class="filter-group">' +
        '<label class="filter-label" for="srv-cat-radar">Categoría:</label>' +
        '<select class="filter-select" id="srv-cat-radar" multiple data-multiselect="true">' + catOptionsHtml() + '</select></div>';
    }

    html += '<div class="filter-group">' +
      '<label class="filter-label" for="srv-fac-' + grupo + '">Facultad:</label>' +
      '<select class="filter-select" id="srv-fac-' + grupo + '">' + facOptionsHtml() + '</select></div>';

    if (!isDetalle) {
      html += '<div class="filter-group">' +
        '<label class="filter-label" for="srv-car-' + grupo + '">Carrera:</label>' +
        '<select class="filter-select" id="srv-car-' + grupo + '">' + carOptionsHtml() + '</select></div>';
    }

    html += '<div class="filter-group">' +
      '<label class="filter-label" for="srv-ciclo-' + grupo + '">Ciclo:</label>' +
      '<select class="filter-select" id="srv-ciclo-' + grupo + '" multiple data-multiselect="true">' + cicloOptionsHtml() + '</select></div>';

    html += '<button class="filter-reset" type="button" data-grupo="' + esc(grupo) + '">Limpiar</button>';

    html += '</div>';

    return html;
  }

  // Re-renderiza SOLO la sección afectada por el filtro del grupo.
  function reRenderGrupo(grupo) {
    if (grupo === 'top3') window.SurveyPortalSurvey.renderTop3Cards(_data.getDimsTop3());
    else if (grupo === 'radar') window.SurveyPortalRadar.renderRadarIndependiente();
    else if (grupo === 'detalle') window.SurveyPortalSurvey.renderTablaDetalle();
    else if (grupo === 'visibilidad') window.SurveyPortalSurvey.renderVisibilidad();
    else if (grupo === 'preguntas') window.SurveyPortalSurvey.renderPreguntas();
  }

  // Filtros de la vista 1.0 (grupos independientes: top3 / radar / detalle)
  function __applyFilter(grupo) {
    const filter = window.__surveyFilter = window.__surveyFilter || {
      top3: { fac: '', car: '', ciclos: [] },
      radar: { fac: '', car: '', ciclos: [], cats: [] },
      preguntas: { fac: '', car: '', ciclos: [] },
      detalle: { fac: '', ciclos: [] }
    };
    const g = filter[grupo] = filter[grupo] || { fac: '', car: '', ciclos: [] };
    g.fac = $('srv-fac-' + grupo).value;
    const carSel = $('srv-car-' + grupo);
    g.car = carSel ? carSel.value : '';
    const cicSel = $('srv-ciclo-' + grupo);
    const cicVals = cicSel ? Array.from(cicSel.selectedOptions).map(o => o.value).filter(Boolean) : [];
    g.ciclos = cicVals.length ? cicVals : '';
    if (grupo === 'radar') {
      const catSel = $('srv-cat-radar');
      g.cats = catSel ? Array.from(catSel.selectedOptions).map(o => o.value) : [];
    }
    // Si cambia facultad, resetear carrera si ya no aplica
    if (g.fac && g.car) {
      const cars = _data.getCarrerasForFiltro(g.fac);
      if (cars.indexOf(g.car) === -1) g.car = '';
    }
    refreshSelects(grupo);
    reRenderGrupo(grupo);
  }

  function __resetFilter(grupo) {
    const filter = window.__surveyFilter = window.__surveyFilter || {};
    if (grupo === 'detalle') {
      filter.detalle = { fac: '', ciclos: [] };
    } else if (grupo === 'radar') {
      filter.radar = { fac: '', car: '', ciclos: [], cats: [] };
    } else if (grupo === 'preguntas') {
      filter.preguntas = { fac: '', car: '', ciclos: [] };
    } else if (grupo === 'visibilidad') {
      filter.visibilidad = { fac: '', car: '', ciclos: [] };
    } else {
      filter.top3 = { fac: '', car: '', ciclos: [] };
    }

    // Resetear el DOM de los selects del grupo (los widgets custom/multiselect no se re-crean)
    const facSel = $('srv-fac-' + grupo);
    if (facSel) {
      facSel.value = '';
      if (facSel.__custom && facSel.__custom.update) facSel.__custom.update();
    }
    const carSel = $('srv-car-' + grupo);
    if (carSel) {
      carSel.value = '';
      if (carSel.__custom && carSel.__custom.update) carSel.__custom.update();
    }
    const cicSel = $('srv-ciclo-' + grupo);
    if (cicSel) {
      Array.from(cicSel.options).forEach(o => { o.selected = false; });
      if (cicSel.__multiselect && cicSel.__multiselect.update) cicSel.__multiselect.update();
    }
    if (grupo === 'radar') {
      const catSel = $('srv-cat-radar');
      if (catSel) {
        Array.from(catSel.options).forEach(o => { o.selected = false; });
        if (catSel.__multiselect && catSel.__multiselect.update) catSel.__multiselect.update();
      }
    }

    refreshSelects(grupo);
    reRenderGrupo(grupo);
  }

  // ── Binding de widgets (reutiliza los componentes externos) ──
  // SurveyCustomSelect.create(sel, onChange) -> {update, close, button, wrapper}
  function bindCustomSelect(id, grupo) {
    const sel = $(id);
    if (!sel) return null;
    sel.__custom = window.SurveyCustomSelect.create(sel, function () { __applyFilter(grupo); });
    return sel.__custom;
  }

  // SurveyMultiselect.create(sel, onChange, defaultLabel, itemName) -> wrapper con .update()
  function bindMultiselect(id, grupo, defaultLabel, itemName) {
    const sel = $(id);
    if (!sel) return null;
    sel.__multiselect = window.SurveyMultiselect.create(sel, function () { __applyFilter(grupo); }, defaultLabel, itemName);
    return sel.__multiselect;
  }

  // Etiqueta de multiselect (delega al helper compartido; se conserva
  // como API pública por compatibilidad).
  function formatMultiselectLabel(labels, placeholder, itemName) {
    return _dh.formatMultiselectLabel(labels, placeholder, itemName);
  }

  // Exposición pública (compatibilidad: otros módulos y pruebas usan estas
  // funciones directamente; ya no se generan manejadores en linea).
  window.__applyFilter = __applyFilter;
  window.__resetFilter = __resetFilter;

  // Delegacion de eventos: un unico listener atiende los botones "Limpiar" de
  // todos los grupos. Los botones llevan data-grupo y se crean con innerHTML,
  // asi que la delegacion es la unica forma de enlazarlos sin onclick en linea
  // (regla del proyecto: nada de manejadores en linea).
  document.addEventListener('click', function (ev) {
    var btn = ev.target && ev.target.closest ? ev.target.closest('.filter-reset[data-grupo]') : null;
    if (!btn) return;
    ev.preventDefault();
    __resetFilter(btn.getAttribute('data-grupo'));
  });

  window.SurveyPortalFilters = {
    buildFiltroHtml: buildFiltroHtml,
    __applyFilter: __applyFilter,
    __resetFilter: __resetFilter,
    refreshSelects: refreshSelects,
    populateSelect: populateSelect,
    getCatsOptions: getCatsOptions,
    bindCustomSelect: bindCustomSelect,
    bindMultiselect: bindMultiselect,
    reRenderGrupo: reRenderGrupo,
    formatMultiselectLabel: formatMultiselectLabel
  };
})();
