/**
 * SURVEY MULTISELECT — Dropdown de selección múltiple con checkboxes.
 *
 * Reemplaza un <select multiple> nativo por un dropdown visual con:
 * - Checkboxes para selección múltiple
 * - Botón muestra conteo ("3 ciclos seleccionados")
 * - Cierre al hacer click fuera
 * - ARIA attributes para accesibilidad
 *
 * Extraído de dashboard.js (v2.0). Sin dependencias externas.
 *
 * @module components/multiselect
 * @version 1.0.0
 */
window.SurveyMultiselect = (() => {
  'use strict';

  // ── Utilidades: delegar a SurveyDOMHelpers ──
  const _dh = window.SurveyDOMHelpers;

  function getSelectedValues(sel) {
    return _dh.getSelectedValues(sel);
  }

  function setSelectedValues(sel, values) {
    _dh.setSelectedValues(sel, values);
  }

  function formatMultiselectLabel(values, placeholder, itemName = 'ciclos') {
    return _dh.formatMultiselectLabel(values, placeholder, itemName);
  }

  // ── Factory ──

  /**
   * Crea un dropdown multiselect que reemplaza visualmente un <select multiple>.
   *
   * @param {HTMLSelectElement} selCic - El elemento <select multiple> original
   * @param {Function} [onChangeCallback] - Callback opcional al cambiar selección
   * @returns {HTMLElement} El elemento wrapper (tiene método .update())
   */
  function create(selCic, onChangeCallback, defaultLabel = 'Todos los ciclos', itemName = 'ciclos') {
    if (!selCic) return null;

    const wrapper = document.createElement('div');
    wrapper.className = 'filter-multiselect';
    wrapper.style.position = 'relative';

    const getSelectedLabels = () => {
      const opts = Array.from(selCic.options).filter(opt => opt.selected);
      return opts.length ? opts.map(opt => opt.textContent) : [];
    };

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-select filter-multiselect-toggle';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');
    button.textContent = formatMultiselectLabel(getSelectedLabels(), defaultLabel, itemName);
    wrapper.appendChild(button);

    const panel = document.createElement('div');
    panel.className = 'filter-multiselect-panel';
    panel.setAttribute('role', 'listbox');
    panel.hidden = true;
    wrapper.appendChild(panel);

    const renderOptions = () => {
      const selected = getSelectedValues(selCic);
      panel.innerHTML = '';
      Array.from(selCic.options).forEach((opt) => {
        if (!opt.value) return;
        const item = document.createElement('label');
        item.className = 'filter-multiselect-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = opt.value;
        checkbox.checked = Array.isArray(selected)
          ? selected.includes(opt.value)
          : selected === opt.value;
        checkbox.addEventListener('change', () => {
          const checkedValues = Array.from(
            panel.querySelectorAll('input[type="checkbox"]:checked'),
          ).map((i) => i.value);
          setSelectedValues(selCic, checkedValues);
          button.textContent = formatMultiselectLabel(getSelectedLabels(), defaultLabel, itemName);
          selCic.classList.toggle('filter-active', checkedValues.length > 0);
          button.classList.toggle('filter-active', checkedValues.length > 0);
          if (onChangeCallback) onChangeCallback();
        });
        const span = document.createElement('span');
        span.textContent = opt.textContent || opt.value;
        item.appendChild(checkbox);
        item.appendChild(span);
        panel.appendChild(item);
      });
      const anySelected =
        Array.from(panel.querySelectorAll('input[type="checkbox"]:checked')).length > 0;
      button.classList.toggle('filter-active', anySelected);
    };

    const openPanel = () => {
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      wrapper.classList.add('open');
      button.classList.add('filter-active');
      selCic.classList.add('filter-active');
    };

    const closePanel = () => {
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      wrapper.classList.remove('open');
      const vals = getSelectedValues(selCic);
      const any = Array.isArray(vals) ? vals.length > 0 : !!vals;
      if (!any) {
        button.classList.remove('filter-active');
        selCic.classList.remove('filter-active');
      }
    };

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (panel.hidden) openPanel();
      else closePanel();
    });
    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openPanel();
      }
    });
    document.addEventListener('click', (event) => {
      if (!wrapper.contains(event.target)) closePanel();
    });

    wrapper.update = () => {
      renderOptions();
      const vals = getSelectedValues(selCic);
      const any = Array.isArray(vals) ? vals.length > 0 : !!vals;
      button.textContent = formatMultiselectLabel(getSelectedLabels(), defaultLabel, itemName);
      button.classList.toggle('filter-active', any);
    };

    // Ocultar el select original (accesible para screen readers, invisible visualmente)
    selCic.style.position = 'absolute';
    selCic.style.opacity = '0';
    selCic.style.pointerEvents = 'none';
    selCic.style.width = '1px';
    selCic.style.height = '1px';
    selCic.style.margin = '0';
    selCic.style.border = 'none';
    selCic.setAttribute('aria-hidden', 'true');
    selCic.tabIndex = -1;

    selCic.parentNode.insertBefore(wrapper, selCic.nextSibling);
    return wrapper;
  }

  return { create };
})();
