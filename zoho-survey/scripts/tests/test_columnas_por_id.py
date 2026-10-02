"""Tests — la columna se resuelve por su id declarado, nunca por el nombre.

Recorren la declaración de preguntas de lib/config.py y exigen que exista una
única vía para pedir una columna (``columna(nivel, id)``) y para recuperar el
texto del cuestionario (``pregunta_de(nivel, id)``). Además, build_json.py
resuelve por id las columnas que usa, y deja de escribir el nombre publicado a
mano: renombrar una pregunta en la declaración no debe romper el ETL.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import config
from lib.config import columna, nombre_publicado, pregunta_de
from build_json import _columnas_de


class TestColumnaPorId(unittest.TestCase):

    def test_columna_resuelve_el_nombre_publicado_declarado(self):
        for nivel, declaraciones in config.PREGUNTAS_POR_NIVEL.items():
            for d in declaraciones:
                with self.subTest(nivel=nivel, id=d["id"]):
                    self.assertEqual(columna(nivel, d["id"]), d["nombre"])

    def test_pregunta_de_devuelve_el_texto_del_cuestionario(self):
        for nivel, declaraciones in config.PREGUNTAS_POR_NIVEL.items():
            for d in declaraciones:
                with self.subTest(nivel=nivel, id=d["id"]):
                    self.assertEqual(pregunta_de(nivel, d["id"]), d["pregunta"])

    def test_nombre_publicado_es_la_version_sin_nivel(self):
        self.assertEqual(nombre_publicado("aulas_de_clase"), "Aulas de clase")
        self.assertEqual(nombre_publicado("csat_sujeto"), "La carrera")
        self.assertEqual(nombre_publicado("nps"), "Recomiendas la Universidad de Lima")

    def test_columna_falla_con_un_id_desconocido(self):
        with self.assertRaises(KeyError):
            columna("undergraduate", "no_existe")
        with self.assertRaises(KeyError):
            pregunta_de("undergraduate", "no_existe")

    def test_columna_sigue_el_rename_y_no_el_nombre_viejo(self):
        original = config.PREGUNTAS_POR_NIVEL["undergraduate"]
        config.PREGUNTAS_POR_NIVEL["undergraduate"] = [
            {**d, "nombre": "Carrera renombrada"} if d["id"] == "carrera" else d
            for d in original
        ]
        try:
            self.assertEqual(columna("undergraduate", "carrera"), "Carrera renombrada")
        finally:
            config.PREGUNTAS_POR_NIVEL["undergraduate"] = original


class TestColumnasDelEtl(unittest.TestCase):

    def test_resuelve_por_id_las_columnas_que_usa_build_json(self):
        esperado = {
            "id_respuesta": "ID",
            "inicio": "Inicio",
            "fin": "Fin",
            "carrera": "Carrera",
            "ciclo": "Ciclo",
            "facultad": "Facultad",
            "nps": "Recomiendas la Universidad de Lima",
            "csat_universidad": "La Universidad de Lima",
            "csat_sujeto": "La carrera",
        }
        for nivel in ("undergraduate", "graduate"):
            with self.subTest(nivel=nivel):
                cols = _columnas_de(nivel)
                for id_col, nombre in esperado.items():
                    self.assertEqual(cols[id_col], nombre)

    def test_las_columnas_siguen_el_rename_de_la_declaracion(self):
        original = config.PREGUNTAS_POR_NIVEL["undergraduate"]
        config.PREGUNTAS_POR_NIVEL["undergraduate"] = [
            {**d, "nombre": "Ciclo renombrado"} if d["id"] == "ciclo" else d
            for d in original
        ]
        try:
            self.assertEqual(_columnas_de("undergraduate")["ciclo"], "Ciclo renombrado")
        finally:
            config.PREGUNTAS_POR_NIVEL["undergraduate"] = original

    def test_los_niveles_sin_declaracion_usan_el_catalogo_comun(self):
        # faculty-ug no está en PREGUNTAS_POR_NIVEL: el nombre sale del catálogo
        # común derivado de las declaraciones (los mismos que publica el ETL).
        cols = _columnas_de("faculty-ug")
        self.assertEqual(cols["carrera"], "Carrera")
        self.assertEqual(cols["facultad"], "Facultad")
        self.assertEqual(cols["nps"], "Recomiendas la Universidad de Lima")

    def test_build_json_no_indexa_por_el_nombre_publicado(self):
        """El ETL no debe volver a escribir el nombre de columna a mano."""
        fuente = (SCRIPTS_DIR / "build_json.py").read_text(encoding="utf-8")
        for literal in (
            'df["Carrera"]',
            'df["Facultad"]',
            'df["Ciclo"]',
            'df["Situación laboral"]',
            'df[[nps_col, "Carrera", "Ciclo", "Facultad"]',
            'nps_col: str = "Recomiendas la Universidad de Lima"',
            'groupby(["Facultad", "Carrera", "Ciclo"])',
        ):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, fuente)


if __name__ == "__main__":
    unittest.main()
