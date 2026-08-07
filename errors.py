# errors.py
from __future__ import annotations

from typing import Any, Optional


def _format_char_repr(ch: str) -> str:
    """Форматирует символ для сообщения лексера."""
    if len(ch) != 1:
        return repr(ch)
    if ch.isprintable() and ch not in ("'", '"', "\\"):
        return f"'{ch}'"
    return f"U+{ord(ch):04X}"


class InterpreterError(Exception):
    """Базовый класс для всех ошибок интерпретатора."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.token: Optional[Any] = None
        self.call_stack: Optional[Any] = None
        self.hint: Optional[str] = None


class LexerError(InterpreterError):
    """Ошибка на этапе лексического анализа."""

    def __init__(self, message: str, line: int, col: int, char: Optional[str] = None) -> None:
        char_part = ""
        if char is not None:
            char_part = f" (символ {_format_char_repr(char)})"
        super().__init__(f"[Строка {line}:{col}] Лексическая ошибка: {message}{char_part}")
        self.line = line
        self.col = col
        self.char = char
        self.hint = "Подсказка: проверьте раскладку клавиатуры и допустимые символы языка .alg."


class ParserError(InterpreterError):
    """Ошибка на этапе синтаксического анализа."""

    def __init__(
        self,
        message: str,
        token: Any,
        context: Optional[str] = None,
    ) -> None:
        ctx = f" Контекст: «{context}»." if context else ""
        super().__init__(
            f"[Строка {token.line}:{token.col}] Синтаксическая ошибка: {message}.{ctx}"
        )
        self.token = token
        self.context = context
        self.hint = (
            "Подсказка: сверьте синтаксис с GRAMMAR.md "
            "(алг … нач … кон, :=, нц … кц)."
        )


class SemanticError(InterpreterError):
    """Ошибка на этапе семантического анализа или выполнения."""

    def __init__(
        self,
        message: str,
        token: Optional[Any] = None,
        call_stack: Optional[Any] = None,
    ) -> None:
        loc = f"[Строка {token.line}:{token.col}] " if token else ""
        super().__init__(f"{loc}Семантическая ошибка: {message}")
        self.token = token
        self.call_stack = call_stack
        self.hint = _semantic_hint(message)


class TranspilerError(InterpreterError):
    """Ошибка на этапе транспиляции в C."""

    def __init__(self, message: str, node: Optional[Any] = None) -> None:
        extra = ""
        if node is not None:
            extra = f" (узел AST: {type(node).__name__})"
            tok = getattr(node, "token", None)
            if tok is not None and hasattr(tok, "line"):
                extra += f", строка {tok.line}"
        super().__init__(f"Ошибка транспиляции: {message}{extra}")
        self.node = node
        self.token = getattr(node, "token", None) if node is not None else None
        self.hint = "Подсказка: не все конструкции .alg поддерживаются в C-транспиляторе; см. README."


def _semantic_hint(message: str) -> str:
    """Подсказка по тексту семантической ошибки."""
    lower = message.lower()
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


def format_error(error: InterpreterError, source_code: str) -> str:
    """Форматирует подробное сообщение об ошибке с указателем и подсказкой."""
    lines = source_code.split("\n")

    stack_trace = ""
    if hasattr(error, "call_stack") and error.call_stack:
        stack_trace += "Трассировка вызовов (от последнего к первому):\n"
        for ar in reversed(error.call_stack):
            if ar.name == "global" and len(error.call_stack) > 1:
                continue
            stack_trace += f"  в «{ar.name}»\n"

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
