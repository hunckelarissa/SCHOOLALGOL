# main.py
from __future__ import annotations

import argparse
import sys
import traceback

from diagnostics import count_ast_nodes, log_verbose
from errors import InterpreterError, LexerError, ParserError, SemanticError, TranspilerError, format_error
from lang_tokens import TokenType, token_type_bilingual_label
from interpreter import Interpreter
from c_transpiler import CTranspiler
from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from version import __version__
from alg_warnings import WarningCollector
from ast_dump import dump_ast_text, dump_ast_json
from repl import run_repl


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=f"Интерпретатор и C-транспилятор языка .alg (версия {__version__})",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Путь к исходному файлу .alg",
    )
    parser.add_argument(
        "--transpile",
        action="store_true",
        help="Транспилировать в C (<имя>.c) вместо выполнения",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод этапов компиляции и выполнения (в stderr)",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Считать предупреждения ошибками (код выхода 3)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Пошаговая трассировка операторов (в stderr)",
    )
    parser.add_argument(
        "--debug-protocol",
        action="store_true",
        help="SHAYDBG JSONL для Eclipse Step Debug",
    )
    parser.add_argument(
        "--break",
        dest="break_lines",
        action="append",
        type=int,
        default=[],
        help="Точка останова (номер строки; можно повторять)",
    )
    parser.add_argument(
        "--permissive",
        action="store_true",
        help="При транспиляции: неподдерживаемые узлы - предупреждение и заглушка в C",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Интерактивный режим (построчный ввод фрагментов .alg)",
    )
    parser.add_argument(
        "--lang",
        choices=("ru", "en"),
        default="ru",
        help="Язык ключевых слов в REPL: ru (по умолчанию) или en",
    )
    parser.add_argument(
        "--dump-ast",
        action="store_true",
        help="Вывести дерево разбора (AST) вместо выполнения",
    )
    parser.add_argument(
        "--dump-ast-format",
        choices=("text", "json"),
        default="text",
        help="Формат вывода AST: text или json (по умолчанию text)",
    )
    parser.add_argument(
        "--keep-cyrillic",
        action="store_true",
        help="При транспиляции: сохранять кириллицу в идентификаторах C (UTF-8)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    return parser


def run_pipeline(
    source_file: str,
    source_code: str,
    *,
    transpile: bool,
    verbose: bool,
    warnings: WarningCollector,
    permissive: bool = False,
    trace: bool = False,
    dump_ast: bool = False,
    dump_ast_format: str = "text",
    keep_cyrillic: bool = False,
    debug_protocol: bool = False,
    break_lines: list[int] | None = None,
) -> int:
    """Выполняет лексический разбор, парсинг и интерпретацию или транспиляцию."""
    quiet = bool(debug_protocol)
    log_verbose(verbose and not quiet, "этап", "Лексический анализ…")
    lexer = Lexer(source_code)
    tokens = list(lexer.generate_tokens())
    token_count = len(tokens)
    log_verbose(verbose and not quiet, "этап", f"Лексический анализ завершён: {token_count} токенов")
    if verbose and not quiet:
        for tok in tokens:
            if tok.type == TokenType.EOF:
                continue
            log_verbose(
                verbose,
                "токен",
                f"«{tok.value}» → {token_type_bilingual_label(tok.type)} [{tok.type.name}]",
            )

    log_verbose(verbose and not quiet, "этап", "Синтаксический анализ…")
    ast_tree = Parser(tokens).parse()
    node_count = count_ast_nodes(ast_tree)
    decl_count = len(ast_tree.declarations)
    log_verbose(
        verbose and not quiet,
        "этап",
        f"Синтаксический анализ завершён: {decl_count} объявлений верхнего уровня, "
        f"~{node_count} узлов AST",
    )

    log_verbose(verbose and not quiet, "этап", "Семантический анализ…")
    SemanticAnalyzer(ast_tree, source_file, verbose=verbose and not quiet).analyze()
    log_verbose(verbose and not quiet, "этап", "Семантический анализ завершён")

    if dump_ast:
        if dump_ast_format == "json":
            print(dump_ast_json(ast_tree))
        else:
            print(dump_ast_text(ast_tree))
        log_verbose(verbose and not quiet, "этап", "AST выведен")
        return warnings.finalize()

    if transpile:
        log_verbose(verbose and not quiet, "этап", "Транспиляция в C…")
        print(f"--- Транспиляция в C (версия {__version__}) ---")
        transpiler = CTranspiler(
            ast_tree,
            source_file,
            verbose=verbose,
            warnings=warnings,
            permissive=permissive,
            keep_cyrillic=keep_cyrillic,
        )
        c_code = transpiler.transpile()
        output_file = source_file.replace(".alg", ".c")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(c_code)
        print(f"Код сохранён в файл: {output_file}")
        log_verbose(verbose and not quiet, "этап", f"Записано {len(c_code)} символов C-кода")
        print("------------------------")
    else:
        log_verbose(verbose and not quiet, "этап", "Интерпретация…")
        if not quiet:
            print(f"--- Вывод программы (версия {__version__}) ---")
        interpreter = Interpreter(
            ast_tree,
            source_file,
            verbose=verbose,
            warnings=warnings,
            trace=trace,
            debug_protocol=debug_protocol,
            break_lines=break_lines,
            source_lines=source_code.splitlines(),
        )
        interpreter.run()
        if not quiet:
            print("-----------------------")
        log_verbose(verbose and not quiet, "этап", "Интерпретация завершена")

    return warnings.finalize()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.repl:
        if args.source or args.transpile or args.dump_ast or args.debug_protocol:
            print("Ошибка: --repl несовместим с файлом, --transpile, --dump-ast и --debug-protocol", file=sys.stderr)
            sys.exit(2)
        sys.exit(run_repl(verbose=args.verbose, trace=args.trace, lang=args.lang))

    if not args.source:
        parser.print_help()
        sys.exit(2)

    source_file = args.source
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл не найден «{source_file}»", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Ошибка чтения файла «{source_file}»: {e}", file=sys.stderr)
        sys.exit(1)

    warnings = WarningCollector(
        verbose=args.verbose,
        warnings_as_errors=args.warnings_as_errors,
    )

    try:
        warn_exit = run_pipeline(
            source_file,
            source_code,
            transpile=args.transpile,
            verbose=args.verbose,
            warnings=warnings,
            permissive=args.permissive,
            trace=args.trace,
            dump_ast=args.dump_ast,
            dump_ast_format=args.dump_ast_format,
            keep_cyrillic=args.keep_cyrillic,
            debug_protocol=args.debug_protocol,
            break_lines=args.break_lines,
        )
        sys.exit(warn_exit)
    except SystemExit:
        raise
    except InterpreterError as e:
        print(format_error(e, source_code), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
