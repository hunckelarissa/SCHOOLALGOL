"""UI language for CLI help, banners, and error wrappers (RU / EN).

Language selection (first match wins):
  1. ``set_lang()`` / CLI ``--lang``
  2. Environment ``ALG_LANG=ru|en``
  3. ``LANG`` / ``LC_ALL`` starting with ``ru`` → Russian
  4. Default: ``ru`` (backward compatible with existing diagnostics)
"""

from __future__ import annotations

import os
from typing import Any, Optional

_LANG: Optional[str] = None

_MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "usage_title": "Интерпретатор/транспилятор языка .alg, версия {version}",
        "usage_line1": "Использование: python main.py <путь_к_файлу.alg> [опции]",
        "usage_line2": "               python main.py --repl [опции]",
        "opt_run": "  --run                   выполнение программы (по умолчанию)",
        "opt_transpile": "  --transpile             вывести C-код в файл <имя>.c вместо выполнения",
        "opt_check": "  --check                 лексика + синтаксис + семантика (без выполнения)",
        "opt_dump_ast": "  --dump-ast              вывести дерево разбора (AST) вместо выполнения",
        "opt_dump_fmt": "  --dump-ast-format F     формат AST: text (по умолчанию) или json",
        "opt_repl": "  --repl                  интерактивный режим",
        "opt_repl_persist": "  --repl-persist          REPL: сохранять переменные между фрагментами",
        "opt_lang": "  --lang ru|en            язык UI (справка, ошибки) и REPL (по умолчанию: ru)",
        "opt_verbose": "  --verbose               этапы пайплайна и предупреждения в stderr",
        "opt_wae": "  --warnings-as-errors    предупреждения → код выхода 3",
        "opt_trace": "  --trace                 пошаговая трассировка операторов (stderr)",
        "opt_perm": "  --permissive            при --transpile: неизвестные узлы → предупреждение",
        "opt_cyr": "  --keep-cyrillic         при --transpile: кириллица в идентификаторах C",
        "opt_dbg": "  --debug-protocol        SHAYDBG JSONL для Eclipse Step Debug",
        "opt_break": "  --break N               точка останова (номер строки; можно повторять)",
        "opt_ver": "  --version, -v           показать версию",
        "opt_help": "  --help, -h              эта справка",
        "err_dump_fmt": "Ошибка: --dump-ast-format требует text или json",
        "err_lang": "Ошибка: --lang требует ru или en",
        "err_break": "Ошибка: --break требует номер строки",
        "err_break_bad": "Ошибка: неверный номер строки для --break: {value!r}",
        "err_unknown_arg": "Ошибка: неизвестный аргумент «{arg}»",
        "err_extra_arg": "Ошибка: лишний аргумент «{arg}»",
        "err_repl_incompat": (
            "Ошибка: --repl несовместим с файлом, --transpile, --dump-ast, "
            "--check и --debug-protocol"
        ),
        "err_check_incompat": "Ошибка: --check несовместим с --transpile и --debug-protocol",
        "err_tr_dbg": "Ошибка: --transpile несовместим с --debug-protocol",
        "err_dump_incompat": "Ошибка: --dump-ast несовместим с --transpile и --debug-protocol",
        "err_file_not_found": "Ошибка: файл не найден «{path}»",
        "err_file_read": "Ошибка чтения файла «{path}»: {error}",
        "ok_check": "OK: синтаксис и семантика в порядке ({path})",
        "banner_transpile": "--- Транспиляция в C (версия {version}) ---",
        "banner_run": "--- Вывод программы (версия {version}) ---",
        "saved_c": "Код сохранен в файл: {path}",
        "lexer_prefix": "[Строка {line}:{col}] Лексическая ошибка: {message}{char_part}",
        "parser_prefix": "[Строка {line}:{col}] Синтаксическая ошибка: {message}.{ctx}",
        "semantic_prefix": "{loc}Семантическая ошибка: {message}",
        "transpiler_prefix": "Ошибка транспиляции: {message}{extra}",
        "hint_lexer": "Подсказка: проверьте раскладку клавиатуры и допустимые символы языка .alg.",
        "hint_parser": (
            "Подсказка: сверьте синтаксис с GRAMMAR.md "
            "(алг … нач … кон, :=, нц … кц)."
        ),
        "hint_transpiler": (
            "Подсказка: не все конструкции .alg поддерживаются в C-транспиляторе; см. README."
        ),
        "stack_header": "Трассировка вызовов (от последнего к первому):\n",
        "stack_frame": "  в «{name}»\n",
        "ctx_prefix": " Контекст: «{context}».",
        "char_part": " (символ {char})",
        "loc_line": "[Строка {line}:{col}] ",
        # Semantic bodies (high-frequency)
        "sem_redeclare": "Повторное объявление «{name}»",
        "sem_undefined": "Переменная, константа или тип «{name}» не определена",
        "sem_unknown_type": "Неизвестный тип «{name}»",
        "sem_no_main": "Не найдена главная программа «алг {label}»",
        "sem_break_outside": "Оператор «выход / break» допустим только внутри цикла нц … кц",
        "sem_continue_outside": "Оператор «продолжить / continue» допустим только внутри цикла нц … кц",
        "sem_return_outside": "Оператор «возврат / return» допустим только внутри процедуры или функции",
        "sem_return_expr_proc": "«возврат выражение» допустим только в функции (алг … рез)",
        "sem_void_in_expr": "Процедура «{name}» не возвращает значение и не может использоваться в выражении",
        "sem_assign_lit": "Тип несовместим при :=: нельзя присвоить лит переменной типа «{left}»",
        "sem_assign_log": "Тип несовместим при :=: нельзя присвоить лог переменной типа «{left}»",
        "sem_assign_to_log": "Тип несовместим при :=: нельзя присвоить «{right}» переменной типа лог",
        "sem_assign_types": "Тип несовместим при :=: «{right}» → «{left}»",
        "sem_bad_lvalue": "Нельзя присвоить значение этому выражению",
        "sem_need_file": "Переменная «{name}» должна иметь тип файл",
        "sem_bool_input": "Ожидалось логическое значение (да/нет/true/false) для «{name}», получено «{text}»",
        "sem_len_number": "«длина» / len ожидает строку, массив или словарь, а не число",
        "sem_assign_undeclared": "Попытка присвоить значение необъявленной локальной переменной «{name}»",
        "sem_const_assign": "Нельзя изменять значение константы «{name}»",
        "sem_div_zero": "Деление на ноль",
        "sem_index_bounds": "Индекс {index} вне границ массива",
        "sem_dict_key": "В словаре нет ключа «{key}»",
        "sem_not_indexable": "Переменная не является массивом или словарем",
        "sem_array_index_num": "Индекс массива должен быть числом",
        "sem_dict_key_str": "Ключ для словаря должен быть строкой",
        "sem_arity": "Функция «{name}» ожидает {expected} аргумент(ов), а получила {got}",
        "sem_sub_undefined": "Процедура или функция «{name}» не определена",
        "sem_args_count": "Неверное количество аргументов для «{name}»",
        "sem_void_value": "Процедура не возвращает значение",
        "sem_void_arg": "Процедура не возвращает значение и не может быть аргументом",
        "sem_field_missing": "У записи нет поля «{name}»",
        "sem_file_var": "Первый аргумент «{name}» должен быть файловой переменной",
        "sem_file_mode": "Неизвестный режим файла: «{mode}»",
        "sem_file_open": "Не удалось открыть файл «{path}» (абсолютный путь «{abs}», режим «{mode}»{errno_hint}): {error}",
        "sem_num_only": "Функция «{name}» применима только к числам",
        "sem_sqrt_neg": "Нельзя извлечь корень из отрицательного числа",
        "sem_div_zero_in": "Деление на ноль в «{name}»",
        "sem_convert": "Невозможно преобразовать «{value}» в {target}",
        "sem_convert_int": "целое число",
        "sem_convert_float": "вещественное число",
        "sem_pow_error": "Ошибка вычисления степени: {error}",
        "sem_eof_file": "Функция «конецфайла» / eof применима только к файлу для чтения",
        "sem_const_redeclare": "Переопределение константы «{name}»",
        "sem_void_const": "Процедура не может быть присвоена константе",
        "sem_array_bounds_decl": "Начальный индекс массива {start} больше конечного {end}",
        "sem_no_member": "Невозможно получить доступ к члену",
        "sem_void_expr": "Выражение не имеет значения (процедура?)",
        "sem_void_index": "Индекс не имеет значения",
        "sem_void_left": "Левый операнд не имеет значения",
        "sem_void_right": "Правый операнд не имеет значения",
        "sem_void_operand": "Операнд не имеет значения",
        "sem_void_print": "Выражение в «вывод» / output не имеет значения",
        "sem_file_not_write": "Переменная «{name}» не открыта для записи",
        "sem_file_not_read": "Переменная «{name}» не открыта для чтения",
        "sem_file_write_err": "Ошибка записи в файл: {error}",
        "sem_for_step_zero": "Шаг цикла «нц для» / for не может быть равен нулю",
    },
    "en": {
        "usage_title": ".alg interpreter/transpiler, version {version}",
        "usage_line1": "Usage: python main.py <path/to/file.alg> [options]",
        "usage_line2": "       python main.py --repl [options]",
        "opt_run": "  --run                   run the program (default)",
        "opt_transpile": "  --transpile             write C code to <name>.c instead of running",
        "opt_check": "  --check                 lex + parse + semantics (no execution)",
        "opt_dump_ast": "  --dump-ast              print the parse tree (AST) instead of running",
        "opt_dump_fmt": "  --dump-ast-format F     AST format: text (default) or json",
        "opt_repl": "  --repl                  interactive mode",
        "opt_repl_persist": "  --repl-persist          REPL: keep variables across fragments",
        "opt_lang": "  --lang ru|en            UI language (help, errors) and REPL (default: ru)",
        "opt_verbose": "  --verbose               pipeline stages and warnings on stderr",
        "opt_wae": "  --warnings-as-errors    warnings → exit code 3",
        "opt_trace": "  --trace                 statement tracing (stderr)",
        "opt_perm": "  --permissive            with --transpile: unknown nodes → warning",
        "opt_cyr": "  --keep-cyrillic         with --transpile: keep Cyrillic in C identifiers",
        "opt_dbg": "  --debug-protocol        SHAYDBG JSONL for Eclipse Step Debug",
        "opt_break": "  --break N               breakpoint (line number; repeatable)",
        "opt_ver": "  --version, -v           show version",
        "opt_help": "  --help, -h              this help",
        "err_dump_fmt": "Error: --dump-ast-format requires text or json",
        "err_lang": "Error: --lang requires ru or en",
        "err_break": "Error: --break requires a line number",
        "err_break_bad": "Error: invalid line number for --break: {value!r}",
        "err_unknown_arg": "Error: unknown argument “{arg}”",
        "err_extra_arg": "Error: extra argument “{arg}”",
        "err_repl_incompat": (
            "Error: --repl is incompatible with a file, --transpile, --dump-ast, "
            "--check, and --debug-protocol"
        ),
        "err_check_incompat": "Error: --check is incompatible with --transpile and --debug-protocol",
        "err_tr_dbg": "Error: --transpile is incompatible with --debug-protocol",
        "err_dump_incompat": "Error: --dump-ast is incompatible with --transpile and --debug-protocol",
        "err_file_not_found": "Error: file not found “{path}”",
        "err_file_read": "Error reading file “{path}”: {error}",
        "ok_check": "OK: syntax and semantics are fine ({path})",
        "banner_transpile": "--- Transpile to C (version {version}) ---",
        "banner_run": "--- Program output (version {version}) ---",
        "saved_c": "Code saved to: {path}",
        "lexer_prefix": "[Line {line}:{col}] Lexical error: {message}{char_part}",
        "parser_prefix": "[Line {line}:{col}] Syntax error: {message}.{ctx}",
        "semantic_prefix": "{loc}Semantic error: {message}",
        "transpiler_prefix": "Transpiler error: {message}{extra}",
        "hint_lexer": "Hint: check keyboard layout and allowed .alg characters.",
        "hint_parser": (
            "Hint: compare syntax with GRAMMAR.md "
            "(proc … begin … end, :=, loop … eloop)."
        ),
        "hint_transpiler": (
            "Hint: not all .alg constructs are supported by the C transpiler; see README."
        ),
        "stack_header": "Call stack (innermost first):\n",
        "stack_frame": "  in “{name}”\n",
        "ctx_prefix": " Context: “{context}”.",
        "char_part": " (character {char})",
        "loc_line": "[Line {line}:{col}] ",
        "sem_redeclare": "Redeclaration of “{name}”",
        "sem_undefined": "Variable, constant, or type “{name}” is not defined",
        "sem_unknown_type": "Unknown type “{name}”",
        "sem_no_main": "Main program not found (“алг {label}” / proc mainprogram)",
        "sem_break_outside": "“выход / break” is only allowed inside a loop (нц … кц / loop … eloop)",
        "sem_continue_outside": "“продолжить / continue” is only allowed inside a loop",
        "sem_return_outside": "“возврат / return” is only allowed inside a procedure or function",
        "sem_return_expr_proc": "“return expression” is only allowed in a function (алг … рез / proc … res)",
        "sem_void_in_expr": "Procedure “{name}” returns no value and cannot be used in an expression",
        "sem_assign_lit": "Type mismatch in :=: cannot assign str to a variable of type “{left}”",
        "sem_assign_log": "Type mismatch in :=: cannot assign bool to a variable of type “{left}”",
        "sem_assign_to_log": "Type mismatch in :=: cannot assign “{right}” to a bool variable",
        "sem_assign_types": "Type mismatch in :=: “{right}” → “{left}”",
        "sem_bad_lvalue": "Cannot assign to this expression",
        "sem_need_file": "Variable “{name}” must have type file",
        "sem_bool_input": "Expected a boolean (да/нет/true/false) for “{name}”, got “{text}”",
        "sem_len_number": "“длина” / len expects a string, array, or dict — not a number",
        "sem_assign_undeclared": "Cannot assign to undeclared local variable “{name}”",
        "sem_const_assign": "Cannot modify constant “{name}”",
        "sem_div_zero": "Division by zero",
        "sem_index_bounds": "Index {index} is out of array bounds",
        "sem_dict_key": "Dict has no key “{key}”",
        "sem_not_indexable": "Value is not an array or dict",
        "sem_array_index_num": "Array index must be a number",
        "sem_dict_key_str": "Dict key must be a string",
        "sem_arity": "Function “{name}” expects {expected} argument(s), got {got}",
        "sem_sub_undefined": "Procedure or function “{name}” is not defined",
        "sem_args_count": "Wrong number of arguments for “{name}”",
        "sem_void_value": "Procedure does not return a value",
        "sem_void_arg": "Procedure does not return a value and cannot be used as an argument",
        "sem_field_missing": "Record has no field “{name}”",
        "sem_file_var": "First argument of “{name}” must be a file variable",
        "sem_file_mode": "Unknown file mode: “{mode}”",
        "sem_file_open": "Could not open file “{path}” (absolute “{abs}”, mode “{mode}”{errno_hint}): {error}",
        "sem_num_only": "Function “{name}” applies only to numbers",
        "sem_sqrt_neg": "Cannot take square root of a negative number",
        "sem_div_zero_in": "Division by zero in “{name}”",
        "sem_convert": "Cannot convert “{value}” to {target}",
        "sem_convert_int": "an integer",
        "sem_convert_float": "a real number",
        "sem_pow_error": "Power computation error: {error}",
        "sem_eof_file": "“конецфайла” / eof applies only to a readable file",
        "sem_const_redeclare": "Redeclaration of constant “{name}”",
        "sem_void_const": "A procedure cannot be assigned to a constant",
        "sem_array_bounds_decl": "Array start index {start} is greater than end index {end}",
        "sem_no_member": "Cannot access member",
        "sem_void_expr": "Expression has no value (procedure?)",
        "sem_void_index": "Index has no value",
        "sem_void_left": "Left operand has no value",
        "sem_void_right": "Right operand has no value",
        "sem_void_operand": "Operand has no value",
        "sem_void_print": "Expression in “вывод” / output has no value",
        "sem_file_not_write": "Variable “{name}” is not open for writing",
        "sem_file_not_read": "Variable “{name}” is not open for reading",
        "sem_file_write_err": "File write error: {error}",
        "sem_for_step_zero": "for-loop step cannot be zero",
    },
}


