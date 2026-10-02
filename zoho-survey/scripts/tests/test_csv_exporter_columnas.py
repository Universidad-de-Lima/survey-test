"""Tests — csv_exporter resuelve las columnas por id declarado.

El CSV exportado no puede depender de nombres publicados escritos a mano:
el encabezado de la satisfacción con la carrera sale del texto del cuestionario
declarado, y el valor se lee de la columna cuyo nombre publica la declaración.
"""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd

from lib import config
from lib.csv_exporter import generar_csvs_y_zip

NIVEL = "graduate"


def _df(columna_carrera=None, valor_carrera="Muy satisfecho"):
    """Una respuesta con las columnas que el exportador usa."""
    col = columna_carrera or config.columna(NIVEL, "csat_sujeto")
    return pd.DataFrame([{
        config.columna(NIVEL, "id_respuesta"): "r1",
        config.columna(NIVEL, "carrera"): "Derecho",
        config.columna(NIVEL, "facultad"): "Facultad de Derecho",
        config.columna(NIVEL, "ciclo"): "1° Ciclo",
        config.columna(NIVEL, "situacion_laboral"): "Trabajador dependiente",
        config.columna(NIVEL, "tiempo_laboral"): "Tiempo completo",
        col: valor_carrera,
        config.columna(NIVEL, "csat_universidad"): "Satisfecho",
        config.columna(NIVEL, "nps"): "9",
        "Comentario NPS": "buena universidad",
    }])


def generar(df=None):
    """Corre el exportador en un directorio temporal y devuelve el CSV2."""
    ruta = Path(tempfile.mkdtemp())
    (ruta / "json").mkdir()
    generar_csvs_y_zip(
        df=df if df is not None else _df(),
        comentarios_detallados=[{
            "id": "r1_1", "comentario_id_original": "r1", "carrera": "Derecho",
            "facultad": "Facultad de Derecho", "ciclo": "1° Ciclo", "nps_score": 9,
            "sentimiento": "positivo", "intensidad": 3,
            "aspecto_normalizado": "Aulas de clase", "categoria_padre": "Infraestructura",
            "comentario_original": "buena universidad", "fragmento_mostrar": "buena universidad",
        }],
        ruta_salida=ruta / "json",
        csv_file=Path("encuesta.csv"),
        nivel=NIVEL,
        categoria_dim={},
        nps_col=config.columna(NIVEL, "nps"),
        csat_col=config.columna(NIVEL, "csat_universidad"),
        comentario_col="Comentario NPS",
    )
    zips = list((ruta / "exports").glob("*.zip"))
    with zipfile.ZipFile(zips[0]) as zf:
        nombre = next(n for n in zf.namelist() if not n.startswith("analisis_cualitativo"))
        return zf.read(nombre).decode("utf-8-sig")


class TestCsvExporterPorId(unittest.TestCase):

    def test_la_satisfaccion_con_la_carrera_lleva_su_texto_de_encuesta(self):
        cabecera = generar().splitlines()[0]
        self.assertIn(config.pregunta_de(NIVEL, "csat_sujeto"), cabecera)

    def test_las_columnas_de_agrupacion_se_resuelven_por_id(self):
        cabecera = generar().splitlines()[0].split(",")
        self.assertIn(config.columna(NIVEL, "situacion_laboral"), cabecera)
        self.assertIn(config.columna(NIVEL, "tiempo_laboral"), cabecera)
        self.assertIn(config.columna(NIVEL, "facultad"), cabecera)

    def test_sigue_el_rename_de_la_declaracion(self):
        """Si se renombra csat_sujeto, el encabezado sigue siendo el texto de la
        encuesta y el valor se lee de la columna con el nombre nuevo."""
        original = config.PREGUNTAS_POR_NIVEL[NIVEL]
        config.PREGUNTAS_POR_NIVEL[NIVEL] = [
            {**d, "nombre": "Mi carrera renombrada"} if d["id"] == "csat_sujeto" else d
            for d in original
        ]
        try:
            nombre_nuevo = config.columna(NIVEL, "csat_sujeto")
            self.assertEqual(nombre_nuevo, "Mi carrera renombrada")
            texto = generar(_df(columna_carrera=nombre_nuevo, valor_carrera="Totalmente satisfecho"))
            self.assertIn(config.pregunta_de(NIVEL, "csat_sujeto"), texto.splitlines()[0])
            self.assertIn("Totalmente satisfecho", texto)
        finally:
            config.PREGUNTAS_POR_NIVEL[NIVEL] = original

    def test_csv_exporter_no_traduce_el_nombre_a_mano(self):
        fuente = (SCRIPTS_DIR / "lib" / "csv_exporter.py").read_text(encoding="utf-8")
        self.assertNotIn('rev_map.get("La carrera"', fuente)
        self.assertNotIn('"Tu carrera"', fuente)


if __name__ == "__main__":
    unittest.main()
