# test_basic.py — базовые тесты лексера, парсера, интерпретатора и интеграция (см. AUDIT.md, план 5).
import unittest
import sys
import os
import io
import tempfile
import subprocess

# Запуск из корня проекта
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)

from lang_tokens import TokenType
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from c_transpiler import CTranspiler
from module_loader import load_alg_file
from errors import LexerError, ParserError, SemanticError
from semantic_analyzer import SemanticAnalyzer
from alg_warnings import (
    AssignTypeWarning,
    UnusedVarWarning,
    WarningCollector,
    RedefinitionWarning,
)
from version import __version__
from ast_dump import dump_ast_text, dump_ast_json
from constants import repl_wrap


class TestLexer(unittest.TestCase):
    def test_numbers(self):
        tokens = list(Lexer("42").generate_tokens())
        self.assertEqual(len(tokens), 2)  # NUMBER + EOF
        self.assertEqual(tokens[0].type, TokenType.NUMBER)
        self.assertEqual(tokens[0].value, "42")

    def test_keywords(self):
        tokens = list(Lexer("алг нач кон").generate_tokens())
        types = [t.type for t in tokens]
        self.assertIn(TokenType.АЛГ, types)
        self.assertIn(TokenType.НАЧ, types)
        self.assertIn(TokenType.КОН, types)
        self.assertEqual(types[-1], TokenType.EOF)

    def test_assign_and_id(self):
        tokens = list(Lexer("x := 1").generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.ID)
        self.assertEqual(tokens[1].type, TokenType.ASSIGN)
        self.assertEqual(tokens[2].type, TokenType.NUMBER)

    def test_string(self):
        tokens = list(Lexer('"привет"').generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, '"привет"')

    def test_string_escape(self):
        tokens = list(Lexer(r'"a\nb"').generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, '"a\nb"')

    def test_comparison_operators(self):
        tokens = list(Lexer("1 >= 2 <= 3 <> 4").generate_tokens())
        types = [t.type for t in tokens if t.type != TokenType.NUMBER]
        self.assertIn(TokenType.GTE, types)
        self.assertIn(TokenType.LTE, types)
        self.assertIn(TokenType.NEQ, types)

    def test_unexpected_char_raises(self):
        with self.assertRaises(LexerError):
            list(Lexer("алг @").generate_tokens())


