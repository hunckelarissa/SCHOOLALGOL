"""
Базовый посетитель AST для интерпретатора, транспилятора и семантического анализа.
"""

from __future__ import annotations

from ast_nodes import AST

# Узлы AST, для которых нужны visit_* в интерпретаторе и (при поддержке) транспиляторе.
# При добавлении нового узла — см. CONTRIBUTING.md «Чеклист узла AST».
AST_NODE_TYPES: tuple[str, ...] = (
    "Program",
    "UseNode",
    "Block",
    "ConstDecl",
    "VarDecl",
    "ArrayDecl",
    "RecordDecl",
    "EnumDecl",
    "Param",
    "ProcDecl",
    "FuncDecl",
    "Assign",
    "Print",
    "Input",
    "IfNode",
    "ForNode",
    "WhileNode",
    "SubroutineCall",
    "BinOp",
    "UnaryOp",
    "Num",
    "String",
    "Bool",
    "Var",
    "ArrayAccess",
    "MemberAccess",
    "Type",
    "CustomType",
    "FormatSpec",
)


class NodeVisitor:
    """Паттерн «Посетитель»: диспетчеризация visit_<ИмяУзла>."""

    def visit(self, node: AST, **kwargs):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node: AST, **kwargs):
        """Вызывается, если подкласс не реализовал visit_<тип>."""
        raise NotImplementedError(
            f"Нет метода visit_{type(node).__name__} в {type(self).__name__}"
        )

    def iter_child_nodes(self, node: AST):
        """
        Итератор по прямым дочерним узлам AST (для обхода/диагностики).
        Пропускает token и не-AST поля.
        """
        if not hasattr(node, "__dict__"):
            return
        for key, value in vars(node).items():
            if key == "token":
                continue
            if isinstance(value, AST):
                yield key, value
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, AST):
                        yield f"{key}[{i}]", item
                    elif isinstance(item, tuple):
                        for j, part in enumerate(item):
                            if isinstance(part, AST):
                                yield f"{key}[{i}][{j}]", part
