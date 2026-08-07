"""Тесты CLI и verbose."""
import os
import tempfile
import unittest

from tests.helpers import ROOT, run_main_cli


class TestVerboseMode(unittest.TestCase):
    def test_verbose_shows_pipeline_stages(self):
        alg = os.path.join(ROOT, "program.alg")
        if not os.path.isfile(alg):
            self.skipTest("program.alg не найден")
        result = run_main_cli([alg, "--verbose"], cwd=ROOT, timeout=15)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        err = result.stderr
        self.assertIn("Лексический анализ", err)
        self.assertIn("Синтаксический анализ", err)
        self.assertIn("Семантический анализ", err)
        self.assertIn("Интерпретация", err)
        self.assertIn("[интерпретатор]", err)

    def test_verbose_does_not_pollute_program_stdout(self):
        source = """
алг основнаяпрограмма
нач
  вывод "только_это"
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            alg_path = f.name
        try:
            result = run_main_cli([alg_path, "--verbose"], timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertIn("только_это", result.stdout)
            self.assertNotIn("[интерпретатор]", result.stdout)
        finally:
            os.unlink(alg_path)


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self):
        result = run_main_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--verbose", result.stdout)
        self.assertIn("--transpile", result.stdout)

    def test_version(self):
        result = run_main_cli(["--version"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("1.1.0", result.stdout.strip())

    def test_trace_flag_in_help(self):
        result = run_main_cli(["--help"])
        self.assertIn("--trace", result.stdout)

    def test_trace_outputs_to_stderr(self):
        source = """
алг основнаяпрограмма
нач
  вывод 1
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            alg_path = f.name
        try:
            result = run_main_cli([alg_path, "--trace"], timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertIn("[трассировка]", result.stderr)
        finally:
            os.unlink(alg_path)

    def test_trace_assign_value(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 42
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            alg_path = f.name
        try:
            result = run_main_cli([alg_path, "--trace"], timeout=10)
            self.assertEqual(result.returncode, 0)
            self.assertIn("x := 42", result.stderr)
        finally:
            os.unlink(alg_path)

    def test_no_args_exits_2(self):
        result = run_main_cli([])
        self.assertEqual(result.returncode, 2)

    def test_missing_file_exits_1(self):
        result = run_main_cli(["nonexistent_file_xyz.alg"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("найден", result.stderr)
