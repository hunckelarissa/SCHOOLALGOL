"""Тесты предупреждений."""
import io
import os
import sys
import tempfile
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from alg_warnings import WarningCollector, RedefinitionWarning
from tests.helpers import run_main_cli


class TestWarnings(unittest.TestCase):
    def test_redefinition_warning(self):
        source = """
алг дубль
нач
кон
алг дубль
нач
кон
алг основнаяпрограмма
нач
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        wc = WarningCollector(verbose=True)
        interp = Interpreter(tree, "<test>", warnings=wc)
        stderr_buf = io.StringIO()
        old_err = sys.stderr
        sys.stderr = stderr_buf
        try:
            interp.run()
        finally:
            sys.stderr = old_err
        self.assertGreaterEqual(wc.count, 1)
        self.assertTrue(any(isinstance(w, RedefinitionWarning) for w in wc.warnings))

    def test_warning_count_increments(self):
        source = """
алг дубль
нач
кон
алг дубль
нач
кон
алг основнаяпрограмма
нач
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        wc = WarningCollector()
        Interpreter(tree, "<test>", warnings=wc).run()
        self.assertEqual(wc.count, 1)

    def test_warnings_as_errors_exit_code(self):
        source = """
алг x
нач
кон
алг x
нач
кон
алг основнаяпрограмма
нач
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            alg_path = f.name
        try:
            result = run_main_cli([alg_path, "--warnings-as-errors"], timeout=10)
            self.assertEqual(result.returncode, 3, msg=result.stderr)
        finally:
            os.unlink(alg_path)
