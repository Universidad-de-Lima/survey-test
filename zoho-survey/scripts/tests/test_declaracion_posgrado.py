"""Tests — los dos públicos de Escuela de Posgrado (estudiantil y docente).

Exigen, en este orden:
  (a) que las cabeceras de ingesta SE DERIVEN de la declaración de lib/config.py
      (el texto de cada pregunta, en el orden del formulario, más la pregunta
      abierta del nivel si la tiene) y que no exista una segunda lista a mano;
  (b) que las claves reales de las bandejas de prueba de los dos públicos nuevos
      pasen al CSV sin perderse;
  (c) que los tres públicos ya publicados sigan con 3998 / 4239 / 598 respuestas.
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

NIVELES_NUEVOS = {
    "postgraduate": "ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - ESCUELA DE POSGRADO - 2026",
    "faculty-pg": "ENCUESTA DE SATISFACCIÓN DOCENTE - ESCUELA DE POSGRADO - 2026",
}
BANDEJA_POR_NIVEL = {
    "postgraduate": BANDEJAS / "encuesta-de-satisfaccion-estudiantil-escuela-de-posgrado-2026.jsonl",
    "faculty-pg": BANDEJAS / "encuesta-de-satisfaccion-docente-escuela-de-posgrado-2026.jsonl",
}
# Respuestas publicadas de los tres públicos que ya funcionan (no se deben mover).
CONTEO_PUBLICADO = {
    "students/undergraduate/2025-2": 3998,
    "students/undergraduate/2026-1": 4239,
    "students/graduate/2026": 598,
}
# El estado del webhook no es una pregunta del formulario.
CLAVES_SISTEMA = {"Estado de respuesta"}


def _leer_primera_respuesta(bandeja: Path) -> dict:
    with open(bandeja, encoding="utf-8") as archivo:
        return json.loads(archivo.readline())


class TestDeclaracionPosgrado(unittest.TestCase):
    """La declaración de cada público nuevo vive una sola vez, en config.py."""

    def test_los_dos_niveles_estan_declarados(self):
        for nivel in NIVELES_NUEVOS:
            with self.subTest(nivel=nivel):
                self.assertIn(nivel, config.PREGUNTAS_POR_NIVEL)
                self.assertTrue(config.PREGUNTAS_FORMULARIO[nivel])

    def test_los_ids_llevan_el_prefijo_del_publico(self):
        prefijo = {"postgraduate": "pg_", "faculty-pg": "dpg_"}
        # Estos ids son los del contrato del ETL (identidad y NPS).
        comunes = {"id_respuesta", "inicio", "fin", "carrera", "nps"}
        for nivel in NIVELES_NUEVOS:
            with self.subTest(nivel=nivel):
                for d in config.PREGUNTAS_FORMULARIO[nivel]:
                    if d["id"] in comunes:
                        continue
                    self.assertTrue(
                        d["id"].startswith(prefijo[nivel]),
                        f"{nivel}: el id '{d['id']}' no lleva el prefijo '{prefijo[nivel]}'",
                    )

    def test_las_escalas_de_cada_publico(self):
        por_nivel = {nivel: {d["id"]: d for d in config.PREGUNTAS_FORMULARIO[nivel]}
                     for nivel in NIVELES_NUEVOS}
        estudiantil = por_nivel["postgraduate"]
        docente = por_nivel["faculty-pg"]
        self.assertEqual(estudiantil["pg_csat_programa"]["escala"], "acuerdo")
        self.assertEqual(estudiantil["pg_lealtad_programa"]["escala"], "acuerdo")
        self.assertEqual(docente["dpg_aula_virtual"]["escala"], "satisfaccion")
        self.assertEqual(docente["dpg_satisfaccion_general"]["escala"], "satisfaccion")
        for nivel in NIVELES_NUEVOS:
            self.assertEqual(por_nivel[nivel]["nps"]["escala"], "NPS")

    def test_las_medidas_de_cierre_quedan_fuera_de_las_dimensiones(self):
        # Estos públicos no tienen el par csat_sujeto/csat_universidad: sus
        # medidas de cierre son propias y también deben quedar fuera del
        # detector de dimensiones.
        for id_cierre in ("pg_csat_programa", "pg_lealtad_programa", "dpg_satisfaccion_general"):
            with self.subTest(id=id_cierre):
                self.assertIn(id_cierre, config.IDS_MEDIDAS_DE_CIERRE)

    def test_las_columnas_derivadas_no_son_preguntas_del_formulario(self):
        # Facultad y Ciclo se publican (derivadas) pero Zoho no las manda: no
        # pueden ser cabeceras de ingesta.
        for nivel in NIVELES_NUEVOS:
            with self.subTest(nivel=nivel):
                declaradas = {d["pregunta"] for d in config.PREGUNTAS_FORMULARIO[nivel]}
                self.assertNotIn("Facultad (derivada; un programa de posgrado no es una carrera de pregrado)",
                                 declaradas)


class TestCabecerasDerivadas(unittest.TestCase):
    """Las cabeceras de ingesta salen de la declaración, no de una copia."""

    def test_las_cabeceras_salgan_de_la_declaracion(self):
        for nivel, encuesta in NIVELES_NUEVOS.items():
            with self.subTest(nivel=nivel):
                textos = [d["pregunta"] for d in config.PREGUNTAS_FORMULARIO[nivel]]
                comentario = config.comentario_de(nivel)
                esperado = textos + ([comentario] if comentario else [])
                self.assertEqual(cabeceras_de(encuesta), esperado)

    def test_no_hay_lista_literal_para_los_niveles_declarados(self):
        # Si la lista de cabeceras fuese una segunda copia, estos niveles
        # volverían a aparecer en CABECERAS_POR_NIVEL.
        for nivel in config.PREGUNTAS_FORMULARIO:
            with self.subTest(nivel=nivel):
                self.assertNotIn(nivel, CABECERAS_POR_NIVEL)

    def test_el_comentario_del_docente_es_su_texto_real(self):
        comentario = config.comentario_de("faculty-pg")
        self.assertTrue(comentario.startswith("Desde su experiencia"))
        self.assertIn(comentario, cabeceras_de(NIVELES_NUEVOS["faculty-pg"]))

    def test_el_estudiantil_de_posgrado_no_tiene_comentario(self):
        self.assertEqual(config.comentario_de("postgraduate"), "")
        # Tampoco debe colarse una pregunta abierta inventada en sus cabeceras.
        self.assertNotIn(
            config.COMENTARIO_NPS_PREGUNTA,
            cabeceras_de(NIVELES_NUEVOS["postgraduate"]),
        )

    def test_se_deduce_el_nivel_de_las_dos_bandejas(self):
        for nivel, encuesta in NIVELES_NUEVOS.items():
            with self.subTest(nivel=nivel):
                self.assertEqual(detectar_nivel(encuesta + ".csv"), nivel)


class TestBandejasPasanAlCsv(unittest.TestCase):
    """Las claves reales de las bandejas de prueba llegan al CSV sin perderse."""

    def _csv(self, nivel):
        bandeja = BANDEJA_POR_NIVEL[nivel]
        if not bandeja.is_file():
            self.skipTest(f"no está la bandeja {bandeja.name}")
        with tempfile.TemporaryDirectory() as tmp:
            salida = convertir_encuesta(bandeja, Path(tmp))
            return salida.read_text(encoding="utf-8")

    def test_todas_las_respuestas_llegan_al_csv(self):
        for nivel in NIVELES_NUEVOS:
            with self.subTest(nivel=nivel):
                bandeja = BANDEJA_POR_NIVEL[nivel]
                if not bandeja.is_file():
                    self.skipTest(f"no está la bandeja {bandeja.name}")
                registro = _leer_primera_respuesta(bandeja)
                respuestas = {
                    k: v for k, v in registro["respuestas"].items() if k not in CLAVES_SISTEMA
                }
                filas = list(csv.reader(io.StringIO(self._csv(nivel))))
                cabeceras, fila = filas[0], filas[1]
                fila_por_columna = dict(zip(cabeceras, fila))

                # La cabecera de cada pregunta es exactamente su clave en Zoho.
                faltantes = sorted(set(respuestas) - set(cabeceras))
                self.assertFalse(faltantes, f"{nivel}: claves que no llegan al CSV: {faltantes}")
                # Y ninguna respuesta se pierde.
                vacias = sorted(k for k, v in respuestas.items() if fila_por_columna.get(k) != str(v))
                self.assertFalse(vacias, f"{nivel}: respuestas vacías o alteradas: {vacias}")

    def test_el_identificador_viaja_aparte(self):
        for nivel in NIVELES_NUEVOS:
            with self.subTest(nivel=nivel):
                bandeja = BANDEJA_POR_NIVEL[nivel]
                if not bandeja.is_file():
                    self.skipTest(f"no está la bandeja {bandeja.name}")
                registro = _leer_primera_respuesta(bandeja)
                filas = list(csv.reader(io.StringIO(self._csv(nivel))))
                self.assertEqual(filas[1][filas[0].index("ID de respuesta")], registro["id_respuesta"])


class TestIdentidadYFacultad(unittest.TestCase):
    """La identidad de posgrado es 'Programa:' y no se fuerza CARRERA_FACULTAD."""

    def test_la_columna_de_agrupacion_es_programa(self):
        for nivel, encuesta in NIVELES_NUEVOS.items():
            with self.subTest(nivel=nivel):
                cfg = config.resolver_config_etl(nivel, cabeceras_de(encuesta))
                self.assertEqual(cfg["carrera"], "Programa:")
                self.assertEqual(cfg["rename"]["Programa:"], "Programa")

    def test_posgrado_no_mapea_carrera_a_facultad(self):
        for nivel, encuesta in NIVELES_NUEVOS.items():
            with self.subTest(nivel=nivel):
                cfg = config.resolver_config_etl(nivel, cabeceras_de(encuesta))
                self.assertFalse(cfg["facultad_map"])
                # No hay pregunta 'Satisfacción con la Universidad' en estos formularios.
                self.assertIsNone(cfg["csat"])

    def test_el_comentario_del_docente_se_renombra(self):
        cabeceras = cabeceras_de(NIVELES_NUEVOS["faculty-pg"])
        cfg = config.resolver_config_etl("faculty-pg", cabeceras)
        self.assertEqual(cfg["rename"][config.comentario_de("faculty-pg")], "Comentario NPS")


class TestPublicosExistentesIntactos(unittest.TestCase):
    """Los tres públicos ya publicados conservan su conteo de respuestas."""

    def test_conteos_publicados(self):
        for ruta_relativa, esperado in CONTEO_PUBLICADO.items():
            with self.subTest(periodo=ruta_relativa):
                ruta = RAIZ / "zoho-survey" / ruta_relativa / "json" / "respuestas.json"
                if not ruta.is_file():
                    self.skipTest(f"no está el respuestas.json publicado: {ruta_relativa}")
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                self.assertEqual(datos["respuestas"], esperado)


if __name__ == "__main__":
    unittest.main()
