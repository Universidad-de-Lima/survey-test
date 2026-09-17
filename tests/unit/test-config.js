/**
 * TESTS — SURVEY_CONFIG
 *
 * Verifica que las constantes de negocio estén definidas correctamente.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const C = window.SURVEY_CONFIG;

  if (!C) {
    console.error('SURVEY_CONFIG no encontrado.');
    return;
  }

  describe('SURVEY_CONFIG', () => {
    it('tiene META_NPS definido', () => {
      assert.isDefined(C.META_NPS);
      assert.typeOf(C.META_NPS, 'number');
    });
    it('tiene META_CSAT definido', () => {
      assert.isDefined(C.META_CSAT);
      assert.typeOf(C.META_CSAT, 'number');
    });
    it('tiene CARRERAS_12_CICLOS como array', () => {
      assert.isTrue(Array.isArray(C.CARRERAS_12_CICLOS));
      assert.isTrue(C.CARRERAS_12_CICLOS.length >= 2);
    });
    it('tiene FACULTADES_12_CICLOS como array', () => {
      assert.isTrue(Array.isArray(C.FACULTADES_12_CICLOS));
    });
    it('tiene PROGRAMA_ESTUDIOS_GENERALES', () => {
      assert.typeOf(C.PROGRAMA_ESTUDIOS_GENERALES, 'string');
    });
    it('tiene CICLOS_ESTUDIOS_GENERALES como array', () => {
      assert.isTrue(Array.isArray(C.CICLOS_ESTUDIOS_GENERALES));
      assert.equal(C.CICLOS_ESTUDIOS_GENERALES.length, 2);
    });
    it('tiene SAT_KEYS con 5 niveles', () => {
      assert.isTrue(Array.isArray(C.SAT_KEYS));
      assert.equal(C.SAT_KEYS.length, 5);
    });
    it('META_CSAT está entre 0 y 100', () => {
      assert.isTrue(C.META_CSAT >= 0 && C.META_CSAT <= 100);
    });
    it('META_NPS está entre -100 y 100', () => {
      assert.isTrue(C.META_NPS >= -100 && C.META_NPS <= 100);
    });
  });
})();
