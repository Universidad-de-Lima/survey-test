/**
 * SURVEY FILTER CONTROLLER — Gestión centralizada de filtros en cascada.
 *
 * Configura filtros de facultad, carrera y ciclo para todas las secciones.
 * Maneja eventos de cambio, sincronización de estado activo y resets.
 *
 * Dependencias: SurveyDOMHelpers, SurveyCustomSelect, SurveyMultiselect, SurveyFormatters
 *
 * @module components/filter-controller
 * @version 1.0.0
 */
window.SurveyFilterController = (() => {
  'use strict';

  const _dh = window.SurveyDOMHelpers;
  const _cs = window.SurveyCustomSelect;
  const _ms = window.SurveyMultiselect;
  const _fmt = window.SurveyFormatters;

  const C = window.SURVEY_CONFIG || {};
  const PROGRAMA_ESTUDIOS_GENERALES = C.PROGRAMA_ESTUDIOS_GENERALES;
  const CICLOS_ESTUDIOS_GENERALES = C.CICLOS_ESTUDIOS_GENERALES;
  const CARRERAS_12_CICLOS = C.CARRERAS_12_CICLOS;
  const FACULTADES_12_CICLOS = C.FACULTADES_12_CICLOS;
  const FACULTAD_PLACEHOLDER = C.FACULTAD_PLACEHOLDER;
  const FACULTAD_PLACEHOLDER_PROG = C.FACULTAD_PLACEHOLDER_PROG;
  const MAX_CICLOS_DEFAULT = C.MAX_CICLOS_DEFAULT;
  const MAX_CICLOS_ESPECIALES = C.MAX_CICLOS_ESPECIALES;

  const esEstudiosGen = _dh.esEstudiosGen;
  const ordenarFacultades = (lista, hasCiclo) =>
    hasCiclo ? [PROGRAMA_ESTUDIOS_GENERALES, ...lista.sort()] : [...lista.sort()];

  const $ = _dh.$;

  function getCarrerasForFiltro(facultad, cacheFiltros) {
    if (!facultad || esEstudiosGen(facultad)) return cacheFiltros.carreras;
    return cacheFiltros.facultad_carrera[facultad] || [];
  }

  function getCiclosForFiltro(facultad, carrera, cacheFiltros) {
    if (esEstudiosGen(facultad)) return CICLOS_ESTUDIOS_GENERALES;
    const max =
      FACULTADES_12_CICLOS.includes(facultad) || CARRERAS_12_CICLOS.includes(carrera)
        ? MAX_CICLOS_ESPECIALES
        : MAX_CICLOS_DEFAULT;
    return cacheFiltros.ciclos.filter((c) => (parseInt(c) || 0) <= max);
  }

  function syncFilterActiveState(selFac, selCar, selCic) {
    const isActive = (sel) => {
      if (!sel) return false;
      const val = _dh.getSelectedValues(sel);
      return Array.isArray(val) ? val.length > 0 : val !== '';
    };
    [selFac, selCar, selCic].forEach((sel) => {
      if (sel) sel.classList.toggle('filter-active', isActive(sel));
    });
  }

  function populateSelect(sel, placeholder, items, texts) {
    const current = _dh.getSelectedValues(sel);
    sel.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach((item, i) => {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = texts ? texts[i] : item;
      if (Array.isArray(current) ? current.includes(item) : item === current) {
        opt.selected = true;
      }
      sel.appendChild(opt);
    });
  }

  function clearFilterSelect(sel) {
    if (!sel) return;
    const emptyOpt = Array.from(sel.options).find((opt) => opt.value === '');
    Array.from(sel.options).forEach((opt) => {
      opt.selected = emptyOpt ? opt === emptyOpt : false;
    });
    if (!sel.multiple) {
      sel.selectedIndex = emptyOpt ? Array.from(sel.options).indexOf(emptyOpt) : 0;
      if (emptyOpt) sel.value = '';
    }
  }

  function populateFacultadSelect(selFac, filtros) {
    const items = ordenarFacultades(filtros.facultades, filtros.has_ciclo);
    const placeholder = filtros.has_ciclo ? FACULTAD_PLACEHOLDER_PROG : FACULTAD_PLACEHOLDER;
    selFac.innerHTML = `<option value="">${placeholder}</option>`;
    items.forEach((f) => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = f;
      selFac.appendChild(opt);
    });
    selFac.selectedIndex = 0;
    selFac.value = '';
  }

  function syncFacultadCustomUI(selFac, hasCiclo) {
    if (!selFac?.__custom) return;
    selFac.__custom.update();
    selFac.__custom.button.textContent = hasCiclo ? FACULTAD_PLACEHOLDER_PROG : FACULTAD_PLACEHOLDER;
    selFac.__custom.button.classList.remove('filter-active');
    selFac.classList.remove('filter-active');
    selFac.__custom.wrapper.classList.remove('open');
  }

  /**
   * Configura los filtros para una sección específica.
   *
   * @param {string} prefix - Prefijo de la sección (ej. 'top3', 'radar')
   * @param {Object} cacheFiltros - Datos de filtros cargados del JSON (filtros.json)
   * @param {Function} onChangeCallback - Callback invocado al cambiar cualquier selección
   */
  function setup(prefix, cacheFiltros, onChangeCallback) {
    const selFac = $(`filter-facultad-${prefix}`);
    const selCar = $(`filter-carrera-${prefix}`);
    const selCic = $(`filter-ciclo-${prefix}`);
    if (!selFac) return;

    populateFacultadSelect(selFac, cacheFiltros);

    const updateCascade = () => {
      const facVal = _dh.getSelectedValues(selFac);
      if (selFac.__custom) selFac.__custom.update();
      if (selCar) {
        populateSelect(selCar, 'Todas las carreras', [...getCarrerasForFiltro(facVal, cacheFiltros)].sort());
        if (selCar.__custom) selCar.__custom.update();
      }
      const carVal = selCar?.value ?? '';
      if (selCic) {
        const ciclos = facVal || carVal ? getCiclosForFiltro(facVal, carVal, cacheFiltros) : cacheFiltros.ciclos;
        populateSelect(selCic, 'Todos los ciclos', ciclos, ciclos.map(_fmt.formatCicloText));
        if (selCic.__multiselect) selCic.__multiselect.update();
      }
      if (onChangeCallback) onChangeCallback();
      syncFilterActiveState(selFac, selCar, selCic);
    };

    selFac.addEventListener('change', updateCascade);
    if (selCar) selCar.addEventListener('change', updateCascade);
    if (selCic) selCic.addEventListener('change', updateCascade);

    if (selFac.dataset.multiselect !== 'true' && !selFac.__custom && _cs) {
      selFac.__custom = _cs.create(selFac, updateCascade);
    }
    if (selCar && selCar.dataset.multiselect !== 'true' && !selCar.__custom && _cs) {
      selCar.__custom = _cs.create(selCar, updateCascade);
    }
    if (selCic && selCic.dataset.multiselect === 'true' && !selCic.__multiselect && _ms) {
      selCic.multiple = true;
      selCic.__multiselect = _ms.create(selCic, updateCascade);
    }

    $(`reset-${prefix}`)?.addEventListener('click', () => {
      if (selFac.__custom) selFac.__custom.close();
      if (selCar && selCar.__custom) selCar.__custom.close();
      populateFacultadSelect(selFac, cacheFiltros);
      syncFacultadCustomUI(selFac, cacheFiltros.has_ciclo);
      if (selCar) {
        clearFilterSelect(selCar);
        populateSelect(selCar, 'Todas las carreras', [...cacheFiltros.carreras].sort());
        if (selCar.__custom) selCar.__custom.update();
      }
      if (selCic && selCic.multiple) {
        Array.from(selCic.options).forEach((opt) => {
          opt.selected = false;
        });
        if (selCic.__multiselect) selCic.__multiselect.update();
      } else if (selCic) {
        clearFilterSelect(selCic);
      }
      updateCascade();
    });

    updateCascade();
  }

  return { setup, esEstudiosGen, getCiclosForFiltro };
})();
