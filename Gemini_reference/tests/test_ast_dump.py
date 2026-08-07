"""Тесты --dump-ast."""
import os
import unittest

from tests.helpers import ROOT, run_main_cli


class TestDumpAst(unittest.TestCase):
    def test_dump_ast_text(self):
        alg = os.path.join(ROOT, "examples", "01_hello.alg")
        if not os.path.isfile(alg):
            self.skipTest("examples/01_hello.alg не найден")
        result = run_main_cli([alg, "--dump-ast"], timeout=10)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Program", result.stdout)
        self.assertIn("ProcDecl", result.stdout)

    def test_dump_ast_json(self):
        alg = os.path.join(ROOT, "examples", "01_hello.alg")
        if not os.path.isfile(alg):
            self.skipTest("examples/01_hello.alg не найден")
        result = run_main_cli([alg, "--dump-ast", "--dump-ast-format", "json"], timeout=10)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('"type": "Program"', result.stdout)

    def test_dump_ast_in_help(self):
        result = run_main_cli(["--help"])
        self.assertIn("--dump-ast", result.stdout)
