"""Tests — el público no docente (nivel 'nonfaculty', la Dependencia).

Exigen, igual que las pruebas de posgrado y de docente de pregrado, en este orden:
  (a) que las cabeceras de ingesta SE DERIVEN de la declaración de lib/config.py
      (el texto de cada pregunta, en el orden del formulario, más la pregunta
      abierta del nivel) y que no exista una segunda lista a mano;
  (b) que las claves reales de la bandeja de prueba pasen al CSV sin perderse;
  (c) que los públicos ya publicados no cambien (3998 / 4239 / 598 y los tres de
      1 respuesta); y
  (d) que el nivel use la Dependencia como identidad (una dependencia NO es una
      carrera de pregrado: no se traduce con CARRERA_FACULTAD) y reconozca su
      pregunta abierta.
"""

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import config
from zoho_a_csv import CABECERAS_POR_NIVEL, cabeceras_de, convertir_encuesta, detectar_nivel

RAIZ = Path(__file__).resolve().parents[3]
BANDEJAS = RAIZ / "data" / "zoho_pendientes"
NIVEL = "nonfaculty"
ENCUESTA = "ENCUESTA DE SATISFACCIÓN NO DOCENTE - 2026"
BANDEJA = BANDEJAS / "encuesta-de-satisfaccion-no-docente-2026.jsonl"

# Ids comunes del contrato del ETL (identidad, cierre, fechas y NPS).
IDS_COMUNES = {"id_respuesta", "inicio", "fin", "carrera", "nps",
               "csat_sujeto", "csat_universidad"}
# El estado del webhook no es una pregunta del formulario.
CLAVES_SISTEMA = {"Estado de respuesta"}
CONTEO_PUBLICADO = {
    "students/undergraduate/2025-2": 3998,
    "students/undergraduate/2026-1": 4239,
    "students/graduate/2026": 598,
}
# Los tres públicos con una respuesta de prueba publicada.
CONTEO_UNA_RESPUESTA = {
    "students/postgraduate/2026": 1,
    "facultystaff/postgraduate/2026": 1,
    "facultystaff/undergraduate/2026": 1,
}


def _primera_respuesta(bandeja: Path) -> dict:
    with open(bandeja, encoding="utf-8") as archivo:
        return json.loads(archivo.readline())


