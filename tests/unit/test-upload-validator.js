/** 
 * Tests del validador del uploader (portal-upload.js) — Fase 3.8.3.
 * Parser tolerante: separadores espacio/guion equivalentes, periodo opcional.
 * Headers por encuesta exacta (categoria + nivel).
 */
(function () {
  'use strict';
  const { assert, describe, it } = window.TestFramework;
  const U = window.SurveyUpload;

  if (!U) {
    console.error('SurveyUpload no encontrado. Cargar shared/js/portal-upload.js antes.');
    return;
  }

  // ---------- parseFilename ----------
  describe('parseFilename — nombres validos (10 CSVs reales)', () => {
    it('DOCENTE - POSGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN DOCENTE - POSGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'DOCENTES');
      assert.equal(r.nivelRaw, 'POSGRADO');
      assert.equal(r.periodo, '2026');
    });
    it('DOCENTE - PREGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN DOCENTE - PREGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'DOCENTES');
      assert.equal(r.nivelRaw, 'PREGRADO');
    });
    it('ESTUDIANTIL - PREGRADO - 2026-1', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-1.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'ESTUDIANTIL');
      assert.equal(r.nivelRaw, 'PREGRADO');
      assert.equal(r.periodo, '2026-1');
    });
    it('ESTUDIANTIL - POSGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - POSGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'ESTUDIANTIL');
      assert.equal(r.nivelRaw, 'POSGRADO');
      assert.equal(r.periodo, '2026');
    });
    it('GRADUADOS - PREGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN GRADUADOS - PREGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'GRADUADOS');
      assert.equal(r.periodo, '2026');
    });
    it('EGRESADOS - PREGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN EGRESADOS - PREGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'EGRESADOS');
    });
    it('EGRESADOS - POSGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN EGRESADOS - POSGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'EGRESADOS');
    });
    it('EMPLEADORES - PREGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN EMPLEADORES - PREGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'EMPLEADORES');
    });
    it('EMPLEADORES - POSGRADO - 2026', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN EMPLEADORES - POSGRADO - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'EMPLEADORES');
      assert.equal(r.nivelRaw, 'POSGRADO');
    });
    it('NO DOCENTE - 2026 (sin nivel, con periodo)', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN NO DOCENTE - 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'NO DOCENTES');
      assert.equal(r.nivelRaw, null);
      assert.equal(r.periodo, '2026');
    });
    it('Sin guiones (solo espacios)', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN GRADUADOS PREGRADO 2026.csv');
      assert.equal(r.ok, true);
      assert.equal(r.categoria, 'GRADUADOS');
      assert.equal(r.periodo, '2026');
    });
    it('Sin periodo', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN GRADUADOS PREGRADO.csv');
      assert.equal(r.ok, true);
      assert.equal(r.periodo, null);
    });
  });

  describe('parseFilename — invalidos', () => {
    it('Extension .txt', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN GRADUADOS PREGRADO 2026.txt');
      assert.equal(r.ok, false);
    });
    it('Sin prefijo ENCUESTA DE SATISFACCION', () => {
      const r = U.parseFilename('GRADUADOS PREGRADO 2026.csv');
      assert.equal(r.ok, false);
    });
    it('Categoria desconocida', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN OTRO PREGRADO 2026.csv');
      assert.equal(r.ok, false);
    });
    it('NO DOCENTE con nivel (no permitido)', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN NO DOCENTE - PREGRADO - 2026-1.csv');
      assert.equal(r.ok, false);
      assert.isTrue(r.error.toLowerCase().includes('nivel'));
    });
    it('ESTUDIANTIL sin nivel (obligatorio)', () => {
      const r = U.parseFilename('ENCUESTA DE SATISFACCIÓN ESTUDIANTIL 2026.csv');
      assert.equal(r.ok, false);
    });
  });

  // ---------- detectNivel ----------
  describe('detectNivel — mapea todas las variantes', () => {
    it('estudiantil pregrado -> undergraduate', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-1.csv'), 'undergraduate');
    });
    it('estudiantil posgrado -> postgraduate', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - POSGRADO - 2026.csv'), 'postgraduate');
    });
    it('graduados pregrado -> graduate', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN GRADUADOS - PREGRADO - 2026.csv'), 'graduate');
    });
    it('docente pregrado -> faculty-ug (singular)', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN DOCENTE - PREGRADO - 2026.csv'), 'faculty-ug');
    });
    it('docente posgrado -> faculty-pg', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN DOCENTE - POSGRADO - 2026.csv'), 'faculty-pg');
    });
    it('docentes plural pregrado -> faculty-ug', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN DOCENTES - PREGRADO - 2026-1.csv'), 'faculty-ug');
    });
    it('no docente -> nonfaculty', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN NO DOCENTE - 2026.csv'), 'nonfaculty');
    });
    it('empleadores -> employers', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN EMPLEADORES - PREGRADO - 2026.csv'), 'employers');
    });
    it('egresados pregrado -> alumni-ug', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN EGRESADOS - PREGRADO - 2026.csv'), 'alumni-ug');
    });
    it('egresados posgrado -> alumni-pg', () => {
      assert.equal(U.detectNivel('ENCUESTA DE SATISFACCIÓN EGRESADOS - POSGRADO - 2026.csv'), 'alumni-pg');
    });
  });

  // ---------- requiredHeaders — por encuesta exacta (categoria + nivel) ----------
  describe('requiredHeaders — headers por encuesta', () => {
    it('ESTUDIANTIL + PREGRADO', () => {
      const req = U.requiredHeaders('ESTUDIANTIL', 'PREGRADO');
      assert.isTrue(req.includes('¿Qué carrera profesional estudias?'));
      assert.isTrue(req.includes('ID de respuesta'));
    });
    it('ESTUDIANTIL + POSGRADO', () => {
      const req = U.requiredHeaders('ESTUDIANTIL', 'POSGRADO');
      assert.isTrue(req.includes('¿Qué programa de posgrado estudias?'));
    });
    it('DOCENTES + PREGRADO', () => {
      const req = U.requiredHeaders('DOCENTES', 'PREGRADO');
      assert.isTrue(req.includes('¿Qué carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?'));
    });
    it('DOCENTES + POSGRADO', () => {
      const req = U.requiredHeaders('DOCENTES', 'POSGRADO');
      assert.isTrue(req.includes('¿Qué programa de posgrado dictas en la Universidad de Lima?'));
    });
    it('NO DOCENTES (sin nivel)', () => {
      const req = U.requiredHeaders('NO DOCENTES', null);
      assert.isTrue(req.includes('¿A qué dependencia perteneces?'));
    });
    it('EMPLEADORES + PREGRADO', () => {
      const req = U.requiredHeaders('EMPLEADORES', 'PREGRADO');
      assert.isTrue(req.includes('¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?'));
    });
    it('EMPLEADORES + POSGRADO (columna "posgrado")', () => {
      const req = U.requiredHeaders('EMPLEADORES', 'POSGRADO');
      assert.isTrue(req.includes('¿Cuál posgrado es el que procede el profesional de la Universidad de Lima contratado por su organización?'));
    });
    it('EGRESADOS + PREGRADO', () => {
      const req = U.requiredHeaders('EGRESADOS', 'PREGRADO');
      assert.isTrue(req.includes('¿Qué carrera profesional estudiaste?'));
    });
    it('EGRESADOS + POSGRADO', () => {
      const req = U.requiredHeaders('EGRESADOS', 'POSGRADO');
      assert.isTrue(req.includes('¿Qué programa de posgrado estudiaste?'));
    });
  });

  // ---------- formatBytes ----------
  describe('formatBytes', () => {
    it('formatea correctamente', () => {
      assert.equal(U.formatBytes(0), '0 B');
      assert.equal(U.formatBytes(1024), '1.0 KB');
      assert.equal(U.formatBytes(5 * 1024 * 1024), '5.0 MB');
      assert.equal(U.formatBytes(50 * 1024 * 1024), '50.0 MB');
    });
  });

  // ---------- constants ----------
  describe('constantes', () => {
    it('limites correctos', () => {
      assert.equal(U.MAX_CSV, 10);
      assert.equal(U.MAX_FILE_BYTES, 5 * 1024 * 1024);
      assert.equal(U.MAX_TOTAL_BYTES, 50 * 1024 * 1024);
    });
  });
})();
