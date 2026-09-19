"""
Tests de la cadena de motores del analisis cualitativo (lib/ia_client).

Comprueba, SIN llamar a ninguna API, que:
  - la cadena se lee de IA_CUALITATIVO_CADENA y cae al valor por defecto;
  - el formato "servicio:modelo" se parsea en orden y tolera erratas;
  - cada servicio arma la peticion en el formato que su proveedor entiende;
  - los motores sin clave configurada se omiten en lugar de romper el ETL.
"""

import json
import os
import unittest
from contextlib import contextmanager
from unittest import mock

from lib.ia_client import (
    CADENA_DEFECTO,
    SERVICIOS,
    MotorIA,
    claves_faltantes,
    construir_motores,
    leer_cadena,
    parsear_cadena,
)

CLAVES = ["GOOGLE_API_KEY", "NVIDIA_API_KEY", "OPENCODE_API_KEY"]


@contextmanager
def entorno(claves):
    """Reemplaza el entorno de claves solo durante el test."""
    limpio = {k: v for k, v in os.environ.items() if k not in CLAVES}
    limpio.update(claves)
    with mock.patch.dict(os.environ, limpio, clear=True):
        yield


class TestParsearCadena(unittest.TestCase):
    def test_orden_preservado(self):
        self.assertEqual(
            parsear_cadena("google:gemini-3.8-flash,nvidia:moonshotai/kimi-k3"),
            [("google", "gemini-3.8-flash"), ("nvidia", "moonshotai/kimi-k3")],
        )

    def test_tolera_espacios_y_comas_repetidas(self):
        self.assertEqual(
            parsear_cadena(" google:gemini-3.8-flash ,, opencode:deepseek-v4.1-flash "),
            [("google", "gemini-3.8-flash"), ("opencode", "deepseek-v4.1-flash")],
        )

    def test_ignora_servicio_desconocido(self):
        self.assertEqual(
            parsear_cadena("inventado:modelo-x,nvidia:nvidia/nemotron-3-ultra-550b-a55b"),
            [("nvidia", "nvidia/nemotron-3-ultra-550b-a55b")],
        )

    def test_ignora_entradas_sin_modelo_o_sin_separador(self):
        self.assertEqual(
            parsear_cadena("google:,nvidia,nvidia:meta/muse-glimmer-30b"),
            [("nvidia", "meta/muse-glimmer-30b")],
        )

    def test_ignora_motor_repetido(self):
        self.assertEqual(
            parsear_cadena("google:a,google:a,google:b"),
            [("google", "a"), ("google", "b")],
        )

    def test_cadena_vacia(self):
        self.assertEqual(parsear_cadena(""), [])


class TestLecturaDeCadena(unittest.TestCase):
    def test_usa_variable_de_entorno(self):
        with entorno({"IA_CUALITATIVO_CADENA": "opencode:deepseek-v4.1-flash"}):
            self.assertEqual(leer_cadena(), "opencode:deepseek-v4.1-flash")

    def test_cae_al_valor_por_defecto(self):
        with entorno({}):
            self.assertEqual(leer_cadena(), CADENA_DEFECTO)

    def test_la_cadena_por_defecto_tiene_el_orden_acordado(self):
        servicios = [servicio for servicio, _ in parsear_cadena(CADENA_DEFECTO)]
        self.assertEqual(
            servicios,
            ["google", "nvidia", "nvidia", "nvidia", "nvidia", "opencode"],
        )
        modelos_nvidia = [m for s, m in parsear_cadena(CADENA_DEFECTO) if s == "nvidia"]
        self.assertEqual(modelos_nvidia, [
            "moonshotai/kimi-k3",
            "deepseek-ai/deepseek-v4-pro-0813",
            "nvidia/nemotron-3-ultra-550b-a55b",
            "meta/muse-glimmer-30b",
        ])


