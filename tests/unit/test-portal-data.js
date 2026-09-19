/**
 * Tests — Capa de datos del portal (portal/portal-data.js)
 *
 * Fija el comportamiento que faltaba: cuando un nivel solo tiene la entrada
 * marcadora de periodos.json (proyecto sin datos publicados), NO hay periodo
 * real y la fase correspondiente debe mostrarse "en construcción" en lugar de
 * intentar cargar un dashboard inexistente.
 *
 * Ejecutar: job `JavaScript unit tests` de GitHub Actions (nada en local).
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const core = window.SurveyPortalCore;
  const data = window.SurveyPortalData;

  const MARCADOR = { id: 'proximamente', label: 'Próximamente', url: 'underconstruction.html', isNew: true };

  describe('portal-data — periodosReales', () => {
    it('descarta el marcador de "en construcción"', () => {
      assert.deepEqual(core.periodosReales([MARCADOR]), []);
    });

    it('conserva los periodos reales, en orden', () => {
      const lista = [{ id: '2025-2', url: '2025-2/index.html' }, MARCADOR, { id: '2026-1', url: '2026-1/index.html' }];
      assert.deepEqual(core.periodosReales(lista), ['2025-2', '2026-1']);
    });

    it('ignora entradas malformadas sin romper', () => {
      assert.deepEqual(core.periodosReales([null, 'texto', {}, { id: '' }, { id: '2026-1' }]), ['2026-1']);
    });

    it('no falla si no recibe una lista', () => {
      assert.deepEqual(core.periodosReales(null), []);
      assert.deepEqual(core.periodosReales(undefined), []);
    });
  });

  describe('portal-data — faseConDatos', () => {
    it('1.0 sin periodos reales no tiene datos', () => {
      assert.equal(core.faseConDatos('1.0', [], []), false);
    });

    it('1.0 con un periodo real si tiene datos', () => {
      assert.equal(core.faseConDatos('1.0', ['2026-1'], []), true);
    });

    it('1.2 depende de la lista de graduados', () => {
      assert.equal(core.faseConDatos('1.2', ['2026-1'], []), false);
      assert.equal(core.faseConDatos('1.2', [], ['2026']), true);
    });

    it('las demas fases no tienen dashboard de datos propio', () => {
      assert.equal(core.faseConDatos('1.1', ['2026-1'], ['2026']), false);
      assert.equal(core.faseConDatos('1.3', ['2026-1'], ['2026']), false);
    });
  });

  describe('portal-data — tieneDatosDeFase (estado real al arrancar)', () => {
    it('sin nada cargado, 1.0 y 1.2 no tienen datos', () => {
      assert.equal(data.tieneDatosDeFase('1.0'), false);
      assert.equal(data.tieneDatosDeFase('1.2'), false);
    });
  });
})();
