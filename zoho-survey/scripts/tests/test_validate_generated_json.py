"""
Tests — validate_generated_json.py (Fase 9)

Valida las funciones del validador usando datos mock.
NO depende de JSON productivos; crea estructuras sintéticas.
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

# Importar el módulo como tal (no solo funciones) para acceder a sus constantes
import validate_generated_json as vj


class TestValidateShape(unittest.TestCase):
    """Tests para validate_shape(value, expected_type, non_empty)."""

    def test_dict_valido(self):
        vj.validate_shape({"a": 1}, dict, True)

    def test_dict_vacio_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.validate_shape({}, dict, True)

    def test_dict_vacio_permitido(self):
        vj.validate_shape({}, dict, False)

    def test_lista_valida(self):
        vj.validate_shape([1, 2, 3], list, True)

    def test_lista_vacia_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.validate_shape([], list, True)

    def test_tipo_incorrecto_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.validate_shape("string", dict, True)

    def test_lista_en_lugar_de_dict(self):
        with self.assertRaises(ValueError):
            vj.validate_shape([1, 2], dict, True)


class TestRequireKeys(unittest.TestCase):
    """Tests para require_keys(value, keys, label)."""

    def test_todas_las_keys_presentes(self):
        vj.require_keys({"a": 1, "b": 2, "c": 3}, {"a", "b", "c"}, "test")

    def test_keys_faltantes_lanzan_error(self):
        with self.assertRaises(ValueError) as ctx:
            vj.require_keys({"a": 1}, {"a", "b", "c"}, "test_obj")
        self.assertIn("test_obj", str(ctx.exception))
        self.assertIn("b", str(ctx.exception))
        self.assertIn("c", str(ctx.exception))

    def test_no_dict_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.require_keys("not a dict", {"a"}, "test")

    def test_set_vacio_pasa(self):
        vj.require_keys({"a": 1}, set(), "test")


class TestValidateFiltrosInvariants(unittest.TestCase):
    """Tests para validate_filtros_invariants(value)."""

    def filtros_validos(self):
        return {
            "version": "2.0",
            "has_ciclo": True,
            "facultades": ["Facultad A", "Facultad B"],
            "carreras": ["Carrera 1", "Carrera 2"],
            "ciclos": ["1° Ciclo", "2° Ciclo"],
            "facultad_carrera": {
                "Facultad A": ["Carrera 1"],
                "Facultad B": ["Carrera 2"]
            }
        }

    def test_filtros_validos_pasa(self):
        vj.validate_filtros_invariants(self.filtros_validos())

    def test_facultad_no_mapeada_lanza_error(self):
        filtros = self.filtros_validos()
        filtros["facultades"].append("Facultad C")  # no está en facultad_carrera
        with self.assertRaises(ValueError) as ctx:
            vj.validate_filtros_invariants(filtros)
        self.assertIn("Facultad C", str(ctx.exception))

    def test_ciclos_vacios_con_has_ciclo_true_lanza_error(self):
        filtros = self.filtros_validos()
        filtros["ciclos"] = []
        with self.assertRaises(ValueError):
            vj.validate_filtros_invariants(filtros)

    def test_ciclos_vacios_con_has_ciclo_false_pasa(self):
        filtros = self.filtros_validos()
        filtros["has_ciclo"] = False
        filtros["ciclos"] = []
        vj.validate_filtros_invariants(filtros)

    def test_facultades_vacias_lanza_error(self):
        filtros = self.filtros_validos()
        filtros["facultades"] = []
        with self.assertRaises(ValueError):
            vj.validate_filtros_invariants(filtros)

    def test_carreras_vacias_lanza_error(self):
        filtros = self.filtros_validos()
        filtros["carreras"] = []
        with self.assertRaises(ValueError):
            vj.validate_filtros_invariants(filtros)


class TestValidateDimensionesInvariants(unittest.TestCase):
    """Tests para validate_dimensiones_invariants(value)."""

    def test_dimensiones_con_datos_pasa(self):
        dim = [
            {"total": 10, "categoria": "A"},
            {"total": 5, "categoria": "B"},
        ]
        vj.validate_dimensiones_invariants(dim)

    def test_dimensiones_todas_cero_lanza_error(self):
        dim = [
            {"total": 0, "categoria": "A"},
            {"total": 0, "categoria": "B"},
        ]
        with self.assertRaises(ValueError):
            vj.validate_dimensiones_invariants(dim)

    def test_dimensiones_vacias_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.validate_dimensiones_invariants([])


class TestValidateIdRowsInvariants(unittest.TestCase):
    """Tests para validate_id_rows_invariants(value, filename)."""

    def test_ids_con_total_pasa(self):
        rows = [
            {"facultad": "A", "carrera": "X", "ciclo": "1", "total": 10},
            {"facultad": "B", "carrera": "Y", "ciclo": "2", "total": 5},
        ]
        vj.validate_id_rows_invariants(rows, "ids.json")

    def test_ids_con_count_pasa(self):
        """El validador acepta 'count' como clave legacy."""
        rows = [
            {"facultad": "A", "carrera": "X", "ciclo": "1", "count": 10},
        ]
        vj.validate_id_rows_invariants(rows, "ids.json")

    def test_ids_todos_cero_lanza_error(self):
        rows = [
            {"facultad": "A", "carrera": "X", "ciclo": "1", "total": 0},
        ]
        with self.assertRaises(ValueError):
            vj.validate_id_rows_invariants(rows, "ids.json")

    def test_ids_sin_total_ni_count_lanza_error(self):
        rows = [
            {"facultad": "A", "carrera": "X", "ciclo": "1"},
        ]
        with self.assertRaises(ValueError):
            vj.validate_id_rows_invariants(rows, "ids.json")

    def test_ids_vacio_lanza_error(self):
        with self.assertRaises(ValueError):
            vj.validate_id_rows_invariants([], "ids.json")


class TestValidateSentimientoInvariants(unittest.TestCase):
    """Tests para validate_sentimiento_invariants(value)."""

    def test_sentimiento_valido_pasa(self):
        sent = {
            "comentarios": [
                {"es_valido": True, "sentimiento": "positivo"},
                {"es_valido": False, "sentimiento": "neutro"},
            ]
        }
        vj.validate_sentimiento_invariants(sent)

    def test_es_valido_no_booleano_lanza_error(self):
        sent = {
            "comentarios": [
                {"es_valido": "yes", "sentimiento": "positivo"},
            ]
        }
        with self.assertRaises(ValueError):
            vj.validate_sentimiento_invariants(sent)

    def test_sentimiento_sin_comentarios_pasa(self):
        vj.validate_sentimiento_invariants({"comentarios": []})
        vj.validate_sentimiento_invariants({})


class TestReadPeriods(unittest.TestCase):
    """Tests para read_periods(level_dir) — lectura de periodos.json."""

    def test_periodos_validos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            periodos = [
                {"id": "2025-1", "isNew": False},
                {"id": "2025-2", "isNew": True},
            ]
            with open(f"{tmpdir}/periodos.json", 'w', encoding='utf-8') as f:
                json.dump(periodos, f)
            result = vj.read_periods(Path(tmpdir))
            self.assertEqual(result, ["2025-1", "2025-2"])

    def test_periodos_sin_isNew_lanza_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            periodos = [{"id": "2025-1"}, {"id": "2025-2"}]
            with open(f"{tmpdir}/periodos.json", 'w', encoding='utf-8') as f:
                json.dump(periodos, f)
            with self.assertRaises(ValueError):
                vj.read_periods(Path(tmpdir))

    def test_periodos_multiples_isNew_lanza_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            periodos = [
                {"id": "2025-1", "isNew": True},
                {"id": "2025-2", "isNew": True},
            ]
            with open(f"{tmpdir}/periodos.json", 'w', encoding='utf-8') as f:
                json.dump(periodos, f)
            with self.assertRaises(ValueError):
                vj.read_periods(Path(tmpdir))

    def test_periodos_duplicados_lanza_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            periodos = [
                {"id": "2025-1", "isNew": True},
                {"id": "2025-1", "isNew": False},
            ]
            with open(f"{tmpdir}/periodos.json", 'w', encoding='utf-8') as f:
                json.dump(periodos, f)
            with self.assertRaises(ValueError):
                vj.read_periods(Path(tmpdir))

    def test_periodos_vacio_lanza_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(f"{tmpdir}/periodos.json", 'w', encoding='utf-8') as f:
                json.dump([], f)
            with self.assertRaises(ValueError):
                vj.read_periods(Path(tmpdir))



class TestValidatePeriodHtml(unittest.TestCase):
    """Tests para validate_period_html(period_dir)."""

    def test_current_qualitative_ids_do_not_warn(self):
        """El contrato HTML cualitativo debe coincidir con sentiment-view.js actual."""
        with tempfile.TemporaryDirectory() as tmpdir:
            period_dir = Path(tmpdir)
            filters = []
            for suffix in ["top3", "radar", "preguntas", "detalle", "visibilidad"]:
                filters.append(f'<div id="filter-facultad-{suffix}"></div>')
                if suffix != "detalle":
                    filters.append(f'<div id="filter-carrera-{suffix}"></div>')
                filters.append(f'<div id="filter-ciclo-{suffix}"></div>')
                filters.append(f'<button id="reset-{suffix}"></button>')

            html = """
