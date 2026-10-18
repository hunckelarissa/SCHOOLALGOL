# module_loader.py — загрузка исходника .alg в AST и учёт импортов модулей.
from __future__ import annotations

import os
from dataclasses import dataclass, field

from lexer import Lexer
from parser import Parser
from ast_nodes import Program


def load_alg_file(filepath: str) -> Program:
    """
    Читает файл .alg, выполняет лексический и синтаксический разбор, возвращает AST (Program).
    Путь может быть относительным или абсолютным.
    Возбуждает: FileNotFoundError, LexerError, ParserError.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tokens = list(Lexer(source).generate_tokens())
    return Parser(tokens).parse()


def resolve_module_path(base_path: str, relative: str) -> str:
    """Путь к модулю относительно каталога текущего файла (без sandbox)."""
    module_dir = os.path.dirname(os.path.abspath(base_path))
    return os.path.normpath(os.path.join(module_dir, relative))


class CyclicImportError(Exception):
    """Циклический импорт `использовать` / `import`."""

    def __init__(self, chain: list[str]):
        self.chain = list(chain)
        display = " → ".join(os.path.basename(p) for p in self.chain)
        super().__init__(f"Циклический импорт модулей: {display}")
        self.display = display


class ModuleFileNotFoundError(FileNotFoundError):
    """Модуль не найден по разрешённому пути."""

    def __init__(self, module_path: str, base_path: str):
        self.module_path = module_path
        self.base_path = base_path
        super().__init__(
            f"Файл модуля не найден: «{module_path}» (искали относительно «{base_path}»)"
        )


@dataclass
class ModuleLoadTracker:
    """Общий учёт уже загруженных модулей и стека импорта (анти-цикл)."""

    loaded: set[str] = field(default_factory=set)
    stack: list[str] = field(default_factory=list)

    def enter(self, module_path: str) -> bool:
        """
        Зарегистрировать начало загрузки.
        Возвращает False, если модуль уже загружен (повторный import — no-op).
        Raises CyclicImportError при цикле.
        """
        if module_path in self.stack:
            raise CyclicImportError(self.stack + [module_path])
        if module_path in self.loaded:
            return False
        self.stack.append(module_path)
        self.loaded.add(module_path)
        return True

    def leave(self, module_path: str) -> None:
        """Снять модуль со стека после успешной обработки объявлений."""
        if self.stack and self.stack[-1] == module_path:
            self.stack.pop()

    def fail(self, module_path: str) -> None:
        """Откатить регистрацию при ошибке открытия/разбора."""
        self.leave(module_path)
        self.loaded.discard(module_path)


def open_module(
    tracker: ModuleLoadTracker,
    base_path: str,
    relative: str,
) -> tuple[str, Program] | None:
    """
    Разрешить путь, проверить цикл/повтор, загрузить AST.
    Возвращает (абсолютный_путь, AST) или None, если модуль уже был загружен.
    Raises CyclicImportError, ModuleFileNotFoundError (и LexerError/ParserError из load_alg_file).
    Вызывающий обязан вызвать tracker.leave(path) в finally после обработки AST.
    При ModuleFileNotFoundError трекер уже откатан через fail().
    """
    module_path = resolve_module_path(base_path, relative)
    if not tracker.enter(module_path):
        return None
    try:
        return module_path, load_alg_file(module_path)
    except FileNotFoundError:
        tracker.fail(module_path)
        raise ModuleFileNotFoundError(module_path, base_path) from None
