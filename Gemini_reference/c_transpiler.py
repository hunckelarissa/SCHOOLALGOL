import os
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
from lang_tokens import TokenType
from errors import TranspilerError
from module_loader import load_alg_file
from version import __version__
from constants import is_main_program, procedure_alg_comment
from builtin_names import resolve_builtin, is_builtin, resolve_file_mode
from types_model import canonical_type

from alg_warnings import TranspilerWarning, WarningCollector, MemoryLeakWarning
from visitors import NodeVisitor


class CTranspiler(NodeVisitor):
    def __init__(self, tree, main_filepath, verbose=False, warnings=None, permissive=False, keep_cyrillic=False):
        self.tree = tree
        self.main_filepath = main_filepath
        self.verbose = verbose
        self.permissive = permissive
        self.keep_cyrillic = keep_cyrillic
        self.warnings = warnings if warnings is not None else WarningCollector()
        self.headers = [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "#include <math.h>",
            "#include <time.h>",
            "#include <stdbool.h>",
            "#include <ctype.h>",
        ]
        self.main_code = []
        self.main_program_name = None
        self.functions_code = []
        self.global_declarations = []
        self.indent_level = 0
        self.var_types = {}
        self.array_offsets = {}
        self.enum_type_names = set()
        self._tmp_counter = 0
        self.loaded_modules = set()
        self._module_load_stack: list[str] = []

        self.runtime_code = """
// --- Runtime Helpers ---
char* str_concat(const char* s1, const char* s2) {
    char* result = malloc(strlen(s1) + strlen(s2) + 1);
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

char* num_to_str(double num) {
    char* buffer = malloc(64);
    if ((long)num == num) sprintf(buffer, "%%ld", (long)num);
    else sprintf(buffer, "%%g", num);
    return buffer;
}

double alg_strlen(const char* s) {
    return (double)strlen(s);
}

char* alg_substr(const char* s, int start, int count) {
    int len = (int)strlen(s);
    int i0 = start - 1;
    if (i0 < 0) i0 = 0;
    if (i0 >= len) { char* e = malloc(1); e[0] = 0; return e; }
    if (count < 0) count = 0;
    if (i0 + count > len) count = len - i0;
    char* out = malloc((size_t)count + 1);
    strncpy(out, s + i0, (size_t)count);
    out[count] = 0;
    return out;
}

char* alg_toupper(const char* s) {
    size_t n = strlen(s);
    char* out = malloc(n + 1);
    for (size_t i = 0; i < n; i++) out[i] = (char)toupper((unsigned char)s[i]);
    out[n] = 0;
    return out;
}

char* alg_tolower(const char* s) {
    size_t n = strlen(s);
    char* out = malloc(n + 1);
    for (size_t i = 0; i < n; i++) out[i] = (char)tolower((unsigned char)s[i]);
    out[n] = 0;
    return out;
}

int alg_randint(int min_v, int max_v) {
    if (max_v < min_v) { int t = min_v; min_v = max_v; max_v = t; }
    return min_v + (int)(rand() % (max_v - min_v + 1));
}

typedef struct AlgDictEntry {
    char* key;
    double value;
    struct AlgDictEntry* next;
} AlgDictEntry;

typedef struct {
    AlgDictEntry* head;
} AlgDict;

void alg_dict_init(AlgDict* d) { d->head = NULL; }

void alg_dict_set(AlgDict* d, const char* key, double val) {
    for (AlgDictEntry* e = d->head; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { e->value = val; return; }
    }
    AlgDictEntry* ne = malloc(sizeof(AlgDictEntry));
    ne->key = strdup(key);
    ne->value = val;
    ne->next = d->head;
    d->head = ne;
}

double alg_dict_get(AlgDict* d, const char* key) {
    for (AlgDictEntry* e = d->head; e; e = e->next) {
        if (strcmp(e->key, key) == 0) return e->value;
    }
    return 0.0;
}
// --- End Runtime Helpers ---
"""

    def _log(self, message: str) -> None:
        if self.verbose:
            import sys
            print(f"[транспилятор] {message}", file=sys.stderr)

    def _transliterate(self, text):
        if self.keep_cyrillic:
            return self._c_identifier(text)
        text = text.lower()
        trans_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        result = []
        for char in text:
            if char in trans_map:
                result.append(trans_map[char])
            elif char.isalnum() or char == '_':
                result.append(char)
            else:
                result.append('_')
        return "".join(result)

    def _c_identifier(self, text: str) -> str:
        """Имя для C с сохранением кириллицы (GCC, UTF-8 исходник)."""
        out = []
        for i, char in enumerate(text.lower()):
            if char.isalnum() or char == "_":
                if char.isdigit() and not out:
                    out.append("_")
                out.append(char)
            else:
                out.append("_")
        return "".join(out) or "_"

    def indent(self):
        return "    " * self.indent_level

    def _c_type(self, type_node, string_const=True):
        if isinstance(type_node, CustomType):
            return self._transliterate(type_node.name)
        if not isinstance(type_node, Type):
            return "double"
        v = canonical_type(type_node.value)
        if v == 'цел':
            return "int"
        if v == 'лит':
            return "const char*" if string_const else "char*"
        if v == 'лог':
            return "bool"
        if v == 'файл':
            return "FILE*"
        if v == 'словарь':
            return "AlgDict"
        return "double"

    def _var_cname(self, var_node):
        return self._transliterate(var_node.name)

    def _array_offset(self, owner_expr):
        if isinstance(owner_expr, Var):
            return self.array_offsets.get(self._var_cname(owner_expr), 1)
        return 1

    def _is_dict_access(self, owner_expr):
        if isinstance(owner_expr, Var):
            return self.var_types.get(self._var_cname(owner_expr)) == "AlgDict"
        return False

    def _dict_key_c(self, index_expr):
        if isinstance(index_expr, String):
            return f'"{index_expr.value}"'
        return self.visit(index_expr)

    def _needs_free(self, val):
        return "str_concat(" in val or "num_to_str(" in val or "alg_substr(" in val or "alg_toupper(" in val or "alg_tolower(" in val

    def _heap_alloc_count(self, c_expr: str) -> int:
        return sum(c_expr.count(marker) for marker in self._STRING_EXPR_MARKERS)

    def _warn_possible_heap_leak(self, node, c_expr: str, reason: str) -> None:
        """
        Предупреждение, если сгенерированное C-выражение может утекать:
        вложенные str_concat/num_to_str или контекст без автоматического free.
        """
        if not self._needs_free(c_expr):
            return
        nested = self._heap_alloc_count(c_expr) > 1
        if not nested and reason not in ("конст", "аргумент вызова", "словарь"):
            return
        token = getattr(node, "token", None)
        if token is None and hasattr(node, "op"):
            token = node.op
        detail = f"heap-вызовов: {self._heap_alloc_count(c_expr)}"
        self.warnings.emit(
            MemoryLeakWarning(
                f"возможная утечка памяти в C ({reason}); {detail}. "
                f"Упростите выражение или разбейте на присваивания во «лит».",
                token,
            )
        )
        if self.verbose:
            preview = c_expr if len(c_expr) <= 120 else c_expr[:117] + "..."
            self._log(f"утечка памяти ({reason}): {preview}")

    def _check_call_args_heap(self, node, args: list[str]) -> None:
        string_builtins = frozenset(
            resolve_builtin(n) for n in ("длина", "подстрока", "вверх", "вниз", "встроку", "len", "substr", "upper", "lower", "tostr")
        )
        if resolve_builtin(node.name) not in string_builtins:
            return
        for arg in args:
            if self._needs_free(arg):
                self._warn_possible_heap_leak(node, arg, "аргумент вызова")

    def _file_mode_c(self, mode_val: str) -> str:
        py_mode = resolve_file_mode(mode_val)
        if py_mode is None:
            return '"r"'
        return f'"{py_mode}"'

    def _append_stmt(self, target_list, code):
        if not code:
            return
        if "\n" in code:
            for part in code.strip().split("\n"):
                line = self.indent() + part.strip()
                s = line.strip()
                if s and not s.endswith("}") and not s.endswith(";") and not s.endswith("{"):
                    line += ";"
                target_list.append(line)
        else:
            line = self.indent() + code
            s = line.strip()
            if s and not s.endswith("}") and not s.endswith(";") and not s.endswith("{"):
                line += ";"
            target_list.append(line)

    _STRING_EXPR_MARKERS = ("str_concat(", "alg_substr(", "alg_toupper(", "alg_tolower(", "num_to_str(")

    def _expr_is_string(self, val: str, cname: str | None = None) -> bool:
        if val.startswith('"'):
            return True
        if any(m in val for m in self._STRING_EXPR_MARKERS):
            return True
        if cname and "char*" in self.var_types.get(cname, ""):
            return True
        return False

    def _format_print_item(self, item, fmt, file_var):
        val = self.visit(item)
        print_fn = "fprintf" if file_var else "printf"
        print_arg = f"{file_var}, " if file_var else ""
        lines = []
        has_heap = self._needs_free(val)

        width = self.visit(fmt.width) if fmt else None
        precision = self.visit(fmt.precision) if fmt and fmt.precision else None

        cname = val if val in self.var_types else None
        is_str = self._expr_is_string(val, cname)

        if fmt and width and precision and not is_str:
            lines.append(f'{print_fn}({print_arg}"%*.*f", (int){width}, (int){precision}, (double){val})')
        elif fmt and width and not is_str:
            t = self.var_types.get(val, "double")
            if "int" in t or "bool" in t:
                lines.append(f'{print_fn}({print_arg}"%*d", (int){width}, (int){val})')
            else:
                lines.append(f'{print_fn}({print_arg}"%*g", (int){width}, (double){val})')
        elif fmt and width and is_str:
            if has_heap:
                self._tmp_counter += 1
                tmp = f"_tmp_{self._tmp_counter}"
                lines.append(f"char* {tmp} = {val}")
                lines.append(f'{print_fn}({print_arg}"%*s", (int){width}, {tmp})')
                lines.append(f"free({tmp})")
                return lines
            lines.append(f'{print_fn}({print_arg}"%*s", (int){width}, {val})')
        else:
            c_fmt, cast = "%g", "(double)"
            if is_str:
                c_fmt, cast = "%s", ""
            elif val in self.var_types:
                t = self.var_types[val]
                if "char*" in t:
                    c_fmt, cast = "%s", ""
                elif "int" in t or "bool" in t:
                    c_fmt, cast = "%d", "(int)"
            if has_heap:
                self._tmp_counter += 1
                tmp = f"_tmp_{self._tmp_counter}"
                lines.append(f"char* {tmp} = {val}")
                lines.append(f'{print_fn}({print_arg}"{c_fmt}", {cast}{tmp})')
                lines.append(f"free({tmp})")
            else:
                lines.append(f'{print_fn}({print_arg}"{c_fmt}", {cast}{val})')
        return lines

    def transpile(self):
        self.visit(self.tree)
        code = []
        code.append(f"/* Generated by .alg C transpiler, version {__version__} */")
        code.append("/* Файловый I/O: fopen/fclose, fprintf/fscanf; пути не фильтруются. */")
        code.extend(self.headers)
        code.append(self.runtime_code)
        code.extend(self.global_declarations)
        code.extend(self.functions_code)
        if self.main_program_name:
            code.append(procedure_alg_comment(self.main_program_name))
        code.append("int main() {")
        code.append("    #ifdef _WIN32")
        code.append('    system("chcp 65001 > nul");')
        code.append("    #endif")
        code.append("    srand((unsigned)time(NULL));")
        for line in self.main_code:
            code.append("    " + line)
        code.append("    return 0;")
        code.append("}")
        return "\n".join(code)

    def generic_visit(self, node, **kwargs):
        msg = f"нет метода для узла {type(node).__name__}"
        if self.permissive:
            self.warnings.emit(TranspilerWarning(msg, getattr(node, "token", None)))
            return "0"
        raise TranspilerError(msg, node)

    def visit_Program(self, node):
        for decl in node.declarations:
            if isinstance(decl, (ProcDecl, FuncDecl, UseNode, RecordDecl, EnumDecl)):
                self.visit(decl)
            elif isinstance(decl, (VarDecl, ConstDecl)):
                code = self.visit(decl)
                if code:
                    self.global_declarations.append(code)

    def visit_ProcDecl(self, node):
        trans_name = self._transliterate(node.name)
        if is_main_program(node.name):
            self.main_program_name = node.name
        elif not is_main_program(node.name):
            self.functions_code.append(procedure_alg_comment(node.name))
            self._log(f"генерация процедуры «{node.name}» → {trans_name}()")
        if is_main_program(node.name):
            self.visit_Block(node.block, target_list=self.main_code)
        else:
            params_code = []
            for param in node.params:
                p_type = self._c_type(param.type_node, string_const=False)
                self.var_types[self._transliterate(param.var_node.name)] = p_type
                params_code.append(f"{p_type} {self._transliterate(param.var_node.name)}")
            param_str = ", ".join(params_code)
            self.functions_code.append(f"void {trans_name}({param_str}) {{")
            self.indent_level += 1
            self.visit_Block(node.block, target_list=self.functions_code)
            self.indent_level -= 1
            self.functions_code.append("}")

    def visit_FuncDecl(self, node):
        trans_name = self._transliterate(node.name)
        self.functions_code.append(procedure_alg_comment(node.name))
        self._log(f"генерация функции «{node.name}» → {trans_name}()")
        return_type = self._c_type(node.return_var_decl.type_node, string_const=False) if node.return_var_decl else "double"
        params_code = []
        for param in node.params:
            p_type = self._c_type(param.type_node, string_const=False)
            self.var_types[self._transliterate(param.var_node.name)] = p_type
            params_code.append(f"{p_type} {self._transliterate(param.var_node.name)}")
        param_str = ", ".join(params_code)
        self.functions_code.append(f"{return_type} {trans_name}({param_str}) {{")
        self.indent_level += 1
        if node.return_var_decl:
            self.functions_code.append(self.indent() + self.visit(node.return_var_decl))
        self.visit_Block(node.block, target_list=self.functions_code)
        if node.return_var_decl:
            self.functions_code.append(
                self.indent() + f"return {self._transliterate(node.return_var_decl.var_node.name)};"
            )
        self.indent_level -= 1
        self.functions_code.append("}")

    def visit_Block(self, node, target_list=None):
        current_list = target_list if target_list is not None else self.main_code
        for decl in node.declarations:
            code = self.visit(decl)
            if code:
                self._append_stmt(current_list, code)
        for stmt in node.statements:
            code = self.visit(stmt)
            self._append_stmt(current_list, code)

    def visit_VarDecl(self, node):
        c_type = self._c_type(node.type_node, string_const=False)
        cname = self._var_cname(node.var_node)
        self.var_types[cname] = c_type
        if c_type == "AlgDict":
            return f"AlgDict {cname}; alg_dict_init(&{cname});"
        if isinstance(node.type_node, CustomType):
            return f"{c_type} {cname} = {{0}};"
        init_val = "0"
        if "char*" in c_type or c_type == "FILE*":
            init_val = "NULL"
        return f"{c_type} {cname} = {init_val};"

    def visit_ConstDecl(self, node):
        val = self.visit(node.expr)
        c_type = "const double"
        if val.startswith('"') or self._needs_free(val):
            c_type = "const char*"
        cname = self._transliterate(node.var_node.name)
        self.var_types[cname] = c_type
        if self._needs_free(val):
            self._warn_possible_heap_leak(node, val, "конст")
        return f"{c_type} {cname} = {val};"

    def _escape_c_string(self, text: str) -> str:
        text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'"{text}"'

    def _assign_to_left(self, node, left_c: str, right_c: str) -> str:
        if isinstance(node.left, Var):
            cname = self._var_cname(node.left)
            vtype = self.var_types.get(cname, "")
            if "char*" in vtype:
                if right_c.startswith('"'):
                    right_c = f"strdup({right_c})"
                if self._needs_free(right_c) or right_c.startswith("strdup("):
                    if self._heap_alloc_count(right_c) > 1:
                        self._warn_possible_heap_leak(node, right_c, "присваивание лит")
                    if self.verbose:
                        self._log(f"присваивание лит: освобождение старого буфера «{cname}»")
                    return f"free({left_c}); {left_c} = {right_c};"
        return f"{left_c} = {right_c};"

    def visit_Assign(self, node):
        if isinstance(node.left, ArrayAccess) and self._is_dict_access(node.left.owner_expr):
            owner = self._var_cname(node.left.owner_expr)
            key = self._dict_key_c(node.left.index_expr)
            val = self.visit(node.right)
            self._warn_possible_heap_leak(node, val, "словарь")
            return f"alg_dict_set(&{owner}, {key}, (double){val});"
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self._assign_to_left(node, left, right)

    def visit_Print(self, node):
        file_var = self._transliterate(node.file_node.name) if node.file_node else None
        out = []
        for item, fmt in node.items:
            out.extend(self._format_print_item(item, fmt, file_var))
        nl = f'fprintf({file_var}, "\\n")' if file_var else 'printf("\\n")'
        out.append(nl)
        return "\n".join(out)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op.value
        if op == '=':
            op = '=='
        elif op == '<>':
            op = '!='
        elif op == 'и':
            op = '&&'
        elif op == 'или':
            op = '||'
        elif op == '+':
            if self._expr_is_string(left) or self._expr_is_string(right):
                result = f"str_concat({left}, {right})"
                self._warn_possible_heap_leak(node, result, "цепочка конкатенации")
                return result
        return f"({left} {op} {right})"

    def visit_UnaryOp(self, node):
        val = self.visit(node.expr)
        op = node.op.value
        if node.op.type == TokenType.НЕ:
            op = '!'
        return f"({op}{val})"

    def visit_Num(self, node):
        try:
            v = float(node.value)
            if int(v) == v:
                return str(int(v))
        except (TypeError, ValueError):
            pass
        return str(node.value)

    def visit_Var(self, node):
        return self._transliterate(node.name)

    def visit_String(self, node):
        return self._escape_c_string(node.value)

    def visit_Bool(self, node):
        return "1" if node.value else "0"

    def visit_IfNode(self, node):
        cond = self.visit(node.condition)
        lines = [f"if ({cond}) {{"]
        self.indent_level += 1
        for stmt in node.then_block:
            sc = self.visit(stmt)
            if sc:
                if "\n" in sc:
                    for part in sc.strip().split("\n"):
                        lines.append(self.indent() + part.strip())
                else:
                    s = sc.strip()
                    if not s.endswith(";") and not s.endswith("{"):
                        sc += ";"
                    lines.append(self.indent() + sc)
        self.indent_level -= 1
        if node.else_block:
            lines.append(self.indent() + "} else {")
            self.indent_level += 1
            for stmt in node.else_block:
                sc = self.visit(stmt)
                if sc:
                    if "\n" in sc:
                        for part in sc.strip().split("\n"):
                            lines.append(self.indent() + part.strip())
                    else:
                        s = sc.strip()
                        if not s.endswith(";") and not s.endswith("{"):
                            sc += ";"
                        lines.append(self.indent() + sc)
            self.indent_level -= 1
        lines.append(self.indent() + "}")
        return "\n".join(lines)

    def visit_WhileNode(self, node):
        cond = self.visit(node.condition)
        lines = [f"while ({cond}) {{"]
        self.indent_level += 1
        for stmt in node.body:
            sc = self.visit(stmt)
            if sc:
                lines.append(self.indent() + (sc if sc.endswith(";") else sc + ";"))
        self.indent_level -= 1
        lines.append(self.indent() + "}")
        return "\n".join(lines)

    def visit_ForNode(self, node):
        var = self._var_cname(node.var_node)
        start = self.visit(node.start_val)
        end = self.visit(node.end_val)
        lines = [f"for ({var} = {start}; {var} <= {end}; {var}++) {{"]
        self.indent_level += 1
        for stmt in node.body:
            sc = self.visit(stmt)
            if sc:
                lines.append(self.indent() + (sc if sc.endswith(";") else sc + ";"))
        self.indent_level -= 1
        lines.append(self.indent() + "}")
        return "\n".join(lines)

    def visit_SubroutineCall(self, node):
        name = resolve_builtin(node.name)
        args = [self.visit(a) for a in node.actual_params]
        self._check_call_args_heap(node, args)
        if name == 'корень' and args:
            return f"sqrt({args[0]})"
        if name == 'случ':
            return "((double)rand() / RAND_MAX)"
        if name == 'модуль' and args:
            return f"fabs({args[0]})"
        if name == 'случцел' and len(args) == 2:
            return f"((double)alg_randint((int){args[0]}, (int){args[1]}))"
        if name == 'длина' and args:
            return f"alg_strlen({args[0]})"
        if name == 'подстрока' and len(args) == 3:
            return f"alg_substr({args[0]}, (int){args[1]}, (int){args[2]})"
        if name == 'вверх' and args:
            return f"alg_toupper({args[0]})"
        if name == 'вниз' and args:
            return f"alg_tolower({args[0]})"
        if name == 'вцел' and args:
            return f"((double)(long)({args[0]}))"
        if name == 'ввещ' and args:
            return f"((double)({args[0]}))"
        if name == 'встроку' and args:
            return f"num_to_str((double)({args[0]}))"
        if name == 'конецфайла' and args:
            return f"feof({args[0]})"
        if name == 'открыть' and len(args) == 3:
            fvar = self._transliterate(node.actual_params[0].name)
            path_c = args[1]
            mode_c = self._file_mode_c(args[2])
            return f"{fvar} = fopen({path_c}, {mode_c})"
        if name == 'закрыть' and args:
            fvar = self._transliterate(node.actual_params[0].name)
            return f"fclose({fvar}); {fvar} = NULL"
        return f"{self._transliterate(name)}({', '.join(args)})"

    def visit_MemberAccess(self, node):
        if isinstance(node.owner_expr, Var):
            owner_name = node.owner_expr.name.lower()
            member = self._transliterate(node.member_token.value)
            if owner_name in self.enum_type_names:
                enum_c = self._transliterate(owner_name)
                return f"{enum_c}_{member}"
        owner = self.visit(node.owner_expr)
        member = self._transliterate(node.member_token.value)
        return f"{owner}.{member}"

    def visit_UseNode(self, node):
        module_dir = os.path.dirname(os.path.abspath(self.main_filepath))
        module_path = os.path.normpath(os.path.join(module_dir, node.filepath))
        if module_path in self._module_load_stack:
            chain = self._module_load_stack + [module_path]
            display = " → ".join(os.path.basename(p) for p in chain)
            raise TranspilerError(f"циклический импорт модулей: {display}", node)
        if module_path in self.loaded_modules:
            return ""
        self._module_load_stack.append(module_path)
        self.loaded_modules.add(module_path)
        self._log(f"подключение модуля «{node.filepath}» из {module_path}")
        try:
            module_ast = load_alg_file(module_path)
        except FileNotFoundError:
            self._module_load_stack.pop()
            self.loaded_modules.discard(module_path)
            if self.permissive:
                self.warnings.emit(TranspilerWarning(f"файл модуля не найден: {module_path}", node.token))
                return ""
            raise TranspilerError(f"файл модуля не найден: {module_path}", node)
        try:
            self.visit(module_ast)
            self._log(f"модуль «{node.filepath}» включён")
        finally:
            if self._module_load_stack and self._module_load_stack[-1] == module_path:
                self._module_load_stack.pop()
        return ""

    def visit_ArrayDecl(self, node):
        start_val = self.visit(node.start_idx)
        end_val = self.visit(node.end_idx)
        try:
            start = int(float(start_val))
        except ValueError:
            start = 1
        try:
            end = int(float(end_val))
        except ValueError:
            end = start
        size = end - start + 1
        c_type = self._c_type(node.type_node)
        cname = self._var_cname(node.var_node)
        self.array_offsets[cname] = start
        self.var_types[cname] = f"{c_type}*"
        return f"{c_type} {cname}[{size}];"

    def visit_ArrayAccess(self, node):
        if self._is_dict_access(node.owner_expr):
            owner = self._var_cname(node.owner_expr)
            key = self._dict_key_c(node.index_expr)
            return f"alg_dict_get(&{owner}, {key})"
        arr = self.visit(node.owner_expr)
        idx = self.visit(node.index_expr)
        offset = self._array_offset(node.owner_expr)
        return f"{arr}[((int){idx}) - {offset}]"

    def visit_Input(self, node):
        file_var = self._transliterate(node.file_node.name) if node.file_node else None
        vars_code = []
        for var in node.var_nodes:
            cname = self._transliterate(var.name)
            t = self.var_types.get(cname, "double")
            if file_var:
                if "int" in t or "bool" in t:
                    vars_code.append(f'fscanf({file_var}, "%d", &{cname});')
                elif "char*" in t:
                    self._tmp_counter += 1
                    buf = f"_inbuf_{self._tmp_counter}"
                    vars_code.extend([
                        f"char {buf}[4096];",
                        f"if (fgets({buf}, (int)sizeof({buf}), {file_var})) {{",
                        f"  size_t _ln = strlen({buf});",
                        f"  if (_ln && {buf}[_ln-1]=='\\n') {buf}[--_ln]=0;",
                        f"  free({cname}); {cname} = strdup({buf});",
                        "}",
                    ])
                else:
                    vars_code.append(f'fscanf({file_var}, "%lf", &{cname});')
            else:
                if "int" in t or "bool" in t:
                    vars_code.append(f'scanf("%d", &{cname});')
                elif "char*" in t:
                    self._tmp_counter += 1
                    buf = f"_inbuf_{self._tmp_counter}"
                    vars_code.extend([
                        f"char {buf}[4096];",
                        f'scanf("%4095s", {buf});',
                        f"free({cname}); {cname} = strdup({buf});",
                    ])
                else:
                    vars_code.append(f'scanf("%lf", &{cname});')
        return "\n".join(vars_code)

    def visit_RecordDecl(self, node):
        self._log(f"объявление struct «{node.name}»")
        fields = []
        for field in node.fields:
            if isinstance(field, VarDecl):
                c_type = self._c_type(field.type_node, string_const=False)
                fields.append(f"    {c_type} {self._transliterate(field.var_node.name)};")
        struct_name = self._transliterate(node.name)
        struct_def = ["typedef struct {"] + fields + [f"}} {struct_name};"]
        self.global_declarations.append("\n".join(struct_def))
        return ""

    def visit_EnumDecl(self, node):
        self.enum_type_names.add(node.name)
        members = [f"{self._transliterate(node.name)}_{self._transliterate(m.value)}" for m in node.members]
        enum_def = f"typedef enum {{ {', '.join(members)} }} {self._transliterate(node.name)};"
        self.global_declarations.append(enum_def)
        return ""