<a href="#cualitativo">Cualitativo</a>
<section id="cualitativo" aria-labelledby="cualitativo-heading">
  <h2 id="cualitativo-heading">ANÁLISIS CUALITATIVO</h2>
  <div id="sentiment-kpis"></div>
  <div id="sentimiento-bar-chart"></div>
  <input id="explorador-search">
  <select id="explorador-sentimiento"></select>
  <table id="tabla-explorador-comentarios"></table>
  <p id="insight-cualitativo"></p>
  <div id="insight-cualitativo-categorias"></div>
</section>
""" + "\n".join(filters)
            (period_dir / "index.html").write_text(html, encoding="utf-8")

            errors, warnings = vj.validate_period_html(period_dir)

        self.assertEqual([], errors)
        self.assertEqual([], warnings)

class TestLoadSchema(unittest.TestCase):
    """Tests para load_schema(schema_filename)."""

    def test_cargar_schema_existente(self):
        """Debe cargar dashboard_data.schema.json desde schemas/."""
        schema = vj.load_schema("dashboard_data.schema.json")
        self.assertIsInstance(schema, dict)
        self.assertIn("properties", schema)

    def test_cargar_schema_inexistente_lanza_error(self):
        with self.assertRaises(FileNotFoundError):
            vj.load_schema("no_existente.schema.json")

    def test_schema_cacheado(self):
        """La segunda llamada debe usar el cache."""
        s1 = vj.load_schema("dashboard_data.schema.json")
        s2 = vj.load_schema("dashboard_data.schema.json")
        self.assertIs(s1, s2)  # misma referencia en memoria


class TestValidateWithSchema(unittest.TestCase):
    """Tests para validate_with_schema(value, schema_filename, json_path)."""

    def test_dashboard_valido_pasa(self):
        """Un dashboard_data válido no debe producir errores de schema."""
        dashboard = {
            "version": "2.0",
            "resumen": {
                "encuestas": 100,
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-06-01",
                "año": 2026,
                "nps": {"score": 50.0, "promotores": 60, "pasivos": 30, "detractores": 10, "total": 100},
                "csat": {"score": 90.0, "t3b": 90, "total": 100}
            },
            "hallazgos": {
                "csat_pct": 90, "nps_score": 50, "nps_tipo": "Bueno",
                "nps_etapas": {}, "tendencia": "se mantiene", "delta": 0
            },
            "nps": {"promotores": 60, "pasivos": 30, "detractores": 10, "score": 50.0},
            "csat": {
                "Totalmente satisfecho": 50, "Muy satisfecho": 30, "Satisfecho": 10,
                "Insatisfecho": 5, "Totalmente insatisfecho": 5
            }
        }
        errors = vj.validate_with_schema(dashboard, "dashboard_data.schema.json", Path("test.json"))
        self.assertEqual(errors, [], f"Errores inesperados: {errors}")

    def test_dashboard_sin_version_falla(self):
        """Un dashboard sin 'version' debe fallar schema validation."""
        dashboard = {"resumen": {}, "hallazgos": {}, "nps": {}, "csat": {}}
        errors = vj.validate_with_schema(dashboard, "dashboard_data.schema.json", Path("test.json"))
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("version" in e for e in errors))

    def test_nps_tipo_invalido_falla(self):
        """nps_tipo debe ser uno del enum."""
        dashboard = {
            "version": "2.0",
            "resumen": {
                "encuestas": 1, "fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-02",
                "año": 2026,
                "nps": {"score": 0, "promotores": 0, "pasivos": 1, "detractores": 0, "total": 1},
                "csat": {"score": 0, "t3b": 0, "total": 1}
            },
            "hallazgos": {
                "csat_pct": 0, "nps_score": 0, "nps_tipo": "InvalidType",
                "nps_etapas": {}, "tendencia": "se mantiene", "delta": 0
            },
            "nps": {"promotores": 0, "pasivos": 1, "detractores": 0},
            "csat": {"Totalmente satisfecho": 0, "Muy satisfecho": 0, "Satisfecho": 1,
                     "Insatisfecho": 0, "Totalmente insatisfecho": 0}
        }
        errors = vj.validate_with_schema(dashboard, "dashboard_data.schema.json", Path("test.json"))
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("nps_tipo" in e for e in errors))


if __name__ == '__main__':
    unittest.main()
