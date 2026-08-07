# diagnostics.py — вспомогательные функции диагностики пайплайна

from __future__ import annotations

from typing import Any, Set


_SKIP_TYPES = (str, int, float, bool, type(None))


def count_ast_nodes(node: Any, _visited: Set[int] | None = None) -> int:
    """Подсчёт узлов AST (без повторного обхода одного объекта)."""
    if node is None:
        return 0
    if _visited is None:
        _visited = set()
    oid = id(node)
    if oid in _visited:
        return 0
    if isinstance(node, _SKIP_TYPES):
        return 0
    if not hasattr(node, "__dict__"):
        return 0
    _visited.add(oid)
    total = 1
    for value in vars(node).values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, tuple):
                    for part in item:
                        total += count_ast_nodes(part, _visited)
                else:
                    total += count_ast_nodes(item, _visited)
        else:
            total += count_ast_nodes(value, _visited)
    return total


def log_verbose(enabled: bool, tag: str, message: str) -> None:
    """Печать диагностического сообщения в stderr."""
    if enabled:
        import sys
        print(f"[{tag}] {message}", file=sys.stderr)
