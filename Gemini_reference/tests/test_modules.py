"""Тесты модулей использовать."""
import io
import os
import sys
import unittest

from interpreter import Interpreter
from errors import SemanticError
from module_loader import load_alg_file
from tests.helpers import ROOT


class TestModules(unittest.TestCase):
    def test_use_loads_constants(self):
        path = os.path.join(ROOT, "tests", "fixtures", "main_use.alg")
        tree = load_alg_file(path)
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            Interpreter(tree, path).run()
        finally:
            sys.stdout = old
        self.assertIn("100", buf.getvalue())

    def test_cyclic_import_error(self):
        path = os.path.join(ROOT, "tests", "fixtures", "cycle_a.alg")
        tree = load_alg_file(path)
        with self.assertRaises(SemanticError) as ctx:
            Interpreter(tree, path).run()
        self.assertIn("Циклический импорт", str(ctx.exception))
        self.assertIn("cycle", str(ctx.exception).lower())
