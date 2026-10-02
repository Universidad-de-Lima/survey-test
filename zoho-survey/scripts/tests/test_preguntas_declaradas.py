"""Tests — declaración de preguntas (Fase 1: un solo lugar para las preguntas).

Recorren TODAS las preguntas declaradas en lib/config.py y exigen que cada una
tenga id (no vacío y único dentro de su encuesta), un tipo válido y, cuando el
tipo es 'medida', una escala no vacía. Además, la tabla de respuestas publica
esa misma declaración dentro del bloque 'preguntas' del respuestas.json.
"""
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import pandas as pd

from lib import config
from lib.tabla_respuestas import construir_tabla


class TestDeclaracionDePreguntas(unittest.TestCase):

    def test_hay_declaracion_para_los_niveles_publicados(self):
        self.assertIn("undergraduate", config.PREGUNTAS_POR_NIVEL)
        self.assertIn("graduate", config.PREGUNTAS_POR_NIVEL)

    def test_cada_pregunta_tiene_id_unico_y_tipo_valido(self):
        for nivel, declaraciones in config.PREGUNTAS_POR_NIVEL.items():
            with self.subTest(nivel=nivel):
                self.assertTrue(declaraciones, f"{nivel} no declara ninguna pregunta")
                ids = []
                for d in declaraciones:
                    self.assertTrue(str(d.get("id", "")).strip(), f"{nivel}: pregunta sin id: {d}")
                    self.assertTrue(str(d.get("pregunta", "")).strip(),
                                    f"{nivel}: '{d.get('id')}' sin texto de pregunta")
                    self.assertTrue(str(d.get("nombre", "")).strip(),
                                    f"{nivel}: '{d.get('id')}' sin nombre publicado")
                    self.assertIn(d.get("tipo"), config.TIPOS_VALIDOS,
                                  f"{nivel}: '{d.get('id')}' tiene tipo invalido: {d.get('tipo')!r}")
                    if d.get("tipo") == "medida":
                        self.assertTrue(str(d.get("escala", "")).strip(),
                                        f"{nivel}: la medida '{d.get('id')}' no declara escala")
                    ids.append(d["id"])
                self.assertEqual(len(ids), len(set(ids)), f"{nivel}: ids de pregunta repetidos")

    def test_toda_columna_publicada_tiene_declaracion(self):
        extras = {"undergraduate": {"Facultad"}, "graduate": {"Ciclo", "Facultad"}}
        fuera = {"ID", "Inicio", "Fin", "Comentario NPS"}
        for nivel, rename in (("undergraduate", config.COLUMN_RENAME_PREGRADO),
                              ("graduate", config.COLUMN_RENAME_GRADUADO)):
            with self.subTest(nivel=nivel):
                declaradas = {d["nombre"] for d in config.PREGUNTAS_POR_NIVEL[nivel]}
                publicadas = {n for n in rename.values() if n not in fuera} | extras[nivel]
                self.assertFalse(publicadas - declaradas,
                                 f"{nivel}: columnas publicadas sin declaracion: "
                                 f"{sorted(publicadas - declaradas)}")

    def test_el_mapa_de_renombrado_sale_de_la_declaracion(self):
        for nivel, rename in (("undergraduate", config.COLUMN_RENAME_PREGRADO),
                              ("graduate", config.COLUMN_RENAME_GRADUADO)):
            with self.subTest(nivel=nivel):
                for d in config.PREGUNTAS_POR_NIVEL[nivel]:
                    if d["pregunta"] in rename:
                        self.assertEqual(rename[d["pregunta"]], d["nombre"],
                                         f"{nivel}: {d['id']} declara un nombre distinto al publicado")

    def test_las_tres_medidas_de_cierre(self):
        for nivel in ("undergraduate", "graduate"):
            with self.subTest(nivel=nivel):
                por_id = {d["id"]: d for d in config.PREGUNTAS_POR_NIVEL[nivel]}
                self.assertEqual(por_id["csat_universidad"]["tipo"], "medida")
                self.assertEqual(por_id["csat_universidad"]["escala"], "CSAT")
                self.assertEqual(por_id["csat_sujeto"]["tipo"], "medida")
                self.assertEqual(por_id["csat_sujeto"]["escala"], "CSAT")
                self.assertEqual(por_id["nps"]["tipo"], "medida")
                self.assertEqual(por_id["nps"]["escala"], "NPS")


class TestBloquePreguntasEnLaTabla(unittest.TestCase):

    def marco(self):
        return pd.DataFrame([
            {"ID": "a", "Carrera": "Economía", "Ciclo": "1° Ciclo",
             "La carrera": "Muy satisfecho", "La Universidad de Lima": "Satisfecho"},
        ])

    def test_la_tabla_trae_el_bloque_de_preguntas(self):
        t = construir_tabla(self.marco(), "undergraduate", "2026-1")
        self.assertEqual(t["version"], config.RESPUESTAS_VERSION)
        self.assertEqual({p["nombre"] for p in t["preguntas"]}, set(t["cabeceras"]))
        for p in t["preguntas"]:
            self.assertIn(p["tipo"], config.TIPOS_VALIDOS)
            self.assertTrue(p["id"] and p["pregunta"])
            if p["tipo"] == "medida":
                self.assertTrue(p["escala"])

    def test_el_id_de_cada_pregunta_es_unico_en_la_tabla(self):
        t = construir_tabla(self.marco(), "undergraduate", "2026-1")
        ids = [p["id"] for p in t["preguntas"]]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
