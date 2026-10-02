"""Tests — declaración de preguntas en los JSON resumidos del portal.

Las páginas del portal NO cargan respuestas.json (es enorme): leen los resumidos que
escribe el ETL (dashboard_data.json, resumenes.json y filtros.json). Por eso su lógica
no tiene cómo saber qué es cada columna y compara por nombre escrito a mano.

Como la declaración única vive en lib/config.py, el ETL publica el mismo bloque
'preguntas' también en esos tres resumidos: mismos ids que el respuestas.json del mismo
período, y los mismos campos obligatorios (id, nombre, tipo y escala). El texto largo de
la pregunta se omite a propósito para que los resumidos sigan siendo de pocos KB.
"""
import json
import os
import sys
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import pandas as pd

from lib import config
from lib.tabla_respuestas import construir_tabla, declaracion_compacta

# students/ vive junto a scripts/ (zoho-survey/students).
ROOT = Path(scripts_dir).parent / "students"

# Campos obligatorios del bloque compacto: el `pregunta` largo no viaja en los resumidos.
CAMPOS_COMPACTOS = {"id", "nombre", "tipo", "escala"}

RESUMIDOS = ("dashboard_data.json", "resumenes.json", "filtros.json")


class TestDeclaracionCompacta(unittest.TestCase):
    """La declaración compacta conserva los ids y los cuatro campos obligatorios."""

    def marco(self):
        return pd.DataFrame([
            {"ID": "a", "Carrera": "Economía", "Ciclo": "1° Ciclo",
             "La carrera": "Muy satisfecho", "La Universidad de Lima": "Satisfecho"},
            {"ID": "b", "Carrera": "Derecho", "Ciclo": "2° Ciclo",
             "La carrera": "Satisfecho", "La Universidad de Lima": "Muy satisfecho"},
        ])

    def test_conserva_ids_y_campos_y_no_repite_la_pregunta(self):
        tabla = construir_tabla(self.marco(), "undergraduate", "2026-1")
        referencia = tabla["preguntas"]
        self.assertTrue(referencia)

        compacta = declaracion_compacta(referencia)

        self.assertEqual([p["id"] for p in compacta], [p["id"] for p in referencia])
        for entrada in compacta:
            self.assertEqual(set(entrada), CAMPOS_COMPACTOS)
            self.assertIn(entrada["tipo"], config.TIPOS_VALIDOS)
            self.assertTrue(entrada["id"] and entrada["nombre"])
            if entrada["tipo"] == "medida":
                self.assertTrue(entrada["escala"])

    def test_la_declaracion_compacta_es_mas_chica_que_la_completa(self):
        tabla = construir_tabla(self.marco(), "undergraduate", "2026-1")
        completa = json.dumps(tabla["preguntas"], ensure_ascii=False)
        compacta = json.dumps(declaracion_compacta(tabla["preguntas"]), ensure_ascii=False)
        self.assertLess(len(compacta), len(completa))


class TestResumidosPublicados(unittest.TestCase):
    """Cada resumido publicado trae la misma declaración (ids y campos) que su respuestas.json."""

    def carpetas_json(self):
        """Las carpetas json/ de los períodos reales publicados."""
        return sorted(ROOT.glob("*/*/json"))

    def test_hay_periodos_publicados(self):
        carpetas = [c for c in self.carpetas_json() if (c / "respuestas.json").exists()]
        self.assertTrue(carpetas, f"no se encontraron respuestas.json bajo {ROOT}")

    def test_los_resumidos_traen_la_declaracion_de_su_respuestas(self):
        for json_dir in self.carpetas_json():
            respuestas_path = json_dir / "respuestas.json"
            if not respuestas_path.exists():
                continue
            with self.subTest(periodo=json_dir.as_posix()):
                respuestas = json.loads(respuestas_path.read_text(encoding="utf-8"))
                ids_referencia = [p["id"] for p in respuestas.get("preguntas", [])]
                self.assertTrue(ids_referencia, f"{json_dir}: respuestas.json no declara preguntas")
                self.assertEqual(len(ids_referencia), len(set(ids_referencia)),
                                 f"{json_dir}: ids repetidos en respuestas.json")

                for nombre in RESUMIDOS:
                    ruta = json_dir / nombre
                    self.assertTrue(ruta.exists(), f"falta {ruta}")
                    doc = json.loads(ruta.read_text(encoding="utf-8"))
                    self.assertIn("preguntas", doc,
                                  f"{json_dir}/{nombre}: no trae el bloque 'preguntas'")
                    declaradas = doc["preguntas"]
                    self.assertTrue(declaradas, f"{json_dir}/{nombre}: el bloque está vacío")

                    ids = [p["id"] for p in declaradas]
                    self.assertEqual(set(ids), set(ids_referencia),
                                     f"{json_dir}/{nombre}: los ids no coinciden con respuestas.json")
                    self.assertEqual(len(ids), len(set(ids)),
                                     f"{json_dir}/{nombre}: ids repetidos")

                    for p in declaradas:
                        self.assertEqual(set(p), CAMPOS_COMPACTOS,
                                         f"{json_dir}/{nombre}: campos inesperados en {p!r}")
                        self.assertIn(p["tipo"], config.TIPOS_VALIDOS)
                        if p["tipo"] == "medida":
                            self.assertTrue(p["escala"],
                                            f"{json_dir}/{nombre}: la medida '{p['id']}' sin escala")


if __name__ == "__main__":
    unittest.main()
