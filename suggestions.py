# suggestions.py — подсказки по похожим идентификаторам

from __future__ import annotations

from builtin_names import (
    BUILTIN_ALIASES,
    BUILTIN_CANONICAL_NAMES,
    is_builtin,
    resolve_builtin,
    builtin_suggestion_pool,
)


def levenshtein(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def expand_bilingual_candidates(name: str, candidates: list[str]) -> list[str]:
    """Добавляет RU/EN-синонимы встроенных к пулу кандидатов для подсказок."""
    pool = {c.lower() for c in candidates if c}
    if is_builtin(name):
        canon = resolve_builtin(name)
        pool.add(canon)
        pool.update(BUILTIN_ALIASES.get(canon, ()))
    for cand in list(pool):
        if cand in BUILTIN_CANONICAL_NAMES:
            pool.update(BUILTIN_ALIASES.get(cand, ()))
    if not pool:
        pool.update(builtin_suggestion_pool())
    return list(pool)


def suggest_similar(name: str, candidates: list[str], *, max_distance: int = 2, limit: int = 3) -> list[str]:
    """Возвращает до limit имён из candidates, ближайших к name."""
    expanded = expand_bilingual_candidates(name, candidates)
    scored = []
    for cand in expanded:
        if not cand or cand.lower() == name.lower():
            continue
        d = levenshtein(name, cand)
        if d <= max_distance:
            scored.append((d, cand))
    scored.sort(key=lambda x: (x[0], x[1].lower()))
    return [c for _, c in scored[:limit]]


def format_suggestion_message(name: str, candidates: list[str]) -> str:
    similar = suggest_similar(name, candidates)
    if not similar:
        return ""
    if len(similar) == 1:
        return f"Возможно, имелось в виду «{similar[0]}»?"
    joined = "», «".join(similar)
    return f"Возможно, имелось в виду: «{joined}»?"
