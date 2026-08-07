"""Стресс-тесты (маркер slow). Запуск: pytest -m slow"""
import sys
import time
import unittest

import pytest

from tests.helpers import interp_stdout_from_source


@pytest.mark.slow
class TestStress(unittest.TestCase):
    def test_large_for_loop(self):
        """нц для 1..100000 — завершение за разумное время."""
        source = """
алг основнаяпрограмма
нач
  цел s
  s := 0
  нц для i от 1 до 100000
    s := s + 1
  кц
  вывод s
кон
"""
        t0 = time.perf_counter()
        out = interp_stdout_from_source(source)
        elapsed = time.perf_counter() - t0
        self.assertIn("100000", out)
        self.assertLess(elapsed, 30.0, msg=f"цикл 10^5 занял {elapsed:.1f} с")

    @pytest.mark.slow
    def test_moderate_recursion(self):
        """Рекурсия глубиной ~200 (в пределах лимита Python)."""
        source = """
алг глубина(арг цел n; рез цел r)
нач
  если n <= 0 то
    r := 0
  иначе
    r := 1 + глубина(n - 1)
  все
кон
алг основнаяпрограмма
нач
  вывод глубина(200)
кон
"""
        old = sys.getrecursionlimit()
        sys.setrecursionlimit(2500)
        try:
            out = interp_stdout_from_source(source)
            self.assertIn("200", out)
        finally:
            sys.setrecursionlimit(old)
