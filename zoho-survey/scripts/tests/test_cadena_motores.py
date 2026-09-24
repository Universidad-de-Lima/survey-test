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
    OPENCODE_AGENTE,
    _primer_objeto_json,
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
        # deepseek-v4.1-flash (OpenCode) es el motor mas actual: va PRIMERO y el
        # resto queda como respaldo. El orden es configurable con la variable
        # IA_CUALITATIVO_CADENA, pero el valor por defecto fija este contrato.
        self.assertEqual(
            parsear_cadena(CADENA_DEFECTO)[0],
            ("opencode", "deepseek-v4.1-flash"),
        )
        servicios = [servicio for servicio, _ in parsear_cadena(CADENA_DEFECTO)]
        self.assertEqual(servicios, ["opencode"] + ["nvidia"] * 7)
        modelos_nvidia = [m for s, m in parsear_cadena(CADENA_DEFECTO) if s == "nvidia"]
        # Todos verificados como activos contra /v1/models de NVIDIA.
        self.assertEqual(modelos_nvidia, [
            "moonshotai/kimi-k3",
            "meta/muse-glimmer-30b",
            "z-ai/glm-5.3",
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "deepseek-ai/deepseek-v4.1-flash",
            "z-ai/glm-5.3-flash",
            "poolside/laguna-xs-2.1",
        ])

    def test_la_cadena_por_defecto_no_lleva_motores_descartados(self):
        # Google salio por sus 503 constantes y el modelo de NVIDIA quedo
        # retirado el 2026-09-14 (410 Gone); ninguno debe volver por descuido.
        cadena = CADENA_DEFECTO
        self.assertNotIn("google", cadena)
        self.assertNotIn("deepseek-v4-pro-0813", cadena)


class TestExtraccionJson(unittest.TestCase):
    """El JSON puede venir con prosa alrededor o escondido en el razonamiento."""

    def test_toma_el_primer_objeto_balanceado_con_prosa_alrededor(self):
        texto = 'Claro, aqui esta: {"sentimiento": "positivo", "detalle": {"a": 1}} y listo.'
        self.assertEqual(
            _primer_objeto_json(texto),
            {"sentimiento": "positivo", "detalle": {"a": 1}},
        )

    def test_no_confunde_las_llaves_dentro_de_una_cadena(self):
        texto = '{"nota": "dijo {hola}", "n": 1}'
        self.assertEqual(_primer_objeto_json(texto), {"nota": "dijo {hola}", "n": 1})

    def test_devuelve_none_si_el_json_quedo_a_medias(self):
        self.assertIsNone(_primer_objeto_json('{"sentimiento": "posi'))

    def test_lee_el_json_del_razonamiento_cuando_el_contenido_viene_vacio(self):
        # Caso real: el modelo agota el presupuesto pensando y deja el JSON en
        # reasoning_content en vez de en content.
        motor = MotorIA(servicio="opencode", modelo="m", api_key="k")
        razonamiento = 'Let me analyze the comment.\n\n{"sentimiento": "positivo"}\n\nListo.'
        self.assertEqual(
            motor._json_de_texto("", razonamiento, "raw"),
            {"sentimiento": "positivo"},
        )


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
        # Ocho motores: OpenCode y los siete modelos vigentes de NVIDIA. Google
        # ya no esta en la cadena por defecto aunque su clave este configurada.
        self.assertEqual(len(motores), 8)
        # deepseek-v4.1-flash (OpenCode) primero; NVIDIA como respaldo.
        self.assertEqual(motores[0].servicio, "opencode")
        self.assertEqual([m.servicio for m in motores[1:]], ["nvidia"] * 7)


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

    def test_google_usa_un_limite_de_ritmo_bajo(self):
        """El plan gratuito de Google tolera ~15 pedidos por minuto: el motor
        se limita a 10 para no recibir rechazos por ritmo (429)."""
        google = MotorIA(servicio="google", modelo="m", api_key="k")
        opencode = MotorIA(servicio="opencode", modelo="m", api_key="k")
        self.assertEqual(google.max_rpm, 10)
        self.assertLess(google.max_rpm, opencode.max_rpm)

    def test_servicio_no_soportado(self):
        with self.assertRaises(ValueError):
            MotorIA(servicio="inventado", modelo="m", api_key="k")

    def test_la_url_de_opencode_se_puede_cambiar_por_entorno(self):
        self.assertEqual(SERVICIOS["opencode"]["url"],
                         os.environ.get(
                             "IA_CUALITATIVO_OPENCODE_URL",
                             "https://opencode.ai/zen/go/v1/chat/completions"))


class TestIdentificacionOpenCode(unittest.TestCase):
    """OpenCode Go bloquea (403, Cloudflare 1010) a los clientes que no se
    identifican: urllib envía "Python-urllib/3.x" si no se declara agente."""

    def test_opencode_declara_agente_propio_y_sesion(self):
        motor = MotorIA(servicio="opencode", modelo="deepseek-v4.1-flash",
                        api_key="k")
        cabeceras = motor._cabeceras()
        self.assertEqual(cabeceras["User-Agent"], OPENCODE_AGENTE)
        self.assertFalse(
            cabeceras["User-Agent"].lower().startswith("python-urllib"))
        self.assertTrue(cabeceras["x-opencode-session"])

    def test_la_sesion_es_estable_dentro_de_la_corrida(self):
        a = MotorIA(servicio="opencode", modelo="m1", api_key="k")._cabeceras()
        b = MotorIA(servicio="opencode", modelo="m2", api_key="k")._cabeceras()
        self.assertEqual(a["x-opencode-session"], b["x-opencode-session"])

    def test_google_y_nvidia_no_llevan_las_cabeceras_de_opencode(self):
        for servicio in ("google", "nvidia"):
            cabeceras = MotorIA(servicio=servicio, modelo="m",
                                api_key="k")._cabeceras()
            self.assertNotIn("User-Agent", cabeceras)
            self.assertNotIn("x-opencode-session", cabeceras)


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
