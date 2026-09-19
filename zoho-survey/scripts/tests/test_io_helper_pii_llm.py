"""Tests de ofuscación PII pre-LLM (Fase 3.5).

Verifica que ofuscar_pii_para_llm() protege PII antes de enviar
comentarios a un motor IA, y que la respuesta del LLM no reintroduce PII
en los JSON públicos.

No depende de ninguna clave de motor ni de la red.
"""

import os
import sys
import unittest

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.io_helper import ofuscar_pii_para_llm


class TestOfuscarPiiParaLlm(unittest.TestCase):
    """Tests de ofuscación PII antes de llamar a un motor IA."""

    def test_email_no_llega_a_llm(self):
        """El correo RAW no debe aparecer en el texto para el LLM."""
        comentario = "Mi correo es ejemplo@gmail.com"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("ejemplo@gmail.com", ofuscado)
        self.assertIn("[EMAIL_1]", ofuscado)
        self.assertEqual(mapping["[EMAIL_1]"], "ejemplo@gmail.com")

    def test_telefono_no_llega_a_llm(self):
        """El teléfono RAW no debe aparecer en el texto para el LLM."""
        comentario = "Llamarme al 987654321"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("987654321", ofuscado)
        self.assertIn("[TELEFONO_1]", ofuscado)
        self.assertEqual(mapping["[TELEFONO_1]"], "987654321")

    def test_codigo_no_llega_a_llm(self):
        """El código de estudiante RAW no debe aparecer en el texto para el LLM."""
        comentario = "Soy el alumno 20201234"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("20201234", ofuscado)
        self.assertIn("[CODIGO_1]", ofuscado)
        self.assertEqual(mapping["[CODIGO_1]"], "20201234")

    def test_multiples_pii(self):
        """Varios tipos de PII deben ofuscarse todos."""
        comentario = (
            "Juan Pérez, mi correo es juan@gmail.com y mi celular 987654321. "
            "Soy el alumno 20201234."
        )
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("juan@gmail.com", ofuscado)
        self.assertNotIn("987654321", ofuscado)
        self.assertNotIn("20201234", ofuscado)
        self.assertIn("[EMAIL_1]", ofuscado)
        self.assertIn("[TELEFONO_1]", ofuscado)
        self.assertIn("[CODIGO_1]", ofuscado)
        self.assertEqual(len(mapping), 3)

    def test_texto_sin_pii_se_mantiene(self):
        """Texto legítimo sin PII no debe alterarse semánticamente."""
        comentario = "La universidad tiene buena infraestructura y buenos profesores."
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertEqual(ofuscado, comentario)
        self.assertEqual(mapping, {})

    def test_pii_repetida(self):
        """Misma PII repetida debe generar placeholders numerados distintos."""
        comentario = "Escribeme a test@ulima.edu.pe o a test@ulima.edu.pe otra vez"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("test@ulima.edu.pe", ofuscado)
        self.assertIn("[EMAIL_1]", ofuscado)
        self.assertIn("[EMAIL_2]", ofuscado)
        self.assertEqual(mapping["[EMAIL_1]"], "test@ulima.edu.pe")
        self.assertEqual(mapping["[EMAIL_2]"], "test@ulima.edu.pe")

    def test_colision_placeholder(self):
        """Texto legítimo con formato similar a placeholder no debe sustituirse."""
        # El estudiante escribe literalmente "[EMAIL_1]" como parte de su opinión
        comentario = "El formato [EMAIL_1] no funciona en el portal"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        # No debe haber colisión: el texto literal se mantiene
        self.assertIn("[EMAIL_1]", ofuscado)
        # Pero el mapping no debe contener una entrada falsa para ese placeholder
        self.assertNotIn("[EMAIL_1]", mapping)

    def test_respuesta_ia_placeholder_no_restaura(self):
        """Si el motor devuelve un placeholder, no se debe restaurar PII."""
        comentario_original = "Mi correo es privado@ulima.edu.pe"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario_original)
        # Simular respuesta del motor que contiene el placeholder
        respuesta_ia = {
            "unidades": [
                {
                    "orden": 1,
                    "texto": "Menciona su correo [EMAIL_1]",
                    "es_valido": True,
                    "motivo_invalidez": None,
                    "sentimiento": "Neutro",
                    "intensidad": 1,
                    "justificacion_sentimiento": "Referencia a contacto",
                    "dimension": "Pendiente de Clasificación",
                    "categoria_padre": "Pendiente de Clasificación",
                    "es_mencion_mejora": False,
                    "es_salvavidas": False,
                    "dimension_evaluada_rating": None,
                    "dimension_evaluada_score": None,
                    "sub_aspectos": [],
                }
            ]
        }
        # PRINCIPIO DE SEGURIDAD: no restaurar PII en la salida pública
        # El placeholder permanece en la respuesta (no se reintroduce PII)
        texto_salida = respuesta_ia["unidades"][0]["texto"]
        self.assertIn("[EMAIL_1]", texto_salida)
        self.assertNotIn("privado@ulima.edu.pe", texto_salida)

    def test_semantic_preservada(self):
        """La ofuscación debe preservar la estructura semántica del comentario."""
        comentario = "Mi correo es a@b.com y mi celular 999888777"
        ofuscado, _ = ofuscar_pii_para_llm(comentario)
        # El LLM debe entender que hay un correo y un teléfono
        self.assertIn("Mi correo es", ofuscado)
        self.assertIn("y mi celular", ofuscado)
        self.assertIn("[EMAIL_1]", ofuscado)
        self.assertIn("[TELEFONO_1]", ofuscado)

    def test_input_vacio(self):
        """Input vacío o no-string debe retornar ('', {})."""
        self.assertEqual(ofuscar_pii_para_llm(""), ("", {}))
        self.assertEqual(ofuscar_pii_para_llm("   "), ("", {}))
        self.assertEqual(ofuscar_pii_para_llm(None), ("", {}))
        self.assertEqual(ofuscar_pii_para_llm(123), ("", {}))

    def test_telefono_con_prefijo(self):
        """Teléfono con prefijo +51 debe ofuscarse."""
        comentario = "Contacto: +51 987 654 321"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("987654321", ofuscado)
        self.assertNotIn("+51", ofuscado)
        self.assertIn("[TELEFONO_1]", ofuscado)

    def test_telefono_con_guiones(self):
        """Teléfono con guiones debe ofuscarse."""
        comentario = "Llamar al 987-654-321"
        ofuscado, mapping = ofuscar_pii_para_llm(comentario)
        self.assertNotIn("987-654-321", ofuscado)
        self.assertIn("[TELEFONO_1]", ofuscado)


if __name__ == "__main__":
    unittest.main()
