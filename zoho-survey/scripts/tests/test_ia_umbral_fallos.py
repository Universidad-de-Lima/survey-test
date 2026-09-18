"""Tests del umbral fail-closed de fallos de API (C-1).

Contexto del incidente: el run del 4-sep-2026 registro 892 de 898 comentarios
con "Error de API (todos los motores fallaron)" y, aun asi, el ETL publico
sentimiento.json calculado sobre 6 comentarios. Estas pruebas fijan el
comportamiento que impide que eso vuelva a pasar sin aviso.
"""

import os
import unittest

from lib.ia_cualitativo import (
    MIN_INTENTOS_UMBRAL,
    MOTIVO_FALLO_API,
    evaluar_fallo_masivo,
)


class TestEvaluarFalloMasivo(unittest.TestCase):
    """Reglas del umbral (IA_CUALITATIVO_MAX_FALLOS_API_PCT, default 20%)."""

    def setUp(self):
        self._previo = os.environ.pop("IA_CUALITATIVO_MAX_FALLOS_API_PCT", None)

    def tearDown(self):
        if self._previo is not None:
            os.environ["IA_CUALITATIVO_MAX_FALLOS_API_PCT"] = self._previo
        else:
            os.environ.pop("IA_CUALITATIVO_MAX_FALLOS_API_PCT", None)

    # ----------------------------------------------------------
    # Caso real del incidente
    # ----------------------------------------------------------
    def test_incidente_2026_1_aborta(self):
        """892 fallos de 898 (99.3%) debe abortar: es el caso que publico basura."""
        msg = evaluar_fallo_masivo(intentos_api=898, fallos_api=892)
        self.assertIsNotNone(msg)
        self.assertIn("892/898", msg)
        self.assertIn("sentimiento.json", msg)

    def test_graduados_2026_no_aborta(self):
        """2 fallos de 142 (1.4%) esta por debajo del umbral: no bloquea."""
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=142, fallos_api=2))

    # ----------------------------------------------------------
    # Limites del umbral
    # ----------------------------------------------------------
    def test_exactamente_en_el_umbral_no_aborta(self):
        """20% exacto no supera el umbral (la regla es estrictamente mayor)."""
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=100, fallos_api=20))

    def test_por_encima_del_umbral_aborta(self):
        msg = evaluar_fallo_masivo(intentos_api=100, fallos_api=21)
        self.assertIsNotNone(msg)
        self.assertIn("21.0%", msg)

    def test_sin_fallos_no_aborta(self):
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=500, fallos_api=0))

    def test_sin_intentos_no_aborta(self):
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=0, fallos_api=0))

    def test_muestra_pequena_no_aplica_el_umbral(self):
        """40% de fallos pero solo 5 intentos: no es significativo, no bloquea."""
        self.assertIsNone(
            evaluar_fallo_masivo(intentos_api=MIN_INTENTOS_UMBRAL - 1, fallos_api=2)
        )

    def test_muestra_minima_si_aplica(self):
        """Con exactamente MIN_INTENTOS_UMBRAL el umbral ya se evalua."""
        self.assertIsNotNone(
            evaluar_fallo_masivo(intentos_api=MIN_INTENTOS_UMBRAL, fallos_api=5)
        )

    # ----------------------------------------------------------
    # Configuracion por entorno
    # ----------------------------------------------------------
    def test_umbral_0_modo_estricto(self):
        """Umbral 0: cualquier fallo por encima de 0% aborta."""
        os.environ["IA_CUALITATIVO_MAX_FALLOS_API_PCT"] = "0"
        self.assertIsNotNone(evaluar_fallo_masivo(intentos_api=100, fallos_api=1))

    def test_umbral_100_desactiva(self):
        os.environ["IA_CUALITATIVO_MAX_FALLOS_API_PCT"] = "100"
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=100, fallos_api=100))

    def test_umbral_invalido_usa_default(self):
        """Un valor no numerico cae al default (20%), no revienta el ETL."""
        os.environ["IA_CUALITATIVO_MAX_FALLOS_API_PCT"] = "no-es-un-numero"
        self.assertIsNotNone(evaluar_fallo_masivo(intentos_api=100, fallos_api=50))
        self.assertIsNone(evaluar_fallo_masivo(intentos_api=100, fallos_api=10))

    # ----------------------------------------------------------
    # Constante compartida con el motor
    # ----------------------------------------------------------
    def test_motivo_fallo_api_es_el_del_placeholder(self):
        """El motivo comparado en el conteo debe ser el que escribe el motor."""
        self.assertEqual(MOTIVO_FALLO_API, "Error de API (todos los motores fallaron)")


if __name__ == "__main__":
    unittest.main()
