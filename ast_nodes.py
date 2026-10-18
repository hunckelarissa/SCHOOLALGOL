# ast_nodes.py

from lang_tokens import TokenType

# --- Базовый класс ---
class AST:
    """Базовый класс для всех узлов AST."""
    pass

# --- Узлы верхнего уровня ---
class Program(AST):
    """Корень дерева, содержит все объявления верхнего уровня."""
    def __init__(self, declarations):
        self.declarations = declarations

class UseNode(AST):
    """Узел для оператора 'использовать "файл.алг"'"""
    def __init__(self, filepath_token):
        self.token = filepath_token
        self.filepath = filepath_token.value[1:-1] # Убираем кавычки

# --- Узлы объявлений ---
class Block(AST):
    """Блок кода между 'нач' и 'кон'."""
    def __init__(self, declarations, statements):
        self.declarations = declarations
        self.statements = statements

class ConstDecl(AST):
    """Объявление константы: конст ИМЯ = выражение"""
    def __init__(self, var_node, expr):
        self.var_node = var_node
        self.expr = expr

class VarDecl(AST):
    """Объявление переменной: тип ИМЯ"""
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node

class ArrayDecl(AST):
    """Объявление массива: таб тип ИМЯ[начало:конец]"""
    def __init__(self, var_node, type_node, start_idx, end_idx):
        self.var_node = var_node
        self.type_node = type_node
        self.start_idx = start_idx
        self.end_idx = end_idx

class RecordDecl(AST):
    """Объявление типа 'запись'"""
    def __init__(self, name_token, fields):
        self.token = name_token
        self.name = name_token.value.lower()
        self.fields = fields

class EnumDecl(AST):
    """Объявление типа 'перечисление'"""
    def __init__(self, name_token, members):
        self.token = name_token
        self.name = name_token.value.lower()
        self.members = members

# --- Узлы для подпрограмм ---
class Param(AST):
    """Формальный параметр в объявлении подпрограммы."""
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node

class ProcDecl(AST):
    """Объявление процедуры."""
    def __init__(self, name_token, params, block):
        self.token = name_token
        self.name = name_token.value.lower()
        self.params = params
        self.block = block

class FuncDecl(AST):
    """Объявление функции."""
    def __init__(self, name_token, params, return_var_decl, block):
        self.token = name_token
        self.name = name_token.value.lower()
        self.params = params
        self.return_var_decl = return_var_decl
        self.block = block

# --- Узлы операторов ---
class Assign(AST):
    """Оператор присваивания: LValue := RValue"""
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Print(AST):
    """Оператор вывода."""
    def __init__(self, items, file_node=None, token=None):
        self.items = items
        self.file_node = file_node
        self.token = token

class Input(AST):
    """Оператор ввода."""
    def __init__(self, var_nodes, file_node=None, token=None):
        self.var_nodes = var_nodes
        self.file_node = file_node
        self.token = token

class IfNode(AST):
    """Условный оператор."""
    def __init__(self, condition, then_block, else_block=None, token=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.token = token

class ForNode(AST):
    """Цикл со счетчиком. step_val=None означает шаг ±1 по направлению от→до."""
    def __init__(self, var_node, start_val, end_val, body, token=None, step_val=None):
        self.var_node = var_node
        self.start_val = start_val
        self.end_val = end_val
        self.step_val = step_val
        self.body = body
        self.token = token

class WhileNode(AST):
    """Цикл с условием."""
    def __init__(self, condition, body, token=None):
        self.condition = condition
        self.body = body
        self.token = token

class BreakNode(AST):
    """Досрочный выход из ближайшего цикла: выход / break."""
    def __init__(self, token):
        self.token = token

class ContinueNode(AST):
    """Переход к следующей итерации цикла: продолжить / continue."""
    def __init__(self, token):
        self.token = token

class ReturnNode(AST):
    """Досрочный возврат из функции: возврат [выражение] / return [expr]."""
    def __init__(self, token, expr=None):
        self.token = token
        self.expr = expr

class SubroutineCall(AST):
    """Вызов процедуры или функции."""
    def __init__(self, name_token, actual_params):
        self.token = name_token
        self.name = name_token.value.lower()
        self.actual_params = actual_params

# --- Узлы выражений ---
class BinOp(AST):
    """Бинарная операция: left OP right"""
    def __init__(self, left, op, right):
        self.left, self.op, self.right = left, op, right

class UnaryOp(AST):
    """Унарная операция: OP expr"""
    def __init__(self, op, expr):
        self.op, self.expr = op, expr

class Num(AST):
    """Числовой литерал."""
    def __init__(self, token):
        self.token = token
        self.value = float(token.value)

class String(AST):
    """Строковый литерал."""
    def __init__(self, token):
        self.token = token
        self.value = token.value[1:-1]

class Bool(AST):
    """Логический литерал."""
    def __init__(self, token):
        self.token = token
        self.value = token.type == TokenType.ДА

class Var(AST):
    """Использование переменной."""
    def __init__(self, token):
        self.token = token
        self.name = token.value.lower()

class ArrayAccess(AST):
    """Доступ к элементу массива: expr[index_expr]"""
    def __init__(self, owner_expr, index_expr):
        self.owner_expr = owner_expr
        self.index_expr = index_expr

class MemberAccess(AST):
    """Доступ к члену: expr.member"""
    def __init__(self, owner_expr, member_token):
        self.owner_expr = owner_expr
        self.member_token = member_token

# --- Узлы для типов и форматирования ---
class Type(AST):
    """Встроенный тип: цел, вещ и т.д."""
    def __init__(self, token):
        self.token = token
        self.value = token.value.lower()
        self.is_array = False

class CustomType(AST):
    """Пользовательский тип (имя записи или перечисления)."""
    def __init__(self, token):
        self.token = token
        self.name = token.value.lower()
        self.is_array = False
        
class FormatSpec(AST):
    """Спецификатор формата для вывода."""
    def __init__(self, width, precision=None):
        self.width = width
        self.precision = precision