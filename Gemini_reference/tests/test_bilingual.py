"""Тесты двуязычного синтаксиса RU + EN (v1.1)."""
import io
import os
import sys
import unittest

from lexer import Lexer
from parser import Parser
from lang_tokens import TokenType
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from tests.helpers import ROOT, interp_stdout_from_source


class TestBilingualLexer(unittest.TestCase):
    def _types(self, source):
        return [t.type for t in Lexer(source).generate_tokens() if t.type != TokenType.EOF]

    def test_english_keywords(self):
        src = "proc mainprogram begin int x end"
        types = self._types(src)
        self.assertEqual(
            types,
            [TokenType.АЛГ, TokenType.ID, TokenType.НАЧ, TokenType.ЦЕЛ, TokenType.ID, TokenType.КОН],
        )

    def test_loop_eloop(self):
        types = self._types("loop for i from 1 to 3 eloop")
        self.assertEqual(
            types,
            [TokenType.НЦ, TokenType.ДЛЯ, TokenType.ID, TokenType.ОТ, TokenType.NUMBER,
             TokenType.ДО, TokenType.NUMBER, TokenType.КЦ],
        )

    def test_true_false(self):
        types = self._types("true false")
        self.assertEqual(types, [TokenType.ДА, TokenType.НЕТ])

    def test_trueish_not_keyword(self):
        types = self._types("trueish")
        self.assertEqual(types, [TokenType.ID])

    def test_case_insensitive_proc(self):
        types = self._types("PROC BEGIN END")
        self.assertEqual(types[:3], [TokenType.АЛГ, TokenType.НАЧ, TokenType.КОН])


class TestBilingualParser(unittest.TestCase):
    def _parse(self, source):
        return Parser(list(Lexer(source).generate_tokens())).parse()

    def test_english_hello_parses(self):
        tree = self._parse("""
proc mainprogram
begin
  output "hi"
end
""")
        self.assertEqual(len(tree.declarations), 1)
        self.assertEqual(tree.declarations[0].name, "mainprogram")

    def test_mixed_syntax(self):
        tree = self._parse("""
proc mainprogram
begin
  if 1 > 0 then
    output 1
  endif
end
""")
        block = tree.declarations[0].block
        self.assertEqual(len(block.statements), 1)

    def test_parser_bilingual_token_in_error(self):
        from errors import ParserError
        tokens = list(Lexer("proc x").generate_tokens())
        with self.assertRaises(ParserError) as ctx:
            Parser(tokens).parse()
        self.assertIn("нач / begin", str(ctx.exception))


class TestBilingualRun(unittest.TestCase):
    EN_HELLO = """
proc mainprogram
begin
  output "bilingual_ok"
end
"""

    RU_HELLO = """
алг основнаяпрограмма
нач
  вывод "bilingual_ok"
кон
"""

    def test_english_runs(self):
        out = interp_stdout_from_source(self.EN_HELLO)
        self.assertIn("bilingual_ok", out)

    def test_ru_en_same_output(self):
        ru = interp_stdout_from_source(self.RU_HELLO)
        en = interp_stdout_from_source(self.EN_HELLO)
        self.assertEqual(ru.strip(), en.strip())

    def test_mainprogram_semantic(self):
        SemanticAnalyzer(
            Parser(list(Lexer(self.EN_HELLO).generate_tokens())).parse(),
            "<test>",
        ).analyze()

    def test_missing_main_en_fails(self):
        source = """
proc other
begin
end
"""
        with self.assertRaises(Exception):
            SemanticAnalyzer(
                Parser(list(Lexer(source).generate_tokens())).parse(),
                "<test>",
            ).analyze()


class TestBilingualBuiltins(unittest.TestCase):
    def test_open_read_mode_fails_semantic_on_missing_file(self):
        source = """
proc mainprogram
begin
  file f
  open(f, "__no_such_file__.alg", "read")
end
"""
        # Should fail at runtime with SemanticError on open, not parse error
        from errors import SemanticError
        with self.assertRaises(SemanticError):
            interp_stdout_from_source(source)


class TestBilingualLoops(unittest.TestCase):
    def test_for_loop_english(self):
        out = interp_stdout_from_source("""
proc mainprogram
begin
  int s
  s := 0
  loop for i from 1 to 3
    s := s + i
  eloop
  output s
end
""")
        self.assertIn("6", out.replace(".0", ""))


class TestBilingualExamples(unittest.TestCase):
    def test_en_hello_runs_via_cli(self):
        from tests.helpers import run_main_cli
        path = os.path.join(ROOT, "examples", "en", "01_hello.alg")
        result = run_main_cli([path])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hello", result.stdout)

    def test_en_module_example(self):
        from tests.helpers import run_main_cli
        path = os.path.join(ROOT, "examples", "en", "10_module.alg")
        result = run_main_cli([path])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("120", result.stdout.replace(".0", ""))


if __name__ == "__main__":
    unittest.main()
