"""
Tests — lib/config.py (Fase 9)

Valida que las constantes críticas existen y tienen rangos válidos.
NO valida lógica de negocio (solo estructura de configuración).
"""
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib import config


class TestConfigConstants(unittest.TestCase):
    """Verifica que todas las constantes críticas del ETL estén definidas."""

    def test_column_rename_pregrado_existe(self):
        self.assertTrue(hasattr(config, 'COLUMN_RENAME_PREGRADO'))
        self.assertIsInstance(config.COLUMN_RENAME_PREGRADO, dict)
        self.assertGreater(len(config.COLUMN_RENAME_PREGRADO), 0)

    def test_column_rename_graduado_existe(self):
        self.assertTrue(hasattr(config, 'COLUMN_RENAME_GRADUADO'))
        self.assertIsInstance(config.COLUMN_RENAME_GRADUADO, dict)
        self.assertGreater(len(config.COLUMN_RENAME_GRADUADO), 0)

    def test_carrera_facultad_existe(self):
        self.assertTrue(hasattr(config, 'CARRERA_FACULTAD'))
        self.assertIsInstance(config.CARRERA_FACULTAD, dict)
        self.assertGreater(len(config.CARRERA_FACULTAD), 0)

    def test_categoria_dimension_pregrado_existe(self):
        self.assertTrue(hasattr(config, 'CATEGORIA_DIMENSION_PREGRADO'))
        self.assertIsInstance(config.CATEGORIA_DIMENSION_PREGRADO, dict)
        self.assertGreater(len(config.CATEGORIA_DIMENSION_PREGRADO), 10)

    def test_categoria_dimension_graduado_existe(self):
        self.assertTrue(hasattr(config, 'CATEGORIA_DIMENSION_GRADUADO'))
        self.assertIsInstance(config.CATEGORIA_DIMENSION_GRADUADO, dict)
        # Graduado debe tener al menos tantas dimensiones como pregrado
        self.assertGreaterEqual(
            len(config.CATEGORIA_DIMENSION_GRADUADO),
            len(config.CATEGORIA_DIMENSION_PREGRADO)
        )

    def test_respuestas_texto_existe(self):
        self.assertTrue(hasattr(config, 'RESPUESTAS_TEXTO'))
        self.assertIsInstance(config.RESPUESTAS_TEXTO, list)
        # Debe tener 5 niveles SAT + 2 visibility = 7
        self.assertEqual(len(config.RESPUESTAS_TEXTO), 7)

    def test_respuestas_texto_contiene_niveles_sat(self):
        sat_keys = config.RESPUESTAS_TEXTO[:5]
        self.assertIn('Totalmente satisfecho', sat_keys)
        self.assertIn('Muy satisfecho', sat_keys)
        self.assertIn('Satisfecho', sat_keys)
        self.assertIn('Insatisfecho', sat_keys)
        self.assertIn('Totalmente insatisfecho', sat_keys)

    def test_respuestas_texto_contiene_visibility(self):
        visibility = config.RESPUESTAS_TEXTO[5:7]
        self.assertIn('No utilizo', visibility)
        self.assertIn('No conozco', visibility)

    def test_etapa_map_existe(self):
        self.assertTrue(hasattr(config, 'ETAPA_MAP'))
        self.assertIsInstance(config.ETAPA_MAP, dict)
        # Debe cubrir ciclos 1-12
        for ciclo in range(1, 13):
            self.assertIn(ciclo, config.ETAPA_MAP, f"Ciclo {ciclo} no está en ETAPA_MAP")

    def test_etapa_map_valores_validos(self):
        etapas_validas = {'Inicial', 'Intermedio', 'Avanzado'}
        for ciclo, etapa in config.ETAPA_MAP.items():
            self.assertIn(etapa, etapas_validas, f"Ciclo {ciclo} tiene etapa inválida: {etapa}")

    def test_empleabilidad_categorias_existe(self):
        self.assertTrue(hasattr(config, 'EMPLEABILIDAD_CATEGORIAS'))
        self.assertIsInstance(config.EMPLEABILIDAD_CATEGORIAS, list)
        self.assertGreater(len(config.EMPLEABILIDAD_CATEGORIAS), 0)

    def test_categorias_padre_pregrado_validas(self):
        """Pregrado debe tener 4 categorías padre oficiales."""
        cats = set(config.CATEGORIA_DIMENSION_PREGRADO.values())
        expected = {'Académico', 'Administrativo y Bienestar', 'Infraestructura', 'Tecnología'}
        self.assertTrue(expected.issubset(cats), f"Faltan categorías: {expected - cats}")

    def test_categorias_padre_graduado_incluye_docencia(self):
        """Graduado debe incluir Docencia y Desarrollo Profesional adicionales."""
        cats_grad = set(config.CATEGORIA_DIMENSION_GRADUADO.values())
        self.assertIn('Docencia', cats_grad, "Docencia debe existir en graduado")
        self.assertIn('Desarrollo Profesional', cats_grad, "Desarrollo Profesional debe existir en graduado")

    def test_no_categoria_valoracion_general(self):
        """'Valoración General' es legacy y NO debe aparecer en la taxonomía oficial."""
        cats_pre = set(config.CATEGORIA_DIMENSION_PREGRADO.values())
        cats_grad = set(config.CATEGORIA_DIMENSION_GRADUADO.values())
        self.assertNotIn('Valoración General', cats_pre, "Valoración General (legacy) en pregrado")
        self.assertNotIn('Valoración General', cats_grad, "Valoración General (legacy) en graduado")

    def test_la_columna_de_ciclo_se_renombra_a_ciclo(self):
        """El ETL busca la columna de ciclo por su nombre interno tras renombrar.

        Si el renombrado deja de apuntar a "Ciclo", build_json.py da la columna por
        ausente y sobrescribe el ciclo real con "NA".
        """
        pregunta = config._NIVEL_CICLO["undergraduate"]
        self.assertEqual(config.COLUMN_RENAME_PREGRADO.get(pregunta), "Ciclo")


if __name__ == '__main__':
    unittest.main()
