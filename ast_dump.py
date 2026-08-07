# ast_dump.py — вывод дерева разбора для учебной диагностики

from __future__ import annotations

import json
from typing import Any

from ast_nodes import AST


def _node_label(node: AST) -> str:
    name = type(node).__name__
    extras = []
    if hasattr(node, "name"):
        extras.append(f"name={node.name!r}")
    elif hasattr(node, "var_node") and hasattr(node.var_node, "name"):
        extras.append(f"var={node.var_node.name!r}")
    if hasattr(node, "value") and not hasattr(node, "var_node"):
        v = node.value
        if isinstance(v, str) and len(v) > 40:
            v = v[:37] + "..."
        extras.append(f"value={v!r}")
    if extras:
        return f"{name} ({', '.join(extras)})"
    return name


def _iter_children(node: AST) -> list[tuple[str, Any]]:
    children: list[tuple[str, Any]] = []
    if not hasattr(node, "__dict__"):
        return children
    for key, value in vars(node).items():
        if key in ("token",):
            continue
        if isinstance(value, AST):
            children.append((key, value))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, AST):
                    children.append((f"{key}[{i}]", item))
                elif isinstance(item, tuple):
                    for j, part in enumerate(item):
                        if isinstance(part, AST):
                            children.append((f"{key}[{i}][{j}]", part))
    return children


def dump_ast_text(node: Any, indent: int = 0) -> str:
    """Текстовое дерево AST с отступами."""
    if node is None:
        return ""
    if isinstance(node, (str, int, float, bool)):
        return "  " * indent + repr(node) + "\n"
    if not isinstance(node, AST):
        return "  " * indent + str(node) + "\n"
    lines = ["  " * indent + _node_label(node)]
    for label, child in _iter_children(node):
        lines.append("  " * indent + f"  {label}:")
        lines.append(dump_ast_text(child, indent + 2).rstrip("\n"))
    return "\n".join(lines) + "\n"


def _node_to_dict(node: Any) -> Any:
    if node is None or isinstance(node, (str, int, float, bool)):
        return node
    if not isinstance(node, AST):
        return str(node)
    data: dict[str, Any] = {"type": type(node).__name__}
    if hasattr(node, "token") and node.token is not None:
        data["line"] = getattr(node.token, "line", None)
        data["col"] = getattr(node.token, "col", None)
    for key, value in vars(node).items():
        if key == "token":
            continue
        if isinstance(value, AST):
            data[key] = _node_to_dict(value)
        elif isinstance(value, list):
            data[key] = [
                _node_to_dict(item) if isinstance(item, AST)
                else [_node_to_dict(p) if isinstance(p, AST) else p for p in item]
                if isinstance(item, tuple) else item
                for item in value
            ]
        else:
            data[key] = value
    return data


def dump_ast_json(node: AST) -> str:
    return json.dumps(_node_to_dict(node), ensure_ascii=False, indent=2)
