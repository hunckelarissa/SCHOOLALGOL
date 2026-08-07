"""Тесты парсера."""
import unittest

from lexer import Lexer
from parser import Parser
from ast_nodes import Assign, IfNode, ForNode, WhileNode, RecordDecl, ArrayDecl


class TestParser(unittest.TestCase):
    def _parse(self, source):
        tokens = list(Lexer(source).generate_tokens())
        return Parser(tokens).parse()

    def test_minimal_program(self):
        tree = self._parse("алг тест нач кон")
        self.assertEqual(len(tree.declarations), 1)
        self.assertEqual(tree.declarations[0].name, "тест")

    def test_const_decl(self):
        tree = self._parse("конст N = 10\nалг основнаяпрограмма нач кон")
        self.assertEqual(len(tree.declarations), 2)
        self.assertEqual(tree.declarations[0].var_node.name, "n")
        self.assertEqual(tree.declarations[0].expr.value, 10.0)

    def test_var_and_assign(self):
        source = """
алг основнаяпрограмма
нач
  цел x
  x := 5
кон
"""
        tree = self._parse(source)
        self.assertEqual(len(tree.declarations), 1)
        block = tree.declarations[0].block
        self.assertEqual(len(block.statements), 1)
        self.assertIsInstance(block.statements[0], Assign)


class TestParserExtended(unittest.TestCase):
    def _parse(self, source):
        return Parser(list(Lexer(source).generate_tokens())).parse()

    def test_if_else(self):
        tree = self._parse("""
алг основнаяпрограмма
нач
  если 1 > 0 то
    вывод 1
  иначе
    вывод 0
  все
кон
""")
        block = tree.declarations[0].block
        self.assertIsInstance(block.statements[0], IfNode)
        self.assertIsNotNone(block.statements[0].else_block)

    def test_loops(self):
        tree = self._parse("""
алг основнаяпрограмма
нач
  нц для i от 1 до 3
    вывод i
  кц
  нц пока 0 = 1
    вывод 0
  кц
кон
""")
        stmts = tree.declarations[0].block.statements
        self.assertIsInstance(stmts[0], ForNode)
        self.assertIsInstance(stmts[1], WhileNode)

    def test_record_and_array(self):
        tree = self._parse("""
запись R
нач
  цел x
кон
алг основнаяпрограмма
нач
  таб цел a[1:2]
кон
""")
        self.assertIsInstance(tree.declarations[0], RecordDecl)
        self.assertIsInstance(tree.declarations[1].block.declarations[0], ArrayDecl)

    def test_use_statement(self):
        tree = self._parse('использовать "lib.alg"\nалг основнаяпрограмма\nнач\nкон')
        from ast_nodes import UseNode
        self.assertIsInstance(tree.declarations[0], UseNode)

    def test_procedure_with_args(self):
        tree = self._parse("""
алг Сумма(арг цел a, цел b; рез цел s)
нач
  s := a + b
кон
алг основнаяпрограмма
нач
кон
""")
        from ast_nodes import FuncDecl
        funcs = [d for d in tree.declarations if isinstance(d, FuncDecl)]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(len(funcs[0].params), 2)


class TestParserBlockRegression(unittest.TestCase):
    """Регрессия: структура блока «нач … кон» и различение объявлений / операторов."""

    def _parse(self, source):
        return Parser(list(Lexer(source).generate_tokens())).parse()

    def test_pre_begin_declaration(self):
        tree = self._parse("""
алг тест
  цел x
нач
  x := 1
кон
""")
        block = tree.declarations[0].block
        self.assertEqual(len(block.declarations), 1)
        self.assertEqual(block.declarations[0].var_node.name, "x")
        self.assertEqual(len(block.statements), 1)

    def test_interleaved_decl_and_statement(self):
        tree = self._parse("""
алг основнаяпрограмма
нач
  цел x
  x := 1
  цел y
  y := 2
кон
""")
        block = tree.declarations[0].block
        var_names = [d.var_node.name for d in block.declarations]
        self.assertEqual(var_names, ["x", "y"])
        self.assertEqual(len(block.statements), 2)
        self.assertIsInstance(block.statements[0], Assign)
        self.assertIsInstance(block.statements[1], Assign)

    def test_custom_type_decl_after_statement(self):
        tree = self._parse("""
запись точка
нач
  цел x
кон
алг основнаяпрограмма
нач
  точка p
  p.x := 1
  точка q
кон
""")
        block = tree.declarations[1].block
        custom_decls = [d for d in block.declarations if d.type_node.name == "точка"]
        self.assertEqual(len(custom_decls), 2)
        self.assertEqual(len(block.statements), 1)

    def test_id_assign_is_statement(self):
        tree = self._parse("""
алг основнаяпрограмма
нач
  цел x
  x := 10
кон
""")
        block = tree.declarations[0].block
        self.assertEqual(len(block.declarations), 1)
        self.assertEqual(len(block.statements), 1)

    def test_procedure_call_after_declarations(self):
        tree = self._parse("""
алг печать
нач
  вывод "ok"
кон
алг основнаяпрограмма
нач
  печать()
кон
""")
        block = tree.declarations[1].block
        self.assertEqual(len(block.declarations), 0)
        self.assertEqual(len(block.statements), 1)
        from ast_nodes import SubroutineCall
        self.assertIsInstance(block.statements[0], SubroutineCall)
