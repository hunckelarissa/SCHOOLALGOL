"""Тесты двуязычного синтаксиса RU + EN (v1.1)."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from lexer import Lexer
from parser import Parser
from lang_tokens import TokenType
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from alg_warnings import WarningCollector


def _interp_stdout(source: str) -> str:
    tree = Parser(list(Lexer(source).generate_tokens())).parse()
    warnings = WarningCollector()
    SemanticAnalyzer(tree, "<test>", warnings=warnings).analyze()
    buf = io.StringIO()
    with redirect_stdout(buf):
        Interpreter(tree, "<test>", warnings=warnings).run()
    return buf.getvalue()


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
            [
                TokenType.НЦ,
                TokenType.ДЛЯ,
                TokenType.ID,
                TokenType.ОТ,
                TokenType.NUMBER,
                TokenType.ДО,
                TokenType.NUMBER,
                TokenType.КЦ,
            ],
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
        tree = self._parse(
            """
proc mainprogram
begin
  output "hi"
end
"""
        )
        self.assertEqual(len(tree.declarations), 1)
        self.assertEqual(tree.declarations[0].name, "mainprogram")

    def test_mixed_syntax(self):
        tree = self._parse(
            """
proc mainprogram
begin
  if 1 > 0 then
    output 1
  endif
end
"""
        )
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
        out = _interp_stdout(self.EN_HELLO)
        self.assertIn("bilingual_ok", out)

    def test_ru_en_same_output(self):
        ru = _interp_stdout(self.RU_HELLO)
        en = _interp_stdout(self.EN_HELLO)
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
    def test_len_alias(self):
        out = _interp_stdout(
            """
proc mainprogram
begin
  output len("abc")
end
"""
        )
        self.assertIn("3", out.replace(".0", ""))

    def test_open_read_mode_fails_semantic_on_missing_file(self):
        from errors import SemanticError

        source = """
proc mainprogram
begin
  file f
  open(f, "__no_such_file__.alg", "read")
end
"""
        with self.assertRaises(SemanticError):
            _interp_stdout(source)


class TestBilingualLoops(unittest.TestCase):
    def test_for_loop_english(self):
        out = _interp_stdout(
            """
proc mainprogram
begin
  int s
  s := 0
  loop for i from 1 to 3
    s := s + i
  eloop
  output s
end
"""
        )
        self.assertIn("6", out.replace(".0", ""))


class TestBilingualAst(unittest.TestCase):
    """AST-изоморфизм RU ↔ EN (по образцу Gemini_reference/ast_compare)."""

    PAIRS = [
        (
            """
алг P
нач
  цел x
  x := 1
кон
""",
            """
proc P
begin
  int x
  x := 1
end
""",
        ),
        (
            """
алг P
нач
  если 1 > 0 то
    вывод 1
  все
кон
""",
            """
proc P
begin
  if 1 > 0 then
    output 1
  endif
end
""",
        ),
        (
            """
алг P
нач
  нц для i от 1 до 2
    вывод i
  кц
кон
""",
            """
proc P
begin
  loop for i from 1 to 2
    output i
  eloop
end
""",
        ),
        (
            """
запись Точка
нач
  вещ x, y
кон
алг основнаяпрограмма
нач
  Точка p
  p.x := 1
кон
""",
            """
rec Point
begin
  real x, y
end
proc mainprogram
begin
  Point p
  p.x := 1
