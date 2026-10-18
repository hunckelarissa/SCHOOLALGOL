# main.py
from __future__ import annotations

import sys
import traceback

from alg_warnings import WarningCollector
from ast_dump import dump_ast_json, dump_ast_text
from diagnostics import count_ast_nodes, log_verbose
from errors import InterpreterError, format_error
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from c_transpiler import CTranspiler
from semantic_analyzer import SemanticAnalyzer
from lang_tokens import TokenType, token_type_bilingual_label
from version import __version__


def _print_usage() -> None:
    print(f"Интерпретатор/транспилятор языка .alg, версия {__version__}")
    print("Использование: python main.py <путь_к_файлу.alg> [опции]")
    print("               python main.py --repl [опции]")
    print("  --run                   выполнение программы (по умолчанию)")
    print("  --transpile             вывести C-код в файл <имя>.c вместо выполнения")
    print("  --check                 лексика + синтаксис + семантика (без выполнения)")
    print("  --dump-ast              вывести дерево разбора (AST) вместо выполнения")
    print("  --dump-ast-format F     формат AST: text (по умолчанию) или json")
    print("  --repl                  интерактивный режим")
    print("  --lang ru|en            язык ключевых слов в REPL (по умолчанию ru)")
    print("  --verbose               этапы пайплайна и предупреждения в stderr")
    print("  --warnings-as-errors    предупреждения → код выхода 3")
    print("  --trace                 пошаговая трассировка операторов (stderr)")
    print("  --permissive            при --transpile: неизвестные узлы → предупреждение")
    print("  --keep-cyrillic         при --transpile: кириллица в идентификаторах C")
    print("  --debug-protocol        SHAYDBG JSONL для Eclipse Step Debug")
    print("  --break N               точка останова (номер строки; можно повторять)")
    print("  --version, -v           показать версию")
    print("  --help, -h              эта справка")


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        _print_usage()
        sys.exit(2)

    if argv[0] in ("--version", "-v"):
        print(__version__)
        sys.exit(0)
    if argv[0] in ("--help", "-h"):
        _print_usage()
        sys.exit(0)

    transpile_mode = False
    check_mode = False
    dump_ast = False
    dump_ast_format = "text"
    repl_mode = False
    debug_protocol = False
    verbose = False
    warnings_as_errors = False
    trace = False
    permissive = False
    keep_cyrillic = False
    break_lines: list[int] = []
    source_file: str | None = None
    repl_lang = "ru"

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--run":
            pass  # Выполнение по умолчанию
        elif arg == "--transpile":
            transpile_mode = True
        elif arg == "--check":
            check_mode = True
        elif arg == "--dump-ast":
            dump_ast = True
        elif arg == "--dump-ast-format":
            i += 1
            if i >= len(argv) or argv[i] not in ("text", "json"):
                print("Ошибка: --dump-ast-format требует text или json", file=sys.stderr)
                sys.exit(2)
            dump_ast_format = argv[i]
        elif arg.startswith("--dump-ast-format="):
            dump_ast_format = arg.split("=", 1)[1]
            if dump_ast_format not in ("text", "json"):
                print("Ошибка: --dump-ast-format требует text или json", file=sys.stderr)
                sys.exit(2)
        elif arg == "--repl":
            repl_mode = True
        elif arg == "--lang":
            i += 1
            if i >= len(argv) or argv[i] not in ("ru", "en"):
                print("Ошибка: --lang требует ru или en", file=sys.stderr)
                sys.exit(2)
            repl_lang = argv[i]
        elif arg.startswith("--lang="):
            repl_lang = arg.split("=", 1)[1]
            if repl_lang not in ("ru", "en"):
                print("Ошибка: --lang требует ru или en", file=sys.stderr)
                sys.exit(2)
        elif arg == "--verbose":
            verbose = True
        elif arg == "--warnings-as-errors":
            warnings_as_errors = True
        elif arg == "--trace":
            trace = True
        elif arg == "--permissive":
            permissive = True
        elif arg == "--keep-cyrillic":
            keep_cyrillic = True
        elif arg == "--debug-protocol":
            debug_protocol = True
        elif arg == "--break":
            i += 1
            if i >= len(argv):
                print("Ошибка: --break требует номер строки", file=sys.stderr)
                sys.exit(2)
            try:
                break_lines.append(int(argv[i]))
            except ValueError:
                print(f"Ошибка: неверный номер строки для --break: {argv[i]!r}", file=sys.stderr)
                sys.exit(2)
        elif arg.startswith("--break="):
            try:
                break_lines.append(int(arg.split("=", 1)[1]))
            except ValueError:
                print(f"Ошибка: неверный номер строки для --break: {arg!r}", file=sys.stderr)
                sys.exit(2)
        elif arg.startswith("-"):
            print(f"Ошибка: неизвестный аргумент «{arg}»", file=sys.stderr)
            _print_usage()
            sys.exit(2)
        else:
            if source_file is not None:
                print(f"Ошибка: лишний аргумент «{arg}»", file=sys.stderr)
                _print_usage()
                sys.exit(2)
            source_file = arg
        i += 1

    if repl_mode:
        if source_file or transpile_mode or dump_ast or debug_protocol or check_mode:
            print(
                "Ошибка: --repl несовместим с файлом, --transpile, --dump-ast, "
                "--check и --debug-protocol",
                file=sys.stderr,
            )
            sys.exit(2)
        from repl import run_repl

        sys.exit(run_repl(verbose=verbose, trace=trace, lang=repl_lang))

    if not source_file:
        _print_usage()
        sys.exit(2)

    if check_mode and (transpile_mode or debug_protocol):
        print("Ошибка: --check несовместим с --transpile и --debug-protocol", file=sys.stderr)
        sys.exit(2)
    if transpile_mode and debug_protocol:
        print("Ошибка: --transpile несовместим с --debug-protocol", file=sys.stderr)
        sys.exit(2)
    if dump_ast and (transpile_mode or debug_protocol):
        print("Ошибка: --dump-ast несовместим с --transpile и --debug-protocol", file=sys.stderr)
        sys.exit(2)

    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл не найден «{source_file}»", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Ошибка чтения файла «{source_file}»: {e}", file=sys.stderr)
        sys.exit(1)

    quiet = bool(debug_protocol)
    show_verbose = verbose and not quiet
    warnings = WarningCollector(verbose=show_verbose, warnings_as_errors=warnings_as_errors)

    try:
        log_verbose(show_verbose, "этап", "Лексический анализ…")
        lexer = Lexer(source_code)
        tokens = list(lexer.generate_tokens())
        log_verbose(
            show_verbose,
            "этап",
            f"Лексический анализ завершён: {len(tokens)} токенов",
        )
        if show_verbose:
            for tok in tokens:
                if tok.type == TokenType.EOF:
                    continue
                log_verbose(
                    show_verbose,
                    "токен",
                    f"«{tok.value}» → {token_type_bilingual_label(tok.type)} [{tok.type.name}]",
                )

        log_verbose(show_verbose, "этап", "Синтаксический анализ…")
        parser = Parser(tokens)
        ast_tree = parser.parse()
        node_count = count_ast_nodes(ast_tree)
        log_verbose(
            show_verbose,
            "этап",
            f"Синтаксический анализ завершён: {len(ast_tree.declarations)} объявлений, "
            f"~{node_count} узлов AST",
        )

        log_verbose(show_verbose, "этап", "Семантический анализ…")
        SemanticAnalyzer(
            ast_tree, source_file, verbose=show_verbose, warnings=warnings
        ).analyze()
        log_verbose(show_verbose, "этап", "Семантический анализ завершён")

        if dump_ast:
            if dump_ast_format == "json":
                print(dump_ast_json(ast_tree))
            else:
                print(dump_ast_text(ast_tree))
            log_verbose(show_verbose, "этап", "AST выведен")
            sys.exit(warnings.finalize())

        if check_mode:
            print(f"OK: синтаксис и семантика в порядке ({source_file})")
            sys.exit(warnings.finalize())
        elif transpile_mode:
            log_verbose(show_verbose, "этап", "Транспиляция в C…")
            print(f"--- Транспиляция в C (версия {__version__}) ---")
            transpiler = CTranspiler(
                ast_tree,
                source_file,
                verbose=show_verbose,
                warnings=warnings,
                permissive=permissive,
                keep_cyrillic=keep_cyrillic,
            )
            c_code = transpiler.transpile()

            output_file = source_file.replace(".alg", ".c")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(c_code)
            print(f"Код сохранен в файл: {output_file}")
            print("------------------------")
            log_verbose(show_verbose, "этап", f"Записано {len(c_code)} символов C-кода")
        else:
            log_verbose(show_verbose, "этап", "Интерпретация…")
            if not quiet:
                print(f"--- Вывод программы (версия {__version__}) ---")
            interpreter = Interpreter(
                ast_tree,
                source_file,
                verbose=show_verbose,
                warnings=warnings,
                trace=trace and not quiet,
                debug_protocol=debug_protocol,
                break_lines=break_lines,
                source_lines=source_code.splitlines(),
            )
            interpreter.run()
            if not quiet:
                print("-----------------------")
            log_verbose(show_verbose, "этап", "Интерпретация завершена")

        sys.exit(warnings.finalize())

    except SystemExit:
        raise
    except InterpreterError as e:
        print(format_error(e, source_code), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
