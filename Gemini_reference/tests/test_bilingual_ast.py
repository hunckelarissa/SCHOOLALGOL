"""AST-паритет RU ↔ EN."""
import os
import unittest

from lexer import Lexer
from parser import Parser
from ast_compare import ast_shapes_equal
from tests.helpers import ROOT


class TestBilingualAst(unittest.TestCase):
    PAIRS = [
        (
            """
алг P
нач
  цел x
  x := 1
кон
""",
            """
proc P
begin
  int x
  x := 1
end
""",
        ),
        (
            """
алг P
нач
  если 1 > 0 то
    вывод 1
  все
кон
""",
            """
proc P
begin
  if 1 > 0 then
    output 1
  endif
end
""",
        ),
        (
            """
алг P
нач
  нц для i от 1 до 2
    вывод i
  кц
кон
""",
            """
proc P
begin
  loop for i from 1 to 2
    output i
  eloop
end
""",
        ),
    ]

    def _parse(self, source: str):
        return Parser(list(Lexer(source).generate_tokens())).parse()

    def test_handcrafted_pairs_isomorphic(self):
        for ru, en in self.PAIRS:
            with self.subTest(ru=ru.strip()[:20]):
                ru_tree = self._parse(ru)
                en_tree = self._parse(en)
                self.assertTrue(
                    ast_shapes_equal(ru_tree, en_tree, normalize_bilingual=True),
                )

    def test_program_files_isomorphic(self):
        ru_dir = os.path.join(ROOT, "tests", "programs")
        en_dir = os.path.join(ru_dir, "en")
        names = [
            "loops.alg",
            "arrays.alg",
            "builtins.alg",
            "format.alg",
            "records.alg",
            "dict.alg",
            "files.alg",
        ]
        for name in names:
            with self.subTest(name=name):
                with open(os.path.join(ru_dir, name), encoding="utf-8") as f:
                    ru_tree = self._parse(f.read())
                with open(os.path.join(en_dir, name), encoding="utf-8") as f:
                    en_tree = self._parse(f.read())
                self.assertTrue(
                    ast_shapes_equal(ru_tree, en_tree, normalize_bilingual=True),
                    msg=f"AST shape mismatch for {name}",
                )


if __name__ == "__main__":
    unittest.main()
