# alg_warnings.py — система предупреждений языка .alg

from __future__ import annotations

import sys
from typing import Any, List, Optional


class AlgWarning:
    """Базовое предупреждение компилятора/интерпретатора."""

    CATEGORY = "общее"

    def __init__(self, message: str, token: Optional[Any] = None) -> None:
        self.message = message
        self.token = token

    def format(self) -> str:
        loc = ""
        if self.token is not None and hasattr(self.token, "line"):
            loc = f"[Строка {self.token.line}:{self.token.col}] "
        return f"{loc}Предупреждение ({self.CATEGORY}): {self.message}"


class RedefinitionWarning(AlgWarning):
    """Повторное объявление процедуры, функции или типа."""

    CATEGORY = "переопределение"

    def __init__(self, kind: str, name: str, token: Optional[Any] = None) -> None:
        super().__init__(f"Повторное объявление {kind} «{name}»", token)


class AssignTypeWarning(AlgWarning):
    """Мягкое предупреждение о сомнительном присваивании типов."""

    CATEGORY = "типы"


class ImplicitDeclareWarning(AlgWarning):
    """Неявное объявление переменной (например, в цикле нц для)."""

    CATEGORY = "неявное объявление"


class TranspilerWarning(AlgWarning):
    """Предупреждение транспилятора (неполная поддержка узла и т.п.)."""

    CATEGORY = "транспилятор"


class MemoryLeakWarning(AlgWarning):
    """Возможная утечка malloc-буфера в сгенерированном C (str_concat и др.)."""

    CATEGORY = "память C"


class WarningCollector:
    """Собирает предупреждения; выводит в stderr по правилам verbose."""

    def __init__(self, verbose: bool = False, warnings_as_errors: bool = False) -> None:
        self.verbose = verbose
        self.warnings_as_errors = warnings_as_errors
        self._warnings: List[AlgWarning] = []

    def emit(self, warning: AlgWarning) -> None:
        self._warnings.append(warning)
        if self.verbose:
            print(warning.format(), file=sys.stderr)

    @property
    def count(self) -> int:
        return len(self._warnings)

    @property
    def warnings(self) -> List[AlgWarning]:
        return list(self._warnings)

    def finalize(self) -> int:
        """
        Итог по предупреждениям. Возвращает код выхода:
        0 — нет предупреждений или только сводка;
        3 — --warnings-as-errors и были предупреждения.
        """
        if self.count == 0:
            return 0
        if not self.verbose:
            print(
                f"Предупреждений: {self.count} (подробности: флаг --verbose)",
                file=sys.stderr,
            )
        if self.warnings_as_errors:
            print(
                "Режим --warnings-as-errors: завершение с ошибкой.",
                file=sys.stderr,
            )
            return 3
        return 0
