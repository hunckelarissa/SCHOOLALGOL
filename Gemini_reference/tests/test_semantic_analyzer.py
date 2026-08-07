"""Тесты статического семантического анализатора."""
import unittest

from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from errors import SemanticError


def analyze_source(source: str, *, verbose: bool = False, path: str = "<test>") -> None:
    tokens = list(Lexer(source).generate_tokens())
    tree = Parser(tokens).parse()
    SemanticAnalyzer(tree, path, verbose=verbose).analyze()


class TestSemanticAnalyzer(unittest.TestCase):
    def test_undefined_variable_before_run(self):
        source = """
алг основнаяпрограмма
нач
  вывод несуществующая
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("не определена", str(ctx.exception).lower())

    def test_wrong_arity_user_procedure(self):
        source = """
алг плюс(арг цел a, цел b)
нач
кон
алг основнаяпрограмма
нач
  плюс(1)
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("аргументов", str(ctx.exception).lower())

    def test_wrong_arity_builtin(self):
        source = """
алг основнаяпрограмма
нач
  вывод корень()
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("корень", str(ctx.exception))

    def test_missing_main_program(self):
        source = """
алг другая
нач
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("основнаяпрограмма", str(ctx.exception).lower())

    def test_unknown_type(self):
        source = """
алг основнаяпрограмма
нач
  несуществующийтип x
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("неизвестный тип", str(ctx.exception).lower())

    def test_valid_program_passes(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 1
  вывод x
кон
"""
        analyze_source(source)

    def test_verbose_symbol_table(self):
        import io
        import sys

        source = """
алг основнаяпрограмма
нач
  цел x
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            SemanticAnalyzer(tree, "<test>", verbose=True).analyze()
        finally:
            sys.stderr = old
        err = buf.getvalue()
        self.assertIn("[семантика]", err)
        self.assertIn("таблица символов", err)
        self.assertIn("процедура основнаяпрограмма", err)

    def test_array_bounds_static(self):
        source = """
алг основнаяпрограмма
нач
  таб цел a[5:1]
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("индекс", str(ctx.exception).lower())

    def test_print_requires_file_type(self):
        source = """
алг основнаяпрограмма
нач
  цел f
  вывод f, "x"
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            analyze_source(source)
        self.assertIn("файл", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
