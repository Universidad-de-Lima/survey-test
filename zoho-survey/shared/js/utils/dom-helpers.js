/**
 * SURVEY DOM HELPERS — Utilidades compartidas de manipulación de DOM.
 *
 * Funciones usadas por custom-select.js, multiselect.js, dashboard.js y otros módulos.
 * Centralizadas aquí para evitar duplicación (A2 de auditoría v2.0).
 * Incluye helpers de propósito general: $, esEstudiosGen, sumKeys.
 *
 * @module utils/dom-helpers
 * @version 1.2.0
 */
window.SurveyDOMHelpers = (() => {
  'use strict';

  // ── Config para helpers de negocio ──
  const C = window.SURVEY_CONFIG || {};
  const PROGRAMA_ESTUDIOS_GENERALES = C.PROGRAMA_ESTUDIOS_GENERALES;

  /**
   * Atajo para document.getElementById.
   * @param {string} id
   * @returns {HTMLElement|null}
   */
  const $ = (id) => document.getElementById(id);

  /**
   * Verifica si una facultad es "Programa de Estudios Generales".
   * @param {string} fac
   * @returns {boolean}
   */
  const esEstudiosGen = (fac) => fac === PROGRAMA_ESTUDIOS_GENERALES;

  /**
   * Suma valores de un objeto para todas las claves dadas.
   * @param {Object} row - Objeto con valores numéricos
   * @param {string[]} keys - Lista de claves a sumar
   * @returns {number}
   */
  const sumKeys = (row, keys) => keys.reduce((acc, key) => acc + (row[key] || 0), 0);

  /**
   * Obtiene el valor(es) seleccionado(s) de un <select>.
   * Soporta select simple y multiple.
   * @param {HTMLSelectElement} sel
   * @returns {string|string[]} Valor(es) seleccionado(s), o '' si ninguno
   */
  function getSelectedValues(sel) {
    if (!sel) return '';
    if (sel.multiple) {
      const vals = Array.from(sel.selectedOptions).map((opt) => opt.value).filter(Boolean);
      return vals.length ? vals : '';
    }
    const opt = sel.options[sel.selectedIndex];
    return opt ? opt.value : '';
  }

  /**
   * Establece el valor(es) seleccionado(s) en un <select>.
   * Dispara evento 'change' automáticamente.
   * @param {HTMLSelectElement} sel
   * @param {string|string[]} values
   */
  function setSelectedValues(sel, values) {
    if (!sel) return;
    if (!sel.multiple) {
      sel.value = Array.isArray(values) ? values[0] || '' : values || '';
    } else {
      const normalized = new Set((Array.isArray(values) ? values : [values]).filter(Boolean));
      Array.from(sel.options).forEach((opt) => {
        opt.selected = normalized.has(opt.value);
      });
    }
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  }

  /**
   * Obtiene el texto del placeholder de un <select>.
   * @param {HTMLSelectElement} sel
   * @returns {string}
   */
  function getPlaceholderText(sel) {
    const emptyOption = sel.querySelector('option[value=""]');
    return emptyOption ? emptyOption.textContent : 'Seleccione';
  }

  /**
   * Formatea la etiqueta visible de un custom select según su valor actual.
   * @param {HTMLSelectElement} sel
   * @returns {string}
   */
  function formatCustomLabel(sel) {
    const selected = getSelectedValues(sel);
    if (!selected) return getPlaceholderText(sel);
    const selectedOption = Array.from(sel.options).find((opt) => opt.value === selected);
    return selectedOption ? selectedOption.textContent : selected;
  }

  /**
   * Formatea la etiqueta de un multiselect mostrando conteo.
   * @param {string[]} values - Valores seleccionados
   * @param {string} placeholder - Texto cuando no hay selección
   * @param {string} [itemName='ciclos'] - Sustantivo plural para el conteo (ej. 'ciclos', 'categorías')
   * @returns {string}
   */
  function formatMultiselectLabel(values, placeholder, itemName = 'ciclos') {
    if (!values || !values.length) return placeholder;
    if (values.length === 1) return values[0];
    return `${values.length} ${itemName} seleccionados`;
  }

  return {
    $,
    esEstudiosGen,
    sumKeys,
    getSelectedValues,
    setSelectedValues,
    getPlaceholderText,
    formatCustomLabel,
    formatMultiselectLabel,
  };
})();
