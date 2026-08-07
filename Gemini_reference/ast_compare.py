"""Сравнение формы AST (для паритетных тестов RU ↔ EN)."""
from __future__ import annotations

from typing import Any

from ast_nodes import AST
from builtin_names import is_builtin, resolve_builtin, resolve_file_mode
from constants import is_main_program
from lang_tokens import Token
from types_model import canonical_type

_FILE_MODE_CANON = {"r": "чтение", "w": "запись", "a": "дозапись"}


def _normalize_field(type_name: str, key: str, value: Any, *, normalize_bilingual: bool) -> Any:
    if key == "value" and type_name == "Type" and isinstance(value, str):
        return canonical_type(value)
    if key == "name" and type_name == "SubroutineCall" and isinstance(value, str) and is_builtin(value):
        return resolve_builtin(value)
    if key == "value" and type_name == "String" and isinstance(value, str) and normalize_bilingual:
        py_mode = resolve_file_mode(value)
        if py_mode:
            return _FILE_MODE_CANON.get(py_mode, value)
    if key == "name" and isinstance(value, str) and normalize_bilingual:
        if is_main_program(value):
            return "__MAIN__"
        if type_name == "RecordDecl":
            return "__RECORD__"
        if type_name == "CustomType":
            return "__TYPE__"
    return value


def ast_shape(node: Any, *, normalize_bilingual: bool = False) -> Any:
    """
    Каноническое представление дерева для сравнения.

    normalize_bilingual=True — имена точки входа, записей и пользовательских типов,
    а также строковые режимы файлов приводятся к плейсхолдерам.
    """
    if node is None:
        return None
    if isinstance(node, (int, float, bool)):
        return node
    if isinstance(node, str):
        return node
    if not isinstance(node, AST):
        return repr(type(node))

    type_name = type(node).__name__
    parts: list[tuple[str, Any]] = []

    for key in sorted(vars(node).keys()):
        if key == "token":
            continue
        value = getattr(node, key)
        if isinstance(value, AST):
            parts.append((key, ast_shape(value, normalize_bilingual=normalize_bilingual)))
        elif isinstance(value, list):
            parts.append(
                (key, [ast_shape(item, normalize_bilingual=normalize_bilingual) for item in value])
            )
        elif isinstance(value, tuple):
            parts.append(
                (
                    key,
                    tuple(ast_shape(item, normalize_bilingual=normalize_bilingual) for item in value),
                )
            )
        else:
            if isinstance(value, Token):
                parts.append((key, value.value))
            else:
                norm = _normalize_field(type_name, key, value, normalize_bilingual=normalize_bilingual)
                parts.append((key, norm))

    return (type_name, tuple(parts))


def ast_shapes_equal(left: AST, right: AST, *, normalize_bilingual: bool = False) -> bool:
    return ast_shape(left, normalize_bilingual=normalize_bilingual) == ast_shape(
        right, normalize_bilingual=normalize_bilingual
    )
