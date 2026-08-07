# lang_tokens.py



from enum import Enum





class TokenType(Enum):

    # Ключевые слова

    АЛГ = "АЛГ"

    АРГ = "АРГ"

    НАЧ = "НАЧ"

    КОН = "КОН"

    КОНСТ = "КОНСТ"

    ЦЕЛ = "ЦЕЛ"

    ВЕЩ = "ВЕЩ"

    ЛОГ = "ЛОГ"

    ЛИТ = "ЛИТ"

    ТАБ = "ТАБ"

    ФАЙЛ = "ФАЙЛ"

    ЗАПИСЬ = "ЗАПИСЬ"

    ПЕРЕЧ = "ПЕРЕЧ"

    СЛОВАРЬ = "СЛОВАРЬ"

    ВВОД = "ВВОД"

    ВЫВОД = "ВЫВОД"

    ЕСЛИ = "ЕСЛИ"

    ТО = "ТО"

    ИНАЧЕ = "ИНАЧЕ"

    ВСЕ = "ВСЕ"

    НЦ = "НЦ"

    ПОКА = "ПОКА"

    ДЛЯ = "ДЛЯ"

    ОТ = "ОТ"

    ДО = "ДО"

    КЦ = "КЦ"

    РЕЗ = "РЕЗ"

    ИСПОЛЬЗОВАТЬ = "ИСПОЛЬЗОВАТЬ"

    # Литералы и операторы

    ДА = "ДА"

    НЕТ = "НЕТ"

    И = "И"

    ИЛИ = "ИЛИ"

    НЕ = "НЕ"

    # Символы

    ID = "ID"

    NUMBER = "NUMBER"

    STRING = "STRING"

    ASSIGN = "ASSIGN"

    EQ = "EQ"

    NEQ = "NEQ"

    LTE = "LTE"

    GTE = "GTE"

    DOT = "DOT"

    LPAREN = "LPAREN"

    RPAREN = "RPAREN"

    LBRACKET = "LBRACKET"

    RBRACKET = "RBRACKET"

    COLON = "COLON"

    COMMA = "COMMA"

    OP = "OP"

    EOF = "EOF"





class Token:

    def __init__(self, type: TokenType, value, line, col):

        self.type = type

        self.value = value

        self.line = line

        self.col = col



    def __repr__(self):

        return f"Token({self.type.name}, {repr(self.value)}, ln {self.line})"





# Русские ключевые слова (канон)

_RU_KEYWORDS: dict[str, TokenType] = {

    "алг": TokenType.АЛГ,

    "арг": TokenType.АРГ,

    "нач": TokenType.НАЧ,

    "кон": TokenType.КОН,

    "конст": TokenType.КОНСТ,

    "цел": TokenType.ЦЕЛ,

    "вещ": TokenType.ВЕЩ,

    "лог": TokenType.ЛОГ,

    "лит": TokenType.ЛИТ,

    "таб": TokenType.ТАБ,

    "файл": TokenType.ФАЙЛ,

    "запись": TokenType.ЗАПИСЬ,

    "переч": TokenType.ПЕРЕЧ,

    "словарь": TokenType.СЛОВАРЬ,

    "ввод": TokenType.ВВОД,

    "вывод": TokenType.ВЫВОД,

    "если": TokenType.ЕСЛИ,

    "то": TokenType.ТО,

    "иначе": TokenType.ИНАЧЕ,

    "все": TokenType.ВСЕ,

    "нц": TokenType.НЦ,

    "пока": TokenType.ПОКА,

    "для": TokenType.ДЛЯ,

    "от": TokenType.ОТ,

    "до": TokenType.ДО,

    "кц": TokenType.КЦ,

    "рез": TokenType.РЕЗ,

    "использовать": TokenType.ИСПОЛЬЗОВАТЬ,

    "да": TokenType.ДА,

    "нет": TokenType.НЕТ,

    "и": TokenType.И,

    "или": TokenType.ИЛИ,

    "не": TokenType.НЕ,

}



# Английские синонимы (v1.1 — модель 1С)

_EN_KEYWORDS: dict[str, TokenType] = {

    "proc": TokenType.АЛГ,

    "arg": TokenType.АРГ,

    "res": TokenType.РЕЗ,

    "begin": TokenType.НАЧ,

    "end": TokenType.КОН,

    "const": TokenType.КОНСТ,

    "int": TokenType.ЦЕЛ,

    "real": TokenType.ВЕЩ,

    "bool": TokenType.ЛОГ,

    "str": TokenType.ЛИТ,

    "tab": TokenType.ТАБ,

    "file": TokenType.ФАЙЛ,

    "rec": TokenType.ЗАПИСЬ,

    "enum": TokenType.ПЕРЕЧ,

    "dict": TokenType.СЛОВАРЬ,

    "input": TokenType.ВВОД,

    "output": TokenType.ВЫВОД,

    "if": TokenType.ЕСЛИ,

    "then": TokenType.ТО,

    "else": TokenType.ИНАЧЕ,

    "endif": TokenType.ВСЕ,

    "loop": TokenType.НЦ,

    "eloop": TokenType.КЦ,

    "for": TokenType.ДЛЯ,

    "while": TokenType.ПОКА,

    "from": TokenType.ОТ,

    "to": TokenType.ДО,

    "import": TokenType.ИСПОЛЬЗОВАТЬ,

    "true": TokenType.ДА,

    "false": TokenType.НЕТ,

    "and": TokenType.И,

    "or": TokenType.ИЛИ,

    "not": TokenType.НЕ,

}



KEYWORDS: dict[str, TokenType] = {**_RU_KEYWORDS, **_EN_KEYWORDS}


# Подписи токенов для сообщений об ошибках (RU / EN)
_TOKEN_LABELS: dict[TokenType, list[str]] = {}
for _word, _tt in _RU_KEYWORDS.items():
    _TOKEN_LABELS.setdefault(_tt, []).append(_word)
for _word, _tt in _EN_KEYWORDS.items():
    if _word not in _TOKEN_LABELS.get(_tt, []):
        _TOKEN_LABELS.setdefault(_tt, []).append(_word)


def token_type_bilingual_label(tt: TokenType) -> str:
    """Человекочитаемая подпись токена: «алг / proc», «нач / begin», …"""
    words = _TOKEN_LABELS.get(tt)
    if not words:
        return tt.name
    return " / ".join(words)

