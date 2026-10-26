"""Tests for UI language (--lang / i18n) and bilingual input contracts."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from i18n import set_lang, t, get_lang, sem
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from alg_warnings import WarningCollector
from builtin_names import resolve_builtin, resolve_file_mode, BUILTIN_ALIASES
from lang_tokens import TokenType, KEYWORDS
from errors import SemanticError

_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _parse(source: str):
    return Parser(list(Lexer(source).generate_tokens())).parse()


class TestI18nHelp(unittest.TestCase):
    def test_help_en(self):
        r = subprocess.run(
            [sys.executable, os.path.join(_root, "main.py"), "--lang", "en", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("Usage:", r.stdout)
        self.assertIn("--lang ru|en", r.stdout)

    def test_help_ru(self):
        r = subprocess.run(
            [sys.executable, os.path.join(_root, "main.py"), "--lang", "ru", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("Использование:", r.stdout)

    def test_semantic_error_prefix_en(self):
        src = """
proc mainprogram
begin
  output undeclared_xyz
end
"""
        with tempfile.NamedTemporaryFile("w", suffix=".alg", delete=False, encoding="utf-8") as f:
            f.write(src)
            path = f.name
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), "--lang", "en", "--check", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Semantic error", r.stderr)
        finally:
            os.unlink(path)

    def test_t_switches(self):
        set_lang("en")
        self.assertIn("Usage", t("usage_line1"))
        set_lang("ru")
        self.assertIn("Использование", t("usage_line1"))

    def test_undefined_body_en(self):
        src = """
proc mainprogram
begin
  output undeclared_xyz
end
"""
        with tempfile.NamedTemporaryFile("w", suffix=".alg", delete=False, encoding="utf-8") as f:
            f.write(src)
            path = f.name
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), "--lang", "en", "--check", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Semantic error", r.stderr)
            self.assertIn("is not defined", r.stderr)
        finally:
            os.unlink(path)

    def test_break_outside_en(self):
        src = """
proc mainprogram
begin
  break
end
"""
        with tempfile.NamedTemporaryFile("w", suffix=".alg", delete=False, encoding="utf-8") as f:
            f.write(src)
            path = f.name
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), "--lang", "en", "--check", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace", env=_ENV,
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("only allowed inside a loop", r.stderr)
        finally:
            os.unlink(path)

    def test_interp_div_zero_en(self):
        src = """
алг основнаяпрограмма
нач
  вывод 1 / 0
кон
"""
        set_lang("en")
        try:
            with self.assertRaises(SemanticError) as ctx:
                Interpreter(_parse(src), "<t>").run()
            self.assertIn("Division by zero", str(ctx.exception))
        finally:
            set_lang("ru")

    def test_sem_arity_en(self):
        set_lang("en")
        try:
            self.assertIn("expects", sem("sem_arity", name="len", expected=1, got=2))
        finally:
            set_lang("ru")

    def test_for_step_zero_en(self):
        src = """
алг основнаяпрограмма
нач
  нц для i от 1 до 10 шаг 0
    вывод i
  кц
кон
"""
        set_lang("en")
        try:
            with self.assertRaises(SemanticError) as ctx:
                Interpreter(_parse(src), "<t>").run()
            self.assertIn("step cannot be zero", str(ctx.exception))
        finally:
            set_lang("ru")

    def test_multi_output_not_file(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  i := 2
  вывод i, "*", 3
кон
"""
        warnings = WarningCollector()
        tree = _parse(src)
        SemanticAnalyzer(tree, "<t>", warnings=warnings).analyze()
        buf = io.StringIO()
        with redirect_stdout(buf):
            Interpreter(tree, "<t>", warnings=warnings).run()
        self.assertEqual(buf.getvalue().strip(), "2*3")


class TestBuiltinAudit(unittest.TestCase):
    def test_every_alias_resolves(self):
        for canon, aliases in BUILTIN_ALIASES.items():
            self.assertEqual(resolve_builtin(canon), canon)
            for a in aliases:
                self.assertEqual(resolve_builtin(a), canon, msg=a)

    def test_sin_cos_ru_canonical(self):
        self.assertEqual(resolve_builtin("sin"), "син")
        self.assertEqual(resolve_builtin("кос"), "кос")
        self.assertEqual(resolve_builtin("cos"), "кос")

    def test_keywords_ru_en_pairs(self):
        # Spot-check critical bilingual tokens exist
        for word in ("продолжить", "continue", "выход", "break", "шаг", "step"):
            self.assertIn(word, KEYWORDS)


class TestBoolInput(unittest.TestCase):
    def _run_with_stdin(self, source: str, stdin: str) -> str:
        tree = _parse(source)
        warnings = WarningCollector()
        SemanticAnalyzer(tree, "<t>", warnings=warnings).analyze()
        buf = io.StringIO()
        with patch("builtins.input", side_effect=stdin.splitlines()), redirect_stdout(buf):
            Interpreter(tree, "<t>", warnings=warnings).run()
        return buf.getvalue()

    def test_input_da_net(self):
        src = """
алг основнаяпрограмма
нач
  лог a, b
  ввод a
  ввод b
  вывод a
  вывод b
кон
"""
        out = self._run_with_stdin(src, "да\nнет\n")
        self.assertEqual(out.split(), ["да", "нет"])

    def test_input_true_false(self):
        src = """
proc mainprogram
begin
  bool a, b
  input a
  input b
  output a
  output b
end
"""
        out = self._run_with_stdin(src, "true\nfalse\n")
        self.assertEqual(out.split(), ["да", "нет"])


class TestFileModes(unittest.TestCase):
    def test_resolve_modes(self):
        self.assertEqual(resolve_file_mode("чтение"), "r")
        self.assertEqual(resolve_file_mode("read"), "r")
        self.assertEqual(resolve_file_mode("запись"), "w")
        self.assertEqual(resolve_file_mode("write"), "w")
        self.assertEqual(resolve_file_mode("дозапись"), "a")
        self.assertEqual(resolve_file_mode("append"), "a")

    def test_open_en_mode_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.txt").replace("\\", "/")
            src = f"""
proc mainprogram
begin
  file f
  int x
  open(f, "{path}", "write")
  output f, 42
  close(f)
  open(f, "{path}", "read")
  input f, x
  close(f)
  output x
end
"""
            tree = _parse(src)
            warnings = WarningCollector()
            SemanticAnalyzer(tree, "<t>", warnings=warnings).analyze()
            buf = io.StringIO()
            with redirect_stdout(buf):
                Interpreter(tree, "<t>", warnings=warnings).run()
            self.assertIn("42", buf.getvalue().replace(".0", ""))


if __name__ == "__main__":
    unittest.main()
