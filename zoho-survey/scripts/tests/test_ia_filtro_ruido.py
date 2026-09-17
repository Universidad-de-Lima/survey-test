"""
TESTS — Filtro de Ruido IA (lib/ia_filtro_ruido.py)

Tests unitarios para el pre-filtro de comentarios ruidosos.
Cubre: los 15 criterios regex, frases cortas válidas, generación de placeholders.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.ia_filtro_ruido import (
    es_ruido_pre_filtro,
    generar_unidad_ruido,
    SENTIMIENTOS_VALIDOS,
    MOTIVOS_INVALIDEZ_VALIDOS,
)


class TestRuidoDeteccion(unittest.TestCase):
    """Tests de detección de comentarios ruidosos."""

    def test_comentario_vacio_es_ruido(self):
        """Comentario vacío es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("")
        self.assertTrue(es_ruido)

    def test_comentario_solo_espacios_es_ruido(self):
        """Comentario con solo espacios es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("   ")
        self.assertTrue(es_ruido)

    def test_comentario_solo_puntuacion_es_ruido(self):
        """Comentario con solo puntuación es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("...")
        self.assertTrue(es_ruido)

    def test_comentario_solo_numero_es_ruido(self):
        """Comentario con solo números es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("12345")
        self.assertTrue(es_ruido)

    def test_letra_repetida_es_ruido(self):
        """Letra repetida es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("aaaaaaa")
        self.assertTrue(es_ruido)

    def test_ruido_teclado_es_ruido(self):
        """Patrones de teclazos son ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("asdfghjkl")
        self.assertTrue(es_ruido)

    def test_repite_calificacion_es_ruido(self):
        """'mi nota 10' (sin verbo) es ruido segun regex actual."""
        # Nota: el regex _RE_REPITE_CALIFICACION requiere 'mi nota 10' (sin 'es').
        # Variaciones con 'es' no matchean (comportamiento del regex legacy).
        es_ruido, motivo = es_ruido_pre_filtro("mi nota 10")
        self.assertTrue(es_ruido)

    def test_palabra_repetida_es_ruido(self):
        """Palabra repetida 5+ veces es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("hola hola hola hola hola")
        self.assertTrue(es_ruido)

    def test_char_repetido_interno_es_ruido(self):
        """Carácter repetido 5+ veces internamente es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro("holaaaaaaa mundo")
        self.assertTrue(es_ruido)

    def test_ruido_sin_contexto_es_ruido(self):
        """Frases sin contexto ('nada', 'ok', 'no se') son ruido."""
        for frase in ["nada", "ok", "no se", "sin comentarios", "ninguno"]:
            es_ruido, motivo = es_ruido_pre_filtro(frase)
            self.assertTrue(es_ruido, f"'{frase}' deberia ser ruido")


class TestFrasesValidas(unittest.TestCase):
    """Tests de frases cortas que NO son ruido."""

    def test_frase_corta_valida_no_es_ruido(self):
        """Frases cortas válidas ('bien', 'muy bien') no son ruido."""
        frases_validas = ["bien", "muy bien", "me gusta", "excelente", "bueno"]
        for frase in frases_validas:
            es_ruido, motivo = es_ruido_pre_filtro(frase)
            self.assertFalse(es_ruido, f"'{frase}' no deberia ser ruido")

    def test_comentario_normal_no_es_ruido(self):
        """Comentario con texto significativo no es ruido."""
        es_ruido, motivo = es_ruido_pre_filtro(
            "La universidad tiene buena infraestructura y profesores"
        )
        self.assertFalse(es_ruido)

    def test_comentario_largo_no_es_ruido(self):
        """Comentario largo no es ruido aunque tenga algunos caracteres repetidos."""
        es_ruido, motivo = es_ruido_pre_filtro(
            "Me gusta mucho la universidad, aunque el wifi podria mejorar"
        )
        self.assertFalse(es_ruido)


class TestGenerarUnidadRuido(unittest.TestCase):
    """Tests de generación de unidades placeholder para ruido."""

    def test_genera_unidad_con_motivo(self):
        """generar_unidad_ruido retorna dict con estructura esperada."""
        unidad = generar_unidad_ruido("Ruido explícito (pre-filtro)")
        self.assertIsInstance(unidad, dict)
        self.assertIn("orden", unidad)
        self.assertIn("texto", unidad)
        self.assertIn("es_valido", unidad)
        self.assertIn("motivo_invalidez", unidad)
        self.assertIn("sentimiento", unidad)

    def test_unidad_ruido_es_invalida(self):
        """Unidad de ruido siempre es inválida."""
        unidad = generar_unidad_ruido("Ruido explícito (pre-filtro)")
        self.assertFalse(unidad["es_valido"])

    def test_unidad_ruido_tiene_motivo(self):
        """Unidad de ruido tiene el motivo especificado."""
        motivo = "Comentario vacío o demasiado corto"
        unidad = generar_unidad_ruido(motivo)
        self.assertEqual(unidad["motivo_invalidez"], motivo)


class TestConstantes(unittest.TestCase):
    """Tests de constantes exportadas."""

    def test_sentimientos_validos(self):
        """SET de sentimientos válidos tiene los 3 valores esperados."""
        self.assertEqual(SENTIMIENTOS_VALIDOS, {"positivo", "negativo", "neutro"})

    def test_motivos_invalidez_validos_no_vacio(self):
        """SET de motivos de invalidez no es vacío."""
        self.assertGreater(len(MOTIVOS_INVALIDEZ_VALIDOS), 0)


if __name__ == "__main__":
    unittest.main()