end
""",
        ),
    ]

    def _parse(self, source: str):
        return Parser(list(Lexer(source).generate_tokens())).parse()

    def test_handcrafted_pairs_isomorphic(self):
        from ast_compare import ast_shapes_equal

        for ru, en in self.PAIRS:
            with self.subTest(ru=ru.strip()[:24]):
                self.assertTrue(
                    ast_shapes_equal(self._parse(ru), self._parse(en), normalize_bilingual=True),
                )

    def test_example_files_isomorphic(self):
        from ast_compare import ast_shapes_equal

        pairs = [
            ("examples/08_control_flow.alg", "examples/en/08_control_flow.alg"),
            ("examples/09_records.alg", "examples/en/09_records.alg"),
        ]
        for ru_rel, en_rel in pairs:
            ru_path = os.path.join(_root, *ru_rel.split("/"))
            en_path = os.path.join(_root, *en_rel.split("/"))
            if not (os.path.isfile(ru_path) and os.path.isfile(en_path)):
                continue
            with self.subTest(pair=ru_rel):
                with open(ru_path, encoding="utf-8") as f:
                    ru_tree = self._parse(f.read())
                with open(en_path, encoding="utf-8") as f:
                    en_tree = self._parse(f.read())
                self.assertTrue(
                    ast_shapes_equal(ru_tree, en_tree, normalize_bilingual=True),
                    msg=f"AST shape mismatch: {ru_rel} vs {en_rel}",
                )


class TestBilingualExamples(unittest.TestCase):
    def _run_example(self, *parts):
        path = os.path.join(_root, *parts)
        if not os.path.isfile(path):
            self.skipTest("/".join(parts) + " не найден")
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, os.path.join(_root, "main.py"), path],
            cwd=os.path.dirname(path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env=env,
        )

    def test_en_hello_runs_via_cli(self):
        result = self._run_example("examples", "en", "01_hello.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hello", result.stdout)

    def test_en_loops_example(self):
        result = self._run_example("examples", "en", "04_loops.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("15", result.stdout.replace(".0", ""))

    def test_en_files_example(self):
        result = self._run_example("examples", "en", "06_files.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("from file:", result.stdout)

    def test_en_records_example(self):
        result = self._run_example("examples", "en", "09_records.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3.5", result.stdout)

    def test_en_module_example(self):
        result = self._run_example("examples", "en", "10_module.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("120", result.stdout.replace(".0", ""))

    def test_ru_records_example(self):
        result = self._run_example("examples", "09_records.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3.5", result.stdout)

    def test_en_control_flow_example(self):
        result = self._run_example("examples", "en", "08_control_flow.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sum step2 =", result.stdout)
        self.assertIn("-1", result.stdout)

    def test_ru_control_flow_example(self):
        result = self._run_example("examples", "08_control_flow.alg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sum step2 =", result.stdout)
        self.assertIn("-1", result.stdout)


class TestControlFlowKeywords(unittest.TestCase):
    def test_token_pairs(self):
        pairs = [
            ("выход break BREAK", TokenType.ВЫХОД),
            ("продолжить continue CONTINUE", TokenType.ПРОДОЛЖИТЬ),
            ("возврат return RETURN", TokenType.ВОЗВРАТ),
            ("шаг step STEP", TokenType.ШАГ),
        ]
        for source, expected in pairs:
            types = [t.type for t in Lexer(source).generate_tokens() if t.type != TokenType.EOF]
            self.assertEqual(types, [expected] * 3, source)

    def test_en_continue_break_step_run(self):
        out = _interp_stdout(
            """
proc mainprogram
begin
  int i
  loop for i from 1 to 5 step 2
    if i = 3 then
      continue
    endif
    if i = 5 then
      break
    endif
    output i
  eloop
end
"""
        )
        self.assertEqual(out.split(), ["1"])

    def test_ru_en_control_same_output(self):
        ru = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 4
    если i = 2 то
      продолжить
    все
    вывод i
  кц
кон
"""
        en = """
proc mainprogram
begin
  int i
  loop for i from 1 to 4
    if i = 2 then
      continue
    endif
    output i
  eloop
end
"""
        self.assertEqual(_interp_stdout(ru).split(), _interp_stdout(en).split())
        self.assertEqual(_interp_stdout(ru).split(), ["1", "3", "4"])


if __name__ == "__main__":
    unittest.main()
