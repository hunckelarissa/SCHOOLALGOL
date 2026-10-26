"""Канонические имена встроенных подпрограмм и алиасы EN ↔ RU."""

from __future__ import annotations

# Канон (RU) → EN-алиасы
BUILTIN_ALIASES: dict[str, tuple[str, ...]] = {
    "открыть": ("open",),
    "закрыть": ("close",),
    "конецфайла": ("eof",),
    "корень": ("sqrt",),
    "модуль": ("abs",),
    "случ": ("rand",),
    "случцел": ("randint",),
    "длина": ("len",),
    "подстрока": ("substr",),
    "вверх": ("upper",),
    "вниз": ("lower",),
    "вцел": ("toint",),
    "ввещ": ("toreal",),
    "встроку": ("tostr",),
    "остаток": ("mod",),
    "целдел": ("div",),
    "степень": ("pow",),
    "мин": ("min",),
    "макс": ("max",),
    "округление": ("round",),
    "знак": ("sign",),
    "син": ("sin",),
    "кос": ("cos",),
    "найти": ("find",),
    "размер": ("size",),
}

_LOOKUP: dict[str, str] = {}
for _canonical, _aliases in BUILTIN_ALIASES.items():
    _LOOKUP[_canonical] = _canonical
    for _alias in _aliases:
        _LOOKUP[_alias] = _canonical

BUILTIN_CANONICAL_NAMES = frozenset(BUILTIN_ALIASES.keys())


def resolve_builtin(name: str) -> str:
    """Возвращает каноническое RU-имя встроенной подпрограммы."""
    return _LOOKUP.get(name.lower(), name.lower())


def is_builtin(name: str) -> bool:
    return resolve_builtin(name) in BUILTIN_CANONICAL_NAMES


# Режимы открыть(..., режим)
FILE_MODE_MAP: dict[str, str] = {
    "чтение": "r",
    "read": "r",
    "запись": "w",
    "write": "w",
    "дозапись": "a",
    "append": "a",
}


def resolve_file_mode(mode_str: str) -> str | None:
    """Python-режим open() или None."""
    return FILE_MODE_MAP.get(str(mode_str).lower().strip('"\''))


def builtin_bilingual_label(name: str) -> str:
    """Подпись встроенной подпрограммы для сообщений: «открыть / open»."""
    canon = resolve_builtin(name)
    if canon not in BUILTIN_CANONICAL_NAMES:
        return name
    aliases = BUILTIN_ALIASES.get(canon, ())
    if aliases:
        return f"{canon} / {aliases[0]}"
    return canon


def builtin_suggestion_pool() -> list[str]:
    """Все канонические и EN-алиасы встроенных (для подсказок)."""
    names: list[str] = []
    for canon, aliases in BUILTIN_ALIASES.items():
        names.append(canon)
        names.extend(aliases)
    return names
