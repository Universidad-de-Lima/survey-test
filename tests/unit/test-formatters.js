/**
 * TESTS — SurveyFormatters
 *
 * Prueba todas las funciones de formateo exportadas por utils/formatters.js.
 * Ejecutar: ver el job `js-tests` en GitHub Actions.
 *
 * Contrato verificado (v1.1.0):
 * - formatDecimal(n, digits=2): SIEMPRE muestra `digits` decimales, incluso
 *   cuando todos son cero. Ej: formatDecimal(3.0) → "3,00".
 * - formatPctSimple / formatPctDecimal: siempre 2 decimales.
 * - formatInteger: enteros sin decimales (conteos).
 * - toFixed() trunca en casos de float impreciso (1.2345 → "1.234").
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const F = window.SurveyFormatters;

  if (!F) {
    console.error('SurveyFormatters no encontrado. Asegúrate de cargar utils/formatters.js antes.');
    return;
  }

  describe('formatInteger', () => {
    it('convierte número a string', () => {
      assert.equal(F.formatInteger(42), '42');
    });
    it('maneja cero', () => {
      assert.equal(F.formatInteger(0), '0');
    });
    it('maneja negativos', () => {
      assert.equal(F.formatInteger(-5), '-5');
    });
  });

  describe('formatDecimal', () => {
    it('formatea con 2 decimales por defecto', () => {
      assert.equal(F.formatDecimal(3.14159), '3,14');
    });
    it('usa coma como separador decimal y respeta digits=2', () => {
      // Contrato: siempre muestra `digits` decimales salvo caso entero.
      // 1.5 con digits=2 → "1,50" (no "1,5").
      assert.equal(F.formatDecimal(1.5), '1,50');
    });
    it('SIEMPRE muestra 2 decimales incluso si son cero (v1.1.0)', () => {
      assert.equal(F.formatDecimal(3.0), '3,00');
    });
    it('retorna vacío para null', () => {
      assert.equal(F.formatDecimal(null), '');
    });
    it('retorna vacío para undefined', () => {
      assert.equal(F.formatDecimal(undefined), '');
    });
    it('formatea con precisión personalizada', () => {
      // toFixed trunca en casos de float impreciso: 1.2345 en float es 1.2344999...
      // Por eso 1.2345.toFixed(3) → "1.234" (no "1.235"). Usar 1.2351 para test de redondeo.
      assert.equal(F.formatDecimal(1.2351, 3), '1,235');
      // Y verificar truncamiento correcto
      assert.equal(F.formatDecimal(1.2344, 3), '1,234');
    });
  });

  describe('formatPercent', () => {
    it('añade símbolo % y respeta digits=2 por defecto', () => {
      assert.equal(F.formatPercent(93.5), '93,50 %');
    });
    it('SIEMPRE muestra 2 decimales incluso para enteros (v1.1.0)', () => {
      assert.equal(F.formatPercent(100.0), '100,00 %');
    });
  });

  describe('formatPctSimple', () => {
    it('calcula porcentaje con 2 decimales (v1.1.0)', () => {
      assert.equal(F.formatPctSimple(3, 10), '30,00 %');
    });
    it('retorna 0,00% para total cero', () => {
      assert.equal(F.formatPctSimple(5, 0), '0,00 %');
    });
  });

  describe('formatPctDecimal', () => {
    it('calcula con 2 decimales (v1.1.0)', () => {
      // 1/3 = 33.333... → "33,33 %"
      assert.equal(F.formatPctDecimal(1, 3), '33,33 %');
    });
    it('retorna 0,00 % para total cero', () => {
      assert.equal(F.formatPctDecimal(5, 0), '0,00 %');
    });
  });

  describe('formatDate', () => {
    it('formatea fecha en español', () => {
      const result = F.formatDate('2025-10-20');
      assert.isTrue(result.includes('octubre'), 'Debe incluir el mes en español');
    });
  });

  describe('formatCicloText', () => {
    it('formatea 1er ciclo', () => {
      assert.equal(F.formatCicloText('1° Ciclo'), '1.ᵉʳ ciclo');
    });
    it('formatea 3er ciclo', () => {
      assert.equal(F.formatCicloText('3° Ciclo'), '3.ᵉʳ ciclo');
    });
    it('formatea ciclos regulares', () => {
      assert.equal(F.formatCicloText('5° Ciclo'), '5.º ciclo');
    });
    it('retorna original si no hay número', () => {
      assert.equal(F.formatCicloText('Sin ciclo'), 'Sin ciclo');
    });
  });

  describe('cortarTexto', () => {
    it('trunca texto largo', () => {
      const result = F.cortarTexto('ABCDEFGHIJKLMNOP', 10);
      assert.isTrue(result.endsWith('…'), 'Debe terminar con elipsis');
      assert.isTrue(result.length <= 10);
    });
    it('no modifica texto corto', () => {
      assert.equal(F.cortarTexto('Hola', 10), 'Hola');
    });
  });

  describe('formatDimensionName', () => {
    it('aplica cursiva a Software', () => {
      const result = F.formatDimensionName('Software especializado empleado en la carrera');
      assert.isTrue(result.includes('<i>Software</i>'), 'Debe tener <i>Software</i>');
    });
    it('no modifica otras dimensiones', () => {
      assert.equal(F.formatDimensionName('Aulas de clase'), 'Aulas de clase');
    });
  });

  describe('formatDimensionNameSVG', () => {
    it('genera tspan para Software', () => {
      const result = F.formatDimensionNameSVG('Software especializado empleado en la carrera', 30);
      assert.isTrue(result.includes('tspan'), 'Debe generar elemento SVG');
    });
  });

  describe('formatDimensionNameForAttr', () => {
    it('escapa HTML para atributos', () => {
      const result = F.formatDimensionNameForAttr('Software especializado empleado en la carrera');
      assert.isTrue(result.includes('&lt;'), 'Debe escapar <');
      assert.isTrue(result.includes('&gt;'), 'Debe escapar >');
    });
  });
})();
