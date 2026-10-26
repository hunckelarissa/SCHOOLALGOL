# -*- coding: utf-8 -*-
"""SHAYDBG wire protocol helpers for Gemini (same contract as Copilot / mainLAST)."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, Set, TextIO

PROTOCOL_PREFIX = "SHAYDBG "

_DEBUG_STDIN_CMDS = frozenset({
    "step",
    "step_into",
    "step_out",
    "step_over",
    "continue",
    "quit",
    "eval",
    "watch",
    "breakpoints",
    "set_breakpoints",
    "bps",
    "vars",
    "set",
    "assign",
})


def is_debug_stdin_command(raw: str) -> bool:
    text = (raw or "").strip()
    if not text.startswith("{"):
        return False
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(obj, dict):
        return False
    cmd = str(obj.get("cmd") or obj.get("command") or "").strip().lower()
    return cmd in _DEBUG_STDIN_CMDS


def emit_event(event: Dict[str, Any], stderr: Optional[TextIO] = None) -> None:
    if stderr is None:
        stderr = sys.stderr
    line = PROTOCOL_PREFIX + json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    print(line, file=stderr, flush=True)


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in list(value.items())[:80]}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in list(value)[:80]]
    return str(value)


def build_stopped(
    *,
    reason: str,
    line: Optional[int],
    source: str,
    path: str,
    globals_map: Dict[str, Any],
    locals_map: Dict[str, Any],
    stack: Optional[List[Dict[str, Any]]] = None,
    arrays: Optional[Dict[str, Any]] = None,
    records: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    reason_key = "breakpoint"
    if reason in ("step", "шаг", "step_over"):
        reason_key = "step"
    elif reason in ("step_into", "into"):
        reason_key = "step_into"
    elif reason in ("step_out", "out"):
        reason_key = "step_out"
    ev: Dict[str, Any] = {
        "shay": "stopped",
        "line": line,
        "source": source or "",
        "reason": reason_key,
        "path": path or "",
        "globals": _jsonable(globals_map or {}),
        "locals": _jsonable(locals_map or {}),
        "stack": stack
        or [
            {
                "name": "main",
                "line": line,
                "source": source or "",
                "path": path or "",
            }
        ],
        "arrays": arrays or {},
        "records": records or {},
    }
    return ev


def build_terminated(exit_code: int = 0) -> Dict[str, Any]:
    return {"shay": "terminated", "exit": int(exit_code)}


def build_eval(*, expr: str, value: Any = None, ok: bool = True, error: str = "") -> Dict[str, Any]:
    return {
        "shay": "eval",
        "expr": expr,
        "value": _jsonable(value) if ok else None,
        "ok": ok,
        "error": error or "",
    }


def build_set(*, name: str, value: Any = None, ok: bool = True, error: str = "") -> Dict[str, Any]:
    return {
        "shay": "set",
        "name": name,
        "value": _jsonable(value) if ok else None,
        "ok": ok,
        "error": error or "",
    }


def build_vars(
    *,
    globals_map: Dict[str, Any],
    locals_map: Dict[str, Any],
    arrays: Optional[Dict[str, Any]] = None,
    records: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Reply to stdin ``vars`` — snapshot without leaving the pause."""
    return {
        "shay": "vars",
        "globals": _jsonable(globals_map or {}),
        "locals": _jsonable(locals_map or {}),
        "arrays": _jsonable(arrays or {}),
        "records": _jsonable(records or {}),
    }


def parse_command(raw: str) -> Optional[Dict[str, Any]]:
    text = (raw or "").strip()
    if not text.startswith("{"):
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def cmd_name(obj: Dict[str, Any]) -> str:
    return str(obj.get("cmd") or obj.get("command") or "").strip().lower()


def extract_break_lines(items: Any) -> Set[int]:
    lines: Set[int] = set()
    if not isinstance(items, list):
        return lines
    for it in items:
        if not isinstance(it, dict):
            continue
        if it.get("enabled") is False:
            continue
        try:
            line = int(it.get("line"))
        except (TypeError, ValueError):
            continue
        if line > 0:
            lines.add(line)
    return lines
