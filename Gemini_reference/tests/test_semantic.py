"""Тесты семантики: подсказки, типы, рекурсия."""
import io
import sys
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import SemanticError
from alg_warnings import WarningCollector, AssignTypeWarning
from suggestions import suggest_similar, levenshtein, expand_bilingual_candidates
from tests.helpers import interp_stdout_from_source


class TestSuggestions(unittest.TestCase):
    def test_levenshtein(self):
        self.assertEqual(levenshtein("abc", "abc"), 0)
        self.assertEqual(levenshtein("abc", "abd"), 1)

    def test_suggest_similar(self):
        out = suggest_similar("суммa", ["сумма", "счетчик", "длина"])
        self.assertIn("сумма", out)

    def test_undefined_variable_hint(self):
        source = """
алг основнаяпрограмма
нач
  цел сумма
  вывод сумм
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        with self.assertRaises(SemanticError) as ctx:
            Interpreter(tree, "<test>").run()
        self.assertIn("сумма", str(ctx.exception.hint).lower())


class TestAssignTypes(unittest.TestCase):
    def test_float_to_int_warning(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 3.14
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        wc = WarningCollector(verbose=True)
        Interpreter(tree, "<test>", warnings=wc).run()
        self.assertTrue(any(isinstance(w, AssignTypeWarning) for w in wc.warnings))

    def test_string_to_int_error(self):
        with self.assertRaises(SemanticError):
            interp_stdout_from_source("""
алг основнаяпрограмма
нач
  цел x
  x := "text"
кон
""")

    def test_to_int_cast_no_warning(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := вцел(3.9)
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        wc = WarningCollector()
        Interpreter(tree, "<test>", warnings=wc).run()
        self.assertFalse(any(isinstance(w, AssignTypeWarning) for w in wc.warnings))

    def test_float_to_int_warning_bilingual_labels(self):
        source = """
proc mainprogram
begin
  int x
  x := 3.14
end
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        wc = WarningCollector(verbose=True)
        Interpreter(tree, "<test>", warnings=wc).run()
        warns = [w for w in wc.warnings if isinstance(w, AssignTypeWarning)]
        self.assertEqual(len(warns), 1)
        msg = warns[0].message
        self.assertIn("цел / int", msg)
        self.assertIn("вцел / toint", msg)

    def test_suggest_builtin_alias(self):
        expanded = expand_bilingual_candidates("len", ["длина"])
        self.assertIn("len", expanded)
        self.assertIn("длина", expanded)


class TestRecursionMessage(unittest.TestCase):
    def test_recursion_error_message(self):
        source = """
алг бесконечная
нач
  бесконечная()
кон
алг основнаяпрограмма
нач
  бесконечная()
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(200)
        try:
            with self.assertRaises(SemanticError) as ctx:
                Interpreter(tree, "<test>").run()
            self.assertIn("рекурсии", str(ctx.exception).lower())
        finally:
            sys.setrecursionlimit(old_limit)
