"""Общая модель типов для семантического анализа (RU + EN алиасы)."""

from __future__ import annotations

from ast_nodes import CustomType, Type
from builtin_names import resolve_builtin

# Канонические внутренние имена типов (RU)
_CANONICAL_TYPES = frozenset({"цел", "вещ", "лог", "лит", "файл", "словарь", "таб"})

# Любое написание → канон
TYPE_ALIASES: dict[str, str] = {
    "цел": "цел",
    "int": "цел",
    "вещ": "вещ",
    "real": "вещ",
    "лог": "лог",
    "bool": "лог",
    "лит": "лит",
    "str": "лит",
    "файл": "файл",
    "file": "файл",
    "словарь": "словарь",
    "dict": "словарь",
    "таб": "таб",
    "tab": "таб",
}

BUILTIN_TYPES = frozenset(TYPE_ALIASES.keys())

# Число аргументов (ключ — каноническое RU-имя)
_BUILTIN_ARITY_CANON: dict[str, int] = {
    "открыть": 3,
    "закрыть": 1,
    "конецфайла": 1,
    "корень": 1,
    "модуль": 1,
    "случ": 0,
    "случцел": 2,
    "длина": 1,
    "подстрока": 3,
    "вверх": 1,
    "вниз": 1,
    "вцел": 1,
    "ввещ": 1,
    "встроку": 1,
    "остаток": 2,
    "целдел": 2,
    "степень": 2,
    "мин": 2,
    "макс": 2,
    "округление": 1,
    "знак": 1,
    "син": 1,
    "кос": 1,
    "найти": 2,
    "размер": 1,
}

# Обратная совместимость
BUILTIN_ARITY: dict[str, int] = dict(_BUILTIN_ARITY_CANON)


def canonical_type(name: str) -> str:
    return TYPE_ALIASES.get(name.lower(), name.lower())


def resolve_type_name(type_node) -> str:
    """Имя типа из узла Type или CustomType (каноническое для встроенных)."""
    if isinstance(type_node, Type):
        return canonical_type(type_node.value)
    if isinstance(type_node, CustomType):
        return type_node.name.lower()
    return "?"


def format_var_type(type_node, *, is_array: bool = False) -> str:
    """Строковое представление типа переменной для таблицы символов."""
    base = resolve_type_name(type_node)
    if is_array:
        return f"таб {base}"
    return base


def is_builtin_type(name: str) -> bool:
    return canonical_type(name) in _CANONICAL_TYPES


def get_builtin_arity(name: str) -> int | None:
    canon = resolve_builtin(name)
    return _BUILTIN_ARITY_CANON.get(canon)


def is_builtin_name(name: str) -> bool:
    return resolve_builtin(name) in _BUILTIN_ARITY_CANON


# Подписи типов для сообщений (канон RU / EN)
_TYPE_BILINGUAL: dict[str, str] = {}
for _alias, _canon in TYPE_ALIASES.items():
    if _canon in _TYPE_BILINGUAL:
        continue
    _en = next(
        (a for a, c in TYPE_ALIASES.items() if c == _canon and a != _canon and a.isascii()),
        None,
    )
    _TYPE_BILINGUAL[_canon] = f"{_canon} / {_en}" if _en else _canon


def type_bilingual_label(name: str) -> str:
    """Человекочитаемая подпись типа: «цел / int», «лит / str», …"""
    return _TYPE_BILINGUAL.get(canonical_type(name), canonical_type(name))
