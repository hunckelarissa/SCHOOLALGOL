"""Тесты базового NodeVisitor."""
import unittest

from ast_nodes import Num, BinOp
from lang_tokens import TokenType
from visitors import NodeVisitor, AST_NODE_TYPES


class _SumVisitor(NodeVisitor):
    def visit_Num(self, node):
        return node.value

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op.value == "+":
            return left + right
        return left - right


class TestNodeVisitor(unittest.TestCase):
    def test_dispatch_to_visit_method(self):
        tree = Num(_token("3"))
        self.assertEqual(_SumVisitor().visit(tree), 3.0)

    def test_binop_traversal(self):
        tree = BinOp(Num(_token("1")), _op("+"), Num(_token("2")))
        self.assertEqual(_SumVisitor().visit(tree), 3.0)

    def test_generic_visit_raises(self):
        class EmptyVisitor(NodeVisitor):
            pass

        with self.assertRaises(NotImplementedError):
            EmptyVisitor().visit(Num(_token("0")))

    def test_ast_node_types_registry(self):
        self.assertIn("Program", AST_NODE_TYPES)
        self.assertIn("Assign", AST_NODE_TYPES)
        self.assertIn("FormatSpec", AST_NODE_TYPES)


def _token(text):
    class T:
        type = TokenType.NUMBER
        value = text
        line = 1
        col = 1

    return T()


def _op(text):
    class T:
        type = TokenType.OP
        value = text
        line = 1
        col = 1

    return T()


if __name__ == "__main__":
    unittest.main()
