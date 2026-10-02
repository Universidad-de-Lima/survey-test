"""Pruebas de la tabla de respuestas por periodo (lib/tabla_respuestas.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from lib.tabla_respuestas import SIN_RESPUESTA, construir_tabla


def marco():
    """Cuatro respuestas con dos preguntas de opciones, una abierta y campos de control."""
    return pd.DataFrame([
        {"ID": "a", "Fecha de inicio": "2026-01-01", "Fecha de fin": "2026-01-01",
         "Carrera": "Economía", "Tiempo laboral": "Tiempo completo",
         "La Universidad de Lima": "Muy satisfecho", "Comentario NPS": "excelente universidad"},
        {"ID": "b", "Fecha de inicio": "2026-01-02", "Fecha de fin": "2026-01-02",
         "Carrera": "Economía", "Tiempo laboral": "Tiempo parcial",
         "La Universidad de Lima": "Satisfecho", "Comentario NPS": "muy buena"},
        {"ID": "c", "Fecha de inicio": "2026-01-03", "Fecha de fin": "2026-01-03",
         "Carrera": "Derecho", "Tiempo laboral": "",
         "La Universidad de Lima": "Insatisfecho", "Comentario NPS": ""},
        {"ID": "d", "Fecha de inicio": "2026-01-04", "Fecha de fin": "2026-01-04",
         "Carrera": "Derecho", "Tiempo laboral": "Tiempo completo",
         "La Universidad de Lima": "Muy satisfecho", "Comentario NPS": "regular"},
    ])


class TablaTest(unittest.TestCase):

    def test_una_fila_por_respuesta_y_una_columna_por_pregunta(self):
        t = construir_tabla(marco(), "graduate", "2026")
        self.assertEqual(t["respuestas"], 4)
        self.assertEqual(len(t["filas"]), 4)
        self.assertEqual(t["cabeceras"], ["Carrera", "Tiempo laboral", "La Universidad de Lima"])
        self.assertTrue(all(len(f) == len(t["cabeceras"]) for f in t["filas"]))

    def test_lleva_el_id_y_la_fecha_aparte_de_las_preguntas(self):
        t = construir_tabla(marco(), "graduate", "2026")
        self.assertEqual(t["ids"], ["a", "b", "c", "d"])
        self.assertEqual(t["fechas"], ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
        self.assertEqual(len(t["ids"]), len(t["filas"]))
        self.assertEqual(len(t["fechas"]), len(t["filas"]))
        # No son columnas de opciones
        for fuera in ("ID", "Fecha de inicio", "Fecha de fin", "Comentario NPS"):
            self.assertNotIn(fuera, t["cabeceras"])
        motivos = {e["pregunta"]: e["motivo"] for e in t.get("excluidas", [])}
        self.assertIn("Comentario NPS", motivos)

    def test_contar_es_contar_filas_y_no_depende_del_id(self):
        t = construir_tabla(marco(), "graduate", "2026")
        tiempo = t["cabeceras"].index("Tiempo laboral")
        opciones = t["opciones"]["Tiempo laboral"]
        completos = [i for i, f in enumerate(t["filas"]) if opciones[f[tiempo]] == "Tiempo completo"]
        self.assertEqual(len(completos), 2)
        # Los mismos indices sirven para leer el ID o la fecha de esas respuestas
        self.assertEqual([t["ids"][i] for i in completos], ["a", "d"])
        self.assertEqual([t["fechas"][i] for i in completos], ["2026-01-01", "2026-01-04"])

    def test_las_filas_apuntan_a_la_opcion_correcta(self):
        t = construir_tabla(marco(), "graduate", "2026")
        opciones = t["opciones"]["Tiempo laboral"]
        tiempo = t["cabeceras"].index("Tiempo laboral")
        leido = [opciones[f[tiempo]] for f in t["filas"]]
        self.assertEqual(leido, ["Tiempo completo", "Tiempo parcial", SIN_RESPUESTA, "Tiempo completo"])

    def test_la_opcion_vacia_existe_cuando_hay_blancos(self):
        t = construir_tabla(marco(), "graduate", "2026")
        self.assertIn(SIN_RESPUESTA, t["opciones"]["Tiempo laboral"])
        self.assertNotIn(SIN_RESPUESTA, t["opciones"]["Carrera"])

    def test_las_opciones_van_ordenadas_y_sin_repetir(self):
        t = construir_tabla(marco(), "graduate", "2026")
        for opciones in t["opciones"].values():
            limpias = [o for o in opciones if o != SIN_RESPUESTA]
            self.assertEqual(limpias, sorted(limpias))
            self.assertEqual(len(limpias), len(set(limpias)))

    def test_una_columna_de_texto_libre_no_entra_por_su_cantidad_de_valores(self):
        # Hace falta superar el tope de opciones (50), asi que el marco se agranda.
        df = marco()
        df["¿Qué mejorarías?"] = [f"respuesta distinta {i}" for i in range(len(df))]
        relleno = pd.DataFrame([{"ID": f"x{i}", "Carrera": "Derecho", "Tiempo laboral": "Tiempo completo",
                                 "La Universidad de Lima": "Satisfecho", "Comentario NPS": "",
                                 "¿Qué mejorarías?": f"texto libre {i}"} for i in range(56)])
        df = pd.concat([df, relleno], ignore_index=True)
        t = construir_tabla(df, "graduate", "2026")
        self.assertNotIn("¿Qué mejorarías?", t["cabeceras"])
        motivos = {e["pregunta"]: e["motivo"] for e in t.get("excluidas", [])}
        self.assertEqual(motivos.get("¿Qué mejorarías?"), "texto libre")


if __name__ == "__main__":
    unittest.main()
