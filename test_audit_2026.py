"""Тесты по плану TODO_2026.md: CRLF, void в выражениях, строки в C, выход/break,
новые встроенные функции, шаги отладчика SHAYDBG."""
from __future__ import annotations

import io
import json
import os
import shutil
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


def _compile_and_run(source: str) -> str:
    """Транспиляция → gcc → запуск; возвращает stdout программы."""
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


class TestLexerCRLF(unittest.TestCase):
    def test_crlf_line_endings(self):
        src = "алг основнаяпрограмма\r\nнач\r\n  вывод 1\r\nкон\r\n"
        tokens = list(Lexer(src).generate_tokens())
        self.assertEqual(tokens[-1].type, TokenType.EOF)
        self.assertEqual(tokens[-2].line, 4)
        self.assertEqual(_run(src).strip(), "1")


class TestVoidInExpression(unittest.TestCase):
    def test_user_procedure_in_expression_rejected(self):
        src = """
алг П(арг цел a)
нач
  вывод a
кон
алг основнаяпрограмма
нач
  цел x
  x := П(5)
кон
"""
        with self.assertRaises(SemanticError):
            _check(src)

    def test_builtin_procedure_in_expression_rejected(self):
        src = """
алг основнаяпрограмма
нач
  файл f
  цел x
  x := закрыть(f)
кон
"""
        with self.assertRaises(SemanticError):
            _check(src)

    def test_procedure_call_statement_allowed(self):
        src = """
алг П
нач
  вывод 1
кон
алг основнаяпрограмма
нач
  П()
кон
"""
        _check(src)


