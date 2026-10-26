"""Тесты бэклога TODO_2026: логические да/нет, ввод строк в C, возврат, шаг цикла."""
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
from lang_tokens import TokenType
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from c_transpiler import CTranspiler
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


def _check(source: str) -> None:
    SemanticAnalyzer(_parse(source), "<test>").analyze()


def _gcc_available() -> bool:
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, timeout=5, check=False)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _compile_and_run(source: str, stdin: str = "") -> str:
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
            [exe], cwd=tmp, input=stdin, capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        if run.returncode != 0:
            raise AssertionError(run.stderr or f"exit {run.returncode}")
        return run.stdout


class TestBoolOutput(unittest.TestCase):
    def test_interpreter_prints_da_net(self):
        src = """
алг основнаяпрограмма
нач
  лог a, b
  a := да
  b := нет
  вывод a
  вывод b
  вывод да
  вывод 1 = 1
  вывод 1 = 2
кон
"""
        self.assertEqual(_run(src).split(), ["да", "нет", "да", "да", "нет"])

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity_bool(self):
        src = """
алг основнаяпрограмма
нач
  лог a
  a := да
  вывод a
  вывод нет
  вывод 2 > 1
кон
"""
        expected = ["да", "нет", "да"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)


class TestForStep(unittest.TestCase):
    def test_step_keyword(self):
        types = [t.type for t in Lexer("шаг step STEP").generate_tokens()][:-1]
        self.assertEqual(types, [TokenType.ШАГ] * 3)

    def test_step_2(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 7 шаг 2
    вывод i
  кц
кон
"""
        self.assertEqual(_run(src).split(), ["1", "3", "5", "7"])

    def test_reverse_auto(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 5 до 1
    вывод i
  кц
кон
"""
        self.assertEqual(_run(src).split(), ["5", "4", "3", "2", "1"])

    def test_reverse_explicit_step(self):
        src = """
proc mainprogram
begin
  int i
  loop for i from 10 to 1 step -3
    output i
  eloop
end
"""
        self.assertEqual(_run(src).split(), ["10", "7", "4", "1"])

    def test_zero_step_error(self):
        with self.assertRaises(SemanticError):
            _run("""
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 5 шаг 0
    вывод i
  кц
кон
""")

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_step_parity(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 5 шаг 2
    вывод i
  кц
кон
"""
        self.assertEqual(_compile_and_run(src).split(), ["1", "3", "5"])


class TestReturn(unittest.TestCase):
    def test_return_with_expr(self):
        src = """
алг Факториал(арг цел n; рез цел r)
нач
  если n <= 1 то
    возврат 1
  все
  r := n * Факториал(n - 1)
кон
алг основнаяпрограмма
нач
  вывод Факториал(5)
кон
"""
        self.assertEqual(_run(src).strip(), "120")

    def test_early_return_in_function(self):
        src = """
алг Знак(арг цел x; рез цел s)
нач
  если x > 0 то
    возврат 1
  все
  если x < 0 то
    возврат -1
  все
  s := 0
кон
алг основнаяпрограмма
нач
  вывод Знак(5)
  вывод Знак(-3)
  вывод Знак(0)
кон
"""
        self.assertEqual(_run(src).split(), ["1", "-1", "0"])

    def test_bare_return_in_procedure(self):
        src = """
алг Печать(арг цел n)
нач
  если n < 0 то
    возврат
  все
  вывод n
кон
алг основнаяпрограмма
нач
  Печать(-1)
  Печать(7)
кон
"""
        self.assertEqual(_run(src).strip(), "7")

    def test_return_expr_in_procedure_rejected(self):
        src = """
алг П
нач
  возврат 1
кон
алг основнаяпрограмма
нач
  П()
кон
"""
        with self.assertRaises(SemanticError):
            _check(src)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_return_parity(self):
        src = """
алг Удвоить(арг цел x; рез цел y)
нач
  если x = 0 то
    возврат 0
  все
  y := x * 2
кон
алг основнаяпрограмма
нач
  вывод Удвоить(0)
  вывод Удвоить(4)
кон
"""
        expected = ["0", "8"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)


@unittest.skipUnless(_gcc_available(), "gcc не найден")
class TestCStringInput(unittest.TestCase):
    def test_fgets_reads_spaces(self):
        src = """
алг основнаяпрограмма
нач
  лит s
  ввод s
  вывод s
кон
"""
        out = _compile_and_run(src, stdin="hello world\n")
        self.assertEqual(out.strip(), "hello world")


class TestCIndent(unittest.TestCase):
    def test_nested_if_preserves_relative_indent(self):
        src = """
алг основнаяпрограмма
нач
  если да то
    если да то
      вывод 1
    все
  все
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        # Вложенный if должен иметь больший отступ, чем внешний
        lines = [l for l in c.splitlines() if "if (" in l and "s1" not in l and "s2" not in l
                 and "num ==" not in l and "i0" not in l and "count" not in l
                 and "max_v" not in l and "strcmp" not in l and "feof" not in l]
        # Берём строки вида "    if (" из main
        main_ifs = [l for l in c.splitlines() if l.lstrip().startswith("if (") and "alg_" not in l
                    and "strcmp" not in l and "!s" not in l and "long" not in l
                    and "i0" not in l and "count" not in l and "max_v" not in l
                    and "feof" not in l and "fgets" not in l]
        # Хотя бы два if с разным отступом
        indents = [len(l) - len(l.lstrip(" ")) for l in main_ifs if "да" in l or "1" in l or "(1)" in l]
        # Fallback: просто проверить, что в main есть вложенная структура с пробелами
        body = c[c.find("int main()"):]
        self.assertIn("if (", body)
        # Относительный отступ внутри блока: строка с большим indent содержит if
        nested = [l for l in body.splitlines() if "if (" in l]
        self.assertGreaterEqual(len(nested), 2)
        self.assertGreater(
            len(nested[1]) - len(nested[1].lstrip(" ")),
            len(nested[0]) - len(nested[0].lstrip(" ")),
        )


class TestContinue(unittest.TestCase):
    def test_continue_keyword(self):
        types = [t.type for t in Lexer("продолжить continue CONTINUE").generate_tokens()][:-1]
        self.assertEqual(types, [TokenType.ПРОДОЛЖИТЬ] * 3)

    def test_continue_skips_iteration(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 5
    если i = 3 то
      продолжить
    все
    вывод i
  кц
кон
"""
        self.assertEqual(_run(src).split(), ["1", "2", "4", "5"])

    def test_continue_outside_loop_rejected(self):
        with self.assertRaises(SemanticError):
            _check("""
алг основнаяпрограмма
нач
  продолжить
кон
""")

    def test_continue_en(self):
        src = """
proc mainprogram
begin
  int i
  loop for i from 1 to 4
    if i = 2 then
      continue
    endif
    output i
  eloop
end
"""
        self.assertEqual(_run(src).split(), ["1", "3", "4"])

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_continue_parity(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 5
    если i = 3 то
      продолжить
    все
    вывод i
  кц
кон
"""
        expected = ["1", "2", "4", "5"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)


class TestCPrototypes(unittest.TestCase):
    def test_forward_declarations_emitted(self):
        src = """
алг А
нач
  Б()
кон
алг Б
нач
  вывод 42
кон
алг основнаяпрограмма
нач
  А()
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("/* Forward declarations */", c)
        # Прототипы до определений
        fwd = c.index("/* Forward declarations */")
        def_a = c.index("void ", fwd + 1)  # первое тело после секции
        self.assertLess(fwd, def_a)
        self.assertIn(");", c[fwd:c.index("\n\n", fwd) if "\n\n" in c[fwd:] else fwd + 200])

    def test_call_before_decl_interpreter(self):
        src = """
алг А
нач
  Б()
кон
алг Б
нач
  вывод 7
кон
алг основнаяпрограмма
нач
  А()
кон
"""
        self.assertEqual(_run(src).strip(), "7")

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_mutual_recursion_c(self):
        src = """
алг Чёт(арг цел n; рез цел r)
нач
  если n = 0 то
    возврат 1
  все
  r := Нечёт(n - 1)
кон
алг Нечёт(арг цел n; рез цел r)
нач
  если n = 0 то
    возврат 0
  все
  r := Чёт(n - 1)
кон
алг основнаяпрограмма
нач
  вывод Чёт(4)
  вывод Нечёт(3)
кон
"""
        expected = ["1", "1"]
        self.assertEqual(_run(src).split(), expected)
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("/* Forward declarations */", c)
        self.assertEqual(_compile_and_run(src).split(), expected)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_bool_func_return_prints_da_net(self):
        src = """
алг Флаг(арг цел n; рез лог r)
нач
  r := n > 0
кон
алг основнаяпрограмма
нач
  вывод Флаг(1)
  вывод Флаг(-1)
кон
"""
        expected = ["да", "нет"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)


class TestRecordStringFieldC(unittest.TestCase):
    def test_transpile_uses_strdup_for_lit_field(self):
        src = """
запись Чел
нач
  лит имя
кон
алг основнаяпрограмма
нач
  Чел c
  c.имя := "Ann"
  вывод c.имя
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("strdup", c)
        self.assertIn("free(", c)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity_lit_field(self):
        src = """
запись Чел
нач
  лит имя
кон
алг основнаяпрограмма
нач
  Чел c
  c.имя := "Ann"
  вывод c.имя
кон
"""
        self.assertEqual(_run(src).strip(), "Ann")
        self.assertEqual(_compile_and_run(src).strip(), "Ann")


class TestDictRuntime(unittest.TestCase):
    def test_alg_dict_free_in_runtime(self):
        src = """
алг основнаяпрограмма
нач
  словарь d
  d["a"] := 1
  вывод d["a"]
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("alg_dict_init(&d)", c)
        self.assertIn("alg_dict_free(&d)", c)
        # free at end of main, before return 0
        free_at = c.index("alg_dict_free(&d)")
        ret_at = c.rindex("return 0;")
        self.assertLess(free_at, ret_at)


class TestRecordArrayFields(unittest.TestCase):
    def test_interp_array_field(self):
        src = """
запись Буф
нач
  таб цел a[1:3]
кон
алг основнаяпрограмма
нач
  Буф b
  b.a[1] := 10
  b.a[3] := 30
  вывод b.a[1]
  вывод b.a[3]
кон
"""
        self.assertEqual(_run(src).split(), ["10", "30"])

    def test_c_emits_array_field(self):
        src = """
запись Буф
нач
  таб цел a[0:2]
кон
алг основнаяпрограмма
нач
  Буф b
  b.a[0] := 1
  вывод b.a[0]
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("a[3]", c)
        self.assertIn("b.a[((int)0) - 0]", c)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity_array_field(self):
        src = """
запись Буф
нач
  таб цел a[1:3]
кон
алг основнаяпрограмма
нач
  Буф b
  b.a[1] := 10
  b.a[3] := 30
  вывод b.a[1]
  вывод b.a[3]
кон
"""
        expected = ["10", "30"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)


class TestLenNumberError(unittest.TestCase):
    def test_semantic_rejects_len_number(self):
        src = """
алг основнаяпрограмма
нач
  вывод длина(42)
кон
"""
        with self.assertRaises(SemanticError):
            _check(src)

    def test_len_string_ok(self):
        src = """
алг основнаяпрограмма
нач
  вывод длина("ab")
кон
"""
        self.assertEqual(_run(src).strip(), "2")


class TestMultiDimArraysRejected(unittest.TestCase):
    def test_comma_bounds_rejected(self):
        from errors import ParserError

        src = """
алг основнаяпрограмма
нач
  таб цел a[1:2, 1:3]
кон
"""
        with self.assertRaises(ParserError) as ctx:
            _parse(src)
        self.assertIn("Многомерные", str(ctx.exception))

    def test_double_bracket_rejected(self):
        from errors import ParserError

        src = """
алг основнаяпрограмма
нач
  таб цел a[1:2][1:3]
кон
"""
        with self.assertRaises(ParserError) as ctx:
            _parse(src)
        self.assertIn("Многомерные", str(ctx.exception))


class TestReplPersist(unittest.TestCase):
    def test_session_keeps_bindings(self):
        from repl import ReplSession, _run_source

        session = ReplSession()
        warnings = WarningCollector()
        _run_source(
            """
алг основнаяпрограмма
нач
  цел x
  x := 7
кон
""",
            verbose=False,
            trace=False,
            warnings=warnings,
            session=session,
        )
        self.assertIn("x", session.members)
        self.assertEqual(session.members["x"][1], 7.0)

        buf = io.StringIO()
        with redirect_stdout(buf):
            _run_source(
                """
алг основнаяпрограмма
нач
  вывод x
кон
""",
                verbose=False,
                trace=False,
                warnings=warnings,
                session=session,
            )
        self.assertIn("7", buf.getvalue().split())


class TestNestedBreakContinue(unittest.TestCase):
    def test_nested_break_nearest_only(self):
        src = """
алг основнаяпрограмма
нач
  цел i, j
  нц для i от 1 до 2
    нц для j от 1 до 5
      если j = 3 то
        выход
      все
      вывод j
    кц
  кц
кон
"""
        # nearest break: each outer i prints 1 2 then breaks inner
        self.assertEqual(_run(src).split(), ["1", "2", "1", "2"])

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_nested_break_c_parity(self):
        src = """
алг основнаяпрограмма
нач
  цел i, j
  нц для i от 1 до 2
    нц для j от 1 до 5
      если j = 3 то
        выход
      все
      вывод j
    кц
  кц
кон
"""
        expected = _run(src).split()
        self.assertEqual(_compile_and_run(src).split(), expected)


class TestOwnedStringConcat(unittest.TestCase):
    def test_nested_concat_uses_owned(self):
        src = """
алг основнаяпрограмма
нач
  лит a, b, c, s
  a := "a"
  b := "b"
  c := "c"
  s := a + b + c
  вывод s
  вывод длина(a + b)
кон
"""
        c = CTranspiler(_parse(src), "t.alg").transpile()
        self.assertIn("alg_str_concat_owned", c)
        self.assertIn("alg_strlen_free", c)

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity_nested_concat(self):
        src = """
алг основнаяпрограмма
нач
  лит s
  s := "a" + "b" + "c"
  вывод s
  вывод длина("xy" + "z")
кон
"""
        expected = _run(src).split()
        self.assertEqual(_compile_and_run(src).split(), expected)


if __name__ == "__main__":
    unittest.main()