class TestDeclaracionNonfaculty(unittest.TestCase):
    """La declaración del público no docente vive una sola vez, en config.py."""

    def test_el_nivel_esta_declarado(self):
        self.assertIn(NIVEL, config.PREGUNTAS_POR_NIVEL)
        self.assertTrue(config.PREGUNTAS_FORMULARIO[NIVEL])

    def test_los_ids_llevan_el_prefijo_nd(self):
        for d in config.PREGUNTAS_FORMULARIO[NIVEL]:
            if d["id"] in IDS_COMUNES:
                continue
            with self.subTest(id=d["id"]):
                self.assertTrue(
                    d["id"].startswith("nd_"),
                    f"el id '{d['id']}' no lleva el prefijo 'nd_'",
                )

    def test_ids_unicos(self):
        ids = [d["id"] for d in config.PREGUNTAS_POR_NIVEL[NIVEL]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_el_nps_usa_su_escala(self):
        por_id = {d["id"]: d for d in config.PREGUNTAS_FORMULARIO[NIVEL]}
        self.assertEqual(por_id["nps"]["escala"], "NPS")

    def test_las_medidas_de_satisfaccion_son_csat(self):
        for d in config.PREGUNTAS_FORMULARIO[NIVEL]:
            if d["tipo"] != "medida" or d["id"] == "nps":
                continue
            with self.subTest(id=d["id"]):
                self.assertEqual(d["escala"], "CSAT")

    def test_las_medidas_de_cierre_quedan_fuera_de_las_dimensiones(self):
        # Este público cierra con el trío estándar (NPS + la Dependencia + la
        # Universidad): los tres deben quedar fuera del detector de dimensiones.
        for id_cierre in ("nps", "csat_sujeto", "csat_universidad"):
            with self.subTest(id=id_cierre):
                self.assertIn(id_cierre, config.IDS_MEDIDAS_DE_CIERRE)

    def test_los_nombres_publicados_no_se_repiten_dentro_del_nivel(self):
        nombres = [d["nombre"] for d in config.PREGUNTAS_POR_NIVEL[NIVEL]]
        self.assertEqual(len(nombres), len(set(nombres)))


class TestCabecerasDerivadas(unittest.TestCase):
    """Las cabeceras de ingesta salen de la declaración, no de una copia."""

    def test_las_cabeceras_salgan_de_la_declaracion(self):
        textos = [d["pregunta"] for d in config.PREGUNTAS_FORMULARIO[NIVEL]]
        comentario = config.comentario_de(NIVEL)
        esperado = textos + ([comentario] if comentario else [])
        self.assertEqual(cabeceras_de(ENCUESTA), esperado)

    def test_no_hay_lista_literal_para_el_nivel(self):
        # Si la lista literal sobreviviera, sería la segunda copia que este
        # cambio elimina (igual que se hizo con posgrado y docente de pregrado).
        self.assertNotIn(NIVEL, CABECERAS_POR_NIVEL)

    def test_el_comentario_se_reconoce_en_su_nivel(self):
        # Su texto real queda declarado en COMENTARIO_POR_NIVEL['nonfaculty'].
        self.assertIn(NIVEL, config.COMENTARIO_POR_NIVEL)
        comentario = config.comentario_de(NIVEL)
        self.assertTrue(comentario.startswith("Explica con tus palabras"))
        self.assertIn(comentario, cabeceras_de(ENCUESTA))

    def test_se_deduce_el_nivel_de_la_bandeja(self):
        self.assertEqual(detectar_nivel(ENCUESTA + ".csv"), NIVEL)


class TestBandejaPasaAlCsv(unittest.TestCase):
    """Las claves reales de la bandeja de prueba llegan al CSV sin perderse."""

    def _csv(self):
        if not BANDEJA.is_file():
            self.skipTest(f"no está la bandeja {BANDEJA.name}")
        with tempfile.TemporaryDirectory() as tmp:
            salida = convertir_encuesta(BANDEJA, Path(tmp))
            return salida.read_text(encoding="utf-8")

    def test_todas_las_respuestas_llegan_al_csv(self):
        if not BANDEJA.is_file():
            self.skipTest(f"no está la bandeja {BANDEJA.name}")
        registro = _primera_respuesta(BANDEJA)
        respuestas = {k: v for k, v in registro["respuestas"].items() if k not in CLAVES_SISTEMA}
        filas = list(csv.reader(io.StringIO(self._csv())))
        cabeceras, fila = filas[0], filas[1]
        fila_por_columna = dict(zip(cabeceras, fila))

        faltantes = sorted(set(respuestas) - set(cabeceras))
        self.assertFalse(faltantes, f"claves que no llegan al CSV: {faltantes}")
        alteradas = sorted(k for k, v in respuestas.items() if fila_por_columna.get(k) != str(v))
        self.assertFalse(alteradas, f"respuestas vacías o alteradas: {alteradas}")

    def test_el_identificador_viaja_aparte(self):
        if not BANDEJA.is_file():
            self.skipTest(f"no está la bandeja {BANDEJA.name}")
        registro = _primera_respuesta(BANDEJA)
        filas = list(csv.reader(io.StringIO(self._csv())))
        self.assertEqual(filas[1][filas[0].index("ID de respuesta")], registro["id_respuesta"])


class TestIdentidadYComentario(unittest.TestCase):
    """No docente: la identidad es la Dependencia, no una carrera de pregrado."""

    def test_la_columna_de_agrupacion_es_la_dependencia(self):
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertIn(cfg["carrera"], cabeceras_de(ENCUESTA))
        self.assertEqual(cfg["carrera"], "¿A qué dependencia perteneces?")
        self.assertEqual(cfg["rename"][cfg["carrera"]], config.columna(NIVEL, "carrera"))
        self.assertEqual(config.columna(NIVEL, "carrera"), "Dependencia")

    def test_una_dependencia_no_se_mapea_a_facultad(self):
        # A diferencia de docente de pregrado, aquí la identidad es una
        # dependencia administrativa: no se traduce con CARRERA_FACULTAD.
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertFalse(cfg["facultad_map"])

    def test_cierra_con_satisfaccion_con_la_universidad(self):
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertEqual(cfg["csat"], "La Universidad de Lima")
        self.assertEqual(cfg["rename"]["La Universidad de Lima"],
                         config.columna(NIVEL, "csat_universidad"))

    def test_el_comentario_se_renombra(self):
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertEqual(cfg["rename"][config.comentario_de(NIVEL)], "Comentario NPS")


class TestPublicosExistentesIntactos(unittest.TestCase):
    """Los públicos ya publicados conservan su conteo de respuestas."""

    def _respuestas(self, ruta_relativa):
        ruta = RAIZ / "zoho-survey" / ruta_relativa / "json" / "respuestas.json"
        if not ruta.is_file():
            self.skipTest(f"no está el respuestas.json publicado: {ruta_relativa}")
        return json.loads(ruta.read_text(encoding="utf-8"))

    def test_conteos_publicados(self):
        for ruta_relativa, esperado in CONTEO_PUBLICADO.items():
            with self.subTest(periodo=ruta_relativa):
                self.assertEqual(self._respuestas(ruta_relativa)["respuestas"], esperado)

    def test_los_publicos_de_una_respuesta_siguen_publicados(self):
        for ruta_relativa, esperado in CONTEO_UNA_RESPUESTA.items():
            with self.subTest(periodo=ruta_relativa):
                self.assertEqual(self._respuestas(ruta_relativa)["respuestas"], esperado)

    def test_nonfaculty_publica_su_respuesta_de_prueba(self):
        # Skip hasta que la corrida del ETL publique el periodo.
        datos = self._respuestas("nonfacultystaff/2026")
        self.assertEqual(datos["nivel"], NIVEL)
        self.assertEqual(datos["respuestas"], 1)
        ids = {p["id"] for p in datos["preguntas"]}
        self.assertIn("nd_clima_laboral", ids)
        self.assertIn("nd_aula_virtual", ids)
        self.assertIn("carrera", ids)


if __name__ == "__main__":
    unittest.main()
