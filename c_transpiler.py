import os
import sys
from ast_nodes import *
from lang_tokens import TokenType
from errors import TranspilerError
from module_loader import (
    CyclicImportError,
    ModuleFileNotFoundError,
    ModuleLoadTracker,
    open_module,
)
from version import __version__
from constants import is_main_program, procedure_alg_comment
from builtin_names import resolve_builtin, resolve_file_mode
from types_model import canonical_type
from alg_warnings import TranspilerWarning, WarningCollector, MemoryLeakWarning
from visitors import NodeVisitor


class CTranspiler(NodeVisitor):
    def __init__(
        self,
        tree,
        main_filepath,
        *,
        verbose=False,
        warnings=None,
        permissive=False,
        keep_cyrillic=False,
    ):
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
            "#include <ctype.h>",
            "#include <math.h>",
            "#include <time.h>",
            "#include <stdbool.h>",
        ]
        self.main_code = []
        self.main_program_name = None
        self.functions_code = []
        self.prototypes: list[str] = []
        self.global_declarations = []
        self.indent_level = 0
        self.var_types = {}  # Name -> C type string
        self.array_offsets = {}
        self.array_sizes = {}
        self.enum_type_names = set()
        self._tmp_counter = 0
        self._modules = ModuleLoadTracker()
        self._current_return_var: str | None = None
        self._in_main = False
        # Имя функции → список индексов параметров-массивов (для передачи размера)
        self._array_param_indices: dict[str, list[int]] = {}
        # Имя функции → C-тип возвращаемого значения (для вывода лог как да/нет)
        self._func_return_ctypes: dict[str, str] = {}
        # Имя параметра-массива → имя C-переменной длины (внутри функции)
        self._array_len_vars: dict[str, str] = {}

        # Runtime helpers: str_concat/num_to_str/alg_* → malloc; вызывающий free при необходимости.
        self.runtime_code = r"""
// --- Runtime Helpers ---
char* str_concat(const char* s1, const char* s2) {
    if (!s1) s1 = "";
    if (!s2) s2 = "";
    char* result = malloc(strlen(s1) + strlen(s2) + 1);
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

char* num_to_str(double num) {
    char* buffer = malloc(64);
    if ((long)num == num) sprintf(buffer, "%ld", (long)num);
    else sprintf(buffer, "%g", num);
    return buffer;
}

double alg_strlen(const char* s) {
    return (double)strlen(s ? s : "");
}

char* alg_substr(const char* s, int start, int count) {
    if (!s) s = "";
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
    if (!s) s = "";
    size_t n = strlen(s);
    char* out = malloc(n + 1);
    for (size_t i = 0; i < n; i++) out[i] = (char)toupper((unsigned char)s[i]);
    out[n] = 0;
    return out;
}

char* alg_tolower(const char* s) {
    if (!s) s = "";
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

double alg_atof(const char* s) {
    return s ? atof(s) : 0.0;
}

long alg_atol(const char* s) {
    return s ? atol(s) : 0L;
}

double alg_find(const char* s, const char* sub) {
    if (!s || !sub) return 0.0;
    char* pos = strstr(s, sub);
    return pos ? (double)(pos - s + 1) : 0.0;
}

double alg_sign(double x) {
    if (x > 0) return 1.0;
    if (x < 0) return -1.0;
    return 0.0;
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
    ne->key = strdup(key ? key : "");
    ne->value = val;
    ne->next = d->head;
    d->head = ne;
}

double alg_dict_get(AlgDict* d, const char* key) {
    for (AlgDictEntry* e = d->head; e; e = e->next) {
        if (strcmp(e->key, key ? key : "") == 0) return e->value;
    }
    return 0.0;
}
// --- End Runtime Helpers ---
"""

    def _log(self, message: str) -> None:
        if self.verbose:
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
        for char in text.lower():
            if char.isalnum() or char == "_":
                if char.isdigit() and not out:
                    out.append("_")
                out.append(char)
            else:
                out.append("_")
        return "".join(out) or "_"

    def _var_cname(self, var_node):
        return self._transliterate(var_node.name)

    def _array_offset(self, owner_expr):
        if isinstance(owner_expr, Var):
            return self.array_offsets.get(self._var_cname(owner_expr), 1)
        return 1

    def indent(self):
        return "    " * self.indent_level

    def _c_type(self, type_node, string_const=True):
        """Единый маппинг типа ALG → C. string_const: для лит использовать const char* (True) или char* (False)."""
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

    def _c_type_ptr(self, type_node) -> str:
        """Тип указателя на элемент массива."""
        base = self._c_type(type_node, string_const=False)
        if base.endswith("*"):
            return base
        return f"{base}*"

    def _param_signature(self, node) -> str:
        """Строка параметров C без побочных эффектов (для прототипов)."""
        parts = []
        for param in node.params:
            cname = self._transliterate(param.var_node.name)
            if getattr(param.type_node, "is_array", False):
                p_type = self._c_type_ptr(param.type_node)
                parts.append(f"{p_type} {cname}")
                parts.append(f"int {cname}_len")
                parts.append(f"int {cname}_off")
            else:
                p_type = self._c_type(param.type_node, string_const=False)
                parts.append(f"{p_type} {cname}")
        return ", ".join(parts)

    def _function_prototype(self, node) -> str:
        """Объявление функции/процедуры для forward-вызовов."""
        if is_main_program(node.name):
            return ""
        trans_name = self._transliterate(node.name)
        params = self._param_signature(node)
        if isinstance(node, FuncDecl) and node.return_var_decl:
            ret = self._c_type(node.return_var_decl.type_node, string_const=False)
        else:
            ret = "void"
        return f"{ret} {trans_name}({params});"

    def _format_params(self, node) -> str:
        """C-параметры; для таб добавляет `_len` и `_off` (размер и offset)."""
        params_code = []
        array_indices: list[int] = []
        for i, param in enumerate(node.params):
            cname = self._transliterate(param.var_node.name)
            if getattr(param.type_node, "is_array", False):
                p_type = self._c_type_ptr(param.type_node)
                len_name = f"{cname}_len"
                off_name = f"{cname}_off"
                self.var_types[cname] = p_type
                self.array_sizes[cname] = len_name
                self.array_offsets[cname] = off_name  # C-выражение offset
                params_code.append(f"{p_type} {cname}")
                params_code.append(f"int {len_name}")
                params_code.append(f"int {off_name}")
                array_indices.append(i)
            else:
                p_type = self._c_type(param.type_node, string_const=False)
                self.var_types[cname] = p_type
                params_code.append(f"{p_type} {cname}")
        self._array_param_indices[self._transliterate(node.name)] = array_indices
        self._array_param_indices[node.name.lower()] = array_indices
        return ", ".join(params_code)

    def _is_dict_access(self, owner_expr):
        if isinstance(owner_expr, Var):
            return self.var_types.get(self._var_cname(owner_expr)) == "AlgDict"
        return False

    def _dict_key_c(self, index_expr):
        if isinstance(index_expr, String):
            return self._escape_c_string(index_expr.value)
        return self.visit(index_expr)

    def _escape_c_string(self, text: str) -> str:
        text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
        return f'"{text}"'

    _STRING_EXPR_MARKERS = ("str_concat(", "alg_substr(", "alg_toupper(", "alg_tolower(", "num_to_str(")

    def _needs_free(self, val):
        """Выражение выделяет память через str_concat/num_to_str/alg_* и требует free()."""
        return any(m in val for m in self._STRING_EXPR_MARKERS)

    def _heap_alloc_count(self, c_expr: str) -> int:
        return sum(c_expr.count(marker) for marker in self._STRING_EXPR_MARKERS)

    def _warn_possible_heap_leak(self, node, c_expr: str, reason: str) -> None:
        if not self._needs_free(c_expr):
            return
        nested = self._heap_alloc_count(c_expr) > 1
        if not nested and reason not in ("конст", "аргумент вызова", "словарь"):
            return
        token = getattr(node, "token", None)
        if token is None and hasattr(node, "op"):
            token = node.op
        self.warnings.emit(
            MemoryLeakWarning(
                f"возможная утечка памяти в C ({reason}); "
                f"heap-вызовов: {self._heap_alloc_count(c_expr)}. "
                f"Упростите выражение или разбейте на присваивания во «лит».",
                token,
            )
        )
        if self.verbose:
            preview = c_expr if len(c_expr) <= 120 else c_expr[:117] + "..."
            self._log(f"утечка памяти ({reason}): {preview}")

    def _check_call_args_heap(self, node, args: list) -> None:
        string_builtins = frozenset(
            resolve_builtin(n)
            for n in ("длина", "подстрока", "вверх", "вниз", "встроку", "len", "substr", "upper", "lower", "tostr")
        )
        if resolve_builtin(node.name) not in string_builtins:
            return
        for arg in args:
            if self._needs_free(arg):
                self._warn_possible_heap_leak(node, arg, "аргумент вызова")

    def _expr_is_c_string(self, val, cname=None):
        if val.startswith('"'):
            return True
        if any(m in val for m in self._STRING_EXPR_MARKERS):
            return True
        if cname and "char*" in self.var_types.get(cname, ""):
            return True
        if val in self.var_types and "char*" in self.var_types[val]:
            return True
        return False

    def _file_mode_c(self, mode_val: str) -> str:
        """Режим файла ALG → C: чтение/read→r, запись/write→w, дозапись/append→a."""
        # mode_val may be a C string literal like "\"чтение\"" or already quoted path expr
        raw = mode_val.strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        py_mode = resolve_file_mode(raw)
        if py_mode is None:
            return '"r"'
        return f'"{py_mode}"'

    def _append_stmt(self, target_list, code):
        if not code:
            return
        raw_lines = code.split("\n")
        non_empty = [l for l in raw_lines if l.strip()]
        if not non_empty:
            return
        min_indent = min(len(l) - len(l.lstrip(" ")) for l in non_empty)
        base = self.indent()
        for part in raw_lines:
            if not part.strip():
                continue
            relative = part[min_indent:] if len(part) >= min_indent else part.lstrip()
            line = base + relative
            s = line.strip()
            if s and not s.endswith("}") and not s.endswith(";") and not s.endswith("{"):
                line += ";"
            target_list.append(line)

    def _expr_is_bool(self, item, val: str) -> bool:
        if isinstance(item, Bool):
            return True
        if isinstance(item, Var):
            return "bool" in self.var_types.get(self._var_cname(item), "")
        if isinstance(item, SubroutineCall):
            key = self._transliterate(item.name)
            ret = self._func_return_ctypes.get(key) or self._func_return_ctypes.get(item.name.lower())
            return bool(ret and "bool" in ret)
        if isinstance(item, UnaryOp) and item.op.type == TokenType.НЕ:
            return True
        if isinstance(item, BinOp):
            if item.op.type in (
                TokenType.И, TokenType.ИЛИ, TokenType.EQ, TokenType.NEQ,
                TokenType.LTE, TokenType.GTE,
            ):
                return True
            if item.op.type == TokenType.OP and item.op.value in (">", "<"):
                return True
        return "bool" in self.var_types.get(val, "")

    def _format_print_item(self, item, fmt, file_var):
        val = self.visit(item)
        print_fn = "fprintf" if file_var else "printf"
        print_arg = f"{file_var}, " if file_var else ""
        lines = []
        has_heap = self._needs_free(val)
        width = self.visit(fmt.width) if fmt else None
        precision = self.visit(fmt.precision) if fmt and fmt.precision else None
        cname = val if val in self.var_types else None
        is_str = self._expr_is_c_string(val, cname)
        is_bool = self._expr_is_bool(item, val)

        if is_bool and not (fmt and width and precision):
            if fmt and width:
                lines.append(
                    f'{print_fn}({print_arg}"%*s ", (int){width}, ({val}) ? "да" : "нет")'
                )
            else:
                lines.append(
                    f'{print_fn}({print_arg}"%s ", ({val}) ? "да" : "нет")'
                )
            return lines

        if fmt and width and precision and not is_str:
            lines.append(f'{print_fn}({print_arg}"%*.*f ", (int){width}, (int){precision}, (double){val})')
        elif fmt and width and not is_str:
            t = self.var_types.get(val, "double")
            if "int" in t:
                lines.append(f'{print_fn}({print_arg}"%*d ", (int){width}, (int){val})')
            else:
                lines.append(f'{print_fn}({print_arg}"%*g ", (int){width}, (double){val})')
        elif fmt and width and is_str:
            if has_heap:
                self._tmp_counter += 1
                tmp = f"_tmp_{self._tmp_counter}"
                lines.append(f"char* {tmp} = {val}")
                lines.append(f'{print_fn}({print_arg}"%*s ", (int){width}, {tmp})')
                lines.append(f"free({tmp})")
            else:
                lines.append(f'{print_fn}({print_arg}"%*s ", (int){width}, {val})')
        else:
            c_fmt, cast = "%g", "(double)"
            if is_str:
                c_fmt, cast = "%s", ""
            elif val in self.var_types:
                t = self.var_types[val]
                if "char*" in t:
                    c_fmt, cast = "%s", ""
                elif "int" in t:
                    c_fmt, cast = "%d", "(int)"
            if has_heap:
                self._tmp_counter += 1
                tmp = f"_tmp_{self._tmp_counter}"
                lines.append(f"char* {tmp} = {val}")
                lines.append(f'{print_fn}({print_arg}"{c_fmt} ", {cast}{tmp})')
                lines.append(f"free({tmp})")
            else:
                lines.append(f'{print_fn}({print_arg}"{c_fmt} ", {cast}{val})')
        return lines

    def transpile(self):
        self.visit(self.tree)
        code = []
        code.append(f"/* Generated by .alg C transpiler, version {__version__} */")
        code.append("/* Файловый I/O: fopen/fclose, fprintf/fscanf; пути не фильтруются. */")
        code.extend(self.headers)
        code.append(self.runtime_code)
        code.extend(self.global_declarations)
        if self.prototypes:
            code.append("/* Forward declarations */")
            code.extend(self.prototypes)
            code.append("")
        code.extend(self.functions_code)
        if self.main_program_name:
            code.append(procedure_alg_comment(self.main_program_name))
        code.append("int main() {")
        code.append("    #ifdef _WIN32")
        code.append("    /* Кодовая страница UTF-8 для вывода русского текста в консоль Windows */")
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

    def _register_subroutine_signature(self, node) -> None:
        idxs = [
            i for i, p in enumerate(node.params)
            if getattr(p.type_node, "is_array", False)
        ]
        cname = self._transliterate(node.name)
        self._array_param_indices[cname] = idxs
        self._array_param_indices[node.name.lower()] = idxs
        if isinstance(node, FuncDecl) and node.return_var_decl:
            ret = self._c_type(node.return_var_decl.type_node, string_const=False)
            self._func_return_ctypes[cname] = ret
            self._func_return_ctypes[node.name.lower()] = ret
        proto = self._function_prototype(node)
        if proto and proto not in self.prototypes:
            self.prototypes.append(proto)

    def visit_Program(self, node):
        # Модули и типы первыми (могут объявить процедуры с таб-параметрами)
        for decl in node.declarations:
            if isinstance(decl, (UseNode, RecordDecl, EnumDecl)):
                self.visit(decl)
            elif isinstance(decl, (VarDecl, ConstDecl)):
                code = self.visit(decl)
                if code:
                    self.global_declarations.append(code)
        # Регистрация сигнатур + прототипы до генерации тел
        for decl in node.declarations:
            if isinstance(decl, (ProcDecl, FuncDecl)):
                self._register_subroutine_signature(decl)
        for decl in node.declarations:
            if isinstance(decl, (ProcDecl, FuncDecl)):
                self.visit(decl)

    def visit_ProcDecl(self, node):
        trans_name = self._transliterate(node.name)
        if is_main_program(node.name):
            self.main_program_name = node.name
            prev_main = self._in_main
            self._in_main = True
            try:
                self.visit_Block(node.block, target_list=self.main_code)
            finally:
                self._in_main = prev_main
        else:
            self.functions_code.append(procedure_alg_comment(node.name))
            self._log(f"генерация процедуры «{node.name}» → {trans_name}()")
            param_str = self._format_params(node)
            self.functions_code.append(f"void {trans_name}({param_str}) {{")
            self.indent_level += 1
            prev_ret = self._current_return_var
            self._current_return_var = None
            try:
                self.visit_Block(node.block, target_list=self.functions_code)
            finally:
                self._current_return_var = prev_ret
            self.indent_level -= 1
            self.functions_code.append("}")

    def visit_FuncDecl(self, node):
        trans_name = self._transliterate(node.name)
        self.functions_code.append(procedure_alg_comment(node.name))
        self._log(f"генерация функции «{node.name}» → {trans_name}()")
        return_type = (
            self._c_type(node.return_var_decl.type_node, string_const=False)
            if node.return_var_decl
            else "double"
        )
        param_str = self._format_params(node)
        self.functions_code.append(f"{return_type} {trans_name}({param_str}) {{")
        self.indent_level += 1
        prev_ret = self._current_return_var
        if node.return_var_decl:
            self._current_return_var = self._transliterate(node.return_var_decl.var_node.name)
            self.functions_code.append(self.indent() + self.visit(node.return_var_decl))
        else:
            self._current_return_var = None
        try:
            self.visit_Block(node.block, target_list=self.functions_code)
            if node.return_var_decl:
                self.functions_code.append(
                    self.indent() + f"return {self._current_return_var};"
                )
        finally:
            self._current_return_var = prev_ret
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
        if self._expr_is_c_string(val):
            c_type = "const char*"
        cname = self._transliterate(node.var_node.name)
        self.var_types[cname] = c_type
        if self._needs_free(val):
            self._warn_possible_heap_leak(node, val, "конст")
        return f"{c_type} {cname} = {val};"

    def _assign_to_left(self, node, left_c: str, right_c: str) -> str:
        if isinstance(node.left, Var):
            cname = self._var_cname(node.left)
            vtype = self.var_types.get(cname, "")
            if "char*" in vtype:
                if right_c.startswith('"'):
                    right_c = f"strdup({right_c})"
                elif not self._needs_free(right_c) and not right_c.startswith("strdup("):
                    right_c = f"strdup({right_c})"
                if self._heap_alloc_count(right_c) > 1:
                    self._warn_possible_heap_leak(node, right_c, "присваивание лит")
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

    # Expressions
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op.value
        is_str = self._expr_is_c_string(left) or self._expr_is_c_string(right)
        if op == '=':
            if is_str:
                return f"(strcmp({left}, {right}) == 0)"
            op = '=='
        elif op == '<>':
            if is_str:
                return f"(strcmp({left}, {right}) != 0)"
            op = '!='
        elif op == '<':
            if is_str:
                return f"(strcmp({left}, {right}) < 0)"
        elif op == '>':
            if is_str:
                return f"(strcmp({left}, {right}) > 0)"
        elif op == '<=':
            if is_str:
                return f"(strcmp({left}, {right}) <= 0)"
        elif op == '>=':
            if is_str:
                return f"(strcmp({left}, {right}) >= 0)"
        elif op == 'и':
            op = '&&'
        elif op == 'или':
            op = '||'
        elif op == '+':
            if is_str:
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
                self._append_stmt(lines, sc)
        self.indent_level -= 1
        if node.else_block:
            lines.append(self.indent() + "} else {")
            self.indent_level += 1
            for stmt in node.else_block:
                sc = self.visit(stmt)
                if sc:
                    self._append_stmt(lines, sc)
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
                self._append_stmt(lines, sc)
        self.indent_level -= 1
        lines.append(self.indent() + "}")
        return "\n".join(lines)

    def visit_ForNode(self, node):
        var = self._var_cname(node.var_node)
        start = self.visit(node.start_val)
        end = self.visit(node.end_val)
        lines = []
        if var not in self.var_types:
            self.var_types[var] = "int"
            lines.append(f"int {var};")
        if node.step_val is not None:
            step = self.visit(node.step_val)
            lines.append(
                f"for ({var} = {start}; "
                f"(({step}) > 0) ? ({var} <= ({end})) : ({var} >= ({end})); "
                f"{var} += ({step})) {{"
            )
        else:
            self._tmp_counter += 1
            st = f"_step_{self._tmp_counter}"
            lines.append(f"int {st} = (({start}) <= ({end})) ? 1 : -1;")
            lines.append(
                f"for ({var} = {start}; "
                f"({st} > 0) ? ({var} <= ({end})) : ({var} >= ({end})); "
                f"{var} += {st}) {{"
            )
        self.indent_level += 1
        for stmt in node.body:
            sc = self.visit(stmt)
            if sc:
                self._append_stmt(lines, sc)
        self.indent_level -= 1
        lines.append(self.indent() + "}")
        return "\n".join(lines)

    def visit_BreakNode(self, node):
        return "break;"

    def visit_ContinueNode(self, node):
        return "continue;"

    def visit_ReturnNode(self, node):
        if node.expr is not None:
            if not self._current_return_var:
                return "/* возврат выражение: не в функции */ return 0;"
            val = self.visit(node.expr)
            rv = self._current_return_var
            vtype = self.var_types.get(rv, "")
            if "char*" in vtype:
                if val.startswith('"'):
                    val = f"strdup({val})"
                elif not self._needs_free(val) and not val.startswith("strdup("):
                    val = f"strdup({val})"
                return f"free({rv}); {rv} = {val};\nreturn {rv};"
            return f"{rv} = {val};\nreturn {rv};"
        if self._in_main:
            return "return 0;"
        if self._current_return_var:
            return f"return {self._current_return_var};"
        return "return;"

    def visit_SubroutineCall(self, node):
        name = resolve_builtin(node.name)
        args = [self.visit(arg) for arg in node.actual_params]
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
            if self._expr_is_c_string(args[0]):
                return f"((double)alg_atol({args[0]}))"
            return f"((double)(long)({args[0]}))"
        if name == 'ввещ' and args:
            if self._expr_is_c_string(args[0]):
                return f"alg_atof({args[0]})"
            return f"((double)({args[0]}))"
        if name == 'встроку' and args:
            if self._expr_is_c_string(args[0]):
                return f"strdup({args[0]} ? {args[0]} : \"\")"
            return f"num_to_str((double)({args[0]}))"
        if name == 'конецфайла' and args:
            return f"(feof({args[0]}) != 0)"
        if name == 'остаток' and len(args) == 2:
            return f"fmod({args[0]}, {args[1]})"
        if name == 'целдел' and len(args) == 2:
            return f"((double)((long)({args[0]}) / (long)({args[1]})))"
        if name == 'степень' and len(args) == 2:
            return f"pow({args[0]}, {args[1]})"
        if name == 'мин' and len(args) == 2:
            return f"fmin({args[0]}, {args[1]})"
        if name == 'макс' and len(args) == 2:
            return f"fmax({args[0]}, {args[1]})"
        if name == 'округление' and args:
            return f"round({args[0]})"
        if name == 'знак' and args:
            return f"alg_sign({args[0]})"
        if name == 'sin' and args:
            return f"sin({args[0]})"
        if name == 'cos' and args:
            return f"cos({args[0]})"
        if name == 'найти' and len(args) == 2:
            return f"alg_find({args[0]}, {args[1]})"
        if name == 'размер' and args:
            raw_arg = args[0]
            if raw_arg in self.array_sizes:
                return f"((double){self.array_sizes[raw_arg]})"
            return f"alg_strlen({args[0]})"
        if name == 'открыть':
            if len(node.actual_params) != 3:
                return "/* открыть: ожидается 3 аргумента */"
            fvar = self._transliterate(node.actual_params[0].name)
            path_c = args[1]
            mode_c = self._file_mode_c(args[2])
            return f"{fvar} = fopen({path_c}, {mode_c})"
        if name == 'закрыть':
            if len(node.actual_params) != 1:
                return "/* закрыть: ожидается 1 аргумент */"
            fvar = self._transliterate(node.actual_params[0].name)
            return f"fclose({fvar}); {fvar} = NULL"
        # Пользовательская подпрограмма: для параметров-массивов передаём ptr, len, offset
        cname = self._transliterate(name)
        arr_idxs = self._array_param_indices.get(cname) or self._array_param_indices.get(name)
        if arr_idxs:
            expanded = []
            for i, arg_c in enumerate(args):
                expanded.append(arg_c)
                if i in arr_idxs:
                    size = self.array_sizes.get(arg_c, 0)
                    off = self.array_offsets.get(arg_c, 1)
                    expanded.append(str(size))
                    expanded.append(str(off))
            args = expanded
        return f"{cname}({', '.join(args)})"

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
        base = self.main_filepath
        try:
            opened = open_module(self._modules, base, node.filepath)
        except CyclicImportError as e:
            raise TranspilerError(str(e), node)
        except ModuleFileNotFoundError as e:
            if self.permissive:
                self.warnings.emit(
                    TranspilerWarning(str(e), node.token)
                )
                return ""
            raise TranspilerError(str(e), node)
        if opened is None:
            return ""
        module_path, module_ast = opened
        self._log(f"подключение модуля «{node.filepath}» из {module_path}")
        try:
            self.visit(module_ast)
            self._log(f"модуль «{node.filepath}» включён")
        finally:
            self._modules.leave(module_path)
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
        self.array_sizes[cname] = size
        self.var_types[cname] = f"{c_type}*"
        return f"{c_type} {cname}[{size}];"

    def visit_ArrayAccess(self, node, is_assign=False):
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
                        f"if (fgets({buf}, (int)sizeof({buf}), stdin)) {{",
                        f"  size_t _ln = strlen({buf});",
                        f"  if (_ln && {buf}[_ln-1]=='\\n') {buf}[--_ln]=0;",
                        f"  if (_ln && {buf}[_ln-1]=='\\r') {buf}[--_ln]=0;",
                        f"  free({cname}); {cname} = strdup({buf});",
                        "}",
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
        self.enum_type_names.add(node.name.lower())
        members = [
            f"{self._transliterate(node.name)}_{self._transliterate(m.value)}"
            for m in node.members
        ]
        enum_def = f"typedef enum {{ {', '.join(members)} }} {self._transliterate(node.name)};"
        self.global_declarations.append(enum_def)
        return ""


