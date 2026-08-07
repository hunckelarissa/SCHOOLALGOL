# module_loader.py — загрузка исходника .alg в AST (единая точка для интерпретатора и транспилятора).
import os
from lexer import Lexer
from parser import Parser
from ast_nodes import Program


def load_alg_file(filepath: str) -> Program:
    """
    Читает файл .alg, выполняет лексический и синтаксический разбор, возвращает AST (Program).
    Путь может быть относительным или абсолютным.
    Возбуждает: FileNotFoundError, LexerError, ParserError.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tokens = list(Lexer(source).generate_tokens())
    return Parser(tokens).parse()
