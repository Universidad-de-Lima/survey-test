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

  // La dimensión "Software" se reconoce por su id declarado, nunca por su nombre
  // publicado: si la declaración publicada renombra la pregunta, la cursiva debe
  // seguir cayendo en su primera palabra. La declaración viaja en el bloque
  // `preguntas` de los resúmenes que el portal carga (filtros.json).
  const ID_DIMENSION_SOFTWARE = 'software_especializado_empleado_en_la_carrera';
  const NOMBRE_SOFTWARE_HEREDADO = 'Software especializado empleado en la carrera';

  const nombreDeDimensionSoftware = () => {
    try {
      const portal = window.SurveyPortalData;
      const datos = portal && portal.getSurveyData ? portal.getSurveyData() : null;
      const lista = (datos && datos.filtros && datos.filtros.preguntas) || [];
      const decl = lista.filter((x) => x && x.id === ID_DIMENSION_SOFTWARE)[0];
      if (decl && decl.nombre) return decl.nombre;
    } catch (e) {
      /* sin datos del portal: se usa el nombre heredado */
    }
    return NOMBRE_SOFTWARE_HEREDADO;
  };

  const esDimensionSoftware = (dim) => dim === nombreDeDimensionSoftware();

  const formatDimensionName = (dim) => {
    if (esDimensionSoftware(dim)) {
      const texto = String(dim);
      const palabra = texto.split(' ')[0];
      return '<span><i>' + escapeHTML(palabra) + '</i>' + escapeHTML(texto.slice(palabra.length)) + '</span>';
    }
    return escapeHTML(dim);
  };

  const formatDimensionNameSVG = (dim, maxLen = 26) => {
    const plain = formatDimensionName(dim).replace(/<[^>]*>/g, '');
    const truncated = cortarTexto(plain, maxLen);
    const palabra = String(dim).split(' ')[0];
    if (esDimensionSoftware(dim) && truncated.startsWith(palabra)) {
      return `<tspan font-style="italic">${palabra}</tspan>${escapeHTML(truncated.slice(palabra.length))}`;
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
    esDimensionSoftware,
  };
})();
