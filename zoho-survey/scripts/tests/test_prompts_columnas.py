"""Tests — los nombres de dimensión del prompt salen de la declaración.

El bloque "Mapeo de frases comunes a dimensiones" del system prompt referencia
dimensiones que son preguntas del formulario. Se piden por su id declarado: si
una pregunta se renombra, el prompt muestra el nombre nuevo. Las dimensiones
catch-all (sin pregunta) siguen viajando como texto.
"""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import config
from lib.prompts_cualitativo import _mapeo_frases_dimensiones


class TestMapeoDeFrases(unittest.TestCase):

    def test_usa_los_nombres_publicados_de_la_declaracion(self):
        bloque = _mapeo_frases_dimensiones()
        self.assertIn("**%s**" % config.nombre_publicado("aulas_de_clase"), bloque)
        self.assertIn("**%s**" % config.nombre_publicado("csat_sujeto"), bloque)
        self.assertIn("**%s**" % config.nombre_publicado("disponibilidad_para_asesorias"), bloque)

    def test_sigue_el_rename_de_la_declaracion(self):
        original = config.PREGUNTAS_POR_NIVEL["undergraduate"]
        config.PREGUNTAS_POR_NIVEL["undergraduate"] = [
            {**d, "nombre": "Aulas renombradas"} if d["id"] == "aulas_de_clase" else d
            for d in original
        ]
        try:
            bloque = _mapeo_frases_dimensiones()
            self.assertIn("**Aulas renombradas**", bloque)
            self.assertNotIn("**Aulas de clase**", bloque)
        finally:
            config.PREGUNTAS_POR_NIVEL["undergraduate"] = original

    def test_las_dimensiones_sin_pregunta_quedan_como_texto(self):
        bloque = _mapeo_frases_dimensiones()
        self.assertIn("**Espacios comunes**", bloque)
        self.assertIn("**Espacios de alimentación**", bloque)
        self.assertIn("**Ubicación**", bloque)

    def test_conserva_las_frases_coloquiales(self):
        bloque = _mapeo_frases_dimensiones()
        self.assertIn('"Aulas" / "salones" / "carpetas" / "aire acondicionado"', bloque)
        self.assertIn("usa estas como guía", bloque)


if __name__ == "__main__":
    unittest.main()
