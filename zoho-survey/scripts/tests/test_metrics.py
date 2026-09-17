"""
Tests — lib/metrics.py (Fase 9)

Valida cálculos NPS y CSAT con casos normales, edge cases y casos vacíos.
Funciones puras sin dependencias externas.
"""
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from lib.metrics import calc_nps, calc_csat, calc_promedio_ponderado


class TestCalcNPS(unittest.TestCase):
    """Tests para calc_nps(promotores, pasivos, detractores)."""

    def test_nps_solo_promotores(self):
        """100% promotores → NPS = 100."""
        self.assertEqual(calc_nps(100, 0, 0), 100.0)

    def test_nps_solo_detractores(self):
        """100% detractores → NPS = -100."""
        self.assertEqual(calc_nps(0, 0, 100), -100.0)

    def test_nps_solo_pasivos(self):
        """100% pasivos → NPS = 0."""
        self.assertEqual(calc_nps(0, 100, 0), 0.0)

    def test_nps_balanceado(self):
        """Igual promotores que detractores → NPS = 0."""
        self.assertEqual(calc_nps(50, 0, 50), 0.0)

    def test_nps_caso_normal(self):
        """3231 promotores, 855 pasivos, 153 detractores → ((3231-153)/4239)*100."""
        result = calc_nps(3231, 855, 153)
        expected = round(((3231 - 153) / 4239) * 100, 2)
        self.assertEqual(result, expected)

    def test_nps_total_cero(self):
        """Sin respuestas (total=0) → NPS = 0 (evitar división por cero)."""
        self.assertEqual(calc_nps(0, 0, 0), 0.0)

    def test_nps_rango_valido(self):
        """NPS siempre debe estar entre -100 y 100."""
        for p in range(0, 101, 10):
            for d in range(0, 101 - p, 10):
                pa = 100 - p - d
                nps = calc_nps(p, pa, d)
                self.assertGreaterEqual(nps, -100.0)
                self.assertLessEqual(nps, 100.0)

    def test_nps_precison_2_decimales(self):
        """El resultado debe redondearse a 2 decimales."""
        result = calc_nps(7, 3, 5)
        # Verificar que no tiene más de 2 decimales
        self.assertEqual(round(result, 2), result)


class TestCalcCSAT(unittest.TestCase):
    """Tests para calc_csat(t3b, total)."""

    def test_csat_100_porciento(self):
        """Todos T3B → CSAT = 100."""
        self.assertEqual(calc_csat(100, 100), 100.0)

    def test_csat_0_porciento(self):
        """Ninguno T3B → CSAT = 0."""
        self.assertEqual(calc_csat(0, 100), 0.0)

    def test_csat_caso_normal(self):
        """4148 T3B de 4239 total → (4148/4239)*100."""
        result = calc_csat(4148, 4239)
        expected = round((4148 / 4239) * 100, 2)
        self.assertEqual(result, expected)

    def test_csat_total_cero(self):
        """Sin respuestas → CSAT = 0 (evitar división por cero)."""
        self.assertEqual(calc_csat(0, 0), 0.0)

    def test_csat_rango_valido(self):
        """CSAT siempre debe estar entre 0 y 100."""
        for t3b in range(0, 101, 10):
            for total in range(t3b, 101, 10):
                if total == 0:
                    continue
                csat = calc_csat(t3b, total)
                self.assertGreaterEqual(csat, 0.0)
                self.assertLessEqual(csat, 100.0)

    def test_csat_t3b_mayor_que_total(self):
        """Si t3b > total (caso anómalo), el cálculo puede dar >100.
        Esto es esperado: la función no valida entrada, solo calcula."""
        result = calc_csat(150, 100)
        self.assertEqual(result, 150.0)

    def test_csat_precision_2_decimales(self):
        result = calc_csat(1, 3)
        self.assertEqual(round(result, 2), result)


class TestMetricasDeterminismo(unittest.TestCase):
    """Las funciones puras deben ser deterministas."""

    def test_nps_determinismo(self):
        r1 = calc_nps(3231, 855, 153)
        r2 = calc_nps(3231, 855, 153)
        self.assertEqual(r1, r2)

    def test_csat_determinismo(self):
        r1 = calc_csat(4148, 4239)
        r2 = calc_csat(4148, 4239)
        self.assertEqual(r1, r2)


class TestCalcPromedioPonderado(unittest.TestCase):
    """Tests para calc_promedio_ponderado(counts, weights, max_scale)."""

    def test_ponderado_caso_real_2026_1(self):
        # 1806, 1281, 1061, 75, 16 → 82.58 % (metodología validada)
        counts = [1806, 1281, 1061, 75, 16]
        result = calc_promedio_ponderado(counts, [5, 4, 3, 2, 1], 5)
        self.assertAlmostEqual(result, 82.5810, places=3)

    def test_ponderado_todos_maximos(self):
        # Todas las respuestas en el nivel de peso máximo → 100 %.
        self.assertEqual(calc_promedio_ponderado([100, 0, 0, 0, 0], [5, 4, 3, 2, 1], 5), 100.0)

    def test_ponderado_todos_minimos(self):
        # Todas las respuestas en el nivel de peso mínimo → 20 % (peso 1 / escala 5 * 100).
        self.assertEqual(calc_promedio_ponderado([0, 0, 0, 0, 100], [5, 4, 3, 2, 1], 5), 20.0)

    def test_ponderado_total_cero(self):
        # Sin respuestas → 0 (evitar división por cero).
        self.assertEqual(calc_promedio_ponderado([0, 0, 0, 0, 0], [5, 4, 3, 2, 1], 5), 0.0)

    def test_ponderado_no_redondea_internamente(self):
        # El resultado conserva precisión completa (no se trunca a 2 decimales).
        result = calc_promedio_ponderado([1806, 1281, 1061, 75, 16], [5, 4, 3, 2, 1], 5)
        self.assertNotEqual(round(result, 2), result)

    def test_ponderado_rango_valido(self):
        # El resultado siempre debe estar entre 0 y 100.
        for c0 in range(0, 101, 20):
            for c4 in range(0, 101 - c0, 20):
                counts = [c0, 0, 0, 0, c4]
                p = calc_promedio_ponderado(counts, [5, 4, 3, 2, 1], 5)
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 100.0)


class TestT2BReutilizaCalcCsat(unittest.TestCase):
    """T2B reutiliza calc_csat (misma fórmula de box score, distinto subset)."""

    def test_t2b_menor_o_igual_que_t3b(self):
        # Invariante de monotonía: t2b <= t3b para cualquier distribución.
        counts = [1806, 1281, 1061, 75, 16]
        total = sum(counts)
        t3b = counts[0] + counts[1] + counts[2]
        t2b = counts[0] + counts[1]
        self.assertLessEqual(calc_csat(t2b, total), calc_csat(t3b, total))

    def test_t2b_caso_real(self):
        # 3087 de 4239 → 72.82 %
        self.assertEqual(calc_csat(3087, 4239), 72.82)


if __name__ == '__main__':
    unittest.main()
