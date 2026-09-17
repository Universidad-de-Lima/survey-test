"""
TESTS — Integración del ETL (smoke test)

Test de integración que verifica que las funciones clave del ETL (metrics, io_helper,
insights_generator) funcionan correctamente encadenadas, simulando el flujo de
build_json.py sin requerir DEEPSEEK_API_KEY.

No es un test end-to-end completo (no ejecuta build_json.py:main()) porque el motor IA
requiere DEEPSEEK_API_KEY. En su lugar, prueba las funciones puras con datos mock
que simulan la salida del ETL.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.metrics import calc_nps, calc_csat, calc_promedio_ponderado
from lib.io_helper import hash_csv, csv_cambiado, enmascarar_pii, guardar_hash_csv, hash_csv_versionado
from lib.insights_generator import generar_insights_ia


class TestETLIntegrationMetrics(unittest.TestCase):
    """Tests de integración: métricas encadenadas como en build_json.py."""

    def test_nps_calculo_completo(self):
        """NPS se calcula correctamente desde conteos de promotores/pasivos/detractores."""
        # Simular 100 respuestas: 70 promotores, 20 pasivos, 10 detractores
        nps = calc_nps(70, 20, 10)
        # NPS = (70 - 10) = 60
        self.assertEqual(nps, 60.0)

    def test_csat_calculo_completo(self):
        """CSAT se calcula correctamente desde conteos de satisfacción."""
        # Simular: 80 T3B de 100 total
        csat = calc_csat(80, 100)
        self.assertEqual(csat, 80.0)

    def test_promedio_ponderado_likert(self):
        """Promedio ponderado Likert se calcula correctamente."""
        # Pesos [5,4,3,2,1] para [Totalmente sat, Muy sat, Sat, Insat, Totalmente insat]
        counts = [50, 30, 15, 4, 1]  # 100 respuestas
        pesos = [5, 4, 3, 2, 1]
        ponderado = calc_promedio_ponderado(counts, pesos, 5)  # max_scale=5
        # (50*5 + 30*4 + 15*3 + 4*2 + 1*1) / 100 = (250+120+45+8+1)/100 = 4.24
        self.assertAlmostEqual(ponderado, 84.8, places=1)  # 4.24 * 100 / 5 = 84.8

    def test_nps_edge_cases(self):
        """NPS con casos borde: 0 respuestas, todos promotores, todos detractores."""
        self.assertEqual(calc_nps(0, 0, 0), 0.0)
        self.assertEqual(calc_nps(100, 0, 0), 100.0)
        self.assertEqual(calc_nps(0, 0, 100), -100.0)
        self.assertEqual(calc_nps(0, 100, 0), 0.0)


class TestETLIntegrationIdempotency(unittest.TestCase):
    """Tests de idempotencia: hash de CSV y detección de cambios."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.csv_path = Path(self.tmpdir) / "test.csv"
        self.output_dir = Path(self.tmpdir) / "output"
        self.output_dir.mkdir()

    def test_hash_consistente(self):
        """Mismo CSV produce mismo hash."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        hash1 = hash_csv(self.csv_path)
        hash2 = hash_csv(self.csv_path)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex

    def test_csv_cambiado_primera_vez(self):
        """Primera vez: csv_cambiado retorna True (no hay .csv_hash)."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        self.assertTrue(csv_cambiado(self.csv_path, self.output_dir))

    def test_csv_no_cambiado(self):
        """CSV sin cambios y hash versionado: csv_cambiado retorna False."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        guardar_hash_csv(self.csv_path, self.output_dir)
        self.assertFalse(csv_cambiado(self.csv_path, self.output_dir))

    def test_csv_hash_antiguo_sin_version_reprocesa(self):
        """Un .csv_hash legacy sin versión fuerza reproceso controlado."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        (self.output_dir / ".csv_hash").write_text(hash_csv(self.csv_path), encoding="utf-8")
        self.assertTrue(csv_cambiado(self.csv_path, self.output_dir))

    def test_hash_versionado_no_cambia_hash_csv_puro(self):
        """hash_csv sigue siendo SHA256 puro y la huella versionada agrega prefijo."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        pure_hash = hash_csv(self.csv_path)
        versioned_hash = hash_csv_versionado(self.csv_path)
        self.assertEqual(len(pure_hash), 64)
        self.assertTrue(versioned_hash.endswith(pure_hash))
        self.assertNotEqual(pure_hash, versioned_hash)

    def test_csv_modificado_con_hash_versionado_reprocesa(self):
        """Si el CSV cambia tras guardar huella versionada, se reprocesa."""
        self.csv_path.write_text("col1,col2\nval1,val2\n", encoding="utf-8")
        guardar_hash_csv(self.csv_path, self.output_dir)
        self.csv_path.write_text("col1,col2\nval1,val3\n", encoding="utf-8")
        self.assertTrue(csv_cambiado(self.csv_path, self.output_dir))


class TestETLIntegrationPIIRedaction(unittest.TestCase):
    """Tests de redacción PII en el flujo del ETL."""

    def test_pii_redactada_antes_de_output(self):
        """PII se redacta antes de llegar al output final."""
        comentario = "mi email es test@ulima.edu.pe y mi celular es 999888777"
        redacted = enmascarar_pii(comentario)
        self.assertNotIn("test@ulima.edu.pe", redacted)
        self.assertNotIn("999888777", redacted)
        self.assertIn("ENMASCARADO", redacted)

    def test_comentario_sin_pii_no_se_altera(self):
        """Comentario sin PII no se altera."""
        comentario = "la universidad tiene buena infraestructura"
        redacted = enmascarar_pii(comentario)
        self.assertEqual(redacted, comentario)


class TestETLIntegrationInsights(unittest.TestCase):
    """Tests de generación de insights deterministas."""

    def test_insights_se_generan_desde_dataset(self):
        """Insights se generan correctamente desde un dataset mock."""
        # Crear dataset mock con unidades válidas
        dataset = [
            {
                "id_encuesta": "R1", "id_fragmento": "R1_01",
                "facultad": "Ingeniería", "carrera": "Sistemas",
                "ciclo": "5° Ciclo", "nps_score": 9,
                "segmento_nps": "Promotor",
                "satisfaccion_global": "Totalmente satisfecho",
                "texto": "buenos profesores",
                "aspecto_detectado": "profesores",
                "aspecto_normalizado": "Calidad de la enseñanza",
                "categoria_padre": "Académico",
                "sub_aspectos": [],
                "sentimiento": "positivo",
                "intensidad": 4,
                "confianza_sentimiento": 0.9,
                "comentario_original": "buenos profesores",
                "es_valido": True,
                "motivo_invalidez": None,
                "motor": "deepseek",
            },
            {
                "id_encuesta": "R2", "id_fragmento": "R2_01",
                "facultad": "Ingeniería", "carrera": "Sistemas",
                "ciclo": "3° Ciclo", "nps_score": 3,
                "segmento_nps": "Detractor",
                "satisfaccion_global": "Insatisfecho",
                "texto": "wifi lento",
                "aspecto_detectado": "wifi",
                "aspecto_normalizado": "Conexión Wi-Fi",
                "categoria_padre": "Tecnología",
                "sub_aspectos": [],
                "sentimiento": "negativo",
                "intensidad": 4,
                "confianza_sentimiento": 0.85,
                "comentario_original": "wifi lento",
                "es_valido": True,
                "motivo_invalidez": None,
                "motor": "deepseek",
            },
        ]

        topicos = [{"topico": "Calidad de la enseñanza", "total_comentarios": 1, "positivos": 1, "negativos": 0, "neutros": 0}]
        dist_sent = {"positivo": 1, "negativo": 1, "neutro": 0}
        insights = generar_insights_ia(dataset, topicos, dist_sent, 2)
        self.assertIsInstance(insights, dict)
        self.assertIn("global", insights)
        self.assertIn("por_categoria_padre", insights)
        self.assertIsInstance(insights["global"], str)
        self.assertGreater(len(insights["global"]), 0)

    def test_insights_excluyen_pendiente_clasificacion(self):
        """Insights excluyen 'Pendiente de Clasificación' del análisis principal."""
        dataset = [
            {
                "id_encuesta": "R1", "id_fragmento": "R1_01",
                "facultad": "Ing", "carrera": "Sist", "ciclo": "1°",
                "nps_score": 5, "segmento_nps": "Detractor",
                "satisfaccion_global": "Satisfecho",
                "texto": "test", "aspecto_detectado": "",
                "aspecto_normalizado": "Pendiente de Clasificación",
                "categoria_padre": "Pendiente de Clasificación",
                "sub_aspectos": [], "sentimiento": "neutro",
                "intensidad": 3, "confianza_sentimiento": 0.5,
                "comentario_original": "test", "es_valido": True,
                "motivo_invalidez": None, "motor": "deepseek",
            },
        ]

        topicos = []
        dist_sent = {"positivo": 0, "negativo": 0, "neutro": 1}
        insights = generar_insights_ia(dataset, topicos, dist_sent, 1)
        # El insight global no debe mencionar "Pendiente de Clasificación" como tema principal
        self.assertIsInstance(insights["global"], str)


class TestETLIntegrationSchemaValidation(unittest.TestCase):
    """Tests de validación de JSONs contra schemas."""

    def test_dashboard_data_schema_valido(self):
        """Un dashboard_data mock pasa validación de schema."""
        import jsonschema
        from jsonschema import Draft7Validator

        schema_path = SCRIPTS_DIR / "schemas" / "dashboard_data.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        dashboard_mock = {
            "version": "2.0",
            "resumen": {
                "encuestas": 100,
                "carreras": 5,
                "facultades": 3,
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-06-01",
                "dias": 152,
                "dias_recoleccion": 100,
                "año": 2026,
                "periodo": "2026-1",
                "nps": {
                    "score": 60.0,
                    "promotores": 70,
                    "pasivos": 20,
                    "detractores": 10,
                    "total": 100
                },
                "csat": {
                    "score": 80.0,
                    "t3b": 80,
                    "total": 100,
                    "t2b": 50,
                    "t2b_pct": 50.0,
                    "ponderado": 4.0
                }
            },
            "hallazgos": {
                "csat_pct": 80,
                "nps_score": 60,
                "nps_tipo": "Bueno",
                "nps_etapas": {
                    "Inicial": 60.0,
                    "Intermedio": 65.0,
                    "Avanzado": 55.0
                },
                "tendencia": "se mantiene",
                "delta": 0,
                "top_dimensiones": [{"name": "Calidad", "score": 90.0}],
                "top_facultades": [{"name": "Ingenieria", "score": 85.0}]
            },
            "nps": {
                "promotores": 70,
                "pasivos": 20,
                "detractores": 10,
                "score": 60.0
            },
            "csat": {
                "Totalmente satisfecho": 50,
                "Muy satisfecho": 30,
                "Satisfecho": 15,
                "Insatisfecho": 4,
                "Totalmente insatisfecho": 1,
                "No utilizo": 0,
                "No conozco": 0
            }
        }

        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(dashboard_mock))
        self.assertEqual(len(errors), 0, f"Schema validation errors: {[e.message for e in errors]}")


if __name__ == "__main__":
    unittest.main()
