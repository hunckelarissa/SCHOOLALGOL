"""Общие хелперы для тестов Gemini."""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_SUBPROC_UTF8 = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def run_main_cli(args, cwd=None, timeout=15):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "main.py")] + list(args),
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=_SUBPROC_UTF8,
    )


def interp_stdout_from_source(source: str) -> str:
    from lexer import Lexer
    from parser import Parser
    from interpreter import Interpreter

    tokens = list(Lexer(source).generate_tokens())
    tree = Parser(tokens).parse()
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        Interpreter(tree, "<test>").run()
    finally:
        sys.stdout = old
    return buf.getvalue()


def interp_stdout(alg_path: str) -> str:
    with open(alg_path, encoding="utf-8") as f:
        source = f.read()
    tokens = list(__import__("lexer").Lexer(source).generate_tokens())
    tree = __import__("parser").Parser(tokens).parse()
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        __import__("interpreter").Interpreter(tree, alg_path).run()
    finally:
        sys.stdout = old
    return buf.getvalue().strip()


def normalize_output(text: str) -> list:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def outputs_match(py_lines: list, c_lines: list) -> bool:
    if len(py_lines) != len(c_lines):
        return False
    for a, b in zip(py_lines, c_lines):
        if a == b:
            continue
        if re.sub(r"(\d+)\.0(?!\d)", r"\1", a) == re.sub(r"(\d+)\.0(?!\d)", r"\1", b):
            continue
        return False
    return True


def gcc_available() -> bool:
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _try_unlink(path: str, retries: int = 8) -> None:
    """Удаляет файл; на Windows повторяет при блокировке exe."""
    for attempt in range(retries):
        try:
            if os.path.isfile(path):
                os.remove(path)
            return
        except PermissionError:
            time.sleep(0.15 * (attempt + 1))


def gcc_compile_and_run(c_code: str, *, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """
    Компилирует C-код через gcc, запускает exe, возвращает результат run.
    Временные файлы удаляются явно (обход WinError 5 при очистке temp).
    """
    tmp = tempfile.mkdtemp()
    c_path = os.path.join(tmp, "out.c")
    exe = os.path.join(tmp, "out.exe" if sys.platform == "win32" else "out")
    try:
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_code)
        comp = subprocess.run(
            ["gcc", "-o", exe, c_path, "-lm"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or tmp,
        )
        if comp.returncode != 0:
            return comp
        return subprocess.run(
            [exe],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            cwd=cwd or tmp,
        )
    finally:
        _try_unlink(exe)
        _try_unlink(c_path)
        shutil.rmtree(tmp, ignore_errors=True)
