"""
Tests — Insights Generator (lib/insights_generator.py).

Verifica la generación de insights_ia (síntesis narrativa) a partir de datos
ya procesados por el ETL. Valida:
  - No aparece "Pendiente de Clasificación" en insights globales.
  - Genera insights globales con datos cuantitativos.
  - Genera insights por categoría para las 7 categorías oficiales.
  - Mantiene estructura JSON compatible con sentimiento.schema.json.
  - Maneja casos edge: sin comentarios, sin tópicos, categoría vacía.
"""
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.insights_generator import (
    generar_insights_ia,
    CATEGORIAS_PADRE_OFICIALES,
    PSEUDO_CATEGORIA_EXCLUIR,
)


class TestInsightsGenerator(unittest.TestCase):
    """Tests del generador de insights cualitativos."""

    def setUp(self):
        """Datos de prueba: comentarios mixtos en varias categorías."""
        self.valid_comments = [
            # Académico
            {"categoria": "Satisfacción estudiantil", "categoria_padre": "Académico", "sentimiento": "positivo", "intensidad": 4},
            {"categoria": "Satisfacción estudiantil", "categoria_padre": "Académico", "sentimiento": "positivo", "intensidad": 3},
            {"categoria": "Calidad de la enseñanza en la carrera", "categoria_padre": "Académico", "sentimiento": "negativo", "intensidad": 4},
            {"categoria": "Calidad de la enseñanza en la carrera", "categoria_padre": "Académico", "sentimiento": "positivo", "intensidad": 3},
            # Infraestructura
            {"categoria": "Aulas de clase", "categoria_padre": "Infraestructura", "sentimiento": "negativo", "intensidad": 4},
            {"categoria": "Aulas de clase", "categoria_padre": "Infraestructura", "sentimiento": "negativo", "intensidad": 5},
            {"categoria": "Ambientes y salas para estudio", "categoria_padre": "Infraestructura", "sentimiento": "positivo", "intensidad": 3},
            # Tecnología
            {"categoria": "Conexión Wi-Fi en el campus", "categoria_padre": "Tecnología", "sentimiento": "negativo", "intensidad": 4},
            # Pendiente de Clasificación (debe excluirse)
            {"categoria": "Pendiente de Clasificación", "categoria_padre": "Pendiente de Clasificación", "sentimiento": "neutro", "intensidad": 2},
            {"categoria": "Pendiente de Clasificación", "categoria_padre": "Pendiente de Clasificación", "sentimiento": "neutro", "intensidad": 2},
        ]
        self.topicos_globales = [
            {"topico": "Pendiente de Clasificación", "total_comentarios": 2, "positivos": 0, "negativos": 0, "neutros": 2},
            {"topico": "Satisfacción estudiantil", "total_comentarios": 2, "positivos": 2, "negativos": 0, "neutros": 0},
            {"topico": "Aulas de clase", "total_comentarios": 2, "positivos": 0, "negativos": 2, "neutros": 0},
        ]
        self.dist_sent = {"positivo": 4, "negativo": 3, "neutro": 3}
        self.total_analizados = 10

    def test_genera_estructura_basica(self):
        """El resultado debe tener claves 'global' y 'por_categoria_padre'."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        self.assertIn("global", result)
        self.assertIn("por_categoria_padre", result)
        self.assertIsInstance(result["global"], str)
        self.assertIsInstance(result["por_categoria_padre"], dict)

    def test_no_pendiente_en_insight_global(self):
        """El insight global NO debe contener 'Pendiente de Clasificación'."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        self.assertNotIn(
            PSEUDO_CATEGORIA_EXCLUIR,
            result["global"],
            f"Insight global contiene '{PSEUDO_CATEGORIA_EXCLUIR}': {result['global']}"
        )

    def test_no_pendiente_en_insights_por_categoria(self):
        """La clave 'Pendiente de Clasificación' no debe aparecer en por_categoria_padre."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        self.assertNotIn(
            PSEUDO_CATEGORIA_EXCLUIR,
            result["por_categoria_padre"],
            f"'{PSEUDO_CATEGORIA_EXCLUIR}' aparece como categoría en insights"
        )

    def test_insight_global_incluye_datos_cuantitativos(self):
        """El insight global debe incluir el nombre del tema top y menciones."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        # Debe mencionar el top tópico real (no Pendiente)
        self.assertIn("Satisfacción estudiantil", result["global"])
        # Debe incluir datos cuantitativos
        self.assertRegex(result["global"], r"\d+")  # al menos un número

    def test_cubre_categorias_oficiales(self):
        """Debe generar insights para las 7 categorías oficiales."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        for cat in CATEGORIAS_PADRE_OFICIALES:
            self.assertIn(cat, result["por_categoria_padre"], f"Categoría '{cat}' no presente en insights")

    def test_categoria_con_comentarios_tiene_insight_sustantivo(self):
        """Categorías con comentarios deben tener insight con datos."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        # Académico tiene 4 comentarios → insight sustantivo
        acad = result["por_categoria_padre"]["Académico"]
        self.assertGreater(len(acad), 50)  # insight sustantivo, no fallback
        self.assertIn("4", acad)  # menciona el total

    def test_categoria_sin_comentarios_tiene_mensaje_ausencia(self):
        """Categorías sin comentarios deben tener mensaje explícito de ausencia."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        # Docencia no tiene comentarios en setUp
        docencia = result["por_categoria_padre"]["Docencia"]
        self.assertIn("No se registran", docencia)

    def test_categoria_pocos_comentarios_tiene_advertencia(self):
        """Categorías con < UMBRAL_COMENTARIOS_INSIGHT deben tener advertencia."""
        result = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        # Tecnología tiene 1 comentario → debajo del umbral (3)
        tecno = result["por_categoria_padre"]["Tecnología"]
        self.assertIn("insuficiente", tecno.lower())

    def test_caso_vacio_sin_comentarios(self):
        """Si no hay comentarios, el insight global debe manejarlo gracefully."""
        result = generar_insights_ia([], [], {"positivo": 0, "negativo": 0, "neutro": 0}, 0)
        self.assertIsInstance(result["global"], str)
        self.assertGreater(len(result["global"]), 10)

    def test_caso_vacio_sin_topicos(self):
        """Si no hay tópicos pero sí comentarios, debe sugerir revisión manual."""
        result = generar_insights_ia(
            self.valid_comments, [],
            self.dist_sent, self.total_analizados
        )
        self.assertIn("Pendiente de Clasificación", result["global"])  # en este caso sí se menciona como advertencia
        self.assertIn("recomienda revisar", result["global"].lower())

    def test_determinismo(self):
        """La misma entrada debe producir la misma salida."""
        r1 = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        r2 = generar_insights_ia(self.valid_comments, self.topicos_globales, self.dist_sent, self.total_analizados)
        self.assertEqual(r1, r2)

    def test_no_llama_api_externa(self):
        """Verifica que el módulo no importe requests, urllib.http, httpx, etc."""
        import lib.insights_generator as mod
        import inspect
        source = inspect.getsource(mod)
        forbidden = ["import requests", "import urllib", "import httpx", "import aiohttp", "openai", "anthropic"]
        for f in forbidden:
            self.assertNotIn(f, source, f"Módulo contiene import prohibido: {f}")

    def test_categoria_extra_no_oficial_se_incluye(self):
        """Si el ETL produce una categoría no oficial, debe incluirse defensivamente."""
        comments_extra = self.valid_comments + [
            {"categoria": "Tema nuevo", "categoria_padre": "Categoría Nueva", "sentimiento": "positivo", "intensidad": 3},
            {"categoria": "Tema nuevo", "categoria_padre": "Categoría Nueva", "sentimiento": "positivo", "intensidad": 3},
            {"categoria": "Tema nuevo", "categoria_padre": "Categoría Nueva", "sentimiento": "positivo", "intensidad": 3},
        ]
        result = generar_insights_ia(comments_extra, self.topicos_globales, self.dist_sent, self.total_analizados + 3)
        self.assertIn("Categoría Nueva", result["por_categoria_padre"])


if __name__ == '__main__':
    unittest.main()
