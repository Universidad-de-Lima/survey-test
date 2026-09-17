/**
 * TESTS — SurveySanitizer
 *
 * Prueba las funciones de sanitización HTML.
 * Ejecutar: abrir tests/run-tests.html en el navegador.
 */
(() => {
  'use strict';

  const { assert, describe, it } = window.TestFramework;
  const S = window.SurveySanitizer;

  if (!S) {
    console.error('SurveySanitizer no encontrado.');
    return;
  }

  describe('escapeHTML', () => {
    it('escapa < y >', () => {
      assert.equal(S.escapeHTML('<script>'), '&lt;script&gt;');
    });
    it('escapa &', () => {
      assert.equal(S.escapeHTML('a & b'), 'a &amp; b');
    });
    it('escapa comillas dobles', () => {
      assert.equal(S.escapeHTML('"hello"'), '&quot;hello&quot;');
    });
    it('escapa comillas simples', () => {
      assert.equal(S.escapeHTML("it's"), 'it&#039;s');
    });
    it('retorna vacío para null', () => {
      assert.equal(S.escapeHTML(null), '');
    });
    it('retorna vacío para undefined', () => {
      assert.equal(S.escapeHTML(undefined), '');
    });
    it('retorna vacío para no-string', () => {
      assert.equal(S.escapeHTML(123), '');
    });
    it('no modifica texto seguro', () => {
      assert.equal(S.escapeHTML('Hola mundo'), 'Hola mundo');
    });
    it('escapa múltiples ocurrencias', () => {
      assert.equal(S.escapeHTML('<b>bold</b>'), '&lt;b&gt;bold&lt;/b&gt;');
    });
  });

  describe('sanitizeHTML', () => {
    it('permite <br>', () => {
      const result = S.sanitizeHTML('línea 1<br>línea 2');
      assert.equal(result, 'línea 1<br>línea 2');
    });
    it('permite <strong>', () => {
      const result = S.sanitizeHTML('<strong>importante</strong>');
      assert.equal(result, '<strong>importante</strong>');
    });
    it('permite <em>', () => {
      const result = S.sanitizeHTML('<em>énfasis</em>');
      assert.equal(result, '<em>énfasis</em>');
    });
    it('permite <i>', () => {
      const result = S.sanitizeHTML('<i>cursiva</i>');
      assert.equal(result, '<i>cursiva</i>');
    });
    it('permite <span>', () => {
      const result = S.sanitizeHTML('<span>texto</span>');
      assert.equal(result, '<span>texto</span>');
    });
    it('escapa <script>', () => {
      const result = S.sanitizeHTML('<script>alert(1)</script>');
      assert.equal(result, '&lt;script&gt;alert(1)&lt;/script&gt;');
    });
    it('escapa <div>', () => {
      const result = S.sanitizeHTML('<div>contenido</div>');
      assert.equal(result, '&lt;div&gt;contenido&lt;/div&gt;');
    });
    it('elimina atributos on*', () => {
      const result = S.sanitizeHTML('<span onclick="alert(1)">x</span>');
      assert.equal(result, '<span>x</span>');
    });
    it('retorna vacío para null', () => {
      assert.equal(S.sanitizeHTML(null), '');
    });
    it('retorna vacío para no-string', () => {
      assert.equal(S.sanitizeHTML(456), '');
    });
    it('permite combinación de tags seguros con texto', () => {
      const result = S.sanitizeHTML('<strong>Título:</strong> descripción<br>fin');
      assert.equal(result, '<strong>Título:</strong> descripción<br>fin');
    });
  });
})();
