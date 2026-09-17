"""
TESTS — Validación de respuestas IA (lib/ia_validacion.py)

Tests unitarios para la validación y corrección de respuestas de DeepSeek.
Cubre: validar_unidad, corregir_unidad, validar_respuesta_ia, redacción PII.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.ia_validacion import validar_unidad, corregir_unidad, validar_respuesta_ia


# Taxonomía de prueba
TAXONOMIA_TEST = {
    "Calidad de la enseñanza": "Académico",
    "Aulas de clase": "Infraestructura",
    "Wi-Fi": "Tecnología",
    "Plan curricular y perfil de egreso": "Académico",
    "Satisfacción estudiantil": "Académico",
    "Atención del personal administrativo": "Administrativo y Bienestar",
    "none": "none",
}


class TestValidarUnidad(unittest.TestCase):
    """Tests de validar_unidad."""

    def test_unidad_valida_retorna_none(self):
        """Unidad válida retorna None (sin error)."""
        unidad = {
            "orden": 1,
            "texto": "buen profesor",
            "sentimiento": "positivo",
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
        }
        err = validar_unidad(unidad, TAXONOMIA_TEST)
        self.assertIsNone(err)

    def test_unidad_no_dict_retorna_error(self):
        """Unidad que no es dict retorna error."""
        err = validar_unidad("no es dict", TAXONOMIA_TEST)
        self.assertIsNotNone(err)

    def test_campo_faltante_retorna_error(self):
        """Campo requerido faltante retorna error."""
        unidad = {
            "orden": 1,
            "texto": "buen profesor",
            # falta sentimiento
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
        }
        err = validar_unidad(unidad, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("sentimiento", err)

    def test_sentimiento_invalido_retorna_error(self):
        """Sentimiento fuera del set válido retorna error."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "muy_positivo",  # inválido
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
        }
        err = validar_unidad(unidad, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("Sentimiento", err)

    def test_intensidad_fuera_rango_retorna_error(self):
        """Intensidad fuera de 1-5 retorna error."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": 10,  # fuera de rango
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
        }
        err = validar_unidad(unidad, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("Intensidad", err)

    def test_corrije_categoria_padre_incoherente(self):
        """Categoría padre incoherente con dimensión se corrige automáticamente."""
        unidad = {
            "orden": 1,
            "texto": "buen profesor",
            "sentimiento": "positivo",
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Infraestructura",  # incoherente
        }
        err = validar_unidad(unidad, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertEqual(unidad["categoria_padre"], "Académico")  # corregido


class TestCorregirUnidad(unittest.TestCase):
    """Tests de corregir_unidad."""

    def test_intensidad_fuera_rango_no_se_corrige(self):
        """Intensidad fuera de rango se conserva para que falle validación."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": 10,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
            "es_valido": True,
        }
        corregir_unidad(unidad)
        self.assertEqual(unidad["intensidad"], 10)

    def test_intensidad_negativa_no_se_corrige(self):
        """Intensidad negativa se conserva para que falle validación."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": -3,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
            "es_valido": True,
        }
        corregir_unidad(unidad)
        self.assertEqual(unidad["intensidad"], -3)

    def test_intensidad_numerica_en_texto_se_normaliza(self):
        """Intensidad numérica como texto se acepta sin corregir rangos."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": "4",
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
            "es_valido": True,
        }
        corregir_unidad(unidad)
        self.assertEqual(unidad["intensidad"], 4)

    def test_es_valido_sincroniza_motivo(self):
        """Si es_valido=True, motivo_invalidez se setea a None."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
            "es_valido": True,
            "motivo_invalidez": "algun motivo",  # debería ser None
        }
        corregir_unidad(unidad)
        self.assertIsNone(unidad["motivo_invalidez"])

    def test_sub_aspectos_limitados_a_5(self):
        """sub_aspectos se limita a máximo 5 elementos."""
        unidad = {
            "orden": 1,
            "texto": "test",
            "sentimiento": "positivo",
            "intensidad": 4,
            "dimension": "Calidad de la enseñanza",
            "categoria_padre": "Académico",
            "es_valido": True,
            "sub_aspectos": ["a", "b", "c", "d", "e", "f", "g", "h"],  # 8 elementos
        }
        corregir_unidad(unidad)
        self.assertEqual(len(unidad["sub_aspectos"]), 5)


class TestValidarRespuestaIA(unittest.TestCase):
    """Tests de validar_respuesta_ia."""

    def test_respuesta_valida_retorna_saneada(self):
        """Respuesta válida retorna dict saneado con unidades."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "buen profesor",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertIsNotNone(saneada)
        self.assertEqual(len(saneada["unidades"]), 1)

    def test_sentimiento_capitalizado_se_normaliza(self):
        """DeepSeek suele devolver Positivo/Negativo/Neutro con mayúscula inicial."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "buen profesor",
                    "sentimiento": "Positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 2,
                    "texto": "wifi lento",
                    "sentimiento": "Negativo",
                    "intensidad": 3,
                    "dimension": "Wi-Fi",
                    "categoria_padre": "Tecnología",
                    "es_valido": True,
                },
                {
                    "orden": 3,
                    "texto": "comentario descriptivo",
                    "sentimiento": "Neutro",
                    "intensidad": 1,
                    "dimension": "Satisfacción estudiantil",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertEqual(
            [u["sentimiento"] for u in saneada["unidades"]],
            ["positivo", "negativo", "neutro"],
        )

    def test_pendiente_sin_tilde_se_canonicaliza(self):
        """Variantes seguras de Pendiente de Clasificación se canonicalizan."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "sin clasificación confiable",
                    "sentimiento": "Neutro",
                    "intensidad": 1,
                    "dimension": "Pendiente de Clasificacion",
                    "categoria_padre": "Pendiente de Clasificacion",
                    "es_valido": False,
                    "motivo_invalidez": "Motivo no especificado",
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        unidad = saneada["unidades"][0]
        self.assertEqual(unidad["dimension"], "Pendiente de Clasificación")
        self.assertEqual(unidad["categoria_padre"], "Pendiente de Clasificación")
        self.assertEqual(unidad["sentimiento"], "neutro")

    def test_respuesta_no_dict_retorna_error(self):
        """Respuesta que no es dict retorna error."""
        saneada, err = validar_respuesta_ia("no dict", TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIsNone(saneada)

    def test_respuesta_sin_unidades_retorna_error(self):
        """Respuesta sin 'unidades' retorna error."""
        saneada, err = validar_respuesta_ia({"sin_unidades": True}, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIsNone(saneada)

    def test_todas_invalidas_retorna_error(self):
        """Si todas las unidades son inválidas, retorna error."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "test",
                    "sentimiento": "muy_positivo",  # inválido real
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("Sentimiento inválido", err)
        self.assertIn("1 unidad descartada", err)
        self.assertIsNone(saneada)

    def test_unidades_mixtas_conserva_validas_descarta_invalidas(self):
        """Una respuesta mixta no debe caer completa si hay unidades válidas."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "buen profesor",
                    "sentimiento": "Positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 2,
                    "texto": "campo con sentimiento inválido",
                    "sentimiento": "muy_positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertEqual(len(saneada["unidades"]), 1)
        self.assertEqual(saneada["unidades"][0]["sentimiento"], "positivo")
        self.assertEqual(saneada["unidades"][0]["orden"], 1)

    def test_intensidad_fuera_rango_en_respuesta_falla(self):
        """Las intensidades fuera de rango no se corrigen silenciosamente."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "test",
                    "sentimiento": "Positivo",
                    "intensidad": 10,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("Intensidad fuera de rango", err)
        self.assertIsNone(saneada)

    def test_dimension_desconocida_en_respuesta_falla(self):
        """No se aceptan dimensiones inventadas por la IA."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "test",
                    "sentimiento": "Positivo",
                    "intensidad": 3,
                    "dimension": "Tema inventado",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNotNone(err)
        self.assertIn("Dimensión desconocida", err)
        self.assertIsNone(saneada)

    def test_unidades_representativas_deepseek_capitalizadas(self):
        """Casos reales analizables no deben fallar por capitalización del sentimiento."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "Falta mas nivel tecnico en especialidades",
                    "sentimiento": "Negativo",
                    "intensidad": 3,
                    "dimension": "Plan curricular y perfil de egreso",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 2,
                    "texto": "La malla curricular de la carrera es muy variada",
                    "sentimiento": "Positivo",
                    "intensidad": 4,
                    "dimension": "Plan curricular y perfil de egreso",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 3,
                    "texto": "Disposición de los profesores de enseñar",
                    "sentimiento": "Positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 4,
                    "texto": "infraestructura de la universidad",
                    "sentimiento": "Positivo",
                    "intensidad": 3,
                    "dimension": "Aulas de clase",
                    "categoria_padre": "Infraestructura",
                    "es_valido": True,
                },
                {
                    "orden": 5,
                    "texto": "apoyo por parte de los administradores",
                    "sentimiento": "Positivo",
                    "intensidad": 3,
                    "dimension": "Atención del personal administrativo",
                    "categoria_padre": "Administrativo y Bienestar",
                    "es_valido": True,
                },
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertEqual(len(saneada["unidades"]), 5)
        self.assertEqual(saneada["unidades"][0]["sentimiento"], "negativo")

    def test_unidades_renumeradas_secuencialmente(self):
        """Unidades válidas se re-numeran secuencialmente desde 1."""
        respuesta = {
            "unidades": [
                {
                    "orden": 5,  # orden original arbitrario
                    "texto": "buen profesor",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                },
                {
                    "orden": 10,
                    "texto": "buenas aulas",
                    "sentimiento": "positivo",
                    "intensidad": 3,
                    "dimension": "Aulas de clase",
                    "categoria_padre": "Infraestructura",
                    "es_valido": True,
                },
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        self.assertEqual(saneada["unidades"][0]["orden"], 1)
        self.assertEqual(saneada["unidades"][1]["orden"], 2)


class TestRedaccionPII(unittest.TestCase):
    """Tests de redacción PII en validar_respuesta_ia (SEG-01)."""

    def test_email_en_texto_se_redacta(self):
        """Email en texto de unidad se redacta tras validación."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "mi email es test@test.com",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        texto = saneada["unidades"][0]["texto"]
        self.assertNotIn("test@test.com", texto)
        self.assertIn("ENMASCARADO", texto)

    def test_telefono_en_texto_se_redacta(self):
        """Teléfono peruano en texto se redacta."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "llamame al 999999999",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        texto = saneada["unidades"][0]["texto"]
        self.assertNotIn("999999999", texto)
        self.assertIn("ENMASCARADO", texto)

    def test_codigo_estudiante_se_redacta(self):
        """Código de estudiante (20XXXXXX) en texto se redacta."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "mi codigo es 20201234",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        texto = saneada["unidades"][0]["texto"]
        self.assertNotIn("20201234", texto)
        self.assertIn("ENMASCARADO", texto)

    def test_justificacion_sentimiento_se_redacta(self):
        """PII en justificacion_sentimiento se redacta."""
        respuesta = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "comentario normal",
                    "sentimiento": "positivo",
                    "intensidad": 4,
                    "dimension": "Calidad de la enseñanza",
                    "categoria_padre": "Académico",
                    "es_valido": True,
                    "justificacion_sentimiento": "el estudiante dejo su email test@test.com",
                }
            ]
        }
        saneada, err = validar_respuesta_ia(respuesta, TAXONOMIA_TEST)
        self.assertIsNone(err)
        justificacion = saneada["unidades"][0]["justificacion_sentimiento"]
        self.assertNotIn("test@test.com", justificacion)


if __name__ == "__main__":
    unittest.main()