class TestBreak(unittest.TestCase):
    def test_break_in_for(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 10
    если i = 4 то
      выход
    все
    вывод i
  кц
кон
"""
        self.assertEqual(_run(src).split(), ["1", "2", "3"])

    def test_break_in_while_en(self):
        src = """
proc mainprogram
begin
  int n
  n := 0
  loop while true
    n := n + 1
    if n >= 5 then
      break
    endif
  eloop
  output n
end
"""
        self.assertEqual(_run(src).strip(), "5")

    def test_break_exits_only_inner_loop(self):
        src = """
алг основнаяпрограмма
нач
  цел i, j, s
  s := 0
  нц для i от 1 до 3
    нц для j от 1 до 10
      если j > 2 то
        выход
      все
      s := s + 1
    кц
  кц
  вывод s
кон
"""
        self.assertEqual(_run(src).strip(), "6")

    def test_break_outside_loop_is_error(self):
        src = "алг основнаяпрограмма\nнач\n  выход\nкон\n"
        with self.assertRaises(SemanticError):
            _check(src)

    def test_break_keyword_tokens(self):
        types = [t.type for t in Lexer("выход break BREAK").generate_tokens()][:-1]
        self.assertEqual(types, [TokenType.ВЫХОД] * 3)


class TestNewBuiltins(unittest.TestCase):
    SRC = """
алг основнаяпрограмма
нач
  таб цел a[1:5]
  вывод остаток(10, 3)
  вывод целдел(17, 5)
  вывод степень(2, 10)
  вывод мин(5, 2)
  вывод макс(5, 2)
  вывод округление(3.7)
  вывод знак(-42)
  вывод найти("hello world", "world")
  вывод найти("abc", "z")
  вывод размер(a)
  вывод sin(0)
  вывод cos(0)
кон
"""
    EXPECTED = ["1", "3", "1024", "2", "5", "4", "-1", "7", "0", "5", "0", "1"]

    def test_interpreter(self):
        self.assertEqual(_run(self.SRC).split(), self.EXPECTED)

    def test_english_aliases(self):
        src = """
proc mainprogram
begin
  output mod(7, 2), " ", div(7, 2), " ", pow(3, 2), " ", find("abc", "c")
end
"""
        self.assertEqual(_run(src).strip(), "1 3 9 3")

    def test_arity_checked(self):
        with self.assertRaises(SemanticError):
            _check("алг основнаяпрограмма\nнач\n  вывод остаток(1)\nкон\n")

    def test_mod_by_zero(self):
        with self.assertRaises(SemanticError):
            _run("алг основнаяпрограмма\nнач\n  вывод остаток(1, 0)\nкон\n")

    @unittest.skipUnless(_gcc_available(), "gcc не найден")
    def test_c_parity(self):
        self.assertEqual(_compile_and_run(self.SRC).split(), self.EXPECTED)


class TestIntegerOutput(unittest.TestCase):
    def test_integers_printed_without_fraction(self):
        src = """
алг основнаяпрограмма
нач
  цел x
  вещ y
  x := 6
  y := 2.5
  вывод x
  вывод y
  вывод "x=" + x
  вывод встроку(12)
кон
"""
        self.assertEqual(_run(src).splitlines(), ["6", "2.5", "x=6", "12"])


@unittest.skipUnless(_gcc_available(), "gcc не найден")
class TestCStrings(unittest.TestCase):
    def test_string_compare_and_assign(self):
        src = """
алг основнаяпрограмма
нач
  лит a, b
  a := "hello"
  b := a
  a := "other"
  если b = "hello" то
    вывод "eq"
  все
  если a <> b то
    вывод "ne"
  все
  вывод b
кон
"""
        expected = ["eq", "ne", "hello"]
        self.assertEqual(_run(src).split(), expected)
        self.assertEqual(_compile_and_run(src).split(), expected)

    def test_implicit_loop_variable_compiles(self):
        src = """
proc mainprogram
begin
  loop for i from 1 to 3
    output i
  eloop
end
"""
        self.assertEqual(_compile_and_run(src).split(), ["1", "2", "3"])

    def test_break_compiles(self):
        src = """
алг основнаяпрограмма
нач
  цел i
  нц для i от 1 до 10
    если i = 3 то
      выход
    все
    вывод i
  кц
кон
"""
        self.assertEqual(_compile_and_run(src).split(), ["1", "2"])


class TestRunFlag(unittest.TestCase):
    def test_run_flag_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            alg = os.path.join(tmp, "p.alg")
            with open(alg, "w", encoding="utf-8") as f:
                f.write("алг основнаяпрограмма\nнач\n  вывод 42\nкон\n")
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg, "--run"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace", env=_ENV,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("42", r.stdout)


class TestDebugSteps(unittest.TestCase):
    SRC = (
        "алг Ф(арг цел a)\n"        # 1
        "нач\n"                     # 2
        "  вывод a\n"               # 3
        "кон\n"                     # 4
        "алг основнаяпрограмма\n"   # 5
        "нач\n"                     # 6
        "  Ф(1)\n"                  # 7
        "  вывод 2\n"               # 8
        "кон\n"                     # 9
    )

    def _stops(self, commands: list[str]) -> list[int]:
        with tempfile.TemporaryDirectory() as tmp:
            alg = os.path.join(tmp, "dbg.alg")
            with open(alg, "w", encoding="utf-8") as f:
                f.write(self.SRC)
            stdin = "".join(json.dumps({"cmd": c}) + "\n" for c in commands)
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg,
                 "--debug-protocol", "--break", "7"],
                input=stdin, capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace", env=_ENV,
            )
        lines = []
        for raw in r.stderr.splitlines():
            if raw.startswith("SHAYDBG "):
                ev = json.loads(raw[len("SHAYDBG "):])
                if ev.get("shay") == "stopped":
                    lines.append(ev["line"])
        return lines

    def test_step_over_skips_callee(self):
        self.assertEqual(self._stops(["step_over", "continue"]), [7, 8])

    def test_step_into_enters_callee(self):
        self.assertEqual(self._stops(["step_into", "continue"]), [7, 3])

    def test_step_out_returns_to_caller(self):
        self.assertEqual(self._stops(["step_into", "step_out", "continue"]), [7, 3, 8])


class TestShaydbgSnapshotEval(unittest.TestCase):
    def _events(self, src: str, break_line: int, commands: list) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            alg = os.path.join(tmp, "dbg.alg")
            with open(alg, "w", encoding="utf-8") as f:
                f.write(src)
            stdin_parts = []
            for c in commands:
                if isinstance(c, dict):
                    stdin_parts.append(json.dumps(c, ensure_ascii=False) + "\n")
                else:
                    stdin_parts.append(json.dumps({"cmd": c}, ensure_ascii=False) + "\n")
            r = subprocess.run(
                [sys.executable, os.path.join(_root, "main.py"), alg,
                 "--debug-protocol", "--break", str(break_line)],
                input="".join(stdin_parts), capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace", env=_ENV,
            )
        out = []
        for raw in r.stderr.splitlines():
            if raw.startswith("SHAYDBG "):
                out.append(json.loads(raw[len("SHAYDBG "):]))
        return out

    def test_stopped_has_arrays_and_records(self):
        src = """
запись Точка
нач
  цел x
кон
алг основнаяпрограмма
нач
  Точка p
  таб цел a[1:2]
  p.x := 5
  a[1] := 9
  вывод p.x
кон
"""
        evs = self._events(src, 12, ["vars", "continue"])
        stopped = next(e for e in evs if e.get("shay") == "stopped")
        self.assertIn("a", stopped.get("arrays") or {})
        self.assertEqual(stopped["arrays"]["a"]["values"][0], 9.0)
        self.assertIn("p", stopped.get("records") or {})
        self.assertEqual(stopped["records"]["p"]["x"], 5.0)
        self.assertNotIn("a", stopped.get("locals") or {})
        vars_ev = next(e for e in evs if e.get("shay") == "vars")
        self.assertIn("a", vars_ev.get("arrays") or {})

    def test_eval_binop_and_member(self):
        src = """
запись Точка
нач
  цел x
кон
алг основнаяпрограмма
нач
  Точка p
  цел n
  p.x := 3
  n := 4
  вывод n
кон
"""
        evs = self._events(
            src,
            12,
            [
                {"cmd": "eval", "expr": "n + 1"},
                {"cmd": "eval", "expr": "p.x"},
                "continue",
            ],
        )
        evals = [e for e in evs if e.get("shay") == "eval"]
        self.assertTrue(evals[0].get("ok"))
        self.assertEqual(evals[0].get("value"), 5.0)
        self.assertTrue(evals[1].get("ok"))
        self.assertEqual(evals[1].get("value"), 3.0)

    def test_disabled_breakpoint_skipped(self):
        src = (
            "алг основнаяпрограмма\n"
            "нач\n"
            "  вывод 1\n"
            "  вывод 2\n"
            "  вывод 3\n"
            "кон\n"
        )
        # Start with break on line 3; then disable it and continue — should not stop on 3 again
        # after resync; we stop once at start, send disabled BP, continue to end.
        evs = self._events(
            src,
            3,
            [
                {
                    "cmd": "breakpoints",
                    "items": [{"line": 3, "enabled": False}, {"line": 5, "enabled": True}],
                },
                "continue",
            ],
        )
        stopped_lines = [e["line"] for e in evs if e.get("shay") == "stopped"]
        self.assertEqual(stopped_lines[0], 3)
        self.assertIn(5, stopped_lines)
        self.assertEqual(stopped_lines.count(3), 1)


if __name__ == "__main__":
    unittest.main()
