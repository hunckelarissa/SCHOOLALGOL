"""Тесты встроенных функций (P2-06)."""
import io
import math
import sys
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import SemanticError
from tests.helpers import interp_stdout_from_source


def _run_expr(source: str) -> str:
    return interp_stdout_from_source(source).strip()


def _run_raises(source: str):
    tokens = list(Lexer(source).generate_tokens())
    tree = Parser(tokens).parse()
    Interpreter(tree, "<test>").run()


class TestBuiltins(unittest.TestCase):
    def test_sqrt(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод корень(9)
кон
""")
        self.assertIn("3", out)

    def test_abs(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод модуль(-7)
кон
""")
        self.assertIn("7", out)

    def test_rand(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вещ r
  r := случ()
  если r >= 0 то
    вывод "ok"
  все
кон
""")
        self.assertIn("ok", out)

    def test_randint(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  цел x
  x := случцел(1, 3)
  если x >= 1 то
    вывод "ok"
  все
кон
""")
        self.assertIn("ok", out)

    def test_len(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод длина("hello")
кон
""")
        self.assertIn("5", out)

    def test_substr(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод подстрока("abcdef", 2, 3)
кон
""")
        self.assertIn("bcd", out)

    def test_upper_lower(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод вверх("abc")
  вывод вниз("XYZ")
кон
""")
        self.assertIn("ABC", out)
        self.assertIn("xyz", out)

    def test_to_int_float_str(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  вывод вцел(3.7)
  вывод ввещ("2.5")
  вывод встроку(42)
кон
""")
        self.assertIn("3", out)
        self.assertIn("2.5", out)
        self.assertIn("42", out)

    def test_eof_and_file_ops(self):
        out = _run_expr("""
алг основнаяпрограмма
нач
  файл f
  открыть(f, "builtin_eof_test.tmp", "запись")
  вывод f, "line1"
  закрыть(f)
  открыть(f, "builtin_eof_test.tmp", "чтение")
  если конецфайла(f) то
    вывод "empty"
  иначе
    вывод "data"
  все
  закрыть(f)
кон
""")
        self.assertIn("data", out)

    def test_wrong_arity(self):
        with self.assertRaises(SemanticError):
            _run_raises("""
алг основнаяпрограмма
нач
  вывод корень(1, 2)
кон
""")

    def test_sqrt_negative(self):
        with self.assertRaises(SemanticError):
            _run_raises("""
алг основнаяпрограмма
нач
  вывод корень(-1)
кон
""")
