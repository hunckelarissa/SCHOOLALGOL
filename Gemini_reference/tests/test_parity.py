"""Паритет интерпретатор vs скомпилированный C."""
import os
import unittest

from c_transpiler import CTranspiler
from module_loader import load_alg_file
from tests.helpers import (
    ROOT, gcc_available, gcc_compile_and_run, interp_stdout, normalize_output, outputs_match,
)


class TestParityPrograms(unittest.TestCase):
    PROGRAMS = [
        "loops.alg",
        "arrays.alg",
        "builtins.alg",
        "format.alg",
        "records.alg",
        "dict.alg",
        "files.alg",
    ]

    def test_parity_suite(self):
        if not gcc_available():
            self.skipTest("gcc не найден")
        programs_dir = os.path.join(ROOT, "tests", "programs")
        if not os.path.isdir(programs_dir):
            self.skipTest("tests/programs не найден")
        for name in self.PROGRAMS:
            alg_path = os.path.join(programs_dir, name)
            if not os.path.isfile(alg_path):
                self.skipTest(f"{name} не найден")
            py_out = normalize_output(interp_stdout(alg_path))
            code = CTranspiler(load_alg_file(alg_path), alg_path).transpile()
            run = gcc_compile_and_run(code)
            self.assertEqual(run.returncode, 0, msg=f"{name}: {run.stderr}")
            c_out = normalize_output(run.stdout)
            self.assertTrue(
                outputs_match(py_out, c_out),
                msg=f"расхождение для {name}\nPython: {py_out}\nC: {c_out}",
            )
