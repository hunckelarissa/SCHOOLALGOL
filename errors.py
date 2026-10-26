# errors.py
from __future__ import annotations

from typing import Any, Optional

from i18n import t


def _format_char_repr(ch: str) -> str:
    """Format a character for lexer messages."""
    if len(ch) != 1:
        return repr(ch)
    if ch.isprintable() and ch not in ("'", '"', "\\"):
        return f"'{ch}'"
    return f"U+{ord(ch):04X}"


class InterpreterError(Exception):
    """Base class for all interpreter errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.token: Optional[Any] = None
        self.call_stack: Optional[Any] = None
        self.hint: Optional[str] = None


class LexerError(InterpreterError):
    """Lexical analysis error."""

    def __init__(self, message: str, line: int, col: int, char: Optional[str] = None) -> None:
        char_part = ""
        if char is not None:
            char_part = t("char_part", char=_format_char_repr(char))
        super().__init__(
            t("lexer_prefix", line=line, col=col, message=message, char_part=char_part)
        )
        self.line = line
        self.col = col
        self.char = char
        self.hint = t("hint_lexer")


class ParserError(InterpreterError):
    """Syntax analysis error."""

    def __init__(
        self,
        message: str,
        token: Any,
        context: Optional[str] = None,
    ) -> None:
        ctx = t("ctx_prefix", context=context) if context else ""
        super().__init__(
            t(
                "parser_prefix",
                line=token.line,
                col=token.col,
                message=message,
                ctx=ctx,
            )
        )
        self.token = token
        self.context = context
        self.hint = t("hint_parser")


class SemanticError(InterpreterError):
    """Semantic analysis or runtime error."""

    def __init__(
        self,
        message: str,
        token: Optional[Any] = None,
        call_stack: Optional[Any] = None,
    ) -> None:
        loc = (
            t("loc_line", line=token.line, col=token.col)
            if token
            else ""
        )
        super().__init__(t("semantic_prefix", loc=loc, message=message))
        self.token = token
        self.call_stack = call_stack
        self.hint = _semantic_hint(message)


class TranspilerError(InterpreterError):
    """C transpilation error."""

    def __init__(self, message: str, node: Optional[Any] = None) -> None:
        extra = ""
        if node is not None:
            extra = f" (AST node: {type(node).__name__})"
            tok = getattr(node, "token", None)
            if tok is not None and hasattr(tok, "line"):
                extra += f", line {tok.line}"
        super().__init__(t("transpiler_prefix", message=message, extra=extra))
        self.node = node
        self.token = getattr(node, "token", None) if node is not None else None
        self.hint = t("hint_transpiler")


def _semantic_hint(message: str) -> str:
    """Hint based on semantic error text (RU body messages still dominate)."""
    lower = message.lower()
    if get_lang_is_en():
        if "не определена" in lower or "не определен" in lower or "not defined" in lower:
            return (
                "Hint: declare the variable (int, real, str …) in the current procedure "
                "or at the top level; names are case-insensitive."
            )
        if "неверное количество аргументов" in lower or (
            "ожидает" in lower and "аргумент" in lower
        ):
            return "Hint: check argument count/order against the declaration (arg …; res …)."
        if "вне границ массива" in lower or "индекс массива" in lower:
            return "Hint: check tab … [lo:hi] declaration and the allowed index range."
        if "деление на ноль" in lower or "division by zero" in lower:
            return "Hint: check the divisor before using /."
        if "не открыта" in lower or "не удалось открыть" in lower:
            return "Hint: call open(f, path, mode) before file input/output."
        if "необъявленной локальной" in lower:
            return "Hint: in a for-loop the variable must be declared first (int i)."
        if "главная программа" in lower or "main program" in lower:
            return "Hint: add a parameterless «алг основнаяпрограмма» or «proc mainprogram»."
        return "Hint: see GRAMMAR.md and run with --verbose for stage tracing."
    if "не определена" in lower or "не определен" in lower:
        return (
            "Подсказка: объявите переменную (цел, вещ, лит …) в текущей процедуре "
            "или на верхнем уровне; имена нечувствительны к регистру."
        )
    if "неверное количество аргументов" in lower or "ожидает" in lower and "аргумент" in lower:
        return "Подсказка: сверьте число и порядок аргументов с объявлением (арг/arg …; рез/res …)."
    if "вне границ массива" in lower or "индекс массива" in lower:
        return "Подсказка: проверьте объявление таб/tab … [нач:кон] и допустимый диапазон индексов."
    if "деление на ноль" in lower:
        return "Подсказка: добавьте проверку делителя перед операцией /."
    if "не открыта" in lower or "не удалось открыть" in lower:
        return "Подсказка: вызовите открыть/open(f, путь, режим) перед вводом/input или выводом/output в файл."
    if "необъявленной локальной" in lower:
        return "Подсказка: в цикле нц/loop для/for переменная должна быть объявлена заранее (цел/int i)."
    if "главная программа" in lower:
        return "Подсказка: добавьте процедуру «алг основнаяпрограмма» или «proc mainprogram» без параметров."
    return "Подсказка: см. GRAMMAR.md и запустите с --verbose для трассировки этапов."


def get_lang_is_en() -> bool:
    from i18n import get_lang

    return get_lang() == "en"


def format_error(error: InterpreterError, source_code: str) -> str:
    """Format a detailed error with pointer and hint."""
    lines = source_code.split("\n")

    stack_trace = ""
    if hasattr(error, "call_stack") and error.call_stack:
        stack_trace += t("stack_header")
        for ar in reversed(error.call_stack):
            if ar.name == "global" and len(error.call_stack) > 1:
                continue
            stack_trace += t("stack_frame", name=ar.name)

    header = str(error)

    hint = ""
    if getattr(error, "hint", None):
        hint = f"\n  {error.hint}"

    code_pointer = ""
    token = getattr(error, "token", None)
    if token and hasattr(token, "line"):
        line_idx = token.line - 1
        if 0 <= line_idx < len(lines):
            error_line = lines[line_idx]
            padding = error_line[: token.col - 1].replace("\t", "    ")
            pointer = " " * len(padding) + "^"
            code_pointer = f"\n  {error_line}\n  {pointer}"
    elif isinstance(error, LexerError):
        line_idx = error.line - 1
        if 0 <= line_idx < len(lines):
            error_line = lines[line_idx]
            padding = error_line[: error.col - 1].replace("\t", "    ")
            pointer = " " * len(padding) + "^"
            code_pointer = f"\n  {error_line}\n  {pointer}"

    return f"\n{stack_trace}{header}{hint}{code_pointer}\n"
