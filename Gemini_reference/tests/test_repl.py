"""Тесты REPL и --keep-cyrillic."""
import os
import subprocess
import sys
import unittest

from lexer import Lexer
from parser import Parser
from c_transpiler import CTranspiler
from tests.helpers import ROOT, run_main_cli


class TestKeepCyrillic(unittest.TestCase):
    def test_transliterate_vs_keep(self):
        src = """
алг Факториал
нач
кон
алг основнаяпрограмма
нач
  вывод 1
кон
"""
        tree = Parser(list(Lexer(src).generate_tokens())).parse()
        c_lat = CTranspiler(tree, "<t>", keep_cyrillic=False).transpile()
        c_cyr = CTranspiler(tree, "<t>", keep_cyrillic=True).transpile()
        self.assertIn("faktorial", c_lat.lower())
        self.assertIn("факториал", c_cyr)

    def test_keep_cyrillic_cli_flag(self):
        source = """
алг Тест
нач
кон
алг основнаяпрограмма
нач
кон
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".alg", delete=False, encoding="utf-8") as f:
            f.write(source)
            alg_path = f.name
        try:
            result = run_main_cli([alg_path, "--transpile", "--keep-cyrillic"], timeout=10)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            c_path = alg_path.replace(".alg", ".c")
            with open(c_path, encoding="utf-8") as fh:
                code = fh.read()
            self.assertIn("тест", code)
        finally:
            os.unlink(alg_path)
            c_path = alg_path.replace(".alg", ".c")
            if os.path.isfile(c_path):
                os.unlink(c_path)

    def test_keep_cyrillic_in_help(self):
        result = run_main_cli(["--help"])
        self.assertIn("--keep-cyrillic", result.stdout)


class TestReplCli(unittest.TestCase):
    def test_repl_in_help(self):
        result = run_main_cli(["--help"])
        self.assertIn("--repl", result.stdout)

    def test_repl_runs_expression(self):
        script = (
            "import sys\n"
            f"sys.path.insert(0, {ROOT!r})\n"
            "from repl import run_repl\n"
            "import io\n"
            "inp = io.StringIO('вывод 99\\nвыход\\n')\n"
            "import builtins\n"
            "builtins.input = lambda p='': inp.readline().rstrip('\\n')\n"
            "run_repl()\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("99", result.stdout)

    def test_repl_en_keywords(self):
        script = (
            "import sys\n"
            f"sys.path.insert(0, {ROOT!r})\n"
            "from repl import run_repl\n"
            "import io\n"
            "inp = io.StringIO('output 42\\nexit\\n')\n"
            "import builtins\n"
            "builtins.input = lambda p='': inp.readline().rstrip('\\n')\n"
            "run_repl(lang='en')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("42", result.stdout)

    def test_lang_en_in_help(self):
        result = run_main_cli(["--help"])
        self.assertIn("--lang", result.stdout)
