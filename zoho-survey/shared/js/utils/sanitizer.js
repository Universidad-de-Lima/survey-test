/**
 * SURVEY SANITIZER — Funciones de sanitización HTML.
 *
 * Previene XSS en contenido dinámico insertado vía innerHTML.
 * Extraído de dashboard.js (v2.0). Sin dependencias externas.
 *
 * Contrato:
 * - escapeHTML(str): escapa & < > " '. Devuelve string seguro.
 * - sanitizeHTML(html): permite solo 9 tags (<br>, <strong>, <em>, <i>, <span>,
 *   <table>, <tr>, <td>, <th>) SIN atributos. Cualquier atributo (incluidos on*) se elimina. Tags no
 *   permitidos se escapan (se muestran como texto literal).
 *   Tags permitidos (9): br, strong, em, i, span, table, tr, td, th.
 *
 * Algoritmo de sanitizeHTML:
 *   1. Extrae placeholders para tags permitidos (open y close) en el string original.
 *   2. Reemplaza cada tag permitido por un placeholder seguro (token único).
 *   3. Escapa TODO el resto (incluye cualquier tag no permitido y cualquier atributo).
 *   4. Restaura los placeholders a los tags permitidos limpios (sin atributos).
 *
 * @module utils/sanitizer
 * @version 1.1.0
 */
window.SurveySanitizer = (() => {
  'use strict';

  const ALLOWED_TAGS = ['br', 'strong', 'em', 'i', 'span', 'table', 'tr', 'td', 'th'];

  /**
   * Escapa caracteres HTML peligrosos.
   * @param {string} str - Texto a escapar
   * @returns {string} Texto seguro para insertar en HTML
   */
  const escapeHTML = (str) => {
    if (!str || typeof str !== 'string') return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };

  /**
   * Sanitiza HTML permitiendo solo una whitelist mínima de tags sin atributos.
   * Tags permitidos (9): <br>, <strong>, <em>, <i>, <span>,
   *                    <table>, <tr>, <td>, <th>.
   * Cualquier atributo (incluidos on*) se elimina silenciosamente.
   * @param {string} html - HTML potencialmente inseguro
   * @returns {string} HTML sanitizado
   */
  const sanitizeHTML = (html) => {
    if (!html || typeof html !== 'string') return '';

    // Construir regex que casa cualquier tag permitido (open o close) con o sin atributos.
    // Ejemplos que casa:
    //   <span>, <span class="x">, <span onclick="alert(1)">, </span>, <br/>, <br />
    const allowedPattern = new RegExp(
      '</?(?:' + ALLOWED_TAGS.join('|') + ')\\b[^>]*?/?>',
      'gi'
    );

    // 1. Reemplazar cada tag permitido por un placeholder seguro.
    //    Los placeholders no contienen < > para sobrevivir al escapeHTML.
    const placeholders = [];
    let safe = html.replace(allowedPattern, (match) => {
      // Determinar si es open o close tag
      const isClose = match.startsWith('</');
      // Extraer nombre del tag
      const tagMatch = match.match(/^<\/?([a-z]+)/i);
      const tagName = tagMatch ? tagMatch[1].toLowerCase() : '';
      // Self-closing? (ej. <br/>)
      const isSelfClosing = match.endsWith('/>') || tagName === 'br';
      // Generar placeholder único
      const placeholder = `\x00PH${placeholders.length}\x00`;
      if (isClose) {
        placeholders.push(`</${tagName}>`);
      } else if (isSelfClosing) {
        placeholders.push(`<${tagName}>`);
      } else {
        placeholders.push(`<${tagName}>`);
      }
      return placeholder;
    });

    // 2. Escapar TODO el resto. Esto escapa cualquier tag no permitido y
    //    cualquier atributo que haya quedado fuera de un tag permitido.
    safe = escapeHTML(safe);

    // 3. Restaurar placeholders a los tags permitidos limpios.
    //    Los placeholders sobrevivieron al escapeHTML porque no contienen < > " ' &.
    placeholders.forEach((replacement, idx) => {
      const placeholder = `\x00PH${idx}\x00`;
      safe = safe.split(placeholder).join(replacement);
    });

    return safe;
  };

  return { escapeHTML, sanitizeHTML };
})();
