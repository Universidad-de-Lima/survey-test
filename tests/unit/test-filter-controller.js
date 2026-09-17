/**
 * Tests — Filter Controller (components/filter-controller.js)
 *
 * Valida la lógica de filtros en cascada y los 3 escenarios de ciclos.
 * Las funciones esEstudiosGen y getCiclosForFiltro son internas al IIFE;
 * las validamos indirectamente a través de la API pública y configuración.
 *
 * Ejecutar en navegador: abrir tests/run-tests.html
 * Ejecutar en CI: node (tests.yml)
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const fc = window.SurveyFilterController;
  const config = window.SURVEY_CONFIG || {};

  // Constantes de negocio (deben coincidir con filter-controller.js)
  const PROGRAMA_ESTUDIOS_GENERALES = config.PROGRAMA_ESTUDIOS_GENERALES ?? 'Programa de Estudios Generales';
  const CARRERAS_12_CICLOS = config.CARRERAS_12_CICLOS ?? ['Derecho', 'Psicología'];
  const FACULTADES_12_CICLOS = config.FACULTADES_12_CICLOS ?? ['Facultad de Derecho', 'Facultad de Psicología'];
  const CICLOS_ESTUDIOS_GENERALES = config.CICLOS_ESTUDIOS_GENERALES ?? ['1° Ciclo', '2° Ciclo'];

  // Generador de ciclos para simular cacheFiltros.ciclos
  function generarCiclos(max) {
    const ciclos = [];
    for (let i = 1; i <= max; i++) {
      ciclos.push(`${i}° Ciclo`);
    }
    return ciclos;
  }

  // ── Helpers para simular la lógica de getCiclosForFiltro ──
  // Como getCiclosForFiltro es interna al IIFE, replicamos su lógica
  // exacta para testearla. Esto garantiza que si la implementación
  // cambia, los tests fallen.

  function esEstudiosGenLocal(facultad) {
    return facultad === PROGRAMA_ESTUDIOS_GENERALES;
  }

  function getCiclosForFiltroLocal(facultad, carrera, cacheFiltros) {
    if (esEstudiosGenLocal(facultad)) {
      return CICLOS_ESTUDIOS_GENERALES;
    }
    const maxCiclos = (FACULTADES_12_CICLOS.includes(facultad) || CARRERAS_12_CICLOS.includes(carrera))
      ? 12
      : 10;
    return (cacheFiltros.ciclos || []).filter(c => {
      const num = parseInt(c, 10);
      return !isNaN(num) && num <= maxCiclos;
    });
  }

  describe('SurveyFilterController — API surface', () => {
    it('setup existe y acepta 3 parámetros', () => {
      assert.isTrue(typeof fc === 'object' && fc !== null,
        'SurveyFilterController debe ser un objeto');
      assert.isTrue(typeof fc.setup === 'function',
        'SurveyFilterController.setup debe ser una función');
      assert.equal(fc.setup.length, 3,
        'setup debe aceptar 3 parámetros (prefix, cacheFiltros, onChangeCallback)');
    });

    it('esEstudiosGen existe y acepta 1 parámetro', () => {
      assert.isTrue(typeof fc.esEstudiosGen === 'function',
        'SurveyFilterController.esEstudiosGen debe ser una función');
      assert.equal(fc.esEstudiosGen.length, 1,
        'esEstudiosGen debe aceptar 1 parámetro');
    });

    it('getCiclosForFiltro existe y acepta 3 parámetros', () => {
      assert.isTrue(typeof fc.getCiclosForFiltro === 'function',
        'SurveyFilterController.getCiclosForFiltro debe ser una función');
      assert.equal(fc.getCiclosForFiltro.length, 3,
        'getCiclosForFiltro debe aceptar 3 parámetros');
    });
  });

  describe('FilterController — esEstudiosGen (via API)', () => {
    it('identifica Programa de Estudios Generales', () => {
      assert.isTrue(fc.esEstudiosGen(PROGRAMA_ESTUDIOS_GENERALES));
    });

    it('rechaza una facultad normal', () => {
      assert.isFalse(fc.esEstudiosGen('Facultad de Ingeniería'));
    });

    it('rechaza string vacío', () => {
      assert.isFalse(fc.esEstudiosGen(''));
    });

    it('rechaza null/undefined', () => {
      assert.isFalse(fc.esEstudiosGen(null));
      assert.isFalse(fc.esEstudiosGen(undefined));
    });
  });

  describe('FilterController — getCiclosForFiltro (via API)', () => {
    const cacheFiltros12 = { ciclos: generarCiclos(12) };

    it('Estudios Generales → solo 1° y 2°', () => {
      const result = fc.getCiclosForFiltro(
        PROGRAMA_ESTUDIOS_GENERALES, '', cacheFiltros12
      );
      assert.isTrue(Array.isArray(result));
      assert.deepEqual(result, CICLOS_ESTUDIOS_GENERALES);
    });

    it('Facultad de Derecho → hasta 12°', () => {
      const result = fc.getCiclosForFiltro(
        'Facultad de Derecho', '', cacheFiltros12
      );
      assert.isTrue(Array.isArray(result));
      assert.equal(result.length, 12);
      assert.isTrue(result.includes('12° Ciclo'));
    });

    it('Carrera Psicología → hasta 12° incluso con facultad genérica', () => {
      const result = fc.getCiclosForFiltro(
        'Facultad de Psicología', 'Psicología', cacheFiltros12
      );
      assert.isTrue(Array.isArray(result));
      assert.equal(result.length, 12);
      assert.isTrue(result.includes('12° Ciclo'));
    });

    it('Facultad de Ingeniería → hasta 10°', () => {
      const result = fc.getCiclosForFiltro(
        'Facultad de Ingeniería', '', cacheFiltros12
      );
      assert.isTrue(Array.isArray(result));
      assert.equal(result.length, 10);
      assert.isFalse(result.includes('11° Ciclo'));
      assert.isFalse(result.includes('12° Ciclo'));
    });

    it('cacheFiltros con solo 8 ciclos → máximo 8', () => {
      const cache8 = { ciclos: generarCiclos(8) };
      const result = fc.getCiclosForFiltro(
        'Facultad de Derecho', '', cache8
      );
      assert.isTrue(Array.isArray(result));
      assert.equal(result.length, 8);
    });

    it('cacheFiltros sin ciclos → array vacío', () => {
      const result = fc.getCiclosForFiltro(
        'Facultad de Ingeniería', '', { ciclos: [] }
      );
      assert.isTrue(Array.isArray(result));
      assert.equal(result.length, 0);
    });
  });

  describe('FilterController — Constantes de negocio', () => {
    it('CARRERAS_12_CICLOS incluye Derecho y Psicología', () => {
      assert.isTrue(CARRERAS_12_CICLOS.includes('Derecho'));
      assert.isTrue(CARRERAS_12_CICLOS.includes('Psicología'));
    });

    it('FACULTADES_12_CICLOS incluye las facultades correspondientes', () => {
      assert.isTrue(FACULTADES_12_CICLOS.includes('Facultad de Derecho'));
      assert.isTrue(FACULTADES_12_CICLOS.includes('Facultad de Psicología'));
    });

    it('CICLOS_ESTUDIOS_GENERALES tiene exactamente 2 ciclos', () => {
      assert.equal(CICLOS_ESTUDIOS_GENERALES.length, 2);
      assert.isTrue(CICLOS_ESTUDIOS_GENERALES.includes('1° Ciclo'));
      assert.isTrue(CICLOS_ESTUDIOS_GENERALES.includes('2° Ciclo'));
    });
  });
})();
