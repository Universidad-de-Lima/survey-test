"""Tests — cambiar el nombre publicado de una pregunta (mismo id) no rompe nada.

La declaración de lib/config.py es la única fuente: renombrar una pregunta no debe
tocar el ETL ni el catálogo de dimensiones. Estas pruebas renombran una pregunta
(conservando su id) y comprueban que todo lo que la usa sigue a la declaración:
las columnas del ETL, la clasificación por dimensión y el detector de columnas
que no son preguntas.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd

from lib import config
from lib.config import pregunta_de
from build_json import _columnas_de, _detectar_dimensiones


class _Renombrado:
    """Contexto: renombra preguntas (mismo id) y las deja como estaban al salir."""

    def __init__(self, nivel, renombres):
        self.nivel = nivel
        self.renombres = renombres
        self.original = None

    def __enter__(self):
        self.original = config.PREGUNTAS_POR_NIVEL[self.nivel]
        config.PREGUNTAS_POR_NIVEL[self.nivel] = [
            {**d, "nombre": self.renombres.get(d["id"], d["nombre"])} for d in self.original
        ]
        return self

    def __exit__(self, *exc):
        config.PREGUNTAS_POR_NIVEL[self.nivel] = self.original
        return False


class TestRenombrarNoRompeElEtl(unittest.TestCase):

    def test_las_columnas_del_etl_siguen_el_nombre_nuevo(self):
        with _Renombrado("undergraduate", {"carrera": "Programa", "nps": "Recomendación X"}):
            cols = _columnas_de("undergraduate")
            self.assertEqual(cols["carrera"], "Programa")
            self.assertEqual(cols["nps"], "Recomendación X")

    def test_el_rename_de_las_columnas_clave_sale_de_la_declaracion(self):
        with _Renombrado("undergraduate", {"id_respuesta": "Código", "nps": "Recomendación X",
                                           "carrera": "Programa",
                                           "csat_universidad": "Satisfacción Ulima"}):
            cfg = config.resolver_config_etl(
                "undergraduate",
                ["ID de respuesta", "Net Promoter Score (de un total de 10)",
                 "¿Qué carrera profesional estudias?", "La Universidad de Lima"],
            )
            self.assertEqual(cfg["rename"]["ID de respuesta"], "Código")
            self.assertEqual(cfg["rename"]["Net Promoter Score (de un total de 10)"], "Recomendación X")
            self.assertEqual(cfg["rename"]["¿Qué carrera profesional estudias?"], "Programa")
            self.assertEqual(cfg["rename"]["La Universidad de Lima"], "Satisfacción Ulima")

    def test_las_requeridas_son_el_texto_del_cuestionario(self):
        # 'requeridas' son textos de la encuesta (antes de renombrar): no cambian
        # con el nombre publicado, pero sí siguen la declaración.
        cfg = config.resolver_config_etl("undergraduate", [])
        self.assertEqual(cfg["requeridas"][:2],
                         [pregunta_de("undergraduate", "id_respuesta"),
                          pregunta_de("undergraduate", "nps")])


class TestRenombrarNoRompeLasDimensiones(unittest.TestCase):

    def test_el_catalogo_de_dimensiones_sigue_el_nombre_nuevo(self):
        with _Renombrado("undergraduate", {"csat_sujeto": "Satisfacción con la carrera"}):
            mapa = config._categoria_dimension(config.DIMENSIONES_PREGRADO)
            self.assertEqual(mapa["Satisfacción con la carrera"], "Académico")
            self.assertNotIn("Satisfacción con tu carrera", mapa)

    def test_las_dimensiones_sin_csat_siguen_el_nombre_nuevo(self):
        with _Renombrado("undergraduate", {"csat_universidad": "Satisfacción Ulima"}):
            self.assertIn("Satisfacción Ulima", config.DIMENSIONES_SIN_CSAT)
            self.assertNotIn("Satisfacción con la Universidad", config.DIMENSIONES_SIN_CSAT)

    def test_el_detector_ignora_las_medidas_de_cierre_con_su_nombre_nuevo(self):
        # Renombrada la satisfacción global, una columna con ese nombre no es
        # dimensión: sigue siendo la medida de cierre.
        with _Renombrado("undergraduate", {"csat_universidad": "Satisfacción Ulima"}):
            df = pd.DataFrame([
                {"ID": "1", "Satisfacción Ulima": "Muy satisfecho",
                 "El servicio médico": "Satisfecho"},
            ])
            dims = _detectar_dimensiones(df)
            self.assertNotIn("Satisfacción Ulima", dims)
            self.assertIn("El servicio médico", dims)


class TestCatalogoPublicadoSinCambios(unittest.TestCase):
    """El catálogo derivado no cambia la salida: mismas dimensiones y categorías."""

    RAIZ = Path(__file__).resolve().parents[3]

    def _pares_publicados(self, ruta_relativa):
        import json
        ruta = self.RAIZ / ruta_relativa
        if not ruta.is_file():
            self.skipTest(f"no está el JSON publicado: {ruta_relativa}")
        filas = json.loads(ruta.read_text(encoding="utf-8"))
        return {(f["dimension"], f["categoria"]) for f in filas}

    def test_pregrado_tiene_sus_dimensiones(self):
        self.assertEqual(len(config.CATEGORIA_DIMENSION_PREGRADO), 33)
        self.assertIn(("Satisfacción con tu carrera", "Académico"),
                      config.CATEGORIA_DIMENSION_PREGRADO.items())
        self.assertEqual(config.CATEGORIA_DIMENSION_PREGRADO["Espacios comunes"], "Infraestructura")

    def test_graduado_tiene_sus_dimensiones(self):
        self.assertEqual(len(config.CATEGORIA_DIMENSION_GRADUADO), 45)
        self.assertIn(("Metodologías", "Docencia"), config.CATEGORIA_DIMENSION_GRADUADO.items())
        self.assertEqual(config.CATEGORIA_DIMENSION_GRADUADO["Habilidades de comunicación"],
                         "Desarrollo Profesional")

    def test_el_catalogo_cubre_lo_publicado(self):
        pares_ug = self._pares_publicados(
            "zoho-survey/students/undergraduate/2025-2/json/dimensiones.json")
        self.assertTrue(pares_ug <= set(config.CATEGORIA_DIMENSION_PREGRADO.items()))
        pares_ge = self._pares_publicados(
            "zoho-survey/students/graduate/2026/json/dimensiones.json")
        self.assertTrue(pares_ge <= set(config.CATEGORIA_DIMENSION_GRADUADO.items()))

    def test_la_unificada_es_pregrado_mas_graduado(self):
        esperado = dict(config.CATEGORIA_DIMENSION_PREGRADO)
        esperado.update(config.CATEGORIA_DIMENSION_GRADUADO)
        self.assertEqual(list(config.CATEGORIA_DIMENSION_UNIFICADA.items()),
                         list(esperado.items()))


if __name__ == "__main__":
    unittest.main()
