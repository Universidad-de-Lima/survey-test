/**
 * TESTS — renderInsightsIA (sentiment-view.js Fase 8)
 *
 * Prueba la función renderInsightsIA que pobla el div #insight-cualitativo
 * con insights_ia del sentimiento.json.
 *
 * Requiere mock mínimo de document/window para ejecutar en Node.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const SV = window.SurveySentimentView;

  if (!SV) {
    console.error('SurveySentimentView no encontrado.');
    return;
  }

  describe('renderInsightsIA', () => {
    it('existe como función pública', () => {
      assert.equal(typeof SV.renderInsightsIA, 'function');
    });

    it('maneja datos nulos sin romper', () => {
      // No debe lanzar excepción cuando sentimientoData es null/undefined
      let threw = false;
      try {
        SV.renderInsightsIA(null);
        SV.renderInsightsIA(undefined);
        SV.renderInsightsIA({});
      } catch (e) {
        threw = true;
      }
      assert.isFalse(threw, 'renderInsightsIA no debe lanzar con datos nulos');
    });

    it('maneja insights_ia ausente', () => {
      // Si el JSON no tiene insights_ia, debe mostrar mensaje de fallback
      // Como no hay DOM real en Node, solo verificamos que no lance excepción
      let threw = false;
      try {
        SV.renderInsightsIA({ comentarios: [], topicos: [] });
      } catch (e) {
        threw = true;
      }
      assert.isFalse(threw, 'renderInsightsIA no debe lanzar sin insights_ia');
    });

    it('acepta estructura completa de insights_ia', () => {
      // Estructura válida: global + por_categoria_padre
      const data = {
        insights_ia: {
          global: 'El análisis revela que el tema más relevante es X con 100 menciones.',
          por_categoria_padre: {
            'Académico': 'Categoría académica concentra 500 menciones.',
            'Tecnología': 'Se registran 50 comentarios sobre tecnología.',
          }
        }
      };
      let threw = false;
      try {
        SV.renderInsightsIA(data);
      } catch (e) {
        threw = true;
      }
      assert.isFalse(threw, 'renderInsightsIA debe aceptar estructura completa');
    });
  });
})();
