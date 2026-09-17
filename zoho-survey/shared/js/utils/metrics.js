/**
 * SURVEY METRICS — Funciones puras de cálculo de indicadores de satisfacción.
 *
 * Gemelo JS de zoho-survey/scripts/lib/metrics.py (calc_csat / calc_promedio_ponderado).
 * Ambas implementaciones deben producir el mismo resultado sobre el mismo input;
 * los tests en tests/unit/test-metrics.js verifican esta equivalencia.
 *
 * Contrato:
 * - calcBoxScore(subset, total): (subset / total) * 100. Reutilizada por T3B y T2B.
 * - calcPromedioPonderado(counts, weights, maxScale): Σ(w·c)/total/maxScale*100.
 *   No redondea internamente (precisión preservada; el redondeo ocurre al mostrar).
 *
 * @module utils/metrics
 * @version 1.0.0
 */
window.SurveyMetrics = (() => {
  'use strict';

  /**
   * Box score genérico: (subset / total) * 100.
   * T3B y T2B son casos particulares que difieren solo en el subset de conteos.
   * Rango: [0, 100]. Devuelve 0 si total es 0 (evita división por cero).
   */
  const calcBoxScore = (subset, total) => {
    if (!total) return 0;
    return (subset / total) * 100;
  };

  /**
   * Promedio Ponderado sobre escala Likert.
   * Metodología:
   *   1. proporción_i = count_i / total
   *   2. suma = Σ (proporción_i * peso_i)
   *   3. normalizado = suma / maxScale
   *   4. porcentaje = normalizado * 100
   * `counts` y `weights` deben estar alineados posicionalmente (más positivo →
   * peso mayor). No redondea: la precisión se preserva para mostrar al final.
   */
  const calcPromedioPonderado = (counts, weights, maxScale) => {
    const total = counts.reduce((a, b) => a + b, 0);
    if (!total || !maxScale) return 0;
    let sumaPonderada = 0;
    for (let i = 0; i < counts.length; i++) {
      sumaPonderada += counts[i] * weights[i];
    }
    return (sumaPonderada / total / maxScale) * 100;
  };

  /**
   * Deriva T2B % desde un objeto de distribución CSAT (los 5 niveles).
   * Útil para vistas filtradas y como fallback cuando el JSON no trae t2b_pct.
   */
  const deriveT2B = (distribution, keys) => {
    const top2Keys = keys || ['Totalmente satisfecho', 'Muy satisfecho'];
    const satKeys = window.SURVEY_CONFIG?.SAT_KEYS || [
      'Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho',
      'Insatisfecho', 'Totalmente insatisfecho',
    ];
    const subset = top2Keys.reduce((acc, k) => acc + (distribution[k] || 0), 0);
    const total = satKeys.reduce((acc, k) => acc + (distribution[k] || 0), 0);
    return calcBoxScore(subset, total);
  };

  /**
   * Deriva Promedio Ponderado % desde un objeto de distribución CSAT (los 5 niveles).
   * Usa CSAT_WEIGHTS y CSAT_SCALE_MAX de SURVEY_CONFIG (gemelo de lib/config.py).
   */
  const derivePonderado = (distribution) => {
    const cfg = window.SURVEY_CONFIG || {};
    const satKeys = cfg.SAT_KEYS || [
      'Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho',
      'Insatisfecho', 'Totalmente insatisfecho',
    ];
    const weights = cfg.CSAT_WEIGHTS || [5, 4, 3, 2, 1];
    const maxScale = cfg.CSAT_SCALE_MAX || 5;
    const counts = satKeys.map((k) => distribution[k] || 0);
    return calcPromedioPonderado(counts, weights, maxScale);
  };

  return {
    calcBoxScore,
    calcPromedioPonderado,
    deriveT2B,
    derivePonderado,
  };
})();
