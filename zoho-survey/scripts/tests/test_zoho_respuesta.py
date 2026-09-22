"""
Tests de la bandeja de entrada de respuestas de Zoho Survey (lib/zoho_respuesta).

Cubren, sin llamar a ningun servicio externo:
  - la normalizacion de la respuesta que llega por webhook;
  - el fallo explicito cuando falta el identificador de respuesta o la encuesta;
  - el enmascarado de datos personales ANTES de guardar (el repositorio es publico);
  - la ausencia de duplicados cuando Zoho reintenta el envio.
"""

import json
import tempfile
import unittest
from pathlib import Path

from lib.zoho_respuesta import (
    agregar_pendiente,
    guardar_pendientes,
    leer_pendientes,
    normalizar_respuesta,
    respuesta_ya_registrada,
    slug_encuesta,
)

MOMENTO = "2026-09-19T10:20:00"

# Respuesta real de la encuesta "ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO -
# 2026-2", tal como llega cuando Zoho la empuja: el identificador viene en la
# clave "ID" y el nombre de la encuesta NO viaja en el cuerpo (se toma del
# título de la incidencia que crea el webhook).
PAYLOAD_INCIDENCIA = {
    "ID": "AxC5U14h",
    "Inicio": "Sep 22, 2026 07:54:09",
    "Fin": "Sep 22, 2026 07:55:25",
    "Estado": "COMPLETED",
    "Carrera": "Administración",
    "Ciclo": "1° Ciclo",
    "NPS": "10",
    "Cualitativo": "Prueba",
}

PAYLOAD = {
    "ID de respuesta": "123430000012345",
    "Encuesta": "ESTUDIANTIL 2026-1",
    "Hora de finalizacion": "19-sep-2026 10:15 a. m.",
    "Net Promoter Score (de un total de 10)": "9",
    "¿Qué carrera profesional estudias?": "Ingeniería Industrial",
    "Comentario": "Excelente, escriban a juan.perez@example.com o al 987 654 321",
    "Correo de contacto": "juan.perez@example.com",
    "Codigo": "20201234",
    "Servicios": ["Biblioteca", "Servicio médico"],
}


class TestNormalizarRespuesta(unittest.TestCase):
    def test_normaliza_el_payload_del_webhook(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        self.assertEqual(r["id_respuesta"], "123430000012345")
        self.assertEqual(r["encuesta"], "ESTUDIANTIL 2026-1")
        self.assertEqual(r["recibido_en"], MOMENTO)
        self.assertEqual(
            r["respuestas"]["¿Qué carrera profesional estudias?"], "Ingeniería Industrial"
        )

    def test_conserva_los_campos_desconocidos(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        self.assertEqual(r["respuestas"]["Servicios"], ["Biblioteca", "Servicio médico"])

    def test_enmascara_datos_personales_antes_de_guardar(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        volcado = json.dumps(r, ensure_ascii=False)
        self.assertNotIn("juan.perez@example.com", volcado)
        self.assertNotIn("987 654 321", volcado)
        self.assertNotIn("20201234", volcado)
        self.assertIn("[CORREO ENMASCARADO]", volcado)

    def test_falla_si_falta_el_identificador_de_respuesta(self):
        sin_id = {k: v for k, v in PAYLOAD.items() if k != "ID de respuesta"}
        with self.assertRaises(ValueError) as ctx:
            normalizar_respuesta(sin_id, momento=MOMENTO)
        self.assertIn("identificador", str(ctx.exception).lower())

    def test_falla_si_falta_la_encuesta(self):
        sin_encuesta = {k: v for k, v in PAYLOAD.items() if k != "Encuesta"}
        with self.assertRaises(ValueError) as ctx:
            normalizar_respuesta(sin_encuesta, momento=MOMENTO)
        self.assertIn("encuesta", str(ctx.exception).lower())

    def test_falla_si_el_payload_no_es_un_objeto(self):
        with self.assertRaises(ValueError):
            normalizar_respuesta([1, 2, 3], momento=MOMENTO)


class TestSinDuplicados(unittest.TestCase):
    def test_detecta_la_respuesta_ya_registrada(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        self.assertFalse(respuesta_ya_registrada([], r["id_respuesta"]))
        self.assertTrue(respuesta_ya_registrada([r], r["id_respuesta"]))

    def test_no_agrega_la_misma_respuesta_dos_veces(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        una = agregar_pendiente([], r)
        dos = agregar_pendiente(una, r)
        self.assertEqual(len(una), 1)
        self.assertEqual(len(dos), 1)


class TestArchivoDePendientes(unittest.TestCase):
    def test_ida_y_vuelta_en_disco(self):
        r = normalizar_respuesta(PAYLOAD, momento=MOMENTO)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "pendientes.jsonl"
            guardar_pendientes(ruta, [r])
            self.assertEqual(leer_pendientes(ruta), [r])

    def test_archivo_inexistente_devuelve_lista_vacia(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(leer_pendientes(Path(tmp) / "no-existe.jsonl"), [])

    def test_slug_de_encuesta(self):
        self.assertEqual(slug_encuesta("ESTUDIANTIL 2026-1"), "estudiantil-2026-1")


class TestRespuestaDeIncidencia(unittest.TestCase):
    """La respuesta llega como cuerpo de la incidencia que crea el webhook.

    Zoho llama a la API de incidencias de GitHub: el identificador viaja en la
    clave "ID" y el nombre de la encuesta NO viaja en el cuerpo, sino en el
    titulo de la incidencia (por eso se admite un nombre por defecto).
    """

    def test_acepta_el_identificador_en_la_clave_ID(self):
        r = normalizar_respuesta(
            PAYLOAD_INCIDENCIA,
            encuesta_por_defecto="ESTUDIANTIL 2026-2",
            momento=MOMENTO,
        )
        self.assertEqual(r["id_respuesta"], "AxC5U14h")
        self.assertEqual(r["encuesta"], "ESTUDIANTIL 2026-2")

    def test_la_encuesta_del_cuerpo_tiene_prioridad_sobre_la_por_defecto(self):
        payload = dict(PAYLOAD_INCIDENCIA, Encuesta="POSGRADO 2026-1")
        r = normalizar_respuesta(
            payload, encuesta_por_defecto="ESTUDIANTIL 2026-2", momento=MOMENTO
        )
        self.assertEqual(r["encuesta"], "POSGRADO 2026-1")

    def test_una_por_defecto_vacia_se_ignora(self):
        payload = dict(PAYLOAD_INCIDENCIA, Encuesta="ESTUDIANTIL 2026-2")
        r = normalizar_respuesta(payload, encuesta_por_defecto="   ", momento=MOMENTO)
        self.assertEqual(r["encuesta"], "ESTUDIANTIL 2026-2")

    def test_sin_encuesta_ni_por_defecto_falla(self):
        with self.assertRaises(ValueError) as ctx:
            normalizar_respuesta(PAYLOAD_INCIDENCIA, momento=MOMENTO)
        self.assertIn("encuesta", str(ctx.exception).lower())

    def test_el_identificador_no_se_guarda_entre_las_respuestas(self):
        r = normalizar_respuesta(
            PAYLOAD_INCIDENCIA,
            encuesta_por_defecto="ESTUDIANTIL 2026-2",
            momento=MOMENTO,
        )
        self.assertNotIn("ID", r["respuestas"])
        self.assertIn("NPS", r["respuestas"])


if __name__ == "__main__":
    unittest.main()
