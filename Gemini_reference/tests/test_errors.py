"""Тесты форматирования ошибок."""
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import SemanticError, ParserError, format_error


class TestErrorFormatting(unittest.TestCase):
    def test_semantic_error_has_hint(self):
        source = """
алг основнаяпрограмма
нач
  вывод несуществующая
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        interp = Interpreter(tree, "<test>")
        with self.assertRaises(SemanticError) as ctx:
            interp.run()
        formatted = format_error(ctx.exception, source)
        self.assertIn("Подсказка:", formatted)

    def test_parser_error_has_context(self):
        tokens = list(Lexer("алг x").generate_tokens())
        with self.assertRaises(ParserError) as ctx:
            Parser(tokens).parse()
        self.assertIn("Контекст:", str(ctx.exception))
