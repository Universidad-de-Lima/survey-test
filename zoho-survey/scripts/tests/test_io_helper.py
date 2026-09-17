"""
Tests — lib/io_helper.py (Fase 9)

Valida lectura CSV robusta, lectura JSON BOM-safe y normalización de fechas.
Usa archivos temporales mock; NO depende de CSV productivos.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.io_helper import load_json, read_csv_robust, normalize_dates


class TestLoadJson(unittest.TestCase):
    """Tests para load_json — lectura JSON BOM-safe."""

    def test_leer_json_valido(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"key": "value", "num": 42}, f)
            path = f.name
        try:
            result = load_json(Path(path))
            self.assertEqual(result["key"], "value")
            self.assertEqual(result["num"], 42)
        finally:
            os.unlink(path)

    def test_leer_json_con_bom(self):
        """JSON con BOM (UTF-8-sig) debe leerse correctamente."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as f:
            f.write(b'\xef\xbb\xbf{"key": "bom_value"}')
            path = f.name
        try:
            result = load_json(Path(path))
            self.assertEqual(result["key"], "bom_value")
        finally:
            os.unlink(path)

    def test_archivo_inexistente_lanza_error(self):
        with self.assertRaises((ValueError, FileNotFoundError, OSError)):
            load_json(Path("/tmp/no_existente_12345.json"))

    def test_json_vacio_lanza_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_json(Path(path))
        finally:
            os.unlink(path)

    def test_json_invalido_lanza_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("{invalid json:}")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_json(Path(path))
        finally:
            os.unlink(path)

    def test_leer_array_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump([1, 2, 3], f)
            path = f.name
        try:
            result = load_json(Path(path))
            self.assertIsInstance(result, list)
            self.assertEqual(result, [1, 2, 3])
        finally:
            os.unlink(path)


class TestReadCsvRobust(unittest.TestCase):
    """Tests para read_csv_robust — lectura CSV con fallback de encoding."""

    def test_leer_csv_utf8(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("col1,col2\nval1,val2\n")
            path = f.name
        try:
            df = read_csv_robust(Path(path))
            self.assertEqual(len(df), 1)
            self.assertEqual(df.columns.tolist(), ['col1', 'col2'])
            self.assertEqual(df.iloc[0]['col1'], 'val1')
        finally:
            os.unlink(path)

    def test_leer_csv_con_tildes(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("nombre,ciudad\nMaría,Lima\nJosé,Madrid\n")
            path = f.name
        try:
            df = read_csv_robust(Path(path))
            self.assertEqual(len(df), 2)
            self.assertEqual(df.iloc[0]['nombre'], 'María')
            self.assertEqual(df.iloc[1]['ciudad'], 'Madrid')
        finally:
            os.unlink(path)

    def test_archivo_inexistente_lanza_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            read_csv_robust(Path("/tmp/no_existente_12345.csv"))

    def test_leer_csv_vacio(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("col1,col2\n")
            path = f.name
        try:
            df = read_csv_robust(Path(path))
            self.assertEqual(len(df), 0)
            self.assertEqual(df.columns.tolist(), ['col1', 'col2'])
        finally:
            os.unlink(path)

    def test_leer_csv_multiples_filas(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("id,nombre\n1,Alice\n2,Bob\n3,Charlie\n")
            path = f.name
        try:
            df = read_csv_robust(Path(path))
            self.assertEqual(len(df), 3)
            self.assertEqual(df.iloc[0]['id'], 1)
            self.assertEqual(df.iloc[2]['nombre'], 'Charlie')
        finally:
            os.unlink(path)


class TestNormalizeDates(unittest.TestCase):
    """Tests para normalize_dates — normalización de fechas en español."""

    def test_normalizar_fecha_espanol(self):
        """Fechas con meses en español deben normalizarse."""
        import pandas as pd
        df = pd.DataFrame({
            'fecha': ['05/11/2025', '24/10/2025'],
            'valor': [1, 2]
        })
        result = normalize_dates(df, ['fecha'])
        # Después de normalizar, fecha debe ser datetime
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result['fecha']))

    def test_normalizar_no_modifica_otras_columnas(self):
        import pandas as pd
        df = pd.DataFrame({
            'fecha': ['05/11/2025'],
            'valor': [42]
        })
        result = normalize_dates(df, ['fecha'])
        self.assertEqual(result['valor'].iloc[0], 42)

    def test_normalizar_columna_inexistente_no_rompe(self):
        """Si la columna no existe, no debe lanzar excepción."""
        import pandas as pd
        df = pd.DataFrame({'valor': [1]})
        # No debe lanzar excepción
        result = normalize_dates(df, ['fecha_inexistente'])
        self.assertEqual(len(result), 1)

    def test_normalizar_devuelve_copia(self):
        """La función debe trabajar sobre una copia, no mutar el original."""
        import pandas as pd
        df = pd.DataFrame({'fecha': ['05/11/2025']})
        original_dtypes = df.dtypes.to_dict()
        normalize_dates(df, ['fecha'])
        # El original no debe haber cambiado
        self.assertEqual(df.dtypes.to_dict(), original_dtypes)


if __name__ == '__main__':
    unittest.main()
