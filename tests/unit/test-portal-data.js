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

  describe('portal-data — nivelDeFase', () => {
    it('mapea cada item con datos a su carpeta', () => {
      assert.equal(core.nivelDeFase('1.0'), 'students/undergraduate');
      assert.equal(core.nivelDeFase('1.1'), 'students/postgraduate');
      assert.equal(core.nivelDeFase('1.2'), 'students/graduate');
      assert.equal(core.nivelDeFase('1.3'), 'alumni/undergraduate');
      assert.equal(core.nivelDeFase('1.4'), 'alumni/postgraduate');
      assert.equal(core.nivelDeFase('1.5'), 'facultystaff/undergraduate');
      assert.equal(core.nivelDeFase('1.6'), 'facultystaff/postgraduate');
      assert.equal(core.nivelDeFase('1.7'), 'nonfacultystaff');
      assert.equal(core.nivelDeFase('1.8'), 'employers');
    });

    it('el item de preguntas (1.9) no tiene carpeta de datos', () => {
      assert.equal(core.nivelDeFase('1.9'), null);
    });

    it('un item desconocido no tiene carpeta', () => {
      assert.equal(core.nivelDeFase('9.9'), null);
    });

    it('cada carpeta del mapa existe en el repositorio con su periodos.json', () => {
      const fs = require('fs');
      const path = require('path');
      const raiz = path.resolve(__dirname, '..', '..');
      Object.keys(core.NIVELES_FASE).forEach(id => {
        const archivo = path.join(raiz, 'zoho-survey', core.NIVELES_FASE[id], 'periodos.json');
        assert.isTrue(fs.existsSync(archivo), 'falta ' + archivo);
      });
    });
  });

  describe('portal-data — periodosDeFase / faseConDatos (puros)', () => {
    const MAPA = { '1.0': ['2026-1', '2025-2'], '1.1': [] };

    it('devuelve los periodos del item pedido', () => {
      assert.deepEqual(core.periodosDeFase('1.0', MAPA), ['2026-1', '2025-2']);
    });

    it('un item sin periodos devuelve lista vacia', () => {
      assert.deepEqual(core.periodosDeFase('1.1', MAPA), []);
      assert.deepEqual(core.periodosDeFase('1.2', MAPA), []);
    });

    it('faseConDatos distingue con y sin datos', () => {
      assert.equal(core.faseConDatos('1.0', MAPA), true);
      assert.equal(core.faseConDatos('1.1', MAPA), false);
    });

    it('sin mapa no falla', () => {
      assert.deepEqual(core.periodosDeFase('1.0', null), []);
      assert.equal(core.faseConDatos('1.0', null), false);
    });
  });

  describe('portal-data — estado real al arrancar', () => {
    it('sin nada cargado, ningun item tiene datos', () => {
      assert.equal(data.tieneDatosDeFase('1.0'), false);
      assert.equal(data.tieneDatosDeFase('1.1'), false);
      assert.equal(data.tieneDatosDeFase('1.8'), false);
    });

    it('getPeriodosDeFase devuelve lista vacia sin datos', () => {
      assert.deepEqual(data.getPeriodosDeFase('1.0'), []);
    });
  });
})();
