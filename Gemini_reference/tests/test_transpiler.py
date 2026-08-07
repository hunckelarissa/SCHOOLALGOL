"""Тесты транспилятора и интеграции C."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from lexer import Lexer
from parser import Parser
from c_transpiler import CTranspiler
from module_loader import load_alg_file
from tests.helpers import ROOT, run_main_cli, interp_stdout, normalize_output, outputs_match, gcc_available


class TestModuleLoader(unittest.TestCase):
    def test_load_alg_returns_program(self):
        program_alg = os.path.join(ROOT, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        tree = load_alg_file(program_alg)
        self.assertTrue(len(tree.declarations) >= 1)
        names = [d.name for d in tree.declarations if hasattr(d, "name")]
        self.assertIn("основнаяпрограмма", names)


class TestTranspilerIntegration(unittest.TestCase):
    def test_transpile_produces_c_file(self):
        program_alg = os.path.join(ROOT, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        tree = load_alg_file(program_alg)
        c_code = CTranspiler(tree, program_alg).transpile()
        self.assertIn("int main()", c_code)
        self.assertIn("faktorial", c_code)
        self.assertIn("str_concat", c_code)

    def test_main_transpile_cli_creates_c(self):
        program_alg = os.path.join(ROOT, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        with tempfile.TemporaryDirectory() as tmp:
            out_c = os.path.join(tmp, "program.c")
            alg_copy = os.path.join(tmp, "program.alg")
            utils_src = os.path.join(ROOT, "utils.alg")
            with open(program_alg, encoding="utf-8") as f:
                with open(alg_copy, "w", encoding="utf-8") as w:
                    w.write(f.read())
            if os.path.isfile(utils_src):
                shutil.copy(utils_src, os.path.join(tmp, "utils.alg"))
            result = subprocess.run(
                [sys.executable, os.path.join(ROOT, "main.py"), alg_copy, "--transpile"],
                cwd=tmp, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(os.path.isfile(out_c))
            with open(out_c, encoding="utf-8") as f:
                self.assertIn("int main()", f.read())


class TestTranspilerCompileRun(unittest.TestCase):
    def test_transpile_compile_run(self):
        program_alg = os.path.join(ROOT, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        if not gcc_available():
            self.skipTest("gcc не найден")
        with tempfile.TemporaryDirectory() as tmp:
            out_c = os.path.join(tmp, "program.c")
            out_exe = os.path.join(tmp, "program.exe" if sys.platform == "win32" else "program")
            alg_copy = os.path.join(tmp, "program.alg")
            utils_src = os.path.join(ROOT, "utils.alg")
            with open(program_alg, encoding="utf-8") as f:
                with open(alg_copy, "w", encoding="utf-8") as w:
                    w.write(f.read())
            if os.path.isfile(utils_src):
                shutil.copy(utils_src, os.path.join(tmp, "utils.alg"))
            result = subprocess.run(
                [sys.executable, os.path.join(ROOT, "main.py"), alg_copy, "--transpile"],
                cwd=tmp, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            comp = subprocess.run(
                ["gcc", "-o", out_exe, out_c, "-lm"],
                cwd=tmp, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)
            run_result = subprocess.run([out_exe], cwd=tmp, capture_output=True, text=True, timeout=10)
            self.assertEqual(run_result.returncode, 0)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "report.txt")))


class TestTranspilerFeatures(unittest.TestCase):
    def test_neq_in_c(self):
        src = """
алг основнаяпрограмма
нач
  если 1 <> 2 то
    вывод 1
  все
кон
"""
        c = CTranspiler(Parser(list(Lexer(src).generate_tokens())).parse(), "<t>").transpile()
        self.assertIn("!=", c)

    def test_string_escape_in_c(self):
        src = r'''
алг основнаяпрограмма
нач
  вывод "a\nb"
кон
'''
        c = CTranspiler(Parser(list(Lexer(src).generate_tokens())).parse(), "<t>").transpile()
        self.assertIn("\\n", c)

    def test_assign_lit_frees_old_buffer(self):
        src = """
