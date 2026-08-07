# lexer.py

import re
from errors import LexerError
from lang_tokens import Token, TokenType, KEYWORDS


def decode_string_literal(raw: str) -> str:
    """Декодирует литерал \"...\" с escape-последовательностями."""
    inner = raw[1:-1]
    out = []
    i = 0
    while i < len(inner):
        if inner[i] == "\\" and i + 1 < len(inner):
            esc = inner[i + 1]
            mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
            out.append(mapping.get(esc, esc))
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


class Lexer:
    """
    Лексический анализатор. Разбивает исходный код на токены.
    """
    def __init__(self, source_code):
        self.source_code = source_code
        self.line = 1
        self.col = 1
        self.line_start_pos = 0

    def generate_tokens(self):
        # Регулярное выражение, которое находит все возможные токены
        token_specs = [
            ('STRING',    r'"(?:[^"\\]|\\.)*"'),
            ('NUMBER',    r'\d+(\.\d*)?'),
            ('ASSIGN',    r':='),
            ('NEQ',       r'<>'),
            ('LTE',       r'<='),
            ('GTE',       r'>='),
            ('ID',        r'[а-яА-ЯёЁa-zA-Z_][а-яА-ЯёЁa-zA-Z0-9_]*'),
            ('DOT',       r'\.'),
            ('LPAREN',    r'\('), ('RPAREN', r'\)'),
            ('LBRACKET',  r'\['), ('RBRACKET', r'\]'),
            ('COLON',     r':'),
            ('COMMA',     r','),
            ('EQ',        r'='),
            ('OP',        r'[+\-*/><]'),
            ('NEWLINE',   r'\n'),
            ('SKIP',      r'[ \t;]+'),
            ('COMMENT',   r'\|.*'),
            ('MISMATCH',  r'.'),
        ]
        token_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specs)
        
        # Итерация по всем найденным совпадениям в коде
        for mo in re.finditer(token_regex, self.source_code, re.IGNORECASE):
            kind, value = mo.lastgroup, mo.group()
            col = mo.start() - self.line_start_pos + 1
            
            if kind == 'SKIP' or kind == 'COMMENT':
                continue
                
            if kind == 'NEWLINE':
                self.line += 1
                self.line_start_pos = mo.end()
                continue

            if kind == 'STRING':
                decoded = decode_string_literal(value)
                value = '"' + decoded + '"'
            
            if kind == 'ID':
                # Если идентификатор - это ключевое слово, меняем его тип
                kind = KEYWORDS.get(value.lower(), TokenType.ID)
            
            if kind == 'MISMATCH':
                raise LexerError(f"Неожиданный символ '{value}'", self.line, col)
            
            # Для всех остальных токенов (кроме ID) тип токена - это имя группы
            if not isinstance(kind, TokenType):
                kind = TokenType[kind]

            yield Token(kind, value, self.line, col)
        
        # Добавляем токен конца файла
        yield Token(TokenType.EOF, None, self.line, 1)
