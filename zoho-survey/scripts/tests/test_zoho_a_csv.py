"""
Tests de la conversion de la bandeja de respuestas al CSV que consume el ETL
(zoho_a_csv).

Cubren, sin llamar a ningun servicio externo:
  - que las cabeceras del CSV sean las del ETL y en su orden;
  - que el identificador viaje aparte y se reponga en 'ID de respuesta';
  - que el CSV salga sin BOM (el lector usa UTF-8 simple);
  - que no se cuente dos veces la misma respuesta;
  - que falle con aviso explicito si no se puede deducir el nivel;
  - que la deteccion de nivel coincida con la de build_json.
"""

import json
import tempfile
import unittest
from pathlib import Path

from zoho_a_csv import (
    CLAVE_ID,
    cabeceras_de,
    convertir,
    convertir_encuesta,
    detectar_nivel,
    nombre_csv,
)

try:  # build_json necesita pandas: en local puede no estar instalado
    from build_json import _detectar_nivel
except Exception:  # pragma: no cover
    _detectar_nivel = None

ENCUESTA = "ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - PREGRADO - 2026-2"

# Respuesta real tal como la guarda la bandeja: las claves ya son las cabeceras
# del CSV y el identificador va aparte.
RESPUESTA = {
    "id_respuesta": "KmC5fTWV",
    "encuesta": ENCUESTA,
    "recibido_en": "2026-09-22T19:02:25+00:00",
    "respuestas": {
        "Estado": "COMPLETED",
        "Start time": "Sep 22, 2026 10:06:20",
        "Hora de finalización": "Sep 22, 2026 10:08:02",
        "¿Qué carrera profesional estudias?": "Derecho",
        "¿Qué ciclo es el que cursas?; considera el ciclo donde más cursos llevas": "10° Ciclo",
        "La Universidad de Lima": "Totalmente satisfecho",
        "Net Promoter Score (de un total de 10)": "10",
        "El perfil de egreso de tu carrera": "Muy satisfecho",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Prueba",
    },
}


def escribir_bandeja(carpeta: Path, registros) -> Path:
    ruta = carpeta / "bandeja.jsonl"
    ruta.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in registros) + "\n",
        encoding="utf-8",
    )
    return ruta


class CabecerasTest(unittest.TestCase):
    def test_usa_las_cabeceras_del_etl_en_su_orden(self):
        cabeceras = cabeceras_de(ENCUESTA)
        self.assertIn(CLAVE_ID, cabeceras)
        self.assertEqual(cabeceras[0], CLAVE_ID)
        self.assertIn("Net Promoter Score (de un total de 10)", cabeceras)
        self.assertIn("La Universidad de Lima", cabeceras)
        self.assertEqual(len(cabeceras), 36)

    def test_el_nombre_del_csv_sale_del_titulo(self):
        self.assertEqual(nombre_csv(ENCUESTA), f"{ENCUESTA}.csv")

    def test_falla_si_no_se_puede_deducir_el_nivel(self):
        with self.assertRaises(ValueError) as caso:
            cabeceras_de("Encuesta sin categoria")
        self.assertIn("nivel", str(caso.exception))

    def test_detecta_el_nivel_igual_que_el_etl(self):
        if _detectar_nivel is None:
            self.skipTest("build_json no disponible en este entorno")
        nombres = [
            f"{ENCUESTA}.csv",
            "ENCUESTA DE SATISFACCIÓN ESTUDIANTIL - POSGRADO - 2026-1.csv",
            "ENCUESTA DE SATISFACCIÓN GRADUADOS 2026.csv",
            "ENCUESTA DE SATISFACCIÓN DOCENTES - POSGRADO 2026.csv",
            "ENCUESTA DE SATISFACCIÓN EGRESADOS 2026.csv",
            "ENCUESTA DE SATISFACCIÓN NO DOCENTES 2026.csv",
            "ENCUESTA DE SATISFACCIÓN EMPLEADORES 2026.csv",
            "cualquier-cosa.csv",
        ]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.assertEqual(detectar_nivel(nombre), _detectar_nivel(nombre))


class ConversionTest(unittest.TestCase):
    def test_arma_el_csv_con_el_identificador_y_sin_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            escribir_bandeja(carpeta, [RESPUESTA])

            salida = convertir_encuesta(carpeta / "bandeja.jsonl", carpeta)

            self.assertEqual(salida.name, f"{ENCUESTA}.csv")
            crudo = salida.read_bytes()
            self.assertFalse(crudo.startswith(b"\xef\xbb\xbf"), "el CSV no debe llevar BOM")
            texto = crudo.decode("utf-8")
            cabeceras = texto.splitlines()[0].split(",")
            self.assertEqual(cabeceras[0], CLAVE_ID)
            self.assertIn("KmC5fTWV", texto)
            self.assertIn("Derecho", texto)
            self.assertIn("10° Ciclo", texto)

    def test_no_cuenta_dos_veces_la_misma_respuesta(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            repetida = dict(RESPUESTA)
            escribir_bandeja(carpeta, [RESPUESTA, repetida])

            salida = convertir_encuesta(carpeta / "bandeja.jsonl", carpeta)

            self.assertEqual(len(salida.read_text(encoding="utf-8").strip().splitlines()), 2)

    def test_ignora_lo_que_no_tiene_identificador(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            sin_id = dict(RESPUESTA, id_respuesta="")
            escribir_bandeja(carpeta, [sin_id])

            with self.assertRaises(ValueError):
                convertir_encuesta(carpeta / "bandeja.jsonl", carpeta)

    def test_convierte_todas_las_bandejas(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            escribir_bandeja(carpeta, [RESPUESTA])
            otra = dict(RESPUESTA, id_respuesta="ADC5rynC")
            (carpeta / "otra.jsonl").write_text(
                json.dumps(otra, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            escritos = convertir(carpeta, carpeta)

            self.assertEqual(len(escritos), 1, "las dos bandejas son de la misma encuesta")

    def test_sin_bandejas_no_escribe_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(convertir(Path(tmp) / "no-existe", Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
