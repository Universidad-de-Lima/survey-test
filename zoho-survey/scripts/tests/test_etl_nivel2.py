"""Tests Fase 2: soporte de las 7 categorias en el ETL (build_json + config)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from lib.config import resolver_config_etl, clasificar_categoria_dimension
from build_json import _detectar_nivel, _detectar_dimensiones


# Headers representativos extraidos de los contratos de datos.
COLS_ESTUDIANTIL_PREGRADO = [
    "ID de respuesta",
    "Net Promoter Score (de un total de 10)",
    "¿Qué carrera profesional estudias?",
    "¿Qué ciclo es el que cursas?; considera el ciclo donde más cursos llevas",
    "La Universidad de Lima",
]

COLS_NO_DOCENTES = [
    "ID de respuesta",
    "Net Promoter Score (de un total de 10)",
    "¿A qué dependencia perteneces?",
    "La Universidad de Lima",
]

COLS_EMPLEADORES_PREGRADO = [
    "ID de respuesta",
    "Net Promoter Score (de un total de 10)",
    "¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?",
]

COLS_DOCENTES_POSGRADO = [
    "ID de respuesta",
    "Net Promoter Score (de un total de 10)",
    "¿Qué programa de posgrado dictas en la Universidad de Lima?",
    "La Universidad de Lima",
]


class TestResolverConfig(unittest.TestCase):
    def test_nonfaculty(self):
        cfg = resolver_config_etl("nonfaculty", COLS_NO_DOCENTES)
        self.assertEqual(cfg["carrera"], "¿A qué dependencia perteneces?")
        self.assertEqual(cfg["csat"], "La Universidad de Lima")
        self.assertIsNone(cfg["ciclo"])
        self.assertFalse(cfg["facultad_map"])
        self.assertIn("ID de respuesta", cfg["requeridas"])

    def test_employers_pre(self):
        cfg = resolver_config_etl("employers", COLS_EMPLEADORES_PREGRADO)
        self.assertEqual(
            cfg["carrera"],
            "¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?",
        )
        self.assertIsNone(cfg["csat"])

    def test_docente_posgrado(self):
        cfg = resolver_config_etl("faculty-pg", COLS_DOCENTES_POSGRADO)
        self.assertEqual(cfg["carrera"], "¿Qué programa de posgrado dictas en la Universidad de Lima?")
        self.assertEqual(cfg["csat"], "La Universidad de Lima")

    def test_estudiantil_pregrado_unchanged(self):
        cfg = resolver_config_etl("undergraduate", COLS_ESTUDIANTIL_PREGRADO)
        self.assertEqual(cfg["carrera"], "¿Qué carrera profesional estudias?")
        self.assertTrue(cfg["facultad_map"])
        self.assertIsNotNone(cfg["ciclo"])


class TestClasificarCategoria(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(clasificar_categoria_dimension("La calidad de la enseñanza en la carrera"), "Académico")
        self.assertEqual(clasificar_categoria_dimension("Los laboratorios en lo referido a equipamiento"), "Infraestructura")
        self.assertEqual(clasificar_categoria_dimension("El portal web de la universidad: Mi Ulima"), "Tecnología")
        self.assertEqual(clasificar_categoria_dimension("El servicio médico y su atención"), "Administrativo y Bienestar")
        self.assertEqual(clasificar_categoria_dimension("¿Qué carrera profesional estudias?"), "General")


class TestDetectarDimensiones(unittest.TestCase):
    def _df_with(self, columns, rows):
        return pd.DataFrame(rows, columns=columns)

    def test_nonfaculty_dimensions_detected(self):
        df = self._df_with(
            ["ID de respuesta", "¿A qué dependencia perteneces?", "La Universidad de Lima", "El servicio médico"],
            [
                ["1", "RRHH", "Totalmente satisfecho", "Muy satisfecho"],
                ["2", "TI", "Satisfecho", "Satisfecho"],
            ],
        )
        dims = _detectar_dimensiones(df)
        self.assertNotIn("¿A qué dependencia perteneces?", dims)
        self.assertIn("El servicio médico", dims)
        self.assertGreaterEqual(len(dims), 1)

    def test_employers_competencies_not_dimensions(self):
        df = self._df_with(
            ["ID de respuesta", "Liderazgo", "Honestidad"],
            [
                ["1", "Siempre", "Siempre"],
                ["2", "A veces", "Nunca"],
            ],
        )
        dims = _detectar_dimensiones(df)
        self.assertNotIn("Liderazgo", dims)
        self.assertNotIn("Honestidad", dims)


class TestDetectarNivelReal(unittest.TestCase):
    def test_filenames(self):
        cases = [
            ("ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-1.csv", "undergraduate"),
            ("ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - POSGRADO - 2026.csv", "postgraduate"),
            ("ENCUESTA DE SATISFACCIÓN GRADUADOS - PREGRADO - 2026.csv", "graduate"),
            ("ENCUESTA DE SATISFACCIÓN EGRESADOS - POSGRADO - 2026.csv", "alumni-pg"),
            ("ENCUESTA DE SATISFACCIÓN DOCENTES - PREGRADO - 2026.csv", "faculty-ug"),
            ("ENCUESTA DE SATISFACCIÓN NO DOCENTE - 2026.csv", "nonfaculty"),
            ("ENCUESTA DE SATISFACCIÓN EMPLEADORES - PREGRADO - 2026.csv", "employers"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(_detectar_nivel(name), expected)


if __name__ == "__main__":
    unittest.main()