class TestConstruirMotores(unittest.TestCase):
    def test_omite_los_motores_sin_clave(self):
        with entorno({"GOOGLE_API_KEY": "clave-falsa"}):
            motores = construir_motores("google:g1,nvidia:n1,opencode:o1")
        self.assertEqual([m.etiqueta for m in motores], ["google:g1"])

    def test_informa_las_claves_que_faltan(self):
        with entorno({"NVIDIA_API_KEY": "clave-falsa"}):
            faltan = claves_faltantes("google:g1,nvidia:n1,opencode:o1")
        self.assertEqual(faltan, ["GOOGLE_API_KEY", "OPENCODE_API_KEY"])

    def test_sin_ninguna_clave_no_hay_motores(self):
        with entorno({}):
            self.assertEqual(construir_motores(CADENA_DEFECTO), [])

    def test_con_las_tres_claves_la_cadena_esta_completa(self):
        with entorno({c: "clave-falsa" for c in CLAVES}):
            motores = construir_motores()
        self.assertEqual(len(motores), 6)
        self.assertEqual(motores[0].servicio, "google")
        self.assertEqual(motores[-1].servicio, "opencode")


class TestFormatoDePeticion(unittest.TestCase):
    def test_google_usa_su_formato_y_no_envia_temperature(self):
        motor = MotorIA(servicio="google", modelo="gemini-3.8-flash", api_key="k")
        cuerpo = json.loads(motor._cuerpo("SISTEMA", "USUARIO", 1234).decode("utf-8"))
        self.assertNotIn("temperature", cuerpo)
        self.assertEqual(cuerpo["systemInstruction"]["parts"][0]["text"], "SISTEMA")
        self.assertEqual(cuerpo["contents"][0]["parts"][0]["text"], "USUARIO")
        self.assertEqual(cuerpo["generationConfig"]["maxOutputTokens"], 1234)
        self.assertEqual(cuerpo["generationConfig"]["responseMimeType"],
                         "application/json")
        self.assertIn("models/gemini-3.8-flash:generateContent", motor.url)
        self.assertEqual(motor._cabeceras()["x-goog-api-key"], "k")

    def test_nvidia_y_opencode_usan_el_formato_openai(self):
        for servicio in ("nvidia", "opencode"):
            motor = MotorIA(servicio=servicio, modelo="modelo/x", api_key="k")
            cuerpo = json.loads(motor._cuerpo("SISTEMA", "USUARIO", 999).decode("utf-8"))
            self.assertEqual(cuerpo["model"], "modelo/x")
            self.assertEqual(cuerpo["messages"][0]["content"], "SISTEMA")
            self.assertEqual(cuerpo["messages"][1]["content"], "USUARIO")
            self.assertNotIn("temperature", cuerpo)
            self.assertTrue(cuerpo["max_tokens"])
            self.assertTrue(motor._cabeceras()["Authorization"].startswith("Bearer "))

    def test_nvidia_usa_un_limite_de_ritmo_mas_bajo(self):
        nvidia = MotorIA(servicio="nvidia", modelo="m", api_key="k")
        google = MotorIA(servicio="google", modelo="m", api_key="k")
        self.assertLess(nvidia.max_rpm, google.max_rpm)

    def test_servicio_no_soportado(self):
        with self.assertRaises(ValueError):
            MotorIA(servicio="inventado", modelo="m", api_key="k")

    def test_la_url_de_opencode_se_puede_cambiar_por_entorno(self):
        self.assertEqual(SERVICIOS["opencode"]["url"],
                         os.environ.get(
                             "IA_CUALITATIVO_OPENCODE_URL",
                             "https://opencode.ai/zen/go/v1/chat/completions"))


class TestExtraccionDeJSON(unittest.TestCase):
    def setUp(self):
        self.motor = MotorIA(servicio="nvidia", modelo="m", api_key="k")

    def test_json_limpio(self):
        self.assertEqual(self.motor._json_de_texto('{"a": 1}', "", "raw"), {"a": 1})

    def test_json_rodeado_de_texto(self):
        self.assertEqual(
            self.motor._json_de_texto('Claro: {"a": 2} listo.', "", "raw"), {"a": 2}
        )

    def test_json_en_el_razonamiento_cuando_el_contenido_viene_vacio(self):
        self.assertEqual(
            self.motor._json_de_texto("", 'pienso {"a": 3}', "raw"), {"a": 3}
        )

    def test_contenido_vacio_sin_razonamiento_falla(self):
        with self.assertRaises(json.JSONDecodeError):
            self.motor._json_de_texto("", "", "raw")


if __name__ == "__main__":
    unittest.main()
