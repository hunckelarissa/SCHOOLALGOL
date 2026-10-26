# alg_builtins.py — встроенные функции и процедуры языка .alg (интерпретатор)
import math
import os
import random
from errors import SemanticError
from ast_nodes import Var
from builtin_names import resolve_file_mode
from i18n import sem

def format_value(value) -> str:
    """Строковое представление значения .alg: логические «да»/«нет», целые без «.0»."""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e16:
        return str(int(value))
    return str(value)

def _check_arity(interp, node, expected_count):
    if len(node.actual_params) != expected_count:
        raise SemanticError(
            sem("sem_arity", name=node.name, expected=expected_count, got=len(node.actual_params)),
            node.token, interp.call_stack,
        )

def built_in_open(interp, node):
    _check_arity(interp, node, 3)
    file_var_node = node.actual_params[0]
    if not isinstance(file_var_node, Var):
        raise SemanticError(sem("sem_file_var", name="открыть"), node.token, interp.call_stack)
    file_var_name = file_var_node.name
    path = interp.visit(node.actual_params[1])[1]
    mode_str = interp.visit(node.actual_params[2])[1]
    py_mode = resolve_file_mode(mode_str)
    if py_mode is None:
        raise SemanticError(sem("sem_file_mode", mode=mode_str), node.actual_params[2].token, interp.call_stack)
    abs_path = os.path.abspath(path)
    interp._log(
        f"открыть: переменная={file_var_name!r}, путь={path!r}, "
        f"абсолютный={abs_path!r}, режим={mode_str!r} → Python '{py_mode}'"
    )
    try:
        file_handle = open(path, py_mode, encoding='utf-8')
        interp._set_variable(file_var_name, file_handle, file_var_node.token)
        interp._log("открыть: успешно, файл доступен для операций")
    except OSError as e:
        errno_hint = f" (errno {e.errno})" if getattr(e, "errno", None) is not None else ""
        raise SemanticError(
            sem("sem_file_open", path=path, abs=abs_path, mode=mode_str, errno_hint=errno_hint, error=e),
            node.actual_params[1].token,
            interp.call_stack,
        )

def built_in_close(interp, node):
    _check_arity(interp, node, 1)
    first_arg = node.actual_params[0]
    if not isinstance(first_arg, Var):
        raise SemanticError(sem("sem_file_var", name="закрыть"), node.token, interp.call_stack)
    var_name = first_arg.name
    file_handle = interp._get_variable(var_name, first_arg.token)[1]
    interp._log(f"закрыть: переменная={var_name!r}")
    if file_handle is not None and hasattr(file_handle, 'close'):
        file_handle.close()
        interp._log("закрыть: дескриптор закрыт")
    else:
        interp._log("закрыть: файл не был открыт или уже закрыт")
    interp._set_variable(var_name, None, first_arg.token)

def built_in_eof(interp, node):
    _check_arity(interp, node, 1)
    file_handle = interp.visit(node.actual_params[0])[1]
    if file_handle is None or not hasattr(file_handle, 'read'):
        raise SemanticError(sem("sem_eof_file"), node.token, interp.call_stack)
    try:
        pos = file_handle.tell()
        chunk = file_handle.read(1)
        file_handle.seek(pos)
        return not chunk
    except (OSError, IOError):
        return True

