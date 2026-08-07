"""Тесты интерпретатора."""
import io
import sys
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import SemanticError
from tests.helpers import interp_stdout_from_source


class TestInterpreter(unittest.TestCase):
    def _run_alg(self, source):
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            Interpreter(tree, "<test>").run()
            return buf.getvalue()
        finally:
            sys.stdout = old

    def test_run_minimal(self):
        out = self._run_alg("""
алг основнаяпрограмма
нач
  вывод 42
кон
""")
        self.assertIn("42", out)

    def test_run_const_and_var(self):
        out = self._run_alg("""
конст N = 10
алг основнаяпрограмма
нач
  цел x
  x := 5
  вывод N
  вывод x
кон
""")
        self.assertIn("10", out)
        self.assertIn("5", out)


class TestInterpreterExtended(unittest.TestCase):
    def test_for_implicit_declare(self):
        out = interp_stdout_from_source("""
алг основнаяпрограмма
нач
  нц для k от 1 до 3
    вывод k
  кц
кон
""")
        self.assertIn("1", out)
        self.assertIn("3", out)

    def test_array_bounds_error(self):
        source = """
алг основнаяпрограмма
нач
  таб цел a[1:2]
  вывод a[5]
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        with self.assertRaises(SemanticError) as ctx:
            Interpreter(tree, "<t>").run()
        self.assertIn("[1..2]", str(ctx.exception))
        self.assertIn("a", str(ctx.exception))

    def test_dict(self):
        out = interp_stdout_from_source("""
алг основнаяпрограмма
нач
  словарь d
  d["x"] := 42
  вывод d["x"]
кон
""")
        self.assertIn("42", out)


class TestComparisonOps(unittest.TestCase):
    def test_neq_lte_gte(self):
        out = interp_stdout_from_source("""
алг основнаяпрограмма
нач
  если 1 <> 2 то
    вывод "neq"
  все
  если 2 <= 2 то
    вывод "lte"
  все
  если 3 >= 2 то
    вывод "gte"
  все
кон
""")
        self.assertIn("neq", out)
        self.assertIn("lte", out)
        self.assertIn("gte", out)


class TestStringEscapes(unittest.TestCase):
    def test_newline_in_string(self):
        out = interp_stdout_from_source(r'''
алг основнаяпрограмма
нач
  лит s
  s := "a\nb"
  вывод s
кон
''')
        self.assertIn("a", out)
        self.assertIn("b", out)


class TestNegative(unittest.TestCase):
    def test_division_by_zero(self):
        with self.assertRaises(SemanticError):
            interp_stdout_from_source("""
алг основнаяпрограмма
нач
  вещ x
  x := 1 / 0
кон
""")

    def test_undefined_variable(self):
        with self.assertRaises(SemanticError):
            interp_stdout_from_source("""
алг основнаяпрограмма
нач
  вывод z
кон
""")

    def test_bad_file_mode(self):
        with self.assertRaises(SemanticError):
            interp_stdout_from_source("""
алг основнаяпрограмма
нач
  файл f
  открыть(f, "x.txt", "плохо")
кон
""")
