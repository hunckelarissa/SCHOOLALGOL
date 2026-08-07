# constants.py — общие константы (интерпретатор, транспилятор).

# Имена главной процедуры (точка входа). RU — канон в сообщениях.
MAIN_PROGRAM_NAME = "основнаяпрограмма"
MAIN_PROGRAM_NAMES = frozenset({"основнаяпрограмма", "mainprogram"})


def is_main_program(name: str) -> bool:
    return name.lower() in MAIN_PROGRAM_NAMES


def main_program_label() -> str:
    """Текст для сообщений об ошибках (оба синонима)."""
    return "основнаяпрограмма / mainprogram"


# Заголовки REPL (тело пользователя оборачивается в процедуру main)
REPL_HEADER_RU = f"алг {MAIN_PROGRAM_NAME}\nнач\n"
REPL_FOOTER_RU = "\nкон\n"
REPL_HEADER_EN = "proc mainprogram\nbegin\n"
REPL_FOOTER_EN = "\nend\n"


def repl_wrap(body: str, lang: str = "ru") -> str:
    """Оборачивает фрагмент REPL в главную процедуру."""
    lang = (lang or "ru").lower()
    if lang == "en":
        return REPL_HEADER_EN + body + REPL_FOOTER_EN
    return REPL_HEADER_RU + body + REPL_FOOTER_RU


def procedure_alg_comment(name: str) -> str:
    """
    Комментарий // alg: для сгенерированного C.
    Для точки входа дублирует синоним RU ↔ EN (B5).
    """
    n = name.lower()
    if is_main_program(n):
        if n == MAIN_PROGRAM_NAME:
            return f"// alg: {n} (mainprogram)"
        return f"// alg: {n} (основнаяпрограмма)"
    return f"// alg: {n}"
