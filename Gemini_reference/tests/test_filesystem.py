"""Тесты файловой системы (без sandbox)."""
import os
import tempfile
import unittest

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from tests.helpers import ROOT, run_main_cli


class TestFilesystemAccess(unittest.TestCase):
    def test_absolute_path_write_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "deep", "data.txt")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            abs_path = os.path.abspath(target).replace("\\", "\\\\")
            source = f'''
алг основнаяпрограмма
нач
  файл f
  лит путь
  путь := "{abs_path}"
  открыть(f, путь, "запись")
  вывод f, "sandbox_test_ok"
  закрыть(f)
кон
'''
            tokens = list(Lexer(source).generate_tokens())
            tree = Parser(tokens).parse()
            interp = Interpreter(tree, "<test>")
            interp.run()
            self.assertTrue(os.path.isfile(target))
            with open(target, encoding="utf-8") as fh:
                self.assertIn("sandbox_test_ok", fh.read())

    def test_open_outside_project_directory(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as alg_f:
            out_file = os.path.join(tempfile.gettempdir(), "gemini_fs_test_out.txt")
            if os.path.isfile(out_file):
                os.unlink(out_file)
            path_for_alg = out_file.replace("\\", "\\\\")
            alg_f.write(f'''
алг основнаяпрограмма
нач
  файл f
  открыть(f, "{path_for_alg}", "запись")
  вывод f, "external"
  закрыть(f)
кон
''')
            alg_path = alg_f.name
        try:
            result = run_main_cli([alg_path], timeout=10)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(os.path.isfile(out_file))
            with open(out_file, encoding="utf-8") as fh:
                self.assertIn("external", fh.read())
        finally:
            os.unlink(alg_path)
            if os.path.isfile(out_file):
                os.unlink(out_file)