алг основнаяпрограмма
нач
  лит s
  s := "a"
  s := s + "b"
кон
"""
        c = CTranspiler(Parser(list(Lexer(src).generate_tokens())).parse(), "<t>").transpile()
        self.assertIn("free(", c)

    def test_member_access_generates_field(self):
        src = """
запись T
нач
  цел x
кон
алг основнаяпрограмма
нач
  T v
  v.x := 1
кон
"""
        c = CTranspiler(Parser(list(Lexer(src).generate_tokens())).parse(), "<t>").transpile()
        self.assertIn("v.x", c)
        self.assertIn("v.x = 1", c)

    def test_array_offset_in_c(self):
        src = """
алг основнаяпрограмма
нач
  таб цел a[0:1]
  a[0] := 7
кон
"""
        c = CTranspiler(Parser(list(Lexer(src).generate_tokens())).parse(), "<t>").transpile()
        self.assertIn("[((int)0) - 0]", c)


class TestConcatAlg(unittest.TestCase):
    def test_concat_interpreter(self):
        path = os.path.join(ROOT, "test_concat.alg")
        if not os.path.isfile(path):
            self.skipTest("test_concat.alg не найден")
        out = interp_stdout(path)
        self.assertIn("Hello", out)
        self.assertIn("World", out)

    def test_concat_c_parity(self):
        path = os.path.join(ROOT, "test_concat.alg")
        if not os.path.isfile(path):
            self.skipTest("test_concat.alg не найден")
        if not gcc_available():
            self.skipTest("gcc не найден")
        py_out = normalize_output(interp_stdout(path))
        with tempfile.TemporaryDirectory() as tmp:
            c_path = os.path.join(tmp, "out.c")
            exe = os.path.join(tmp, "out.exe" if sys.platform == "win32" else "out")
            code = CTranspiler(load_alg_file(path), path).transpile()
            with open(c_path, "w", encoding="utf-8") as f:
                f.write(code)
            comp = subprocess.run(["gcc", "-o", exe, c_path, "-lm"], capture_output=True, text=True, timeout=30)
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)
            run = subprocess.run(
                [exe], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            )
            self.assertTrue(outputs_match(py_out, normalize_output(run.stdout)))


class TestTranspilerMemoryWarnings(unittest.TestCase):
    def _transpile(self, source: str, *, verbose: bool = False):
        from alg_warnings import WarningCollector, MemoryLeakWarning

        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        wc = WarningCollector(verbose=verbose)
        CTranspiler(tree, "<test>", verbose=verbose, warnings=wc).transpile()
        return wc

    def test_nested_concat_emits_warning(self):
        wc = self._transpile("""
алг основнаяпрограмма
нач
  лит a
  лит b
  a := "Hello"
  b := "World"
  вывод a + " " + b
кон
""")
        from alg_warnings import MemoryLeakWarning
        leaks = [w for w in wc.warnings if isinstance(w, MemoryLeakWarning)]
        self.assertGreaterEqual(len(leaks), 1)
        self.assertIn("цепочка", leaks[0].message)

    def test_simple_concat_no_nested_warning(self):
        wc = self._transpile("""
алг основнаяпрограмма
нач
  лит a
  a := "x"
  вывод a + "y"
кон
""")
        from alg_warnings import MemoryLeakWarning
        nested = [
            w for w in wc.warnings
            if isinstance(w, MemoryLeakWarning) and "цепочка" in w.message
        ]
        self.assertEqual(len(nested), 0)

    def test_verbose_logs_leak_detail(self):
        import io
        import sys

        source = """
алг основнаяпрограмма
нач
  лит a
  a := "x"
  вывод a + " " + a
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            from alg_warnings import WarningCollector
            CTranspiler(tree, "<test>", verbose=True, warnings=WarningCollector(verbose=True)).transpile()
        finally:
            sys.stderr = old
        self.assertIn("утечка памяти", buf.getvalue())