def built_in_sqrt(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    if not isinstance(value, (int, float)):
        raise SemanticError(sem("sem_num_only", name="корень"), node.token, interp.call_stack)
    if value < 0:
        raise SemanticError(sem("sem_sqrt_neg"), node.token, interp.call_stack)
    return math.sqrt(value)

def built_in_abs(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    if not isinstance(value, (int, float)):
        raise SemanticError(sem("sem_num_only", name="модуль"), node.token, interp.call_stack)
    return abs(value)

def built_in_rand(interp, node):
    _check_arity(interp, node, 0)
    return random.random()

def built_in_randint(interp, node):
    _check_arity(interp, node, 2)
    min_val = interp.visit(node.actual_params[0])[1]
    max_val = interp.visit(node.actual_params[1])[1]
    return float(random.randint(int(min_val), int(max_val)))

def built_in_len(interp, node):
    _check_arity(interp, node, 1)
    val = interp.visit(node.actual_params[0])[1]
    if isinstance(val, dict) and val.get('_type') == 'array':
        return float(len(val['values']))
    if isinstance(val, dict):
        return float(len(val))
    if isinstance(val, str):
        return float(len(val))
    if isinstance(val, bool) or isinstance(val, (int, float)):
        raise SemanticError(sem("sem_len_number"), node.token, interp.call_stack)
    return float(len(format_value(val)))

def built_in_substr(interp, node):
    _check_arity(interp, node, 3)
    s = str(interp.visit(node.actual_params[0])[1])
    start = int(interp.visit(node.actual_params[1])[1]) - 1
    count = int(interp.visit(node.actual_params[2])[1])
    return s[start : start + count]

def built_in_upper(interp, node):
    _check_arity(interp, node, 1)
    return str(interp.visit(node.actual_params[0])[1]).upper()

def built_in_lower(interp, node):
    _check_arity(interp, node, 1)
    return str(interp.visit(node.actual_params[0])[1]).lower()

def built_in_to_int(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    try:
        return float(int(float(value)))
    except (ValueError, TypeError):
        raise SemanticError(sem("sem_convert", value=value, target=sem("sem_convert_int")), node.token, interp.call_stack)

def built_in_to_float(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    try:
        return float(value)
    except (ValueError, TypeError):
        raise SemanticError(sem("sem_convert", value=value, target=sem("sem_convert_float")), node.token, interp.call_stack)

def built_in_to_str(interp, node):
    _check_arity(interp, node, 1)
    return format_value(interp.visit(node.actual_params[0])[1])

def built_in_mod(interp, node):
    _check_arity(interp, node, 2)
    a = interp.visit(node.actual_params[0])[1]
    b = interp.visit(node.actual_params[1])[1]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SemanticError(sem("sem_num_only", name="остаток"), node.token, interp.call_stack)
    if float(b) == 0:
        raise SemanticError(sem("sem_div_zero_in", name="остаток"), node.token, interp.call_stack)
    return float(a % b)

def built_in_div(interp, node):
    _check_arity(interp, node, 2)
    a = interp.visit(node.actual_params[0])[1]
    b = interp.visit(node.actual_params[1])[1]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SemanticError(sem("sem_num_only", name="целдел"), node.token, interp.call_stack)
    if int(b) == 0:
        raise SemanticError(sem("sem_div_zero_in", name="целдел"), node.token, interp.call_stack)
    return float(int(a) // int(b))

def built_in_pow(interp, node):
    _check_arity(interp, node, 2)
    a = interp.visit(node.actual_params[0])[1]
    b = interp.visit(node.actual_params[1])[1]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SemanticError(sem("sem_num_only", name="степень"), node.token, interp.call_stack)
    try:
        return float(math.pow(a, b))
    except (ValueError, OverflowError) as e:
        raise SemanticError(sem("sem_pow_error", error=e), node.token, interp.call_stack)

def built_in_min(interp, node):
    _check_arity(interp, node, 2)
    a = interp.visit(node.actual_params[0])[1]
    b = interp.visit(node.actual_params[1])[1]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SemanticError(sem("sem_num_only", name="мин"), node.token, interp.call_stack)
    return float(min(a, b))

def built_in_max(interp, node):
    _check_arity(interp, node, 2)
    a = interp.visit(node.actual_params[0])[1]
    b = interp.visit(node.actual_params[1])[1]
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise SemanticError(sem("sem_num_only", name="макс"), node.token, interp.call_stack)
    return float(max(a, b))

def built_in_round(interp, node):
    _check_arity(interp, node, 1)
    val = interp.visit(node.actual_params[0])[1]
    if not isinstance(val, (int, float)):
        raise SemanticError(sem("sem_num_only", name="округление"), node.token, interp.call_stack)
    return float(round(val))

def built_in_sign(interp, node):
    _check_arity(interp, node, 1)
    val = interp.visit(node.actual_params[0])[1]
    if not isinstance(val, (int, float)):
        raise SemanticError(sem("sem_num_only", name="знак"), node.token, interp.call_stack)
    if val > 0:
        return 1.0
    elif val < 0:
        return -1.0
    return 0.0

def built_in_sin(interp, node):
    _check_arity(interp, node, 1)
    val = interp.visit(node.actual_params[0])[1]
    if not isinstance(val, (int, float)):
        raise SemanticError(sem("sem_num_only", name="sin"), node.token, interp.call_stack)
    return math.sin(val)

def built_in_cos(interp, node):
    _check_arity(interp, node, 1)
    val = interp.visit(node.actual_params[0])[1]
    if not isinstance(val, (int, float)):
        raise SemanticError(sem("sem_num_only", name="cos"), node.token, interp.call_stack)
    return math.cos(val)

def built_in_find(interp, node):
    _check_arity(interp, node, 2)
    s = str(interp.visit(node.actual_params[0])[1])
    sub = str(interp.visit(node.actual_params[1])[1])
    idx = s.find(sub)
    return float(idx + 1 if idx >= 0 else 0)

def built_in_size(interp, node):
    return built_in_len(interp, node)

# Словарь имён встроенных процедур/функций → реализация (interp, node)
BUILTINS = {
    'открыть': built_in_open,
    'закрыть': built_in_close,
    'конецфайла': built_in_eof,
    'корень': built_in_sqrt,
    'модуль': built_in_abs,
    'случ': built_in_rand,
    'случцел': built_in_randint,
    'длина': built_in_len,
    'подстрока': built_in_substr,
    'вверх': built_in_upper,
    'вниз': built_in_lower,
    'вцел': built_in_to_int,
    'ввещ': built_in_to_float,
    'встроку': built_in_to_str,
    'остаток': built_in_mod,
    'целдел': built_in_div,
    'степень': built_in_pow,
    'мин': built_in_min,
    'макс': built_in_max,
    'округление': built_in_round,
    'знак': built_in_sign,
    'син': built_in_sin,
    'кос': built_in_cos,
    'найти': built_in_find,
    'размер': built_in_size,
}
