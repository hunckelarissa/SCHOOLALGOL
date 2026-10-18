"""Тесты B7 (module_loader) и B8 (размер массива-параметра в C)."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from c_transpiler import CTranspiler
from module_loader import (
    CyclicImportError,
    ModuleFileNotFoundError,
    ModuleLoadTracker,
    open_module,
    resolve_module_path,
)
from errors import SemanticError
from alg_warnings import WarningCollector

_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _parse(source: str):
    return Parser(list(Lexer(source).generate_tokens())).parse()


def _run(source: str) -> str:
    tree = _parse(source)
    warnings = WarningCollector()
    SemanticAnalyzer(tree, "<test>", warnings=warnings).analyze()
    buf = io.StringIO()
    with redirect_stdout(buf):
        Interpreter(tree, "<test>", warnings=warnings).run()
    return buf.getvalue()


def _gcc_available() -> bool:
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, timeout=5, check=False)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _compile_and_run(source: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        alg = os.path.join(tmp, "prog.alg")
        c_file = os.path.join(tmp, "prog.c")
        exe = os.path.join(tmp, "prog.exe" if sys.platform == "win32" else "prog")
        with open(alg, "w", encoding="utf-8") as f:
            f.write(source)
        r = subprocess.run(
            [sys.executable, os.path.join(_root, "main.py"), alg, "--transpile"],
            cwd=tmp, capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace", env=_ENV,
        )
        if r.returncode != 0:
            raise AssertionError(r.stderr or r.stdout)
        comp = subprocess.run(
            ["gcc", "-o", exe, c_file, "-lm"],
            cwd=tmp, capture_output=True, text=True, timeout=30,
        )
        if comp.returncode != 0:
            with open(c_file, encoding="utf-8") as f:
                raise AssertionError(comp.stderr + "\n" + f.read())
        run = subprocess.run(
            [exe], cwd=tmp, capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        if run.returncode != 0:
            raise AssertionError(run.stderr)
        return run.stdout


class TestModuleLoader(unittest.TestCase):
    def test_resolve_relative(self):
        base = os.path.join(_root, "program.alg")
        path = resolve_module_path(base, "utils.alg")
        self.assertTrue(path.endswith("utils.alg"))
        self.assertTrue(os.path.isabs(path))

    def test_open_module_ok(self):
        tracker = ModuleLoadTracker()
        base = os.path.join(_root, "program.alg")
        opened = open_module(tracker, base, "utils.alg")
        self.assertIsNotNone(opened)
        path, ast = opened
        self.assertTrue(os.path.isfile(path))
        self.assertTrue(ast.declarations)
        tracker.leave(path)
        # повтор — no-op
        self.assertIsNone(open_module(tracker, base, "utils.alg"))

    def test_open_module_missing(self):
        tracker = ModuleLoadTracker()
        with self.assertRaises(ModuleFileNotFoundError):
            open_module(tracker, os.path.join(_root, "program.alg"), "no_such_mod.alg")

    def test_cyclic_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.alg")
            b = os.path.join(tmp, "b.alg")
            with open(a, "w", encoding="utf-8") as f:
                f.write('использовать "b.alg"\nалг основнаяпрограмма\nнач\nкон\n')
            with open(b, "w", encoding="utf-8") as f:
                f.write('использовать "a.alg"\nалг П\nнач\nкон\n')
            with self.assertRaises(SemanticError) as ctx:
                SemanticAnalyzer(_parse(open(a, encoding="utf-8").read()), a).analyze()
            self.assertIn("Циклический", str(ctx.exception))


class TestArrayParamSize(unittest.TestCase):
    SRC = """
алг Сумма(арг таб цел a; рез цел s)
нач
  цел i, n
  n := размер(a)
  s := 0
  нц для i от 1 до n
    s := s + a[i]
  кц
кон
алг основнаяпрограмма
нач
  таб цел data[1:3]
  data[1] := 10
  data[2] := 20
  data[3] := 30
  вывод размер(data)
  вывод Сумма(data)
кон
"""

    def test_interpreter(self):
        self.assertEqual(_run(self.SRC).split(), ["3", "60"])

    def test_c_signature_has_len(self):
        c = CTranspiler(_parse(self.SRC), "t.alg").transpile()
        self.assertIn("a_len", c)
        self.assertIn("a_off", c)
        self.assertIn("summa(data, 3, 1)", c)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity(self):
        expected = ["3", "60"]
        self.assertEqual(_run(self.SRC).split(), expected)
        self.assertEqual(_compile_and_run(self.SRC).split(), expected)


if __name__ == "__main__":
    unittest.main()