class TestParser(unittest.TestCase):
    def _parse(self, source):
        tokens = list(Lexer(source).generate_tokens())
        return Parser(tokens).parse()

    def test_minimal_program(self):
        # Минимальная программа: алг Имя нач кон
        tree = self._parse("алг тест нач кон")
        self.assertEqual(len(tree.declarations), 1)
        self.assertEqual(tree.declarations[0].name, "тест")

    def test_const_decl(self):
        tree = self._parse("конст N = 10\nалг основнаяпрограмма нач кон")
        self.assertEqual(len(tree.declarations), 2)
        self.assertEqual(tree.declarations[0].var_node.name, "n")
        self.assertEqual(tree.declarations[0].expr.value, 10.0)

    def test_var_and_assign(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 5
кон
"""
        tree = self._parse(source)
        self.assertEqual(len(tree.declarations), 1)
        block = tree.declarations[0].block
        self.assertEqual(len(block.statements), 1)
        from ast_nodes import Assign
        self.assertIsInstance(block.statements[0], Assign)


class TestInterpreter(unittest.TestCase):
    def _run_alg(self, source, capture_stdout=True):
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        interp = Interpreter(tree, "<test>")
        if capture_stdout:
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                interp.run()
                return buf.getvalue()
            finally:
                sys.stdout = old
        else:
            interp.run()

    def test_run_minimal(self):
        source = """
алг основнаяпрограмма
нач
  вывод 42
кон
"""
        out = self._run_alg(source)
        self.assertIn("42", out)

    def test_run_const_and_var(self):
        source = """
конст N = 10
алг основнаяпрограмма
нач
  цел x
  x := 5
  вывод N
  вывод x
кон
"""
        out = self._run_alg(source)
        self.assertIn("10", out)
        self.assertIn("5", out)

    def test_comparison_ops(self):
        out = self._run_alg("""
алг основнаяпрограмма
нач
  если 1 <> 2 то
    вывод "neq"
  все
  если 2 <= 2 то
    вывод "lte"
  все
  если 3 >= 2 то
    вывод "gte"
  все
кон
""")
        self.assertIn("neq", out)
        self.assertIn("lte", out)
        self.assertIn("gte", out)

    def test_string_escape_runtime(self):
        out = self._run_alg(r'''
алг основнаяпрограмма
нач
  лит s
  s := "a\nb"
  вывод s
кон
''')
        self.assertIn("a", out)
        self.assertIn("b", out)

    def test_dict(self):
        out = self._run_alg("""
алг основнаяпрограмма
нач
  словарь d
  d["x"] := 42
  вывод d["x"]
кон
""")
        self.assertIn("42", out)

    def test_circular_import_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.alg")
            b = os.path.join(tmp, "b.alg")
            with open(a, "w", encoding="utf-8") as f:
                f.write('использовать "b.alg"\nалг foo\nнач\nкон\n')
            with open(b, "w", encoding="utf-8") as f:
                f.write('использовать "a.alg"\nалг bar\nнач\nкон\n')
            main_src = f'использовать "a.alg"\nалг основнаяпрограмма\nнач\nкон\n'
            main_path = os.path.join(tmp, "main.alg")
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(main_src)
            tokens = list(Lexer(main_src).generate_tokens())
            tree = Parser(tokens).parse()
            with self.assertRaises(SemanticError) as ctx:
                Interpreter(tree, main_path).run()
            self.assertIn("Циклический", str(ctx.exception))


class TestTranspilerFeatures(unittest.TestCase):
    def _transpile(self, source):
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        return CTranspiler(tree, "<t>").transpile()

    def test_neq_in_c(self):
        c = self._transpile("""
алг основнаяпрограмма
нач
  если 1 <> 2 то
    вывод 1
  все
кон
""")
        self.assertIn("!=", c)

    def test_string_escape_in_c(self):
        c = self._transpile(r'''
алг основнаяпрограмма
нач
  вывод "a\nb"
кон
''')
        self.assertIn("\\n", c)

    def test_dict_in_c(self):
        c = self._transpile("""
алг основнаяпрограмма
нач
  словарь d
  d["x"] := 42
  вывод d["x"]
кон
""")
        self.assertIn("AlgDict", c)
        self.assertIn("alg_dict_set", c)
        self.assertIn("alg_dict_get", c)

    def test_member_access_record_in_c(self):
        c = self._transpile("""
запись Точка
нач
  вещ x
  вещ y
кон
алг основнаяпрограмма
нач
  Точка p
  p.x := 3
  вывод p.x
кон
""")
        self.assertIn("typedef struct", c)
        self.assertIn(".x", c)

    def test_enum_in_c(self):
        c = self._transpile("""
переч Цвет (Красный, Синий)
алг основнаяпрограмма
нач
  Цвет c
  c := Цвет.Красный
  вывод c
кон
""")
        self.assertIn("typedef enum", c)
        self.assertIn("tsvet_krasnyy", c)

    def test_array_offset_in_c(self):
        c = self._transpile("""
алг основнаяпрограмма
нач
  таб цел a[0:2]
  a[0] := 7
  вывод a[0]
кон
""")
        self.assertIn("[((int)0) - 0]", c)

    def test_string_to_int_builtin_in_c(self):
        c = self._transpile("""
алг основнаяпрограмма
нач
  вывод вцел("42")
кон
""")
        self.assertIn("alg_atol", c)

    def test_keep_cyrillic(self):
        tokens = list(Lexer("""
алг основнаяпрограмма
нач
  цел счёт
  счёт := 1
  вывод счёт
кон
""").generate_tokens())
        tree = Parser(tokens).parse()
        c_lat = CTranspiler(tree, "<t>", keep_cyrillic=False).transpile()
        c_cyr = CTranspiler(tree, "<t>", keep_cyrillic=True).transpile()
        self.assertIn("schyot", c_lat)
        self.assertIn("счёт", c_cyr)

    def test_format_spec_in_c(self):
        c = self._transpile("""
алг основнаяпрограмма
нач
  вещ x
  x := 3.1415
  вывод x:10:2
кон
""")
        self.assertIn("%*.*f", c)


class TestShaydbgSmoke(unittest.TestCase):
    def test_emit_event_prefix(self):
        from shay_debug_protocol import PROTOCOL_PREFIX, emit_event
        buf = io.StringIO()
        emit_event({"shay": "ready", "version": 1}, stderr=buf)
        line = buf.getvalue()
        self.assertTrue(line.startswith(PROTOCOL_PREFIX))
        self.assertIn('"shay":"ready"', line.replace(" ", ""))


def _analyze_source(source: str, *, verbose: bool = False) -> None:
    tokens = list(Lexer(source).generate_tokens())
    tree = Parser(tokens).parse()
    SemanticAnalyzer(tree, "<test>", verbose=verbose).analyze()


class TestSemanticAnalyzer(unittest.TestCase):
    def test_undefined_variable(self):
        source = """
алг основнаяпрограмма
нач
  вывод несуществующая
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            _analyze_source(source)
        self.assertIn("не определена", str(ctx.exception).lower())

    def test_wrong_arity_builtin(self):
        source = """
алг основнаяпрограмма
нач
  вывод корень()
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            _analyze_source(source)
        self.assertIn("корень", str(ctx.exception))

    def test_missing_main(self):
        source = """
алг другая
нач
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            _analyze_source(source)
        self.assertIn("основнаяпрограмма", str(ctx.exception).lower())

    def test_valid_passes(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 1
  вывод x
кон
"""
        _analyze_source(source)

    def test_array_bounds(self):
        source = """
алг основнаяпрограмма
нач
  таб цел a[5:1]
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            _analyze_source(source)
        self.assertIn("индекс", str(ctx.exception).lower())

    def test_assign_string_to_int_error(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := "text"
кон
"""
        with self.assertRaises(SemanticError) as ctx:
            _analyze_source(source)
        self.assertIn("несовместим", str(ctx.exception).lower())

    def test_assign_float_to_int_warning(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 3.14
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        wc = WarningCollector(verbose=True)
        SemanticAnalyzer(tree, "<test>", warnings=wc).analyze()
        self.assertTrue(any(isinstance(w, AssignTypeWarning) for w in wc.warnings))

    def test_unused_var_warning(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  цел y
  x := 1
  вывод x
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        wc = WarningCollector()
        SemanticAnalyzer(tree, "<test>", warnings=wc).analyze()
        unused = [w for w in wc.warnings if isinstance(w, UnusedVarWarning)]
        self.assertEqual(len(unused), 1)
        self.assertIn("y", unused[0].message)


class TestAstDump(unittest.TestCase):
    def test_dump_ast_text_contains_nodes(self):
        source = """
алг основнаяпрограмма
нач
  вывод 1
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        text = dump_ast_text(tree)
        self.assertIn("Program", text)
        self.assertIn("ProcDecl", text)

    def test_dump_ast_json_contains_type(self):
        source = """
алг основнаяпрограмма
нач
кон
"""
        tree = Parser(list(Lexer(source).generate_tokens())).parse()
        data = dump_ast_json(tree)
        self.assertIn('"type": "Program"', data)


class TestWarningsCollector(unittest.TestCase):
    def test_redefinition_warning_semantic(self):
        source = """
алг дубль
нач
кон
алг дубль
нач
кон
алг основнаяпрограмма
нач
кон
"""
        tokens = list(Lexer(source).generate_tokens())
        tree = Parser(tokens).parse()
        wc = WarningCollector()
        SemanticAnalyzer(tree, "<test>", warnings=wc).analyze()
        self.assertTrue(any(isinstance(w, RedefinitionWarning) for w in wc.warnings))

    def test_repl_wrap(self):
        wrapped = repl_wrap("вывод 1")
        self.assertIn("основнаяпрограмма", wrapped)
        self.assertIn("вывод 1", wrapped)


class TestCLIFlags(unittest.TestCase):
    def _run_main(self, args, timeout=10):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, os.path.join(_root, "main.py")] + list(args),
            cwd=_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )

    def test_version(self):
        result = self._run_main(["--version"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), __version__)

    def test_help_lists_verbose_trace(self):
        result = self._run_main(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--verbose", result.stdout)
        self.assertIn("--trace", result.stdout)
        self.assertIn("--permissive", result.stdout)
        self.assertIn("--keep-cyrillic", result.stdout)

    def test_keep_cyrillic_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            alg = os.path.join(tmp, "t.alg")
            with open(alg, "w", encoding="utf-8") as f:
                f.write(
                    "алг основнаяпрограмма\nнач\n  цел счёт\n  счёт := 1\n  вывод счёт\nкон\n"
                )
            result = self._run_main([alg, "--transpile", "--keep-cyrillic"], timeout=15)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            with open(os.path.join(tmp, "t.c"), encoding="utf-8") as f:
                c = f.read()
            self.assertIn("счёт", c)

    def test_help_lists_modes(self):
        result = self._run_main(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--dump-ast", result.stdout)
        self.assertIn("--repl", result.stdout)
        self.assertIn("--warnings-as-errors", result.stdout)

    def test_verbose_stages(self):
        source = """
алг основнаяпрограмма
нач
  вывод "ok"
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            path = f.name
        try:
            result = self._run_main([path, "--verbose"])
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Лексический анализ", result.stderr)
            self.assertIn("Семантический анализ", result.stderr)
            self.assertIn("Интерпретация", result.stderr)
            self.assertIn("ok", result.stdout)
            self.assertNotIn("[этап]", result.stdout)
        finally:
            os.unlink(path)

    def test_trace_assign(self):
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
            path = f.name
        try:
            result = self._run_main([path, "--trace"])
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("[трассировка]", result.stderr)
            self.assertIn("x := 42", result.stderr)
        finally:
            os.unlink(path)

    def test_check_catches_semantic(self):
        source = """
алг основнаяпрограмма
нач
  вывод xyz_undefined
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            path = f.name
        try:
            result = self._run_main([path, "--check"])
            self.assertEqual(result.returncode, 1)
            self.assertIn("не определена", result.stderr.lower())
        finally:
            os.unlink(path)

    def test_dump_ast_cli(self):
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
            path = f.name
        try:
            result = self._run_main([path, "--dump-ast"])
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Program", result.stdout)
            self.assertIn("ProcDecl", result.stdout)
            result_j = self._run_main([path, "--dump-ast", "--dump-ast-format", "json"])
            self.assertEqual(result_j.returncode, 0, msg=result_j.stderr)
            self.assertIn('"type": "Program"', result_j.stdout)
        finally:
            os.unlink(path)

    def test_warnings_as_errors_exit_code(self):
        source = """
алг дубль
нач
кон
алг дубль
нач
кон
алг основнаяпрограмма
нач
кон
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".alg", delete=False, encoding="utf-8"
        ) as f:
            f.write(source)
            path = f.name
        try:
            result = self._run_main([path, "--warnings-as-errors"])
            self.assertEqual(result.returncode, 3, msg=result.stderr)
        finally:
            os.unlink(path)

    def test_repl_runs_expression(self):
        script = (
            "import sys\n"
            f"sys.path.insert(0, {_root!r})\n"
            "from repl import run_repl\n"
            "import io\n"
            "inp = io.StringIO('вывод 99\\nвыход\\n')\n"
            "import builtins\n"
            "builtins.input = lambda p='': inp.readline().rstrip('\\n')\n"
            "raise SystemExit(run_repl())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("99", result.stdout)


class TestModuleLoader(unittest.TestCase):
    def test_load_alg_returns_program(self):
        program_alg = os.path.join(_root, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        tree = load_alg_file(program_alg)
        self.assertEqual(len(tree.declarations) >= 1, True)
        names = [d.name for d in tree.declarations if hasattr(d, "name")]
        self.assertIn("основнаяпрограмма", names)


class TestTranspilerIntegration(unittest.TestCase):
    def test_transpile_produces_c_file(self):
        program_alg = os.path.join(_root, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        tree = load_alg_file(program_alg)
        transpiler = CTranspiler(tree, program_alg)
        c_code = transpiler.transpile()
        self.assertIn("int main()", c_code)
        self.assertIn("faktorial", c_code)
        self.assertIn("str_concat", c_code)  # runtime для строк

    def test_main_transpile_cli_creates_c(self):
        program_alg = os.path.join(_root, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        with tempfile.TemporaryDirectory() as tmp:
            out_c = os.path.join(tmp, "program.c")
            alg_copy = os.path.join(tmp, "program.alg")
            with open(program_alg, "r", encoding="utf-8") as f:
                with open(alg_copy, "w", encoding="utf-8") as w:
                    w.write(f.read())
            utils_src = os.path.join(_root, "utils.alg")
            if os.path.isfile(utils_src):
                import shutil
                shutil.copy(utils_src, os.path.join(tmp, "utils.alg"))
            result = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg_copy, "--transpile"],
                cwd=tmp, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(os.path.isfile(out_c), "program.c должен быть создан")
            with open(out_c, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("int main()", content)


class TestTranspilerCompileRun(unittest.TestCase):
    """Интеграционный тест: транспиляция → компиляция GCC → запуск exe (если gcc доступен)."""

    def test_transpile_compile_run(self):
        program_alg = os.path.join(_root, "program.alg")
        if not os.path.isfile(program_alg):
            self.skipTest("program.alg не найден")
        gcc_cmd = "gcc"
        try:
            subprocess.run([gcc_cmd, "--version"], capture_output=True, timeout=5, check=False)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("gcc не найден или не запускается")
        with tempfile.TemporaryDirectory() as tmp:
            out_c = os.path.join(tmp, "program.c")
            out_exe = os.path.join(tmp, "program.exe" if sys.platform == "win32" else "program")
            alg_copy = os.path.join(tmp, "program.alg")
            utils_src = os.path.join(_root, "utils.alg")
            with open(program_alg, "r", encoding="utf-8") as f:
                with open(alg_copy, "w", encoding="utf-8") as w:
                    w.write(f.read())
            if os.path.isfile(utils_src):
                import shutil
                shutil.copy(utils_src, os.path.join(tmp, "utils.alg"))
            result = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg_copy, "--transpile"],
                cwd=tmp, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(os.path.isfile(out_c), "program.c должен быть создан")
            comp = subprocess.run(
                [gcc_cmd, "-o", out_exe, out_c, "-lm"],
                cwd=tmp, capture_output=True, text=True, timeout=15
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr or comp.stdout)
            self.assertTrue(os.path.isfile(out_exe), "исполняемый файл должен быть создан")
            run_result = subprocess.run(
                [out_exe], cwd=tmp, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            report_txt = os.path.join(tmp, "report.txt")
            self.assertTrue(os.path.isfile(report_txt), "report.txt должен быть создан программой")

    def test_builtins_transpile_compile_run(self):
        gcc_cmd = "gcc"
        try:
            subprocess.run([gcc_cmd, "--version"], capture_output=True, timeout=5, check=False)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("gcc не найден или не запускается")
        source = """
алг основнаяпрограмма
нач
  вывод корень(9)
  вывод модуль(-5)
  вывод длина("abc")
  вывод подстрока("abcdef", 2, 3)
  вывод вверх("hi")
  вывод вниз("HI")
  вывод вцел("7")
  вывод ввещ("2.5")
  вывод встроку(12)
кон
"""
        with tempfile.TemporaryDirectory() as tmp:
            alg = os.path.join(tmp, "builtins.alg")
            out_c = os.path.join(tmp, "builtins.c")
            out_exe = os.path.join(tmp, "builtins.exe" if sys.platform == "win32" else "builtins")
            with open(alg, "w", encoding="utf-8") as f:
                f.write(source)
            result = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg, "--transpile"],
                cwd=tmp, capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            with open(out_c, encoding="utf-8") as f:
                c = f.read()
            self.assertIn("alg_substr", c)
            self.assertIn("alg_atol", c)
            comp = subprocess.run(
                [gcc_cmd, "-o", out_exe, out_c, "-lm"],
                cwd=tmp, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr or comp.stdout)
            run_result = subprocess.run(
                [out_exe], cwd=tmp, capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace",
            )
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr)
            out = run_result.stdout
            self.assertIn("3", out)
            self.assertIn("5", out)
            self.assertIn("bcd", out)
            self.assertIn("HI", out)
            self.assertIn("hi", out)
            self.assertIn("7", out)
            self.assertIn("2.5", out)
            self.assertIn("12", out)


if __name__ == "__main__":
    unittest.main()
