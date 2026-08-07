# interpreter.py

import sys
import os
from errors import SemanticError
from lang_tokens import TokenType
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
from constants import MAIN_PROGRAM_NAME, MAIN_PROGRAM_NAMES, is_main_program, main_program_label
from module_loader import load_alg_file
from alg_warnings import RedefinitionWarning, WarningCollector, ImplicitDeclareWarning, AssignTypeWarning
import alg_builtins
from suggestions import format_suggestion_message
from types_model import canonical_type, type_bilingual_label
from builtin_names import builtin_bilingual_label, resolve_builtin, is_builtin
from visitors import NodeVisitor

# --- Вспомогательные классы для представления данных в памяти ---

class EnumMember:
    """Представление значения перечисления в памяти."""
    def __init__(self, type_name, member_name):
        self.type_name = type_name.lower()
        self.member_name = member_name.lower()
    def __repr__(self): return f'{self.type_name.upper()}.{self.member_name.upper()}'
    def __eq__(self, other):
        return (isinstance(other, EnumMember) and
                self.type_name == other.type_name and
                self.member_name == other.member_name)

class RecordInstance:
    """Представление экземпляра записи в памяти."""
    def __init__(self, record_decl):
        self.record_decl = record_decl
        self.fields = {}
        # Инициализируем поля значениями по умолчанию
        for field_decl in record_decl.fields:
            if isinstance(field_decl, VarDecl):
                self.fields[field_decl.var_node.name] = None
            elif isinstance(field_decl, ArrayDecl):
                 self.fields[field_decl.var_node.name] = None
                 
class ActivationRecord:
    """Запись активации (стековый кадр), хранит локальные переменные для одного вызова."""
    def __init__(self, name, type, members=None, types=None):
        self.name, self.type = name, type
        self.members = members if members is not None else {}
        self.types = types if types is not None else {}
    def __str__(self): return f'{self.type} {self.name}'
    def get(self, key): return self.members.get(key.lower())
    def set(self, key, value): self.members[key.lower()] = value
    def has(self, key): return key.lower() in self.members
    def get_type(self, key): return self.types.get(key.lower())
    def set_type(self, key, type_name): self.types[key.lower()] = type_name.lower()

# --- Основные классы интерпретатора ---

