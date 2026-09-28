'''Pruebas del modulo de conteos por pregunta (lib/conteos.py).'''
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from lib.config import EMPLEABILIDAD_CATEGORIAS
from lib.conteos import construir_conteos, es_pregunta_de_escala

# Tres categorias reales del catalogo (cuentan como empleado) y una que no.
EMPLEADO_1, EMPLEADO_2, EMPLEADO_3 = EMPLEABILIDAD_CATEGORIAS[:3]
NO_EMPLEADO = "No disponible para trabajar"
NPS = "Recomiendas la Universidad de Lima"
CSAT = "La Universidad de Lima"
MAPA = {"La carrera": "Académico"}          # lo que ya publica dimensiones.json


def marco():
    '''Cuatro respuestas de graduados: dos de Economia y dos de Derecho.'''
    return pd.DataFrame([
        {"ID": "a", "Carrera": "Economía", "Facultad": "Facultad de Ciencias Empresariales",
         "Ciclo": "NA", "Estado de respuesta": "COMPLETED",
         "Situación laboral": EMPLEADO_1, "Tiempo laboral": "Tiempo completo",
         "Disponibilidad para asesorias": "Muy satisfecho", CSAT: "Muy satisfecho",
         NPS: 10, "La carrera": "Muy satisfecho", "Comentario NPS": "buena"},
        {"ID": "b", "Carrera": "Economía", "Facultad": "Facultad de Ciencias Empresariales",
         "Ciclo": "NA", "Situación laboral": EMPLEADO_2, "Tiempo laboral": "Tiempo parcial",
         "Disponibilidad para asesorias": "Satisfecho", CSAT: "Satisfecho",
         NPS: 9, "La carrera": "Satisfecho", "Comentario NPS": ""},
        {"ID": "c", "Carrera": "Derecho", "Facultad": "Facultad de Derecho",
         "Ciclo": "NA", "Situación laboral": NO_EMPLEADO, "Tiempo laboral": "",
         "Disponibilidad para asesorias": "Insatisfecho", CSAT: "Totalmente satisfecho",
         NPS: 8, "La carrera": "Totalmente satisfecho", "Comentario NPS": ""},
        {"ID": "d", "Carrera": "Derecho", "Facultad": "Facultad de Derecho",
         "Ciclo": "NA", "Situación laboral": EMPLEADO_3, "Tiempo laboral": "Tiempo completo",
         "Disponibilidad para asesorias": "Totalmente insatisfecho", CSAT: "Insatisfecho",
         NPS: 7, "La carrera": "Insatisfecho", "Comentario NPS": ""},
    ])


def arma(df=None, escala=MAPA, ciclo=False):
    return construir_conteos(df if df is not None else marco(), "graduate", escala, ciclo,
                             nps_col=NPS, csat_col=CSAT)


class ConteosTest(unittest.TestCase):

    def test_reconoce_una_pregunta_de_escala(self):
        df = marco()
        self.assertTrue(es_pregunta_de_escala(df["La carrera"]))
        self.assertFalse(es_pregunta_de_escala(df["Situación laboral"]))

    def test_no_cuenta_columnas_de_control_ni_las_ya_publicadas(self):
        nombres = [q["pregunta"] for q in arma()["preguntas"]]
        self.assertIn("Situación laboral", nombres)
        self.assertIn("Tiempo laboral", nombres)
        self.assertNotIn("ID", nombres)
        self.assertNotIn("Carrera", nombres)
        self.assertNotIn("La carrera", nombres)          # ya esta en dimensiones.json
        self.assertNotIn(NPS, nombres)                   # ya esta en nps_carrera.json
        self.assertNotIn(CSAT, nombres)                  # ya esta en csat_carrera.json
        self.assertNotIn("Comentario NPS", nombres)      # ya esta en sentimiento.json
        self.assertNotIn("Estado de respuesta", nombres)  # lo agrega el conversor, no es pregunta

    def test_una_escala_fuera_del_mapa_si_se_cuenta(self):
        d = arma()
        pregunta = [q for q in d["preguntas"] if q["pregunta"] == "Disponibilidad para asesorias"][0]
        self.assertEqual(len(pregunta["por_opcion"]), 4)
        catalogo = {c["pregunta"]: c for c in d["catalogo"]}
        self.assertEqual(catalogo["Disponibilidad para asesorias"]["donde"], "conteos.json")
        self.assertEqual(catalogo["Disponibilidad para asesorias"]["tipo"], "escala")

    def test_cuenta_opciones_y_abre_por_carrera(self):
        pregunta = [q for q in arma()["preguntas"] if q["pregunta"] == "Situación laboral"][0]
        opciones = {o["opcion"]: o for o in pregunta["por_opcion"]}
        self.assertEqual(opciones[EMPLEADO_1]["total"], 1)
        self.assertEqual(opciones[EMPLEADO_1]["por_carrera"]["Economía"], 1)
        self.assertEqual(opciones[NO_EMPLEADO]["por_carrera"]["Derecho"], 1)
        self.assertEqual(pregunta["total"], 4)

    def test_cuenta_los_vacios_como_sin_respuesta(self):
        pregunta = [q for q in arma()["preguntas"] if q["pregunta"] == "Tiempo laboral"][0]
        self.assertEqual(pregunta["sin_respuesta"], 1)
        self.assertEqual(len(pregunta["por_opcion"]), 2)   # los vacios no son una opcion

    def test_empleabilidad_por_carrera_y_total(self):
        e = arma()["empleabilidad"]
        self.assertEqual(e["total"]["empleados"], 3)
        self.assertEqual(e["total"]["total"], 4)
        self.assertEqual(e["total"]["score"], 75.0)
        por_carrera = {c["carrera"]: c for c in e["por_carrera"]}
        self.assertEqual(por_carrera["Economía"]["score"], 100.0)
        self.assertEqual(por_carrera["Derecho"]["score"], 50.0)

    def test_el_catalogo_dice_donde_esta_cada_pregunta(self):
        catalogo = {c["pregunta"]: c for c in arma()["catalogo"]}
        self.assertEqual(catalogo["Situación laboral"]["donde"], "conteos.json")
        self.assertEqual(catalogo["La carrera"]["donde"], "dimensiones.json")
        self.assertEqual(catalogo["Comentario NPS"]["donde"], "sentimiento.json")
        self.assertEqual(catalogo[NPS]["donde"], "nps_carrera.json")
        self.assertEqual(catalogo[CSAT]["donde"], "csat_carrera.json")

    def test_sin_situacion_laboral_no_inventa_empleabilidad(self):
        df = marco().drop(columns=["Situación laboral"])
        self.assertNotIn("empleabilidad", arma(df))


if __name__ == "__main__":
    unittest.main()
