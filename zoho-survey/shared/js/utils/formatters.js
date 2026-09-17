/**
 * SURVEY FORMATTERS — Funciones puras de formateo.
 *
 * Extraídas de dashboard.js (v2.0). Sin dependencias externas.
 * Usar como: SurveyFormatters.formatDecimal(3.14159, 2) → "3,14"
 *
 * Contrato:
 * - formatDecimal(n, digits=2): SIEMPRE muestra `digits` decimales, incluso
 *   cuando todos son cero. Ejemplo: formatDecimal(1.5) → "1,50"; formatDecimal(3.0) → "3,00".
 *   Usa toFixed() que trunca (no redondea) en casos de float impreciso
 *   (ej. 1.2345 → "1,234" porque 1.2345 en float es 1.2344999...).
 *
 * @module utils/formatters
 * @version 1.1.0
 */
window.SurveyFormatters = (() => {
  'use strict';

  // ── Números ──
  const formatInteger = (n) => {
    if (n === null || n === undefined) return '';
    // Enteros SIN separador de miles (1000, no 1,000)
    return Number(n).toLocaleString('es-PE', { useGrouping: false });
  };

  const formatDecimal = (n, digits = 2) => {
    if (n === null || n === undefined) return '';
    return n.toFixed(digits).replace('.', ',');
  };

  const formatPercent = (n, digits = 2) => formatDecimal(n, digits) + ' %';

  // Formatea un indicador de satisfacción preservando precisión interna y
  // redondeando únicamente al mostrar (contrato de T2B y Promedio Ponderado).
  const formatScore = (n, digits = 2) => {
    if (n === null || n === undefined) return '';
    return formatDecimal(n, digits) + ' %';
  };

  // Label de barra con 2 decimales (valor real). El layout ajusta el ancho
  // si el texto desborda el segmento (ver adjustSegmentLabels en dashboard.js).
  const formatPctSimple = (v, t) => (t === 0 ? '0,00 %' : formatDecimal((v / t) * 100, 2) + ' %');

  // Alias explícito para casos donde se quiera 2 decimales con símbolo %.
  const formatPctSimple2 = (v, t) => (t === 0 ? '0,00 %' : formatDecimal((v / t) * 100, 2) + ' %');

  const formatPctDecimal = (v, t) => {
    if (t === 0) return '0,00 %';
    return formatDecimal((v / t) * 100, 2) + ' %';
  };

  // ── Fechas ──
  const formatDate = (ds) =>
    new Date(`${ds}T12:00:00`).toLocaleDateString('es-PE', { day: 'numeric', month: 'long' });

  // ── Ciclos ──
  const formatCicloText = (ciclo) => {
    const match = ciclo.match(/^(\d+)/);
    if (!match) return ciclo;
    const num = match[1];
    return num === '1' || num === '3' ? `${num}.ᵉʳ ciclo` : `${num}.º ciclo`;
  };

  // ── Texto ──
  const cortarTexto = (t, max) => (t.length > max ? `${t.slice(0, max - 1)}…` : t);

  // ── Nombres de dimensión ──
  const escapeHTML = (s) =>
    String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
    );

  const formatDimensionName = (dim) => {
    if (dim === 'Software especializado empleado en la carrera') {
      return '<span><i>Software</i> especializado empleado en la carrera</span>';
    }
    return escapeHTML(dim);
  };

  const formatDimensionNameSVG = (dim, maxLen = 26) => {
    const plain = formatDimensionName(dim).replace(/<[^>]*>/g, '');
    const truncated = cortarTexto(plain, maxLen);
    if (
      dim === 'Software especializado empleado en la carrera' &&
      truncated.startsWith('Software')
    ) {
      return `<tspan font-style="italic">Software</tspan>${escapeHTML(truncated.slice('Software'.length))}`;
    }
    return truncated;
  };

  const formatDimensionNameForAttr = (dim) =>
    formatDimensionName(dim)
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

  return {
    formatInteger,
    formatDecimal,
    formatPercent,
    formatScore,
    formatPctSimple,
    formatPctSimple2,
    formatPctDecimal,
    formatDate,
    formatCicloText,
    cortarTexto,
    formatDimensionName,
    formatDimensionNameSVG,
    formatDimensionNameForAttr,
  };
})();
