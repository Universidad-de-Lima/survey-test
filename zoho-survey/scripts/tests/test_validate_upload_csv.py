
"""Tests para validate_upload_csv.py (Fase 3.8.3)."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_upload_csv import parse_filename, required_headers, validate_batch


class TestParseFilename(unittest.TestCase):

    def test_valid_real_docente_posgrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N DOCENTE - POSGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "DOCENTES")
        self.assertEqual(nivel, "POSGRADO")
        self.assertEqual(period, "2026")

    def test_valid_real_docente_pregrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N DOCENTE - PREGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "DOCENTES")

    def test_valid_real_estudiantil_pregrado_semestral(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N ESTUDIANTIL - PREGRADO - 2026-1.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "ESTUDIANTIL")
        self.assertEqual(period, "2026-1")

    def test_valid_real_estudiantil_posgrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N ESTUDIANTIL - POSGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "ESTUDIANTIL")

    def test_valid_real_graduados(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N GRADUADOS - PREGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "GRADUADOS")

    def test_valid_real_egresados_pregrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N EGRESADOS - PREGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "EGRESADOS")

    def test_valid_real_egresados_posgrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N EGRESADOS - POSGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "EGRESADOS")

    def test_valid_real_empleadores_pregrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N EMPLEADORES - PREGRADO - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "EMPLEADORES")

    def test_valid_real_empleadores_posgrado(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N EMPLEADORES - POSGRADO - 2026.csv")
        self.assertTrue(ok)

    def test_valid_real_no_docente(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N NO DOCENTE - 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "NO DOCENTES")
        self.assertIsNone(nivel)
        self.assertEqual(period, "2026")

    def test_valid_sin_guiones(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N GRADUADOS PREGRADO 2026.csv")
        self.assertTrue(ok)
        self.assertEqual(cat, "GRADUADOS")
        self.assertEqual(nivel, "PREGRADO")

    def test_valid_sin_periodo(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N GRADUADOS PREGRADO.csv")
        self.assertTrue(ok)
        self.assertIsNone(period)

    def test_invalid_extension(self):
        ok, *_ = parse_filename("ENCUESTA DE SATISFACCI\u00d3N GRADUADOS PREGRADO 2026.txt")
        self.assertFalse(ok)

    def test_invalid_no_prefix(self):
        ok, *_ = parse_filename("GRADUADOS PREGRADO 2026.csv")
        self.assertFalse(ok)

    def test_invalid_category(self):
        ok, *_ = parse_filename("ENCUESTA DE SATISFACCI\u00d3N OTRO PREGRADO 2026.csv")
        self.assertFalse(ok)

    def test_no_docente_with_level_fails(self):
        ok, cat, nivel, period, err = parse_filename("ENCUESTA DE SATISFACCI\u00d3N NO DOCENTE - PREGRADO - 2026-1.csv")
        self.assertFalse(ok)
        self.assertIn("nivel", err.lower())

    def test_estudiantil_missing_level_fails(self):
        ok, *_ = parse_filename("ENCUESTA DE SATISFACCI\u00d3N ESTUDIANTIL 2026.csv")
        self.assertFalse(ok)


class TestRequiredHeaders(unittest.TestCase):

    def test_estudiantil_pregrado(self):
        cols = required_headers("ESTUDIANTIL", "PREGRADO")
        self.assertIn("\u00bfQu\u00e9 carrera profesional estudias?", cols)
        self.assertIn("ID de respuesta", cols)

    def test_estudiantil_posgrado(self):
        cols = required_headers("ESTUDIANTIL", "POSGRADO")
        self.assertIn("\u00bfQu\u00e9 programa de posgrado estudias?", cols)

    def test_empleadores_posgrado(self):
        cols = required_headers("EMPLEADORES", "POSGRADO")
        self.assertIn("\u00bfCu\u00e1l posgrado es el que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?", cols)

    def test_empleadores_pregrado(self):
        cols = required_headers("EMPLEADORES", "PREGRADO")
        self.assertIn("\u00bfQu\u00e9 carrera es la que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?", cols)

    def test_no_docente(self):
        cols = required_headers("NO DOCENTES", None)
        self.assertIn("\u00bfA qu\u00e9 dependencia perteneces?", cols)


class TestWithRealFiles(unittest.TestCase):

    def test_real_csvs_validate(self):
        pdf_dir = Path(__file__).resolve().parent.parent.parent.parent / "PDF"
        if not pdf_dir.is_dir():
            self.skipTest("No hay CSVs en PDF/")
        csv_files = sorted(f for f in pdf_dir.iterdir()
                          if f.suffix.lower() == ".csv" and "ENCUESTA" in f.name.upper())
        result = validate_batch(csv_files)
        self.assertTrue(result["ok"],
                       f"CSVs reales fallaron: {result['errors']}")

    def test_real_csvs_count(self):
        pdf_dir = Path(__file__).resolve().parent.parent.parent.parent / "PDF"
        if not pdf_dir.is_dir():
            self.skipTest("No hay CSVs en PDF/")
        csv_files = sorted(f for f in pdf_dir.iterdir()
                          if f.suffix.lower() == ".csv" and "ENCUESTA" in f.name.upper())
        self.assertGreaterEqual(len(csv_files), 2)
        self.assertLessEqual(len(csv_files), 10)


class TestBatchLimits(unittest.TestCase):

    def test_empty_batch(self):
        result = validate_batch([])
        self.assertFalse(result["ok"])

    def test_eleven_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i in range(11):
                p = Path(d) / "ENCUESTA DE SATISFACCI\u00d3N GRADUADOS - PREGRADO - 2026.csv"
                p.write_text("ID de respuesta\n", encoding="utf-8")
                paths.append(p)
            result = validate_batch(paths)
            self.assertFalse(result["ok"])
            self.assertTrue(any("10" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
