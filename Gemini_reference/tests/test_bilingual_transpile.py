"""Транспиляция EN-синтаксиса в валидный C."""
import os
import unittest

from lexer import Lexer
from parser import Parser
from c_transpiler import CTranspiler
from module_loader import load_alg_file
from tests.helpers import ROOT, gcc_available, gcc_compile_and_run, interp_stdout, normalize_output, outputs_match


class TestBilingualTranspile(unittest.TestCase):
    PROGRAMS = [
        "loops.alg",
        "builtins.alg",
        "records.alg",
        "dict.alg",
    ]

    def test_en_transpile_main_comment(self):
        source = """
proc mainprogram
begin
  output 1
end
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        code = CTranspiler(tree, "<test>").transpile()
        self.assertIn("// alg: mainprogram (основнаяпрограмма)", code)

    def test_ru_transpile_main_comment(self):
        source = """
алг основнаяпрограмма
нач
  вывод 1
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        code = CTranspiler(tree, "<test>").transpile()
        self.assertIn("// alg: основнаяпрограмма (mainprogram)", code)

    def test_en_transpile_compiles(self):
        if not gcc_available():
            self.skipTest("gcc не найден")
        en_dir = os.path.join(ROOT, "tests", "programs", "en")
        for name in self.PROGRAMS:
            alg_path = os.path.join(en_dir, name)
            with self.subTest(name=name):
                py_out = normalize_output(interp_stdout(alg_path))
                code = CTranspiler(load_alg_file(alg_path), alg_path).transpile()
                self.assertIn("int main(", code)
                run = gcc_compile_and_run(code)
                self.assertEqual(run.returncode, 0, msg=run.stderr)
                c_out = normalize_output(run.stdout)
                self.assertTrue(outputs_match(py_out, c_out), msg=f"{name}\nPy: {py_out}\nC: {c_out}")


if __name__ == "__main__":
    unittest.main()
