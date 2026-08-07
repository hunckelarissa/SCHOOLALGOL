# repl.py — интерактивный режим языка .alg (русские ключевые слова)

from __future__ import annotations

import sys
from typing import List

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from semantic_analyzer import SemanticAnalyzer
from errors import InterpreterError, ParserError, LexerError, SemanticError, format_error
from alg_warnings import WarningCollector
from constants import repl_wrap

_EXIT_WORDS = frozenset({"выход", "exit", "quit", ".выход", ".exit", ".quit"})


def _configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def _looks_incomplete(error: ParserError) -> bool:
    msg = str(error).lower()
    markers = (
        "ожидалось",
        "неожиданный конец",
        "кон'",
        "все'",
        "кц'",
        "то'",
        "иначе'",
    )
    return any(m in msg for m in markers)


def _run_source(
    source: str,
    *,
    verbose: bool,
    trace: bool,
    warnings: WarningCollector,
) -> None:
    tokens = list(Lexer(source).generate_tokens())
    tree = Parser(tokens).parse()
    SemanticAnalyzer(tree, "<repl>", verbose=verbose, warnings=warnings).analyze()
    print("--- REPL (выполнение) ---")
    interpreter = Interpreter(
        tree,
        "<repl>",
        verbose=verbose,
        warnings=warnings,
        trace=trace,
    )
    interpreter.run()
    print("------------------------")


def run_repl(*, verbose: bool = False, trace: bool = False, lang: str = "ru") -> int:
    """Интерактивный цикл: накопление строк тела программы и выполнение."""
    _configure_utf8()
    warnings = WarningCollector(verbose=verbose)
    lang = (lang or "ru").lower()
    prompt = "alg> "

    try:
        import readline  # noqa: F401 — история на Unix/macOS
    except ImportError:
        pass

    history: List[str] = []
    body: List[str] = []
    continuation = False

    if lang == "en":
        print("Interactive .alg mode (English keywords)")
        print("Commands: exit | quit | .reset | .history")
        print("Empty line — run accumulated fragment.")
        print("Multiline (if/loop): continue on ...> prompt")
    else:
        print("Интерактивный режим .alg")
        print("Команды: выход | .reset (очистить накопленный код) | .история")
        print("Пустая строка — выполнить накопленный фрагмент.")
        print("Многострочные конструкции (если/нц): продолжайте ввод на приглашении ...>")

    while True:
        try:
            line_prompt = "...> " if continuation else prompt
            line = input(line_prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nLeaving REPL." if lang == "en" else "\nВыход из REPL.")
            return warnings.finalize()

        stripped = line.strip()
        if stripped.lower() in _EXIT_WORDS:
            print("Leaving REPL." if lang == "en" else "Выход из REPL.")
            return warnings.finalize()

        if stripped == ".reset":
            body.clear()
            continuation = False
            print("Buffer cleared." if lang == "en" else "Буфер очищен.")
            continue

        if stripped in (".история", ".history"):
            if not history:
                print("(history empty)" if lang == "en" else "(история пуста)")
            else:
                for i, h in enumerate(history, 1):
                    print(f"  {i}: {h}")
            continue

        if stripped == "":
            if not body:
                continue
            source = repl_wrap("\n".join(body), lang)
            try:
                _run_source(source, verbose=verbose, trace=trace, warnings=warnings)
                continuation = False
            except (LexerError, ParserError, InterpreterError, SemanticError) as e:
                if isinstance(e, ParserError) and _looks_incomplete(e):
                    print(
                        "... syntax incomplete, continue typing"
                        if lang == "en"
                        else "... синтаксис не завершён, продолжайте ввод",
                        file=sys.stderr,
                    )
                    continuation = True
                else:
                    print(format_error(e, source), file=sys.stderr)
                    continuation = False
            continue

        history.append(line)
        body.append(line)
        source = repl_wrap("\n".join(body), lang)
        try:
            _run_source(source, verbose=verbose, trace=trace, warnings=warnings)
            continuation = False
        except ParserError as e:
            if _looks_incomplete(e):
                continuation = True
            else:
                print(format_error(e, source), file=sys.stderr)
                body.pop()
                continuation = False
        except (LexerError, InterpreterError, SemanticError) as e:
            print(format_error(e, source), file=sys.stderr)
            body.pop()
            continuation = False
