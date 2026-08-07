"""Тесты лексера."""
import unittest

from lang_tokens import TokenType
from lexer import Lexer
from errors import LexerError


class TestLexer(unittest.TestCase):
    def test_numbers(self):
        tokens = list(Lexer("42").generate_tokens())
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0].type, TokenType.NUMBER)
        self.assertEqual(tokens[0].value, "42")

    def test_keywords(self):
        tokens = list(Lexer("алг нач кон").generate_tokens())
        types = [t.type for t in tokens]
        self.assertIn(TokenType.АЛГ, types)
        self.assertIn(TokenType.НАЧ, types)
        self.assertIn(TokenType.КОН, types)
        self.assertEqual(types[-1], TokenType.EOF)

    def test_assign_and_id(self):
        tokens = list(Lexer("x := 1").generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.ID)
        self.assertEqual(tokens[1].type, TokenType.ASSIGN)
        self.assertEqual(tokens[2].type, TokenType.NUMBER)

    def test_string(self):
        tokens = list(Lexer('"привет"').generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, '"привет"')

    def test_string_escape(self):
        tokens = list(Lexer('"a\\nb"').generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, '"a\nb"')

    def test_comparison_operators(self):
        tokens = list(Lexer("1 >= 2 <= 3 <> 4").generate_tokens())
        types = [t.type for t in tokens if t.type != TokenType.NUMBER]
        self.assertIn(TokenType.GTE, types)
        self.assertIn(TokenType.LTE, types)
        self.assertIn(TokenType.NEQ, types)

    def test_unexpected_char_raises(self):
        with self.assertRaises(LexerError):
            list(Lexer("алг @").generate_tokens())

    def test_all_keywords_recognized(self):
        from lang_tokens import KEYWORDS
        for word, expected in KEYWORDS.items():
            tokens = list(Lexer(word).generate_tokens())
            self.assertEqual(tokens[0].type, expected, msg=word)
            self.assertEqual(tokens[-1].type, TokenType.EOF)

    def test_case_insensitive_keywords(self):
        tokens = list(Lexer("АЛГ Нач КОН").generate_tokens())
        types = [t.type for t in tokens[:-1]]
        self.assertEqual(types, [TokenType.АЛГ, TokenType.НАЧ, TokenType.КОН])

    def test_comment_skipped(self):
        tokens = list(Lexer("| комментарий\nалг").generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.АЛГ)

    def test_empty_file_eof_only(self):
        tokens = list(Lexer("").generate_tokens())
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.EOF)

    def test_comments_only(self):
        tokens = list(Lexer("| a\n| b").generate_tokens())
        self.assertEqual(tokens[-1].type, TokenType.EOF)
        self.assertEqual(len(tokens), 1)

    def test_unicode_identifier(self):
        tokens = list(Lexer("переменная_ё").generate_tokens())
        self.assertEqual(tokens[0].type, TokenType.ID)
        self.assertEqual(tokens[0].value.lower(), "переменная_ё")
