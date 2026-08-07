"""Паритет RU ↔ EN: одинаковый stdout и (при наличии gcc) интерпретатор vs C для EN."""
import os
import unittest

from c_transpiler import CTranspiler
from module_loader import load_alg_file
from tests.helpers import (
    ROOT, gcc_available, gcc_compile_and_run, interp_stdout, normalize_output, outputs_match,
)

PROGRAMS = [
    "loops.alg",
    "arrays.alg",
    "builtins.alg",
    "format.alg",
    "records.alg",
    "dict.alg",
    "files.alg",
]


class TestBilingualParity(unittest.TestCase):
    def test_ru_en_interp_same_output(self):
        ru_dir = os.path.join(ROOT, "tests", "programs")
        en_dir = os.path.join(ru_dir, "en")
        for name in PROGRAMS:
            ru_path = os.path.join(ru_dir, name)
            en_path = os.path.join(en_dir, name)
            with self.subTest(name=name):
                ru_out = normalize_output(interp_stdout(ru_path))
                en_out = normalize_output(interp_stdout(en_path))
                self.assertEqual(ru_out, en_out, msg=f"RU/EN mismatch for {name}")

    def test_en_interp_vs_gcc(self):
        if not gcc_available():
            self.skipTest("gcc не найден")
        en_dir = os.path.join(ROOT, "tests", "programs", "en")
        for name in PROGRAMS:
            alg_path = os.path.join(en_dir, name)
            with self.subTest(name=name):
                py_out = normalize_output(interp_stdout(alg_path))
                code = CTranspiler(load_alg_file(alg_path), alg_path).transpile()
                run = gcc_compile_and_run(code)
                self.assertEqual(run.returncode, 0, msg=run.stderr)
                c_out = normalize_output(run.stdout)
                self.assertTrue(
                    outputs_match(py_out, c_out),
                    msg=f"EN parity {name}\nPy: {py_out}\nC: {c_out}",
                )


if __name__ == "__main__":
    unittest.main()
