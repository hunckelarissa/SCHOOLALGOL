"""Статический семантический анализ AST до выполнения или транспиляции."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

from ast_nodes import (
    ArrayAccess,
    ArrayDecl,
    Assign,
    BinOp,
    Block,
    Bool,
    ConstDecl,
    CustomType,
    EnumDecl,
    ForNode,
    FuncDecl,
    IfNode,
    Input,
    MemberAccess,
    Num,
    Print,
    ProcDecl,
    Program,
    RecordDecl,
    String,
    SubroutineCall,
    Type,
    UnaryOp,
    UseNode,
    Var,
    VarDecl,
    WhileNode,
)
from constants import MAIN_PROGRAM_NAMES, main_program_label
from errors import SemanticError
from module_loader import load_alg_file
from suggestions import format_suggestion_message
from types_model import BUILTIN_ARITY, format_var_type, is_builtin_type, resolve_type_name, get_builtin_arity, canonical_type
from builtin_names import resolve_builtin, is_builtin
from visitors import NodeVisitor


@dataclass
class Symbol:
    name: str
    kind: str  # var, const, sub, type_record, type_enum
    type_name: Optional[str] = None
    token: Any = None
    node: Any = None


class AnalysisFrame:
    """Кадр стека анализа (совместим с format_error: атрибут name)."""

    def __init__(self, name: str, table: "SymbolTable") -> None:
        self.name = name
        self.table = table


class SymbolTable:
    def __init__(self, name: str = "global", parent: Optional["SymbolTable"] = None) -> None:
        self.name = name
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}
        self.type_defs: dict[str, RecordDecl | EnumDecl] = {}

    def define(
        self,
        name: str,
        kind: str,
        *,
        type_name: Optional[str] = None,
        token: Any = None,
        node: Any = None,
    ) -> Symbol:
        key = name.lower()
        if key in self.symbols:
            raise SemanticError(
                f"Повторное объявление «{name}»",
                token,
            )
        sym = Symbol(key, kind, type_name=type_name, token=token, node=node)
        self.symbols[key] = sym
        return sym

    def define_type(self, name: str, decl: RecordDecl | EnumDecl) -> None:
        key = name.lower()
        self.type_defs[key] = decl

    def lookup(self, name: str) -> Optional[Symbol]:
        key = name.lower()
        if key in self.symbols:
            return self.symbols[key]
        if self.parent:
            return self.parent.lookup(key)
        return None

    def lookup_type_def(self, name: str) -> Optional[RecordDecl | EnumDecl]:
        key = name.lower()
        if key in self.type_defs:
            return self.type_defs[key]
        if self.parent:
            return self.parent.lookup_type_def(key)
        return None

    def has(self, name: str) -> bool:
        return self.lookup(name) is not None

    def visible_names(self) -> list[str]:
        names: set[str] = set(self.symbols.keys())
        if self.parent:
            names.update(self.parent.visible_names())
        return sorted(names)

class SemanticAnalyzer(NodeVisitor):
    """Предварительный семантический проход: символы, типы, статические ошибки."""

    def __init__(self, tree: Program, main_filepath: str, verbose: bool = False) -> None:
        self.tree = tree
        self.main_filepath = main_filepath
        self.verbose = verbose
        self.global_table = SymbolTable("global")
        self.current_table = self.global_table
        self.frames: list[AnalysisFrame] = [AnalysisFrame("global", self.global_table)]
        self.loaded_modules: set[str] = set()
        self._module_load_stack: list[str] = []

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[семантика] {message}", file=sys.stderr)

    def _call_stack(self) -> list[AnalysisFrame]:
        return self.frames

    def _raise_undefined(self, name: str, token: Any) -> None:
        hint = format_suggestion_message(name, self.current_table.visible_names())
        err = SemanticError(
            f"Переменная, константа или тип «{name}» не определена",
            token,
            self._call_stack(),
        )
        if hint:
            err.hint = hint
        raise err

    def analyze(self) -> None:
        self.visit(self.tree)
        self._dump_symbol_table()

    def generic_visit(self, node, **kwargs) -> None:
        raise SemanticError(
            f"Семантический анализатор не поддерживает узел {type(node).__name__}",
            getattr(node, "token", None),
            self._call_stack(),
        )

    def _resolve_type(self, type_node, token: Any) -> str:
        name = resolve_type_name(type_node)
        if is_builtin_type(name):
            return name
        if self.current_table.lookup_type_def(name):
            return name
        raise SemanticError(f"Неизвестный тип «{name}»", token, self._call_stack())

    def _process_declarations(self, declarations, base_path: str) -> None:
        for decl in declarations:
            if isinstance(decl, UseNode):
                self.visit(decl, base_path=base_path)
            elif isinstance(decl, (ProcDecl, FuncDecl)):
                kind = "функция" if isinstance(decl, FuncDecl) else "процедура"
                if self.global_table.has(decl.name):
                    self._log(f"повторное объявление {kind} «{decl.name}» (предупреждение на этапе выполнения)")
                else:
                    self.global_table.define(
                        decl.name,
                        "sub",
                        type_name=kind,
                        token=decl.token,
                        node=decl,
                    )
            elif isinstance(decl, RecordDecl):
                self.global_table.define_type(decl.name, decl)
                self.global_table.define(
                    decl.name,
                    "type_record",
                    type_name="запись",
                    token=decl.token,
                    node=decl,
                )
            elif isinstance(decl, EnumDecl):
                self.global_table.define_type(decl.name, decl)
                self.global_table.define(
                    decl.name,
                    "type_enum",
                    type_name="переч",
                    token=decl.token,
                    node=decl,
                )
            elif isinstance(decl, ConstDecl):
                if self.current_table.has(decl.var_node.name):
                    raise SemanticError(
                        f"Переопределение константы «{decl.var_node.name}»",
                        decl.var_node.token,
                        self._call_stack(),
                    )
                self.check_expr(decl.expr)
                self.current_table.define(
                    decl.var_node.name,
                    "const",
                    type_name="конст",
                    token=decl.var_node.token,
                    node=decl,
                )
            elif isinstance(decl, VarDecl):
                self.visit(decl)
            elif isinstance(decl, ArrayDecl):
                self.visit(decl)

    def _analyze_block(self, block: Block) -> None:
        child = SymbolTable(parent=self.current_table, name=self.frames[-1].name)
        prev = self.current_table
        self.current_table = child
        try:
            for decl in block.declarations:
                if isinstance(decl, VarDecl):
                    self.visit(decl)
                elif isinstance(decl, ArrayDecl):
                    self.visit(decl)
                elif isinstance(decl, ConstDecl):
                    if self.current_table.has(decl.var_node.name):
                        raise SemanticError(
                            f"Переопределение константы «{decl.var_node.name}»",
                            decl.var_node.token,
                            self._call_stack(),
                        )
                    self.check_expr(decl.expr)
                    self.current_table.define(
                        decl.var_node.name,
                        "const",
                        type_name="конст",
                        token=decl.var_node.token,
                    )
            for stmt in block.statements:
                self.check_statement(stmt)
        finally:
            self.current_table = prev

    def visit_Program(self, node: Program) -> None:
        self._process_declarations(node.declarations, self.main_filepath)
        main_sym = None
        for main_name in MAIN_PROGRAM_NAMES:
            candidate = self.global_table.lookup(main_name)
            if candidate and candidate.kind == "sub" and isinstance(candidate.node, ProcDecl):
                main_sym = candidate
                break
        if not main_sym:
            raise SemanticError(f"Не найдена главная программа «алг {main_program_label()}»")
        for decl in node.declarations:
            if isinstance(decl, (ProcDecl, FuncDecl)):
                self._analyze_subroutine(decl)

    def _analyze_subroutine(self, decl: ProcDecl | FuncDecl) -> None:
        frame_name = decl.name
        local_table = SymbolTable(parent=self.global_table, name=frame_name)
        self.frames.append(AnalysisFrame(frame_name, local_table))
        prev = self.current_table
        self.current_table = local_table
        try:
            for param in decl.params:
                type_name = self._resolve_type(param.type_node, param.var_node.token)
                local_table.define(
                    param.var_node.name,
                    "var",
                    type_name=type_name,
                    token=param.var_node.token,
                )
            if isinstance(decl, FuncDecl) and decl.return_var_decl:
                rv = decl.return_var_decl
                type_name = self._resolve_type(rv.type_node, rv.var_node.token)
                local_table.define(
                    rv.var_node.name,
                    "var",
                    type_name=type_name,
                    token=rv.var_node.token,
                )
            self._analyze_block(decl.block)
            self._log(f"область «{frame_name}»: {len(local_table.symbols)} символ(ов)")
        finally:
            self.current_table = prev
            self.frames.pop()

    def visit_UseNode(self, node: UseNode, base_path: str) -> None:
        module_dir = os.path.dirname(os.path.abspath(base_path))
        module_path = os.path.normpath(os.path.join(module_dir, node.filepath))
        if module_path in self._module_load_stack:
            chain = self._module_load_stack + [module_path]
            display = " → ".join(os.path.basename(p) for p in chain)
            raise SemanticError(
                f"Циклический импорт модулей: {display}",
                node.token,
                self._call_stack(),
            )
        if module_path in self.loaded_modules:
            self._log(f"модуль уже загружен: {node.filepath}")
            return
        self._module_load_stack.append(module_path)
        self.loaded_modules.add(module_path)
        self._log(f"загрузка модуля «{node.filepath}» из {module_path}")
        try:
            module_ast = load_alg_file(module_path)
        except FileNotFoundError:
            self._module_load_stack.pop()
            self.loaded_modules.discard(module_path)
            raise SemanticError(
                f"Файл модуля не найден: «{module_path}» (искали относительно «{base_path}»)",
                node.token,
                self._call_stack(),
            )
        try:
            self._process_declarations(module_ast.declarations, module_path)
            for d in module_ast.declarations:
                if isinstance(d, (ProcDecl, FuncDecl)):
                    self._analyze_subroutine(d)
        finally:
            if self._module_load_stack and self._module_load_stack[-1] == module_path:
                self._module_load_stack.pop()

    def visit_VarDecl(self, node: VarDecl) -> None:
        type_name = self._resolve_type(node.type_node, node.var_node.token)
        self.current_table.define(
            node.var_node.name,
            "var",
            type_name=type_name,
            token=node.var_node.token,
            node=node,
        )

    def visit_ArrayDecl(self, node: ArrayDecl) -> None:
        type_name = format_var_type(node.type_node, is_array=True)
        self._resolve_type(node.type_node, node.var_node.token)
        start = self._eval_const_expr(node.start_idx)
        end = self._eval_const_expr(node.end_idx)
        if start is not None and end is not None and int(start) > int(end):
            raise SemanticError(
                f"Начальный индекс массива {int(start)} больше конечного {int(end)}",
                node.var_node.token,
                self._call_stack(),
            )
        self.current_table.define(
            node.var_node.name,
            "var",
            type_name=type_name,
            token=node.var_node.token,
            node=node,
        )

    def _eval_const_expr(self, expr) -> Optional[float]:
        if isinstance(expr, Num):
            return expr.value
        if isinstance(expr, UnaryOp) and expr.op.value == "-":
            inner = self._eval_const_expr(expr.expr)
            return -inner if inner is not None else None
        if isinstance(expr, BinOp) and expr.op.value in ("+", "-"):
            left = self._eval_const_expr(expr.left)
            right = self._eval_const_expr(expr.right)
            if left is None or right is None:
                return None
            return left + right if expr.op.value == "+" else left - right
        self.check_expr(expr)
        return None

    def check_statement(self, stmt) -> None:
        if isinstance(stmt, Assign):
            self._check_assign(stmt)
        elif isinstance(stmt, SubroutineCall):
            self._check_subroutine_call(stmt, allow_void=True)
        elif isinstance(stmt, Print):
            self._check_print(stmt)
        elif isinstance(stmt, Input):
            self._check_input(stmt)
        elif isinstance(stmt, IfNode):
            self.check_expr(stmt.condition)
            for s in stmt.then_block:
                self.check_statement(s)
            if stmt.else_block:
                for s in stmt.else_block:
                    self.check_statement(s)
        elif isinstance(stmt, ForNode):
            self.check_expr(stmt.start_val)
            self.check_expr(stmt.end_val)
            var_name = stmt.var_node.name
            if not self.current_table.has(var_name):
                self.current_table.define(
                    var_name,
                    "var",
                    type_name="цел",
                    token=stmt.var_node.token,
                )
                self._log(f"нц для: неявное объявление цел «{var_name}»")
            for s in stmt.body:
                self.check_statement(s)
        elif isinstance(stmt, WhileNode):
            self.check_expr(stmt.condition)
            for s in stmt.body:
                self.check_statement(s)
        else:
            self.visit(stmt)

    def _node_token(self, node) -> Any:
        if hasattr(node, "token") and node.token is not None:
            return node.token
        if isinstance(node, ArrayAccess):
            return self._node_token(node.owner_expr)
        if isinstance(node, MemberAccess):
            return node.member_token
        return None

    def _check_assign(self, node: Assign) -> None:
        self.check_expr(node.right)
        self._check_lvalue(node.left, self._node_token(node.left))

    def _check_lvalue(self, node, token: Any) -> None:
        if isinstance(node, Var):
            if not self._resolve_var_or_type(node.name, node.token):
                self._raise_undefined(node.name, node.token)
        elif isinstance(node, ArrayAccess):
            self.check_expr(node.owner_expr)
            self.check_expr(node.index_expr)
        elif isinstance(node, MemberAccess):
            self.check_expr(node.owner_expr)
        else:
            raise SemanticError(
                "Нельзя присвоить значение этому выражению",
                token,
                self._call_stack(),
            )

    def _resolve_var_or_type(self, name: str, token: Any) -> bool:
        if self.current_table.lookup(name):
            return True
        if self.current_table.lookup_type_def(name):
            return True
        return False

    def check_expr(self, expr) -> None:
        if isinstance(expr, Num):
            return
        if isinstance(expr, String):
            return
        if isinstance(expr, Bool):
            return
        if isinstance(expr, Var):
            if not self._resolve_var_or_type(expr.name, expr.token):
                self._raise_undefined(expr.name, expr.token)
            return
        if isinstance(expr, UnaryOp):
            self.check_expr(expr.expr)
            return
        if isinstance(expr, BinOp):
            self.check_expr(expr.left)
            self.check_expr(expr.right)
            return
        if isinstance(expr, SubroutineCall):
            self._check_subroutine_call(expr, allow_void=False)
            return
        if isinstance(expr, ArrayAccess):
            self.check_expr(expr.owner_expr)
            self.check_expr(expr.index_expr)
            return
        if isinstance(expr, MemberAccess):
            self.check_expr(expr.owner_expr)
            return
        self.visit(expr)

    def _check_subroutine_call(self, node: SubroutineCall, *, allow_void: bool) -> None:
        name = node.name
        for arg in node.actual_params:
            self.check_expr(arg)
        if is_builtin(name):
            expected = get_builtin_arity(name)
            if expected is not None and len(node.actual_params) != expected:
                raise SemanticError(
                    f"Функция «{name}» ожидает {expected} аргумент(ов), "
                    f"а получила {len(node.actual_params)}",
                    node.token,
                    self._call_stack(),
                )
            return
        sym = self.global_table.lookup(name)
        if not sym or sym.kind != "sub" or sym.node is None:
            hint = format_suggestion_message(name, self.global_table.visible_names())
            err = SemanticError(
                f"Процедура или функция «{name}» не определена",
                node.token,
                self._call_stack(),
            )
            if hint:
                err.hint = hint
            raise err
        sub_decl = sym.node
        if len(node.actual_params) != len(sub_decl.params):
            param_names = ", ".join(p.var_node.name for p in sub_decl.params)
            raise SemanticError(
                f"Неверное количество аргументов для «{name}»: ожидается {len(sub_decl.params)} "
                f"({param_names}), передано {len(node.actual_params)}",
                node.token,
                self._call_stack(),
            )

    def _check_print(self, node: Print) -> None:
        if node.file_node:
            self._check_file_var(node.file_node)
        for expr, _fmt in node.items:
            self.check_expr(expr)

    def _check_input(self, node: Input) -> None:
        if node.file_node:
            self._check_file_var(node.file_node)
        for var_node in node.var_nodes:
            if not self.current_table.lookup(var_node.name):
                self._raise_undefined(var_node.name, var_node.token)

    def _check_file_var(self, var_node: Var) -> None:
        sym = self.current_table.lookup(var_node.name)
        if not sym:
            self._raise_undefined(var_node.name, var_node.token)
        if sym.type_name != "файл" and canonical_type(sym.type_name or "") != "файл":
            raise SemanticError(
                f"Переменная «{var_node.name}» должна иметь тип файл",
                var_node.token,
                self._call_stack(),
            )

    def _dump_symbol_table(self) -> None:
        if not self.verbose:
            return
        self._log("таблица символов (global):")
        for name, sym in sorted(self.global_table.symbols.items()):
            if sym.kind == "sub":
                self._log(f"  {sym.type_name} {name}")
            elif sym.kind.startswith("type_"):
                self._log(f"  {sym.type_name} {name}")
            else:
                t = sym.type_name or "?"
                self._log(f"  {t} {name}")
