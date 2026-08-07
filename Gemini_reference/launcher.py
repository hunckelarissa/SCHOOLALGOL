#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Полный цикл: интерпретация -> транспиляция -> GCC -> запуск exe."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def run_main_step(args: list[str], title: str, verbose: bool) -> tuple[bool, float]:
    """Запускает main.py как подпроцесс. Возвращает (успех, секунды)."""
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "main.py")] + args
    if verbose:
        print(f"\n>>> команда: {' '.join(cmd)}", file=sys.stderr)
    t0 = time.perf_counter()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        cmd,
        cwd=SCRIPT_DIR,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.perf_counter() - t0
    ok = result.returncode == 0
    if not ok:
        print(f"\n>>> {title}: код возврата {result.returncode}", file=sys.stderr)
    return ok, elapsed


def main() -> None:
    _configure_utf8()
    os.chdir(SCRIPT_DIR)

    parser = argparse.ArgumentParser(description="Полный цикл Gemini (.alg -> C -> exe)")
    parser.add_argument("program", nargs="?", default="program.alg", help="Файл .alg")
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод этапов")
    args = parser.parse_args()

    program = args.program
    verbose = args.verbose
    extra = ["--verbose"] if verbose else []

    if not os.path.isfile(os.path.join(SCRIPT_DIR, "main.py")):
        print("ОШИБКА: main.py не найден", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(os.path.join(SCRIPT_DIR, program)):
        print(f"ОШИБКА: {program} не найден", file=sys.stderr)
        sys.exit(1)

    timings: list[tuple[str, float]] = []

    print(f"Рабочая директория: {os.getcwd()}")
    print(f"Программа: {program}")

    ok, t = run_main_step([program] + extra, "интерпретация", verbose)
    timings.append(("Интерпретация", t))
    if not ok:
        sys.exit(1)

    ok, t = run_main_step([program, "--transpile"] + extra, "транспиляция", verbose)
    timings.append(("Транспиляция", t))
    if not ok:
        sys.exit(1)

    c_file = program.replace(".alg", ".c")
    exe_file = "program.exe" if os.name == "nt" else program.replace(".alg", "")
    if not c_file.endswith(".c"):
        exe_file = "out.exe" if os.name == "nt" else "out"
    c_path = os.path.join(SCRIPT_DIR, c_file)
    exe_path = os.path.join(SCRIPT_DIR, exe_file if program == "program.alg" else program.replace(".alg", ".exe" if os.name == "nt" else ""))

    # Имя exe по имени .c
    base = os.path.splitext(c_file)[0]
    exe_path = os.path.join(SCRIPT_DIR, base + (".exe" if os.name == "nt" else ""))

    print("\n" + "=" * 60)
    print("КОМПИЛЯЦИЯ (GCC)")
    print("=" * 60)
    t0 = time.perf_counter()
    try:
        comp = subprocess.run(
            ["gcc", c_path, "-o", exe_path, "-lm"],
            cwd=SCRIPT_DIR,
            capture_output=not verbose,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print("ОШИБКА: GCC не найден в PATH", file=sys.stderr)
        sys.exit(1)
    timings.append(("Компиляция GCC", time.perf_counter() - t0))
    if comp.returncode != 0:
        print(comp.stderr or comp.stdout, file=sys.stderr)
        sys.exit(1)
    if verbose:
        print("Компиляция успешна")

    print("\n" + "=" * 60)
    print("ЗАПУСК EXE")
    print("=" * 60)
    t0 = time.perf_counter()
    try:
        subprocess.run([exe_path], cwd=SCRIPT_DIR, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)
    timings.append(("Запуск exe", time.perf_counter() - t0))

    print("\n" + "=" * 60)
    print("УСПЕХ: все этапы пройдены")
    print("=" * 60)
    total = sum(t for _, t in timings)
    print("Время этапов:")
    for name, sec in timings:
        print(f"  {name}: {sec:.3f} с")
    print(f"  Итого: {total:.3f} с")


if __name__ == "__main__":
    main()
