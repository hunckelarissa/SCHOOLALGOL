# main.py
from __future__ import annotations

import sys
import traceback

from alg_warnings import WarningCollector
from ast_dump import dump_ast_json, dump_ast_text
from diagnostics import count_ast_nodes, log_verbose
from errors import InterpreterError, format_error
from i18n import set_lang, t
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from c_transpiler import CTranspiler
from semantic_analyzer import SemanticAnalyzer
from lang_tokens import TokenType, token_type_bilingual_label
from version import __version__


def _print_usage() -> None:
    print(t("usage_title", version=__version__))
    print(t("usage_line1"))
    print(t("usage_line2"))
    print(t("opt_run"))
    print(t("opt_transpile"))
    print(t("opt_check"))
    print(t("opt_dump_ast"))
    print(t("opt_dump_fmt"))
    print(t("opt_repl"))
    print(t("opt_repl_persist"))
    print(t("opt_lang"))
    print(t("opt_verbose"))
    print(t("opt_wae"))
    print(t("opt_trace"))
    print(t("opt_perm"))
    print(t("opt_cyr"))
    print(t("opt_dbg"))
    print(t("opt_break"))
    print(t("opt_ver"))
    print(t("opt_help"))


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        _print_usage()
        sys.exit(2)

    # Early --lang so help/errors use the requested language
    for i, arg in enumerate(argv):
        if arg == "--lang" and i + 1 < len(argv) and argv[i + 1] in ("ru", "en"):
            set_lang(argv[i + 1])
            break
        if arg.startswith("--lang=") and arg.split("=", 1)[1] in ("ru", "en"):
            set_lang(arg.split("=", 1)[1])
            break
    else:
        set_lang(None)  # detect from env / default ru

    # Allow `--lang en --help` / `--lang ru --version` (not only as argv[0])
    if "--help" in argv or "-h" in argv:
        _print_usage()
        sys.exit(0)
    if ("--version" in argv or "-v" in argv) and not any(
        a.endswith(".alg") for a in argv
    ) and "--repl" not in argv:
        print(__version__)
        sys.exit(0)

    transpile_mode = False
    check_mode = False
    dump_ast = False
    dump_ast_format = "text"
    repl_mode = False
    repl_persist = False
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
            pass  # default execution
        elif arg == "--transpile":
            transpile_mode = True
        elif arg == "--check":
            check_mode = True
        elif arg == "--dump-ast":
            dump_ast = True
        elif arg == "--dump-ast-format":
            i += 1
            if i >= len(argv) or argv[i] not in ("text", "json"):
                print(t("err_dump_fmt"), file=sys.stderr)
                sys.exit(2)
            dump_ast_format = argv[i]
        elif arg.startswith("--dump-ast-format="):
            dump_ast_format = arg.split("=", 1)[1]
            if dump_ast_format not in ("text", "json"):
                print(t("err_dump_fmt"), file=sys.stderr)
                sys.exit(2)
        elif arg == "--repl":
            repl_mode = True
        elif arg == "--repl-persist":
            repl_persist = True
            repl_mode = True
        elif arg == "--lang":
            i += 1
            if i >= len(argv) or argv[i] not in ("ru", "en"):
                print(t("err_lang"), file=sys.stderr)
                sys.exit(2)
            repl_lang = argv[i]
            set_lang(repl_lang)
        elif arg.startswith("--lang="):
            repl_lang = arg.split("=", 1)[1]
            if repl_lang not in ("ru", "en"):
                print(t("err_lang"), file=sys.stderr)
                sys.exit(2)
            set_lang(repl_lang)
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
                print(t("err_break"), file=sys.stderr)
                sys.exit(2)
            try:
                break_lines.append(int(argv[i]))
            except ValueError:
                print(t("err_break_bad", value=argv[i]), file=sys.stderr)
                sys.exit(2)
        elif arg.startswith("--break="):
            try:
                break_lines.append(int(arg.split("=", 1)[1]))
            except ValueError:
                print(t("err_break_bad", value=arg), file=sys.stderr)
                sys.exit(2)
        elif arg.startswith("-"):
            print(t("err_unknown_arg", arg=arg), file=sys.stderr)
            _print_usage()
            sys.exit(2)
        else:
            if source_file is not None:
                print(t("err_extra_arg", arg=arg), file=sys.stderr)
                _print_usage()
                sys.exit(2)
            source_file = arg
        i += 1

    if repl_mode:
        if source_file or transpile_mode or dump_ast or debug_protocol or check_mode:
            print(t("err_repl_incompat"), file=sys.stderr)
            sys.exit(2)
        from repl import run_repl

        sys.exit(
            run_repl(
                verbose=verbose,
                trace=trace,
                lang=repl_lang,
                persist=repl_persist,
            )
        )

    if not source_file:
        _print_usage()
        sys.exit(2)

    if check_mode and (transpile_mode or debug_protocol):
        print(t("err_check_incompat"), file=sys.stderr)
        sys.exit(2)
    if transpile_mode and debug_protocol:
        print(t("err_tr_dbg"), file=sys.stderr)
        sys.exit(2)
    if dump_ast and (transpile_mode or debug_protocol):
        print(t("err_dump_incompat"), file=sys.stderr)
        sys.exit(2)

    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(t("err_file_not_found", path=source_file), file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(t("err_file_read", path=source_file, error=e), file=sys.stderr)
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
            print(t("ok_check", path=source_file))
            sys.exit(warnings.finalize())
        elif transpile_mode:
            log_verbose(show_verbose, "этап", "Транспиляция в C…")
            print(t("banner_transpile", version=__version__))
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
            print(t("saved_c", path=output_file))
            print("------------------------")
            log_verbose(show_verbose, "этап", f"Записано {len(c_code)} символов C-кода")
        else:
            log_verbose(show_verbose, "этап", "Интерпретация…")
            if not quiet:
                print(t("banner_run", version=__version__))
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
        from i18n import get_lang

        prefix = "Error" if get_lang() == "en" else "Ошибка"
        print(f"{prefix}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
