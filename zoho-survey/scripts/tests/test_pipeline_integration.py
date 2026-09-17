"""
Tests de integración mínimos (Fase 9)

Validan el flujo completo:
  Mock CSV → ETL (lib funciones) → JSON generado → Schema validation

NO usan datasets productivos. Crean CSV sintéticos mínimos.
Objetivo: confirmar que una modificación futura no rompa el pipeline.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.metrics import calc_nps, calc_csat
from lib.io_helper import read_csv_robust, load_json
from lib.insights_generator import generar_insights_ia
import validate_generated_json as vj


class TestPipelineIntegracion(unittest.TestCase):
    """Smoke tests del pipeline ETL con datos mock."""

    def setUp(self):
        """Crear CSV mock mínimo con estructura esperada por el ETL."""
        self.tmpdir = tempfile.mkdtemp()
        self.csv_path = Path(self.tmpdir) / "mock_survey.csv"

        # CSV mock con columnas mínimas que el ETL espera
        csv_content = (
            "ID de respuesta,Net Promoter Score (de un total de 10),"
            "¿Qué carrera profesional estudias?,¿Qué ciclo es el que cursas?,"
            "La Universidad de Lima,Start time,Hora de finalización\n"
            "resp001,10,Administración,1° Ciclo,Totalmente satisfecho,01/01/2026,01/01/2026\n"
            "resp002,9,Administración,1° Ciclo,Totalmente satisfecho,01/01/2026,01/01/2026\n"
            "resp003,7,Administración,2° Ciclo,Muy satisfecho,01/01/2026,01/01/2026\n"
            "resp004,5,Derecho,3° Ciclo,Insatisfecho,01/01/2026,01/01/2026\n"
            "resp005,10,Ingeniería de Sistemas,5° Ciclo,Totalmente satisfecho,01/01/2026,01/01/2026\n"
        )
        self.csv_path.write_text(csv_content, encoding='utf-8')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_csv_mock_se_leido_correctamente(self):
        """El CSV mock debe leerse con read_csv_robust."""
        df = read_csv_robust(self.csv_path)
        self.assertEqual(len(df), 5)
        self.assertIn('ID de respuesta', df.columns)
        self.assertIn('Net Promoter Score (de un total de 10)', df.columns)

    def test_pipeline_nps_calculo_desde_csv_mock(self):
        """Calcular NPS desde el CSV mock debe dar resultado coherente."""
        df = read_csv_robust(self.csv_path)
        nps_col = 'Net Promoter Score (de un total de 10)'
        nps_values = df[nps_col].dropna().astype(int)

        promotores = (nps_values >= 9).sum()
        pasivos = ((nps_values >= 7) & (nps_values <= 8)).sum()
        detractores = (nps_values <= 6).sum()
        total = len(nps_values)

        nps = calc_nps(promotores, pasivos, detractores)
        # 3 promotores, 1 pasivo, 1 detractor de 5 total → ((3-1)/5)*100 = 40
        self.assertEqual(promotores, 3)
        self.assertEqual(pasivos, 1)
        self.assertEqual(detractores, 1)
        self.assertEqual(nps, 40.0)

    def test_pipeline_csat_calculo_desde_csv_mock(self):
        """Calcular CSAT desde el CSV mock debe dar resultado coherente."""
        df = read_csv_robust(self.csv_path)
        csat_col = 'La Universidad de Lima'
        csat_values = df[csat_col].dropna()

        t3b = csat_values.isin(['Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho']).sum()
        total = csat_values.isin([
            'Totalmente satisfecho', 'Muy satisfecho', 'Satisfecho',
            'Insatisfecho', 'Totalmente insatisfecho'
        ]).sum()

        csat = calc_csat(t3b, total)
        # 4 T3B (3 Totalmente + 1 Muy) de 5 total → 80%
        self.assertEqual(t3b, 4)
        self.assertEqual(total, 5)
        self.assertEqual(csat, 80.0)

    def test_insights_generator_integracion_con_datos_mock(self):
        """insights_generator debe producir estructura válida con datos mock."""
        valid_comments = [
            {"categoria": "Satisfacción estudiantil", "categoria_padre": "Académico",
             "sentimiento": "positivo", "intensidad": 4},
            {"categoria": "Satisfacción estudiantil", "categoria_padre": "Académico",
             "sentimiento": "positivo", "intensidad": 3},
            {"categoria": "Aulas de clase", "categoria_padre": "Infraestructura",
             "sentimiento": "negativo", "intensidad": 4},
            {"categoria": "Pendiente de Clasificación", "categoria_padre": "Pendiente de Clasificación",
             "sentimiento": "neutro", "intensidad": 2},
        ]
        topicos = [
            {"topico": "Pendiente de Clasificación", "total_comentarios": 1},
            {"topico": "Satisfacción estudiantil", "total_comentarios": 2},
        ]
        dist = {"positivo": 2, "negativo": 1, "neutro": 1}

        insights = generar_insights_ia(valid_comments, topicos, dist, 4)

        # Validar estructura
        self.assertIn("global", insights)
        self.assertIn("por_categoria_padre", insights)
        # NO debe citar Pendiente de Clasificación
        self.assertNotIn("Pendiente de Clasificación", insights["global"])
        # Debe citar el tema real
        self.assertIn("Satisfacción estudiantil", insights["global"])

    def test_schema_validation_dashboard_mock(self):
        """Un dashboard_data mock debe pasar validación schema."""
        dashboard = {
            "version": "2.0",
            "resumen": {
                "encuestas": 5,
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-01-02",
                "año": 2026,
                "periodo": "2026-1",
                "nps": {"score": 40.0, "promotores": 3, "pasivos": 1, "detractores": 1, "total": 5},
                "csat": {"score": 80.0, "t3b": 4, "total": 5}
            },
            "hallazgos": {
                "csat_pct": 80, "nps_score": 40, "nps_tipo": "Bueno",
                "nps_etapas": {}, "tendencia": "se mantiene", "delta": 0
            },
            "nps": {"promotores": 3, "pasivos": 1, "detractores": 1, "score": 40.0},
            "csat": {
                "Totalmente satisfecho": 3, "Muy satisfecho": 1, "Satisfecho": 0,
                "Insatisfecho": 1, "Totalmente insatisfecho": 0
            }
        }
        errors = vj.validate_with_schema(dashboard, "dashboard_data.schema.json", Path("mock.json"))
        self.assertEqual(errors, [], f"Dashboard mock debe validar. Errores: {errors}")

    def test_schema_validation_filtros_mock(self):
        """Un filtros.json mock debe pasar validación schema + invariantes."""
        filtros = {
            "version": "2.0",
            "has_ciclo": True,
            "facultades": ["Facultad A"],
            "carreras": ["Carrera 1"],
            "ciclos": ["1° Ciclo"],
            "facultad_carrera": {"Facultad A": ["Carrera 1"]}
        }
        # Schema validation
        errors = vj.validate_with_schema(filtros, "filtros.schema.json", Path("mock.json"))
        self.assertEqual(errors, [])
        # Invariantes
        vj.validate_filtros_invariants(filtros)


class TestPipelineDeterminismo(unittest.TestCase):
    """Verifica que el pipeline es determinista con misma entrada."""

    def test_metrics_determinismo(self):
        r1 = calc_nps(3, 1, 1)
        r2 = calc_nps(3, 1, 1)
        self.assertEqual(r1, r2)

        c1 = calc_csat(4, 5)
        c2 = calc_csat(4, 5)
        self.assertEqual(c1, c2)

    def test_insights_generator_determinismo(self):
        comments = [
            {"categoria": "X", "categoria_padre": "Académico", "sentimiento": "positivo", "intensidad": 3},
            {"categoria": "Y", "categoria_padre": "Académico", "sentimiento": "negativo", "intensidad": 4},
        ]
        topicos = [{"topico": "X", "total_comentarios": 1}]
        dist = {"positivo": 1, "negativo": 1, "neutro": 0}

        r1 = generar_insights_ia(comments, topicos, dist, 2)
        r2 = generar_insights_ia(comments, topicos, dist, 2)
        self.assertEqual(r1, r2)


class TestPipelineEdgeCases(unittest.TestCase):
    """Casos borde del pipeline ETL."""

    def test_nps_all_promoters(self):
        """100% promotores debe dar NPS=100."""
        nps = calc_nps(100, 0, 0)
        self.assertEqual(nps, 100.0)

    def test_nps_all_detractors(self):
        """100% detractores debe dar NPS=-100."""
        nps = calc_nps(0, 0, 100)
        self.assertEqual(nps, -100.0)

    def test_nps_balanced(self):
        """Igual número de promotores y detractores debe dar NPS=0."""
        nps = calc_nps(50, 0, 50)
        self.assertEqual(nps, 0.0)

    def test_nps_all_passives(self):
        """Solo pasivos debe dar NPS=0."""
        nps = calc_nps(0, 50, 0)
        self.assertEqual(nps, 0.0)

    def test_nps_zero_total(self):
        """ZeroDivisionError debe manejarse. calc_nps(0,0,0) debe dar 0 no crash."""
        nps = calc_nps(0, 0, 0)
        self.assertEqual(nps, 0.0)

    def test_csat_perfect(self):
        """100% T3B debe dar CSAT=100."""
        csat = calc_csat(100, 100)
        self.assertEqual(csat, 100.0)

    def test_csat_zero(self):
        """0% T3B debe dar CSAT=0."""
        csat = calc_csat(0, 100)
        self.assertEqual(csat, 0.0)

    def test_csat_zero_total(self):
        """ZeroDivisionError debe manejarse."""
        csat = calc_csat(0, 0)
        self.assertEqual(csat, 0.0)


class TestDetectNivelAndPeriod(unittest.TestCase):
    """Validación de detección de nivel y periodo desde nombres de archivo CSV."""

    def setUp(self):
        """Importar _detectar_nivel desde build_json."""
        import build_json as bj
        self._detectar_nivel = bj._detectar_nivel

    def test_detect_undergraduate(self):
        self.assertEqual(
            self._detectar_nivel("ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv"),
            "undergraduate"
        )

    def test_detect_graduate(self):
        self.assertEqual(
            self._detectar_nivel("ENCUESTA DE SATISFACCIÓN GRADUADOS - PREGRADO - 2026.csv"),
            "graduate"
        )

    def test_detect_postgraduate(self):
        self.assertEqual(
            self._detectar_nivel("ENCUESTA ESTUDIANTIL POSGRADO 2026-1.csv"),
            "postgraduate"
        )

    def test_detect_nonfaculty(self):
        self.assertEqual(
            self._detectar_nivel("ENCUESTA NO DOCENTES 2026.csv"),
            "nonfaculty"
        )

    def test_detect_employers(self):
        self.assertEqual(
            self._detectar_nivel("ENCUESTA EMPLEADORES 2026.csv"),
            "employers"
        )

    def test_detect_unknown(self):
        self.assertIsNone(
            self._detectar_nivel("ARCHIVO_DESCONOCIDO.csv")
        )

    def test_period_regex(self):
        """La regex de periodo debe capturar años y semestres."""
        import re
        pattern = r"(20\d{2}(?:-[12])?)"

        self.assertTrue(re.search(pattern, "2026-1"))
        self.assertTrue(re.search(pattern, "2025-2"))
        self.assertTrue(re.search(pattern, "2026"))
        self.assertIsNotNone(re.search(pattern, "ENCUESTA 2026-1.csv"))
        self.assertIsNotNone(re.search(pattern, "ENCUESTA 2025.csv"))


class TestCSVHashDetection(unittest.TestCase):
    """Validación de detección de cambios por hash de CSV."""

    def setUp(self):
        from lib.io_helper import hash_csv, csv_cambiado
        self._hash_csv = hash_csv
        self._csv_cambiado = csv_cambiado

    def test_hash_csv_produce_string(self):
        """_hash_csv debe retornar un string hexadecimal de 64 chars (SHA256)."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2\nval1,val2\n")
            tmp_path = Path(f.name)

        try:
            h = self._hash_csv(tmp_path)
            self.assertIsInstance(h, str)
            self.assertEqual(len(h), 64)
            # Debe ser hexadecimal
            int(h, 16)
        finally:
            tmp_path.unlink()

    def test_hash_same_content_same_hash(self):
        """Dos CSVs idénticos deben producir el mismo hash."""
        import tempfile
        content = "a,b\n1,2\n"
        f1 = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        f1.write(content)
        f1.close()
        f2 = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        f2.write(content)
        f2.close()

        try:
            h1 = self._hash_csv(Path(f1.name))
            h2 = self._hash_csv(Path(f2.name))
            self.assertEqual(h1, h2)
        finally:
            Path(f1.name).unlink(missing_ok=True)
            Path(f2.name).unlink(missing_ok=True)

    def test_csv_cambiado_sin_hash_file(self):
        """Si no existe .csv_hash, debe retornar True (procesar)."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x,y\n1,2\n")
            tmp_csv = Path(f.name)

        try:
            # Directorio temporal sin .csv_hash
            tmp_dir = Path(tempfile.mkdtemp())
            result = self._csv_cambiado(tmp_csv, tmp_dir)
            self.assertTrue(result)
        finally:
            tmp_csv.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