class Interpreter(NodeVisitor):
    def __init__(
        self,
        tree,
        main_filepath,
        verbose=False,
        warnings=None,
        trace=False,
        *,
        debug_protocol=False,
        break_lines=None,
        source_lines=None,
    ):
        self.tree = tree
        self.main_filepath = main_filepath
        self.verbose = verbose and not debug_protocol
        self.trace = trace and not debug_protocol
        self.warnings = warnings if warnings is not None else WarningCollector()
        self.call_stack = []
        self.loaded_modules = set()
        self._module_load_stack: list[str] = []
        self._built_ins = {
            name: (lambda node, f=func: f(self, node))
            for name, func in alg_builtins.BUILTINS.items()
        }
        # SHAYDBG (Eclipse Step Debug)
        self.debug_protocol = bool(debug_protocol)
        self.breakpoints = {int(n) for n in (break_lines or []) if int(n) > 0}
        # (norm_path or "", line) — path "" matches any / launch file
        self._bp_items = [("", int(n)) for n in (break_lines or []) if int(n) > 0]
        self._program_path = os.path.abspath(main_filepath) if main_filepath else ""
        self._source_lines = list(source_lines or [])
        self._source_cache = {}
        if self._program_path:
            self._source_cache[self._norm_path(self._program_path)] = list(self._source_lines)
        self._protocol_auto = True
        self._pause_reason = "breakpoint"
        self._input_banner_shown = False
        if self.tree is not None and self._program_path:
            self._stamp_source_path(self.tree, self._program_path)

    @staticmethod
    def _norm_path(path: str) -> str:
        if not path:
            return ""
        try:
            return os.path.normcase(os.path.abspath(path))
        except OSError:
            return str(path).replace("\\", "/").lower()

    def _stamp_source_path(self, node, path: str, _seen=None) -> None:
        if node is None:
            return
        if isinstance(node, (list, tuple)):
            for n in node:
                self._stamp_source_path(n, path, _seen)
            return
        if not hasattr(node, "__dict__"):
            return
        # Tokens / builtins — не обходим (циклы / шум)
        cls = type(node).__name__
        if cls in ("Token", "dict", "str", "int", "float", "bool"):
            return
        if _seen is None:
            _seen = set()
        nid = id(node)
        if nid in _seen:
            return
        _seen.add(nid)
        if not getattr(node, "source_path", None):
            try:
                node.source_path = path
            except Exception:
                pass
        for key, v in list(vars(node).items()):
            if key in ("token", "name_token", "filepath_token", "member_token"):
                continue
            if isinstance(v, (list, tuple)):
                for item in v:
                    if hasattr(item, "__dict__"):
                        self._stamp_source_path(item, path, _seen)
            elif hasattr(v, "__dict__"):
                self._stamp_source_path(v, path, _seen)

    def _stmt_path(self, stmt) -> str:
        p = getattr(stmt, "source_path", None) or self._program_path
        return os.path.abspath(p) if p else ""

    def _at_breakpoint(self, stmt) -> bool:
        line = self._stmt_line_num(stmt)
        if line <= 0:
            return False
        sp = self._norm_path(self._stmt_path(stmt))
        for bp_path, bp_line in self._bp_items:
            if bp_line != line:
                continue
            if not bp_path or bp_path == sp:
                return True
        # fallback: plain --break lines (launch file only)
        if line in self.breakpoints and (
            not sp or sp == self._norm_path(self._program_path)
        ):
            return True
        return False

    def generic_visit(self, node, **kwargs):
        raise SemanticError(
            f"Интерпретатор не поддерживает узел {type(node).__name__}",
            getattr(node, "token", None),
            self.call_stack,
        )

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[интерпретатор] {message}", file=sys.stderr)

    def _trace_statement(self, stmt) -> None:
        if not self.trace or self.debug_protocol:
            return
        line = self._stmt_line(stmt)
        print(f"[трассировка] {type(stmt).__name__} (строка {line})", file=sys.stderr)

    def _stmt_line(self, stmt) -> str:
        if hasattr(stmt, "token") and stmt.token is not None:
            return str(stmt.token.line)
        if hasattr(stmt, "var_node") and hasattr(stmt.var_node, "token"):
            return str(stmt.var_node.token.line)
        if hasattr(stmt, "left") and hasattr(stmt.left, "token"):
            return str(stmt.left.token.line)
        return "?"

    def _stmt_line_num(self, stmt) -> int:
        line = self._stmt_line(stmt)
        try:
            return int(line)
        except (TypeError, ValueError):
            return 0

    def _before_stmt(self, stmt) -> None:
        self._maybe_protocol_pause(stmt)
        self._trace_statement(stmt)

    def _ar_plain(self, ar: ActivationRecord) -> dict:
        out = {}
        for k, v in ar.members.items():
            if k.startswith("_"):
                continue
            if isinstance(v, tuple):
                if v[0] in ("var", "const"):
                    out[k] = v[1]
                # skip sub/type_name
            else:
                out[k] = v
        return out

    def _snapshot_vars(self):
        gmap, lmap = {}, {}
        if not self.call_stack:
            return gmap, lmap
        gmap = self._ar_plain(self.call_stack[0])
        if len(self.call_stack) > 1:
            lmap = self._ar_plain(self.call_stack[-1])
        return gmap, lmap

    def _protocol_source_line(self, line: int, path: str = "") -> str:
        key = self._norm_path(path) if path else self._norm_path(self._program_path)
        lines = self._source_cache.get(key) or self._source_lines
        if line and 1 <= int(line) <= len(lines):
            return lines[int(line) - 1].rstrip("\n")
        return ""

    def _protocol_stack(self, line: int, source: str, path: str):
        frames = []
        for ar in self.call_stack[1:]:
            frames.append({
                "name": ar.name,
                "line": line,
                "source": source,
                "path": path,
            })
        frames.append({
            "name": self.call_stack[-1].name if self.call_stack else "main",
            "line": line,
            "source": source,
            "path": path,
        })
        return frames

    def debug_evaluate(self, expression: str):
        try:
            name = (expression or "").strip()
            if not name:
                return None
            if name.startswith('"') and name.endswith('"') and len(name) >= 2:
                return name[1:-1]
            if name in ("да", "нет", "истина", "ложь"):
                return name in ("да", "истина")
            try:
                if "." in name:
                    return float(name)
                return int(name)
            except ValueError:
                pass
            key = name.lower()
            for ar in reversed(self.call_stack):
                if ar.has(key):
                    val = ar.get(key)
                    if isinstance(val, tuple) and val[0] in ("var", "const"):
                        return val[1]
                    return val
            return f"Ошибка оценки: переменная '{name}' не определена"
        except Exception as e:
            return f"Ошибка оценки: {e}"

    def debug_set_var(self, name: str, value):
        key = name.lower()
        for ar in reversed(self.call_stack):
            if ar.has(key):
                cur = ar.get(key)
                if isinstance(cur, tuple) and cur[0] == "const":
                    raise SemanticError(f"Нельзя изменять константу '{name}'", None, self.call_stack)
                ar.set(key, ("var", value))
                return value
        if self.call_stack:
            self.call_stack[-1].set(key, ("var", value))
        return value

    def _maybe_protocol_pause(self, stmt) -> None:
        if not self.debug_protocol:
            return
        line = self._stmt_line_num(stmt)
        at_bp = self._at_breakpoint(stmt)
        if (self._protocol_auto and at_bp) or (not self._protocol_auto):
            self._protocol_pause(stmt, at_break=at_bp and self._protocol_auto)

    def _protocol_pause(self, stmt, *, at_break: bool) -> None:
        from shay_debug_protocol import (
            build_eval,
            build_set,
            build_stopped,
            cmd_name,
            emit_event,
            extract_break_lines,
            parse_command,
        )

        reason = "breakpoint" if at_break else self._pause_reason
        self._pause_reason = "step"
        line = self._stmt_line_num(stmt)
        stmt_path = self._stmt_path(stmt)
        source = self._protocol_source_line(line, stmt_path) or type(stmt).__name__
        gmap, lmap = self._snapshot_vars()
        emit_event(
            build_stopped(
                reason=reason,
                line=line or None,
                source=source,
                path=stmt_path,
                globals_map=gmap,
                locals_map=lmap,
                stack=self._protocol_stack(line, source, stmt_path),
            )
        )
        print(
            "[ШАЯ][отладка] Пауза. Step/Continue — из IDE. "
            "Оператор «ввод» — обычный текст в Console (не JSON).",
            file=sys.stderr,
            flush=True,
        )
        while True:
            raw = sys.stdin.readline()
            if raw == "":
                raise SystemExit(0)
            obj = parse_command(raw)
            if obj is None:
                continue
            cmd = cmd_name(obj)
            if cmd in ("step", "step_over", "s", "n", "next"):
                self._protocol_auto = False
                self._pause_reason = "step"
                return
            if cmd in ("step_into", "into"):
                self._protocol_auto = False
                self._pause_reason = "step_into"
                return
            if cmd in ("step_out", "out"):
                self._protocol_auto = False
                self._pause_reason = "step_out"
                return
            if cmd in ("continue", "c", "cont"):
                self._protocol_auto = True
                return
            if cmd in ("quit", "q", "exit"):
                raise SystemExit(0)
            if cmd in ("breakpoints", "set_breakpoints", "bps"):
                items = obj.get("items")
                self.breakpoints = extract_break_lines(items)
                self._bp_items = []
                if isinstance(items, list):
                    for it in items:
                        if not isinstance(it, dict) or it.get("enabled") is False:
                            continue
                        try:
                            bline = int(it.get("line"))
                        except (TypeError, ValueError):
                            continue
                        if bline <= 0:
                            continue
                        bpath = self._norm_path(str(it.get("path") or ""))
                        self._bp_items.append((bpath, bline))
                continue
            if cmd in ("eval", "watch", "evaluate"):
                expr = str(obj.get("expr") or obj.get("expression") or "")
                try:
                    value = self.debug_evaluate(expr)
                    if isinstance(value, str) and value.startswith("Ошибка оценки:"):
                        emit_event(build_eval(expr=expr, value=None, ok=False, error=value))
                    else:
                        emit_event(build_eval(expr=expr, value=value, ok=True))
                except Exception as exc:
                    emit_event(build_eval(expr=expr, value=None, ok=False, error=str(exc)))
                continue
            if cmd in ("set", "assign"):
                name = str(obj.get("name") or "").strip()
                value_expr = str(obj.get("value") or "")
                try:
                    value = self.debug_evaluate(value_expr)
                    if isinstance(value, str) and value.startswith("Ошибка оценки:"):
                        emit_event(build_set(name=name, value=None, ok=False, error=value))
                    else:
                        self.debug_set_var(name, value)
                        emit_event(build_set(name=name, value=value, ok=True))
                except Exception as exc:
                    emit_event(build_set(name=name, value=None, ok=False, error=str(exc)))
                continue

    def _read_user_input(self, prompt: str = "") -> str:
        if self.debug_protocol and not self._input_banner_shown:
            print(
                "[ШАЯ][ввод] Ожидается значение (обычный текст + Enter). "
                "Не вводите JSON-команды отладки — ими управляет IDE на паузе.",
                file=sys.stderr,
                flush=True,
            )
            self._input_banner_shown = True
        while True:
            try:
                raw = input(prompt)
            except EOFError:
                return ""
            if self.debug_protocol:
                try:
                    from shay_debug_protocol import is_debug_stdin_command
                    if is_debug_stdin_command(raw):
                        continue
                except Exception:
                    pass
            return raw

    def _visible_names(self) -> list[str]:
        names = set()
        for ar in self.call_stack:
            names.update(ar.members.keys())
            if ar.name == 'global':
                for key, val in ar.members.items():
                    if isinstance(val, tuple) and val[0] == 'sub':
                        names.add(key)
        return sorted(names)

    def _get_variable(self, name, token):
        name = name.lower()
        # Ищем в локальной области видимости (сверху стека)
        if self.call_stack[-1].has(name):
            return self.call_stack[-1].get(name)
        # Ищем в глобальной области видимости (в самом низу стека)
        if self.call_stack[0].has(name):
            return self.call_stack[0].get(name)
        
        # Проверяем, не является ли имя названием типа
        type_storage = self.call_stack[0].get('_types_')
        if type_storage.get(name):
            return ('type_name', type_storage.get(name))

        hint = format_suggestion_message(name, self._visible_names())
        err = SemanticError(f"Переменная, константа или тип '{name}' не определена", token, self.call_stack)
        if hint:
            err.hint = hint
        raise err

    def _get_var_type(self, var_name: str) -> str | None:
        var_name = var_name.lower()
        for ar in reversed(self.call_stack):
            t = ar.get_type(var_name)
            if t:
                return t
        return None

    def _is_to_int_cast(self, expr) -> bool:
        return isinstance(expr, SubroutineCall) and resolve_builtin(expr.name) == "вцел"

    def _check_assign_types(self, var_name: str, value, right_expr, token) -> None:
        declared = self._get_var_type(var_name)
        if not declared:
            return
        declared = canonical_type(declared)
        if declared == 'лит':
            return
        if isinstance(value, str):
            if declared in ('цел', 'вещ', 'лог'):
                raise SemanticError(
                    f"Нельзя присвоить строку переменной типа «{type_bilingual_label(declared)}» "
                    f"(«{var_name}»)",
                    token,
                    self.call_stack,
                )
            return
        if declared == 'цел' and isinstance(value, float) and not self._is_to_int_cast(right_expr):
            self.warnings.emit(
                AssignTypeWarning(
                    f"присваивание вещественного значения {value!r} в «{var_name}» "
                    f"({type_bilingual_label('цел')}); "
                    f"рекомендуется {builtin_bilingual_label('вцел')}(...)",
                    token,
                )
            )

    def _set_variable(self, name, value, token):
        name = name.lower()
        ar = self.call_stack[-1]
        
        # Переменные можно менять только в локальной области видимости
        if not ar.has(name):
            raise SemanticError(f"Попытка присвоить значение необъявленной локальной переменной '{name}'", token, self.call_stack)
        
        current_val_tuple = ar.get(name)
        if isinstance(current_val_tuple, tuple) and current_val_tuple[0] == 'const':
             raise SemanticError(f"Нельзя изменять значение константы '{name}'", token, self.call_stack)

        ar.set(name, ('var', value))

    def run(self):
        global_scope = ActivationRecord('global', 'program')
        global_scope.members['_types_'] = {} # Хранилище для объявлений записей/перечислений
        self.call_stack.append(global_scope)
        exit_code = 0
        try:
            self.visit(self.tree)
        except SystemExit as e:
            exit_code = int(e.code) if isinstance(e.code, int) else (0 if e.code is None else 1)
            raise
        except RecursionError:
            exit_code = 1
            depth = len(self.call_stack)
            proc = self.call_stack[-1].name if self.call_stack else "?"
            raise SemanticError(
                f"Превышена глубина рекурсии Python при выполнении «{proc}» "
                f"(кадров в стеке: {depth}). Упростите рекурсию или увеличьте лимит sys.setrecursionlimit.",
                call_stack=self.call_stack,
            )
        except Exception:
            exit_code = 1
            raise
        finally:
            if self.call_stack:
                self.call_stack.pop()
            if self.debug_protocol:
                try:
                    from shay_debug_protocol import build_terminated, emit_event
                    emit_event(build_terminated(exit_code))
                except Exception:
                    pass

    def _process_declarations(self, declarations, base_path):
        scope = self.call_stack[-1]
        type_storage = self.call_stack[0].get('_types_')

        for declaration in declarations:
            if isinstance(declaration, UseNode):
                self.visit(declaration, base_path=base_path)
            elif isinstance(declaration, (ProcDecl, FuncDecl)):
                if scope.has(declaration.name):
                    self.warnings.emit(
                        RedefinitionWarning("процедуры/функции", declaration.name, declaration.token)
                    )
                scope.set(declaration.name, ('sub', declaration))
            elif isinstance(declaration, RecordDecl):
                 if type_storage.get(declaration.name):
                     self.warnings.emit(
                         RedefinitionWarning("типа записи", declaration.name, declaration.token)
                     )
                 type_storage[declaration.name] = declaration
            elif isinstance(declaration, EnumDecl):
                 if type_storage.get(declaration.name):
                     self.warnings.emit(
                         RedefinitionWarning("типа перечисления", declaration.name, declaration.token)
                     )
                 type_storage[declaration.name] = declaration
            elif isinstance(declaration, ConstDecl):
                 if scope.has(declaration.var_node.name): raise SemanticError(f"Переопределение константы '{declaration.var_node.name}'", declaration.var_node.token)
                 value_tuple = self.visit(declaration.expr)
                 if value_tuple[0] == 'void': raise SemanticError("Процедура не может быть присвоена константе", declaration.var_node.token, self.call_stack)
                 value = value_tuple[1] if isinstance(value_tuple, tuple) else value_tuple
                 scope.set(declaration.var_node.name, ('const', value))
            elif isinstance(declaration, VarDecl):
                 self.visit(declaration, scope=scope)
            elif isinstance(declaration, ArrayDecl):
                 self.visit(declaration, scope=scope)

    def visit_Program(self, node):
        self._process_declarations(node.declarations, self.main_filepath)
        
        # Находим и вызываем главную программу
        global_scope = self.call_stack[0]
        main_decl_tuple = None
        for main_name in MAIN_PROGRAM_NAMES:
            if global_scope.has(main_name):
                main_decl_tuple = global_scope.get(main_name)
                break
        if not main_decl_tuple or not isinstance(main_decl_tuple[1], ProcDecl):
            raise SemanticError(f"Не найдена главная программа «алг {main_program_label()}»")
        main_decl = main_decl_tuple[1]
        
        # Запускаем выполнение с вызова главной процедуры
        self.visit(SubroutineCall(main_decl.token, []))

    def visit_Block(self, node, ar=None):
        target_scope = ar if ar else self.call_stack[-1]
        for declaration in node.declarations:
            self.visit(declaration, scope=target_scope)
        for statement in node.statements:
            self._before_stmt(statement)
            self.visit(statement)

    def visit_ConstDecl(self, node, scope=None):
        scope = scope if scope else self.call_stack[-1]
        if scope.has(node.var_node.name):
            raise SemanticError(f"Переопределение константы '{node.var_node.name}'", node.var_node.token, self.call_stack)
        value_tuple = self.visit(node.expr)
        if value_tuple[0] == 'void':
             raise SemanticError("Процедура не может быть присвоена константе", node.var_node.token, self.call_stack)
        value = value_tuple[1] if isinstance(value_tuple, tuple) else value_tuple
        scope.set(node.var_node.name, ('const', value))
    def visit_RecordDecl(self, node, scope): pass
    def visit_EnumDecl(self, node, scope): pass
    
    def visit_UseNode(self, node, base_path):
        module_dir = os.path.dirname(os.path.abspath(base_path))
        module_path = os.path.normpath(os.path.join(module_dir, node.filepath))
        if module_path in self._module_load_stack:
            chain = self._module_load_stack + [module_path]
            display = " → ".join(os.path.basename(p) for p in chain)
            raise SemanticError(
                f"Циклический импорт модулей: {display}",
                node.token,
                self.call_stack,
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
                self.call_stack,
            )
        self._stamp_source_path(module_ast, module_path)
        try:
            with open(module_path, "r", encoding="utf-8") as mf:
                self._source_cache[self._norm_path(module_path)] = mf.read().splitlines()
        except OSError:
            pass
        try:
            decl_names = []
            for d in module_ast.declarations:
                if hasattr(d, "name"):
                    decl_names.append(d.name)
                elif isinstance(d, ConstDecl):
                    decl_names.append(d.var_node.name)
            if decl_names:
                self._log(f"модуль «{node.filepath}»: объявления — {', '.join(decl_names)}")
            self._process_declarations(module_ast.declarations, module_path)
        finally:
            if self._module_load_stack and self._module_load_stack[-1] == module_path:
                self._module_load_stack.pop()
        
    def visit_VarDecl(self, node, scope=None):
        var_name = node.var_node.name
        type_node = node.type_node
        scope = scope if scope else self.call_stack[-1]
        if scope.has(var_name): raise SemanticError(f"Повторное объявление переменной '{var_name}'", node.var_node.token, self.call_stack)

        if isinstance(type_node, Type):
            tname = canonical_type(type_node.value)
            scope.set_type(var_name, tname)
            if tname == 'словарь': scope.set(var_name, ('var', {}))
            else: scope.set(var_name, ('var', None))
        elif isinstance(type_node, CustomType):
            type_name = type_node.name
            scope.set_type(var_name, type_name)
            type_storage = self.call_stack[0].get('_types_')
            type_decl = type_storage.get(type_name)
            if not type_decl: raise SemanticError(f"Неизвестный тип '{type_name}'", type_node.token, self.call_stack)
            if isinstance(type_decl, RecordDecl): scope.set(var_name, ('var', RecordInstance(type_decl)))
            elif isinstance(type_decl, EnumDecl): scope.set(var_name, ('var', None))

    def visit_ArrayDecl(self, node, scope=None):
        var_name = node.var_node.name
        scope = scope if scope else self.call_stack[-1]
        if scope.has(var_name): raise SemanticError(f"Повторное объявление массива '{var_name}'", node.var_node.token, self.call_stack)
        start_idx = self.visit(node.start_idx)[1]
        end_idx = self.visit(node.end_idx)[1]
        start_idx, end_idx = int(start_idx), int(end_idx)
        if start_idx > end_idx: raise SemanticError(f"Начальный индекс массива {start_idx} больше конечного {end_idx}", node.var_node.token, self.call_stack)
        size = end_idx - start_idx + 1
        array_data = {'_type': 'array', 'offset': start_idx, 'values': [None] * size}
        elem_type = node.type_node.value if isinstance(node.type_node, Type) else '?'
        scope.set_type(var_name, f'таб {elem_type}')
        scope.set(var_name, ('var', array_data))

    def visit_Assign(self, node):
        value_tuple = self.visit(node.right)
        if value_tuple[0] == 'void': raise SemanticError("Процедура не возвращает значение", node.right.token if hasattr(node.right, 'token') else node.right.owner_expr.token, self.call_stack)
        value_to_assign = value_tuple[1]
        
        left_side_tuple = self.visit(node.left, is_assign=True)
        var_type = left_side_tuple[0]

        if var_type == 'var':
            var_name = left_side_tuple[1]
            self._check_assign_types(var_name, value_to_assign, node.right, node.left.token)
            self._set_variable(var_name, value_to_assign, node.left.token)
        elif var_type == 'array_val':
            collection, real_idx = left_side_tuple[2], left_side_tuple[3]
            collection['values'][real_idx] = value_to_assign
        elif var_type == 'dict_val':
            collection, key = left_side_tuple[2], left_side_tuple[3]
            collection[key] = value_to_assign
        elif var_type == 'field':
            record_instance, field_name = left_side_tuple[2], left_side_tuple[3]
            record_instance.fields[field_name] = value_to_assign
        else: raise SemanticError("Нельзя присвоить значение этому выражению", node.left.token, self.call_stack)
        if self.trace:
            self._trace_assign(node.left, value_to_assign)

    def _trace_assign(self, left, value) -> None:
        target = self._assign_target_repr(left)
        print(f"[трассировка]   {target} := {value!r}", file=sys.stderr)

    def _assign_target_repr(self, left) -> str:
        if isinstance(left, Var):
            return left.name
        if isinstance(left, ArrayAccess):
            owner = getattr(left.owner_expr, "name", "?")
            return f"{owner}[...]"
        if isinstance(left, MemberAccess):
            owner = getattr(left.owner_expr, "name", "?")
            return f"{owner}.{left.member_token.value}"
        return type(left).__name__

    def visit_Var(self, node, is_assign=False):
        val_tuple = self._get_variable(node.name, node.token)
        if is_assign:
            return ('var', node.name) # Возвращаем имя переменной для присваивания
        return val_tuple

    def visit_SubroutineCall(self, node):
        sub_name = resolve_builtin(node.name)
        if is_builtin(sub_name):
            val = self._built_ins[sub_name](node)
            if val is None: return ('void', None)
            return ('builtin_val', val)
            
        sub_decl_tuple = self.call_stack[0].get(sub_name)
        if not sub_decl_tuple or sub_decl_tuple[0] != 'sub': raise SemanticError(f"Процедура или функция '{sub_name}' не определена", node.token, self.call_stack)
        sub_decl = sub_decl_tuple[1]
        ar = ActivationRecord(sub_name, 'procedure' if isinstance(sub_decl, ProcDecl) else 'function')
        
        # Проверка аргументов на void (нельзя передавать результат процедуры как аргумент)
        actual_params = []
        for p in node.actual_params:
            val_tuple = self.visit(p)
            if val_tuple[0] == 'void': raise SemanticError("Процедура не возвращает значение и не может быть аргументом", node.token, self.call_stack)
            actual_params.append(val_tuple[1])

        if len(actual_params) != len(sub_decl.params):
            param_names = ", ".join(p.var_node.name for p in sub_decl.params)
            raise SemanticError(
                f"Неверное количество аргументов для «{sub_name}»: ожидается {len(sub_decl.params)} "
                f"({param_names}), передано {len(actual_params)}",
                node.token,
                self.call_stack,
            )

        args_repr = ", ".join(repr(v) for v in actual_params)
        self._log(f"→ вызов «{sub_name}»({args_repr})")

        # Сначала инициализируем аргументы
        for formal_param, actual_param_val in zip(sub_decl.params, actual_params):
            ar.set(formal_param.var_node.name, ('var', actual_param_val))
            if isinstance(formal_param.type_node, Type):
                ar.set_type(formal_param.var_node.name, formal_param.type_node.value)
            elif isinstance(formal_param.type_node, CustomType):
                ar.set_type(formal_param.var_node.name, formal_param.type_node.name)
            
        # Затем обрабатываем декларации
        for declaration in sub_decl.block.declarations:
            self.visit(declaration, scope=ar)

        if isinstance(sub_decl, FuncDecl): ar.set(sub_decl.return_var_decl.var_node.name, ('var', None))
        
        self.call_stack.append(ar)
        for statement in sub_decl.block.statements:
            self._before_stmt(statement)
            self.visit(statement)
        
        return_val = None
        tag = 'sub_val'
        if isinstance(sub_decl, FuncDecl): 
            return_val = ar.get(sub_decl.return_var_decl.var_node.name)[1]
            self._log(f"← возврат из «{sub_name}» = {return_val!r}")
        else:
            tag = 'void'
            self._log(f"← возврат из «{sub_name}» (процедура)")
            
        self.call_stack.pop()
        return (tag, return_val)

    def visit_MemberAccess(self, node, is_assign=False):
        owner_tuple = self.visit(node.owner_expr)
        if owner_tuple[0] == 'type_name':
            type_name, member_name = owner_tuple[1].name, node.member_token.value
            type_storage = self.call_stack[0].get('_types_')
            enum_decl = type_storage.get(type_name)
            if enum_decl and isinstance(enum_decl, EnumDecl):
                if member_name.lower() in [m.value.lower() for m in enum_decl.members]:
                    return ('enum_literal', EnumMember(type_name, member_name))
        
        owner_val = owner_tuple[1]
        if isinstance(owner_val, RecordInstance):
            field_name = node.member_token.value.lower()
            if field_name not in owner_val.fields: raise SemanticError(f"У записи нет поля '{field_name}'", node.member_token, self.call_stack)
            if is_assign: return ('field', owner_val.fields.get(field_name), owner_val, field_name)
            return ('var', owner_val.fields.get(field_name))
        
        raise SemanticError(f"Невозможно получить доступ к члену", node.owner_expr.token, self.call_stack)
    
    def visit_ArrayAccess(self, node, is_assign=False):
        coll_tuple = self.visit(node.owner_expr)
        if coll_tuple[0] == 'void': raise SemanticError("Выражение не имеет значения (процедура?)", node.owner_expr.token, self.call_stack)
        collection = coll_tuple[1]
        
        idx_tuple = self.visit(node.index_expr)
        if idx_tuple[0] == 'void': raise SemanticError("Индекс не имеет значения", node.index_expr.token, self.call_stack)
        index_or_key = idx_tuple[1]
        
        if isinstance(collection, dict) and collection.get('_type') == 'array':
            if not isinstance(index_or_key, (int, float)): raise SemanticError("Индекс массива должен быть числом", node.index_expr.token, self.call_stack)
            index, offset = int(index_or_key), collection['offset']
            end_index = offset + len(collection['values']) - 1
            array_name = node.owner_expr.name if hasattr(node.owner_expr, "name") else "?"
            if not (offset <= index <= end_index):
                raise SemanticError(
                    f"Индекс {index} вне границ массива «{array_name}» [{offset}..{end_index}]",
                    node.index_expr.token,
                    self.call_stack,
                )
            real_idx = index - offset
            if is_assign: return ('array_val', collection['values'][real_idx], collection, real_idx)
            return ('var', collection['values'][real_idx])
        elif isinstance(collection, dict):
            if not isinstance(index_or_key, str): raise SemanticError("Ключ для словаря должен быть строкой", node.index_expr.token, self.call_stack)
            value = collection.get(index_or_key)
            if value is None and not is_assign: raise SemanticError(f"В словаре нет ключа '{index_or_key}'", node.index_expr.token, self.call_stack)
            if is_assign: return ('dict_val', value, collection, index_or_key)
            return ('var', value)
        raise SemanticError(f"Переменная не является массивом или словарем", node.owner_expr.token, self.call_stack)

    def visit_BinOp(self, node):
        left_tuple = self.visit(node.left)
        if left_tuple[0] == 'void': raise SemanticError("Левый операнд не имеет значения", node.left.token, self.call_stack)
        left = left_tuple[1]
        
        right_tuple = self.visit(node.right)
        if right_tuple[0] == 'void': raise SemanticError("Правый операнд не имеет значения", node.right.token, self.call_stack)
        right = right_tuple[1]
        
        op_type, op_val = node.op.type, node.op.value
        if op_type == TokenType.И: return ('var', bool(left) and bool(right))
        if op_type == TokenType.ИЛИ: return ('var', bool(left) or bool(right))
        if op_val == '>': return ('var', left > right)
        if op_val == '<': return ('var', left < right)
        if op_val == '>=' or op_type == TokenType.GTE: return ('var', left >= right)
        if op_val == '<=' or op_type == TokenType.LTE: return ('var', left <= right)
        if op_val == '<>' or op_type == TokenType.NEQ: return ('var', left != right)
        if op_type == TokenType.EQ: return ('var', left == right)
        if op_val == '+':
            if isinstance(left, (int, float)) and isinstance(right, (int, float)): return ('var', left + right)
            else: return ('var', str(left) + str(right))
        if op_val == '-': return ('var', float(left) - float(right))
        if op_val == '*': return ('var', float(left) * float(right))
        if op_val == '/':
            if float(right) == 0: raise SemanticError("Деление на ноль", node.right.token, self.call_stack)
            return ('var', float(left) / float(right))

    def visit_UnaryOp(self, node):
        value_tuple = self.visit(node.expr)
        if value_tuple[0] == 'void': raise SemanticError("Операнд не имеет значения", node.expr.token if hasattr(node.expr, 'token') else node.op, self.call_stack)
        value = value_tuple[1]
        if node.op.type == TokenType.НЕ: return ('var', not bool(value))
        if node.op.value == '-': return ('var', -float(value))
        if node.op.value == '+': return ('var', +float(value))

    def visit_Num(self, node): return ('var', node.value)
    def visit_String(self, node): return ('var', node.value)
    def visit_Bool(self, node): return ('var', node.value)
    def visit_Type(self, node): pass
    def visit_CustomType(self, node): pass
    
    def visit_IfNode(self, node):
        cond_val = self.visit(node.condition)[1]
        if bool(cond_val):
            for statement in node.then_block:
                self._before_stmt(statement)
                self.visit(statement)
        elif node.else_block:
            for statement in node.else_block:
                self._before_stmt(statement)
                self.visit(statement)

    def visit_ForNode(self, node):
        start_val = int(self.visit(node.start_val)[1])
        end_val = int(self.visit(node.end_val)[1])
        var_name = node.var_node.name
        scope = self.call_stack[-1]
        if not scope.has(var_name) and not self.call_stack[0].has(var_name):
            scope.set(var_name, ('var', None))
            scope.set_type(var_name, 'цел')
            self.warnings.emit(
                ImplicitDeclareWarning(
                    f"неявное объявление переменной цикла «{var_name}» как цел",
                    node.var_node.token,
                )
            )
            self._log(f"нц для: неявное объявление цел «{var_name}»")
        for i in range(start_val, end_val + 1):
            self._set_variable(var_name, float(i), node.var_node.token)
            for statement in node.body:
                self._before_stmt(statement)
                self.visit(statement)

    def visit_WhileNode(self, node):
        while bool(self.visit(node.condition)[1]):
            for statement in node.body:
                self._before_stmt(statement)
                self.visit(statement)

    def _apply_format(self, value, format_spec):
        if not format_spec: return str(value)
        width = int(self.visit(format_spec.width)[1])
        precision = None
        if format_spec.precision: precision = int(self.visit(format_spec.precision)[1])
        if isinstance(value, float):
            if precision is not None: return f"{value:{width}.{precision}f}"
            else: return f"{value:{width}}"
        else: return f"{str(value):>{width}}"

    def visit_Print(self, node):
        output_parts = []
        for expr, fmt in node.items:
            val_tuple = self.visit(expr)
            if val_tuple[0] == 'void': raise SemanticError("Выражение в 'вывод' не имеет значения", expr.token if hasattr(expr, 'token') else node.file_node.token, self.call_stack)
            output_parts.append(self._apply_format(val_tuple[1], fmt))
        output_str = ''.join(output_parts)
        if node.file_node:
            file_handle = self._get_variable(node.file_node.name, node.file_node.token)[1]
            if not hasattr(file_handle, 'write'): raise SemanticError(f"Переменная '{node.file_node.name}' не открыта для записи", node.file_node.token, self.call_stack)
            try: file_handle.write(output_str + '\n')
            except IOError as e: raise SemanticError(f"Ошибка записи в файл: {e}", node.file_node.token, self.call_stack)
        else:
            print(output_str)

    def visit_Input(self, node):
        for var_node in node.var_nodes:
            value = None
            if node.file_node:
                file_handle = self._get_variable(node.file_node.name, node.file_node.token)[1]
                if not hasattr(file_handle, 'read'): raise SemanticError(f"Переменная '{node.file_node.name}' не открыта для чтения", node.file_node.token, self.call_stack)
                line = file_handle.readline()
                # Семантика при EOF: в переменную записывается 0.0 (фиксированный контракт ввода из файла)
                if not line:
                    value = 0.0
                    self._log(
                        f"ввод из файла: EOF, в «{var_node.name}» записано 0.0 (контракт языка)"
                    )
                else:
                    try: value = float(line.strip())
                    except ValueError: value = line.strip()
            else:
                line = self._read_user_input()
                try: value = float(line.strip())
                except ValueError: value = line.strip()
            self._set_variable(var_node.name, value, var_node.token)
    