/**
 * TESTS — SurveyMetrics (gemelo JS de lib/metrics.py)
 *
 * Verifica que las funciones JS produzcan los mismos resultados que su
 * contraparte Python sobre los mismos inputs. Ejecutar: abrir tests/run-tests.html.
 *
 * Contrato verificado:
 * - calcBoxScore(subset, total): (subset / total) * 100, 0 si total=0.
 * - calcPromedioPonderado(counts, weights, maxScale): Σ(w·c)/total/maxScale*100,
 *   sin redondeo interno (precisión preservada).
 * - deriveT2B / derivePonderado: derivan desde un objeto de distribución CSAT.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const M = window.SurveyMetrics;

  if (!M) {
    console.error('SurveyMetrics no encontrado. Asegúrate de cargar utils/metrics.js antes.');
    return;
  }

  describe('calcBoxScore', () => {
    it('calcula (subset / total) * 100', () => {
      assert.equal(M.calcBoxScore(4148, 4239), (4148 / 4239) * 100);
    });
    it('retorna 0 para total cero (evita división por cero)', () => {
      assert.equal(M.calcBoxScore(5, 0), 0);
    });
    it('100% cuando subset = total', () => {
      assert.equal(M.calcBoxScore(100, 100), 100);
    });
  });

  describe('calcPromedioPonderado', () => {
    it('caso real 2026-1: 1806,1281,1061,75,16 → 82.58 % (aprox)', () => {
      // Gemelo del test Python; verifica equivalencia Python↔JS.
      const result = M.calcPromedioPonderado([1806, 1281, 1061, 75, 16], [5, 4, 3, 2, 1], 5);
      assert.isTrue(Math.abs(result - 82.5810) < 0.001, `esperado ~82.581, obtenido ${result}`);
    });
    it('todos en peso máximo → 100 %', () => {
      assert.equal(M.calcPromedioPonderado([100, 0, 0, 0, 0], [5, 4, 3, 2, 1], 5), 100);
    });
    it('todos en peso mínimo → 20 %', () => {
      assert.equal(M.calcPromedioPonderado([0, 0, 0, 0, 100], [5, 4, 3, 2, 1], 5), 20);
    });
    it('retorna 0 para total cero', () => {
      assert.equal(M.calcPromedioPonderado([0, 0, 0, 0, 0], [5, 4, 3, 2, 1], 5), 0);
    });
    it('no redondea internamente (precisión preservada)', () => {
      const result = M.calcPromedioPonderado([1806, 1281, 1061, 75, 16], [5, 4, 3, 2, 1], 5);
      assert.isTrue(result !== Math.round(result * 100) / 100, 'debe conservar decimales');
    });
  });

  describe('deriveT2B', () => {
    it('deriva T2B desde la distribución CSAT', () => {
      const dist = {
        'Totalmente satisfecho': 1806,
        'Muy satisfecho': 1281,
        'Satisfecho': 1061,
        'Insatisfecho': 75,
        'Totalmente insatisfecho': 16,
      };
      // 3087 / 4239 * 100 ≈ 72.82
      const result = M.deriveT2B(dist);
      assert.isTrue(Math.abs(result - 72.82) < 0.01, `esperado ~72.82, obtenido ${result}`);
    });
  });

  describe('derivePonderado', () => {
    it('deriva Promedio Ponderado desde la distribución CSAT', () => {
      const dist = {
        'Totalmente satisfecho': 1806,
        'Muy satisfecho': 1281,
        'Satisfecho': 1061,
        'Insatisfecho': 75,
        'Totalmente insatisfecho': 16,
      };
      const result = M.derivePonderado(dist);
      assert.isTrue(Math.abs(result - 82.5810) < 0.001, `esperado ~82.581, obtenido ${result}`);
    });
  });
})();
