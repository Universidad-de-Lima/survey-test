"""Tests — el público docente de pregrado (nivel facu lty-ug).

Exigen, igual que las pruebas de posgrado, en este orden:
  (a) que las cabeceras de ingesta SE DERIVEN de la declaración de lib/config.py
      (el texto de cada pregunta, en el orden del formulario, más la pregunta
      abierta del nivel) y que no exista una segunda lista a mano;
  (b) que las claves reales de la bandeja de prueba pasen al CSV sin perderse;
  (c) que los públicos ya publicados no cambien (3998 / 4239 / 598 y los dos de
      posgrado con 1 respuesta); y
  (d) que el nivel use la identidad y la facultad de una carrera de pregrado y
      reconozca su pregunta abierta (distinta de la de pregrado).
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
NIVEL = "faculty-ug"
ENCUESTA = "ENCUESTA DE SATISFACCIÓN DOCENTE - PREGRADO - 2026"
BANDEJA = BANDEJAS / "encuesta-de-satisfaccion-docente-pregrado-2026.jsonl"

# Ids comunes del contrato del ETL (identidad, cierre y NPS).
IDS_COMUNES = {"id_respuesta", "inicio", "fin", "carrera", "nps",
               "csat_sujeto", "csat_universidad"}
# El estado del webhook no es una pregunta del formulario.
CLAVES_SISTEMA = {"Estado de respuesta"}
CONTEO_PUBLICADO = {
    "students/undergraduate/2025-2": 3998,
    "students/undergraduate/2026-1": 4239,
    "students/graduate/2026": 598,
}
# Los dos públicos de posgrado declarados ayer publican su respuesta de prueba.
CONTEO_POSGRADO = {
    "students/postgraduate/2026": 1,
    "facultystaff/postgraduate/2026": 1,
}


def _primera_respuesta(bandeja: Path) -> dict:
    with open(bandeja, encoding="utf-8") as archivo:
        return json.loads(archivo.readline())


class TestDeclaracionDocenteUg(unittest.TestCase):
    """La declaración del público docente de pregrado vive una sola vez, en config.py."""

    def test_el_nivel_esta_declarado(self):
        self.assertIn(NIVEL, config.PREGUNTAS_POR_NIVEL)
        self.assertTrue(config.PREGUNTAS_FORMULARIO[NIVEL])

    def test_los_ids_llevan_el_prefijo_dug(self):
        for d in config.PREGUNTAS_FORMULARIO[NIVEL]:
            if d["id"] in IDS_COMUNES:
                continue
            with self.subTest(id=d["id"]):
                self.assertTrue(
                    d["id"].startswith("dug_"),
                    f"el id '{d['id']}' no lleva el prefijo 'dug_'",
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
        # Este público cierra con el par estándar (facultad/programa + Universidad)
        # y el NPS: los tres deben quedar fuera del detector de dimensiones.
        for id_cierre in ("nps", "csat_sujeto", "csat_universidad"):
            with self.subTest(id=id_cierre):
                self.assertIn(id_cierre, config.IDS_MEDIDAS_DE_CIERRE)

    def test_las_columnas_derivadas_no_son_preguntas_del_formulario(self):
        declaradas = {d["pregunta"] for d in config.PREGUNTAS_FORMULARIO[NIVEL]}
        for derivada in config.PREGUNTAS_POR_NIVEL[NIVEL]:
            if derivada["id"] in ("facultad", "ciclo"):
                self.assertNotIn(derivada["pregunta"], declaradas)


class TestCabecerasDerivadas(unittest.TestCase):
    """Las cabeceras de ingesta salen de la declaración, no de una copia."""

    def test_las_cabeceras_salgan_de_la_declaracion(self):
        textos = [d["pregunta"] for d in config.PREGUNTAS_FORMULARIO[NIVEL]]
        comentario = config.comentario_de(NIVEL)
        esperado = textos + ([comentario] if comentario else [])
        self.assertEqual(cabeceras_de(ENCUESTA), esperado)

    def test_no_hay_lista_literal_para_el_nivel(self):
        # Si la lista literal sobreviviera, sería la segunda copia que este
        # cambio elimina (igual que se hizo con posgrado).
        self.assertNotIn(NIVEL, CABECERAS_POR_NIVEL)

    def test_el_comentario_es_su_texto_real(self):
        comentario = config.comentario_de(NIVEL)
        # El cuestionario nuevo usa un texto distinto al de pregrado (sin punto
        # tras "anterior" y con punto final).
        self.assertNotEqual(comentario, config.COMENTARIO_NPS_PREGUNTA)
        self.assertTrue(comentario.startswith("Explica con tus palabras"))
        self.assertIn(comentario, cabeceras_de(ENCUESTA))

    def test_el_estudiantil_de_pregrado_no_cambia(self):
        self.assertEqual(config.comentario_de("undergraduate"), config.COMENTARIO_NPS_PREGUNTA)

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


class TestIdentidadFacultadYComentario(unittest.TestCase):
    """Docente de pregrado: carrera real, facultad por mapa y comentario propio."""

    def test_la_columna_de_agrupacion_es_la_carrera_real(self):
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertIn(cfg["carrera"], cabeceras_de(ENCUESTA))
        self.assertEqual(cfg["rename"][cfg["carrera"]], config.columna(NIVEL, "carrera"))

    def test_un_docente_de_pregrado_si_mapea_carrera_a_facultad(self):
        cfg = config.resolver_config_etl(NIVEL, cabeceras_de(ENCUESTA))
        self.assertTrue(cfg["facultad_map"])

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

    def test_posgrado_sigue_publicado(self):
        for ruta_relativa, esperado in CONTEO_POSGRADO.items():
            with self.subTest(periodo=ruta_relativa):
                self.assertEqual(self._respuestas(ruta_relativa)["respuestas"], esperado)

    def test_faculty_ug_publica_su_respuesta_de_prueba(self):
        # Skip hasta que la corrida del ETL publique el periodo.
        datos = self._respuestas("facultystaff/undergraduate/2026")
        self.assertEqual(datos["nivel"], NIVEL)
        self.assertEqual(datos["respuestas"], 1)
        ids = {p["id"] for p in datos["preguntas"]}
        self.assertIn("dug_clima_laboral", ids)
        self.assertIn("dug_aula_virtual", ids)


if __name__ == "__main__":
    unittest.main()
