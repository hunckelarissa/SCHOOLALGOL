"""Тесты файлового ввода-вывода и конецфайла."""
import io
import os
import sys
import tempfile
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import SemanticError
from tests.helpers import ROOT, interp_stdout_from_source, run_main_cli


class TestFileIO(unittest.TestCase):
    def test_write_read_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.txt").replace("\\", "\\\\")
            out = interp_stdout_from_source(f'''
алг основнаяпрограмма
нач
  файл f
  лит s
  открыть(f, "{path}", "запись")
  вывод f, "alpha"
  вывод f, "beta"
  закрыть(f)
  открыть(f, "{path}", "чтение")
  ввод f, s
  вывод s
  закрыть(f)
кон
''')
            self.assertIn("alpha", out)

    def test_eof_while_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "lines.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("10\n20\n")
            path_alg = path.replace("\\", "\\\\")
            out = interp_stdout_from_source(f'''
алг основнаяпрограмма
нач
  файл f
  вещ v
  открыть(f, "{path_alg}", "чтение")
  нц пока не конецфайла(f)
    ввод f, v
    вывод v
  кц
  закрыть(f)
кон
''')
            self.assertIn("10", out)
            self.assertIn("20", out)

    def test_eof_at_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.txt")
            open(path, "w", encoding="utf-8").close()
            path_alg = path.replace("\\", "\\\\")
            out = interp_stdout_from_source(f'''
алг основнаяпрограмма
нач
  файл f
  открыть(f, "{path_alg}", "чтение")
  если конецфайла(f) то
    вывод "eof_ok"
  иначе
    вывод "has_data"
  все
  закрыть(f)
кон
''')
            self.assertIn("eof_ok", out)

    def test_console_and_file_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.txt")
            path_alg = path.replace("\\", "\\\\")
            out = interp_stdout_from_source(f'''
алг основнаяпрограмма
нач
  файл f
  открыть(f, "{path_alg}", "запись")
  вывод "console"
  вывод f, "file_only"
  закрыть(f)
кон
''')
            self.assertIn("console", out)
            with open(path, encoding="utf-8") as fh:
                self.assertIn("file_only", fh.read())

    def test_eof_verbose_logs_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "one.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("5\n")
            path_alg = path.replace("\\", "\\\\")
            source = f'''
алг основнаяпрограмма
нач
  файл f
  вещ v
  открыть(f, "{path_alg}", "чтение")
  ввод f, v
  ввод f, v
  закрыть(f)
кон
'''
            with tempfile.NamedTemporaryFile(mode="w", suffix=".alg", delete=False, encoding="utf-8") as af:
                af.write(source)
                alg_path = af.name
            try:
                result = run_main_cli([alg_path, "--verbose"], timeout=10)
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIn("EOF", result.stderr)
            finally:
                os.unlink(alg_path)


class TestFileIONegative(unittest.TestCase):
    def test_open_missing_file_informative(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "no_such_file_xyz.alg.txt")
            path_alg = missing.replace("\\", "\\\\")
            with self.assertRaises(SemanticError) as ctx:
                interp_stdout_from_source(f'''
алг основнаяпрограмма
нач
  файл f
  открыть(f, "{path_alg}", "чтение")
кон
''')
            msg = str(ctx.exception)
            self.assertIn("Не удалось открыть", msg)
            self.assertIn("no_such_file", msg.lower())
