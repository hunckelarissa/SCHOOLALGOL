# alg_builtins.py — встроенные функции и процедуры языка .alg (интерпретатор)

import math
import os
import random
from errors import SemanticError
from ast_nodes import Var
from builtin_names import resolve_file_mode


def _check_arity(interp, node, expected_count):
    if len(node.actual_params) != expected_count:
        raise SemanticError(
            f"Функция '{node.name}' ожидает {expected_count} аргумент(ов), а получила {len(node.actual_params)}",
            node.token, interp.call_stack,
        )


def built_in_open(interp, node):
    _check_arity(interp, node, 3)
    file_var_node = node.actual_params[0]
    if not isinstance(file_var_node, Var):
        raise SemanticError("Первый аргумент 'открыть' должен быть файловой переменной", node.token, interp.call_stack)
    file_var_name = file_var_node.name
    path = interp.visit(node.actual_params[1])[1]
    mode_str = interp.visit(node.actual_params[2])[1]
    py_mode = resolve_file_mode(mode_str)
    if py_mode is None:
        raise SemanticError(f"Неизвестный режим файла: '{mode_str}'", node.actual_params[2].token, interp.call_stack)
    abs_path = os.path.abspath(path)
    interp._log(
        f"открыть: переменная={file_var_name!r}, путь={path!r}, "
        f"абсолютный={abs_path!r}, режим={mode_str!r} → Python '{py_mode}'"
    )
    try:
        file_handle = open(path, py_mode, encoding='utf-8')
        interp._set_variable(file_var_name, file_handle, file_var_node.token)
        interp._log(f"открыть: успешно, файл доступен для операций")
    except OSError as e:
        errno_hint = f" (errno {e.errno})" if getattr(e, "errno", None) is not None else ""
        raise SemanticError(
            f"Не удалось открыть файл «{path}» (абсолютный путь «{abs_path}», режим «{mode_str}»{errno_hint}): {e}",
            node.actual_params[1].token,
            interp.call_stack,
        )


def built_in_close(interp, node):
    _check_arity(interp, node, 1)
    first_arg = node.actual_params[0]
    if not isinstance(first_arg, Var):
        raise SemanticError("Первый аргумент 'закрыть' должен быть файловой переменной", node.token, interp.call_stack)
    var_name = first_arg.name
    file_handle = interp._get_variable(var_name, first_arg.token)[1]
    interp._log(f"закрыть: переменная={var_name!r}")
    if file_handle is not None and hasattr(file_handle, 'close'):
        file_handle.close()
        interp._log(f"закрыть: дескриптор закрыт")
    else:
        interp._log(f"закрыть: файл не был открыт или уже закрыт")
    interp._set_variable(var_name, None, first_arg.token)


def built_in_eof(interp, node):
    _check_arity(interp, node, 1)
    file_handle = interp.visit(node.actual_params[0])[1]
    if file_handle is None or not hasattr(file_handle, 'read'):
        raise SemanticError("Функция 'конецфайла' применима только к файлу для чтения", node.token, interp.call_stack)
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
        raise SemanticError("Функция 'корень' применима только к числам", node.token, interp.call_stack)
    if value < 0:
        raise SemanticError("Нельзя извлечь корень из отрицательного числа", node.token, interp.call_stack)
    return math.sqrt(value)


def built_in_abs(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    if not isinstance(value, (int, float)):
        raise SemanticError("Функция 'модуль' применима только к числам", node.token, interp.call_stack)
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
    return float(len(str(interp.visit(node.actual_params[0])[1])))


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
        raise SemanticError(f"Невозможно преобразовать '{value}' в целое число", node.token, interp.call_stack)


def built_in_to_float(interp, node):
    _check_arity(interp, node, 1)
    value = interp.visit(node.actual_params[0])[1]
    try:
        return float(value)
    except (ValueError, TypeError):
        raise SemanticError(f"Невозможно преобразовать '{value}' в вещественное число", node.token, interp.call_stack)


def built_in_to_str(interp, node):
    _check_arity(interp, node, 1)
    return str(interp.visit(node.actual_params[0])[1])


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
}