def sem(key: str, **kwargs: Any) -> str:
    """Translate a semantic-error body (``sem_*`` keys)."""
    return t(key, **kwargs)


def detect_lang() -> str:
    env = (os.environ.get("ALG_LANG") or "").strip().lower()
    if env in ("ru", "en"):
        return env
    for key in ("LC_ALL", "LANG"):
        val = (os.environ.get(key) or "").strip().lower()
        if val.startswith("ru"):
            return "ru"
        if val.startswith("en"):
            return "en"
    return "ru"


def get_lang() -> str:
    return _LANG if _LANG in ("ru", "en") else detect_lang()


def set_lang(lang: Optional[str]) -> str:
    """Set process UI language. Returns the effective language."""
    global _LANG
    if lang is None:
        _LANG = None
        return get_lang()
    lang = str(lang).strip().lower()
    if lang not in ("ru", "en"):
        raise ValueError(f"unsupported lang: {lang}")
    _LANG = lang
    return _LANG


def t(key: str, **kwargs: Any) -> str:
    """Translate message key for the current UI language."""
    lang = get_lang()
    table = _MESSAGES.get(lang) or _MESSAGES["ru"]
    template = table.get(key) or _MESSAGES["ru"].get(key) or key
    if kwargs:
        return template.format(**kwargs)
    return template
