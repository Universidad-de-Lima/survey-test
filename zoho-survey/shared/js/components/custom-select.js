/**
 * SURVEY CUSTOM SELECT — Dropdown personalizado accesible.
 *
 * Reemplaza un <select> nativo por un dropdown visual con:
 * - Búsqueda por teclado (ArrowDown, Enter, Space)
 * - Cierre al hacer click fuera
 * - Estado activo reflejado en el botón
 * - ARIA attributes para accesibilidad
 *
 * Extraído de dashboard.js (v2.0). Sin dependencias externas.
 *
 * @module components/custom-select
 * @version 1.0.0
 */
window.SurveyCustomSelect = (() => {
  'use strict';

  // ── Utilidades: delegar a SurveyDOMHelpers ──
  const _dh = window.SurveyDOMHelpers;

  function getSelectedValues(sel) {
    return _dh.getSelectedValues(sel);
  }

  function setSelectedValues(sel, values) {
    _dh.setSelectedValues(sel, values);
  }

  function getPlaceholderText(sel) {
    return _dh.getPlaceholderText(sel);
  }

  function formatCustomLabel(sel) {
    return _dh.formatCustomLabel(sel);
  }

  // ── Factory ──

  /**
   * Crea un dropdown personalizado que reemplaza visualmente un <select>.
   *
   * @param {HTMLSelectElement} sel - El elemento <select> original
   * @param {Function} [onChangeCallback] - Callback opcional al cambiar selección
   * @returns {{ update: Function, close: Function, button: HTMLElement, wrapper: HTMLElement }}
   */
  function create(sel, onChangeCallback) {
    if (!sel) return null;

    const wrapper = document.createElement('div');
    wrapper.className = 'filter-custom-select';
    wrapper.style.position = 'relative';

    sel.classList.add('filter-select-hidden');
    sel.parentNode.insertBefore(wrapper, sel);
    wrapper.appendChild(sel);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-select filter-custom-toggle';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');
    button.textContent = formatCustomLabel(sel);
    wrapper.appendChild(button);

    const panel = document.createElement('div');
    panel.className = 'filter-custom-panel';
    panel.setAttribute('role', 'listbox');
    panel.hidden = true;
    wrapper.appendChild(panel);

    const renderOptions = () => {
      const currentValue = getSelectedValues(sel);
      panel.innerHTML = '';
      Array.from(sel.options).forEach((opt) => {
        if (!opt.value) return;
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'filter-custom-item';
        item.setAttribute('role', 'option');
        item.dataset.value = opt.value;
        item.textContent = opt.textContent || opt.value;
        if (opt.value === currentValue) {
          item.classList.add('active');
          item.setAttribute('aria-selected', 'true');
        }
        item.addEventListener('click', () => {
          setSelectedValues(sel, opt.value);
          button.textContent = item.textContent;
          renderOptions();
          closePanel();
          if (onChangeCallback) onChangeCallback();
        });
        panel.appendChild(item);
      });
      const any = Boolean(getSelectedValues(sel));
      button.classList.toggle('filter-active', any);
    };

    const openPanel = () => {
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      wrapper.classList.add('open');
      button.classList.add('filter-active');
      sel.classList.add('filter-active');
    };

    const closePanel = () => {
      panel.hidden = true;
      button.setAttribute('aria-expanded', 'false');
      wrapper.classList.remove('open');
      if (!getSelectedValues(sel)) {
        button.classList.remove('filter-active');
        sel.classList.remove('filter-active');
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

    sel.addEventListener('change', () => {
      const selected = getSelectedValues(sel);
      button.textContent = selected ? formatCustomLabel(sel) : getPlaceholderText(sel);
      const any = Boolean(selected);
      button.classList.toggle('filter-active', any);
      sel.classList.toggle('filter-active', any);
      renderOptions();
    });

    const update = () => {
      renderOptions();
      const selected = getSelectedValues(sel);
      button.textContent = selected ? formatCustomLabel(sel) : getPlaceholderText(sel);
      const active = Boolean(selected);
      button.classList.toggle('filter-active', active);
      sel.classList.toggle('filter-active', active);
    };

    renderOptions();
    return { update, close: closePanel, button, wrapper };
  }

  return { create };
})();
