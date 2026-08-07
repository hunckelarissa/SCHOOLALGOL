# parser.py

from errors import ParserError
from lang_tokens import TokenType, token_type_bilingual_label
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
    FormatSpec,
    FuncDecl,
    IfNode,
    Input,
    MemberAccess,
    Num,
    Param,
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

class Parser:
    """Синтаксический анализатор языка .alg."""

    # Токены, с которых начинается объявление переменной, массива или константы
    _VAR_DECL_START = (
        TokenType.ЦЕЛ,
        TokenType.ВЕЩ,
        TokenType.ЛОГ,
        TokenType.ЛИТ,
        TokenType.ТАБ,
        TokenType.ФАЙЛ,
        TokenType.СЛОВАРЬ,
        TokenType.КОНСТ,
    )
    # После ID в теле блока эти токены означают оператор, а не объявление типа ID
    _STMT_AFTER_ID = (
        TokenType.ASSIGN,
        TokenType.LBRACKET,
        TokenType.DOT,
        TokenType.LPAREN,
    )

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos]

    def lookahead(self, offset=1):
        """Безопасный доступ к токену вперёд; при выходе за границы возвращает последний токен (EOF)."""
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def _token_context(self, count: int = 5) -> str:
        """Фрагмент потока токенов вокруг текущей позиции для сообщений об ошибках."""
        parts = []
        for i in range(count):
            t = self.lookahead(i)
            if t.type == TokenType.EOF:
                parts.append("<EOF>")
                break
            val = getattr(t, "value", None)
            if t.type == TokenType.ID and val:
                parts.append(str(val)[:24])
            elif val is not None and t.type in (TokenType.NUMBER, TokenType.STRING):
                parts.append(str(val)[:24])
            elif val:
                parts.append(str(val))
            else:
                parts.append(t.type.name)
        return " ".join(parts)

    def eat(self, token_type):
        """Потребляет токен ожидаемого типа и переходит к следующему."""
        if self.current_token().type == token_type:
            token = self.current_token()
            self.pos += 1
            return token
        else:
            raise ParserError(
                f"ожидался токен «{token_type_bilingual_label(token_type)}», "
                f"а получен «{token_type_bilingual_label(self.current_token().type)}»",
                self.current_token(),
                context=self._token_context(),
            )

    # --- Иерархия разбора выражений (с учетом приоритетов) ---

    def factor(self):
        """Разбирает самые базовые элементы: литералы, переменные, вызовы функций, выражения в скобках."""
        token = self.current_token()
        node = None
        if token.type == TokenType.NUMBER:
            node = Num(self.eat(TokenType.NUMBER))
        elif token.type == TokenType.STRING:
            node = String(self.eat(TokenType.STRING))
        elif token.type in (TokenType.ДА, TokenType.НЕТ):
            node = Bool(self.eat(token.type))
        elif token.type == TokenType.ID:
            var_token = self.eat(TokenType.ID)
            if self.current_token().type == TokenType.LPAREN:
                # Это вызов функции, которая возвращает значение
                self.eat(TokenType.LPAREN)
                actual_params = []
                if self.current_token().type != TokenType.RPAREN:
                    actual_params.append(self.logical_or_expr())
                    while self.current_token().type == TokenType.COMMA:
                        self.eat(TokenType.COMMA)
                        actual_params.append(self.logical_or_expr())
                self.eat(TokenType.RPAREN)
                node = SubroutineCall(var_token, actual_params)
            else:
                # Это просто переменная
                node = Var(var_token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.logical_or_expr()
            self.eat(TokenType.RPAREN)
        else:
            # Если ничего не подошло, вызываем унарное выражение для обработки "не" или "-/+"
            return self.unary_expr()

        # Цикл для обработки доступа к членам/элементам: a.b[i].c
        while self.current_token().type in (TokenType.LBRACKET, TokenType.DOT):
            if self.current_token().type == TokenType.LBRACKET:
                self.eat(TokenType.LBRACKET)
                index_expr = self.logical_or_expr()
                self.eat(TokenType.RBRACKET)
                node = ArrayAccess(node, index_expr)
            elif self.current_token().type == TokenType.DOT:
                self.eat(TokenType.DOT)
                member_token = self.eat(TokenType.ID)
                node = MemberAccess(node, member_token)
        return node

    def unary_expr(self):
        """Разбирает унарные операции: +, -, не"""
        token = self.current_token()
        if token.type == TokenType.НЕ:
            op = self.eat(TokenType.НЕ)
            return UnaryOp(op, self.unary_expr())
        elif token.type == TokenType.OP and token.value in ('+', '-'):
            op = self.eat(TokenType.OP)
            return UnaryOp(op, self.unary_expr())
        return self.factor()

    def term(self):
        """Разбирает умножение и деление."""
        node = self.unary_expr()
        while self.current_token().type == TokenType.OP and self.current_token().value in ('*', '/'):
            op_token = self.eat(TokenType.OP)
            node = BinOp(left=node, op=op_token, right=self.unary_expr())
        return node

    def expr(self):
        """Разбирает сложение и вычитание."""
        node = self.term()
        while self.current_token().type == TokenType.OP and self.current_token().value in ('+', '-'):
            op_token = self.eat(TokenType.OP)
            node = BinOp(left=node, op=op_token, right=self.term())
        return node
    
    def _is_comparison_token(self, token):
        if token.type in (TokenType.EQ, TokenType.NEQ, TokenType.LTE, TokenType.GTE):
            return True
        return token.type == TokenType.OP and token.value in (">", "<")

    def comparison_expr(self):
        """Разбирает операции сравнения."""
        node = self.expr()
        if self._is_comparison_token(self.current_token()):
            op_token = self.eat(self.current_token().type)
            node = BinOp(left=node, op=op_token, right=self.expr())
        return node

    def logical_and_expr(self):
        """Разбирает логическое 'и'."""
        node = self.comparison_expr()
        while self.current_token().type == TokenType.И:
            op_token = self.eat(TokenType.И)
            node = BinOp(left=node, op=op_token, right=self.comparison_expr())
        return node
        
    def logical_or_expr(self):
        """Разбирает логическое 'или' (самый низкий приоритет)."""
        node = self.logical_and_expr()
        while self.current_token().type == TokenType.ИЛИ:
            op_token = self.eat(TokenType.ИЛИ)
            node = BinOp(left=node, op=op_token, right=self.logical_and_expr())
        return node

    # --- Разбор операторов ---

    def statement(self):
        """Диспетчер для разбора операторов."""
        current = self.current_token()
        if current.type == TokenType.ID:
            # Если за ID следуют ':=', '[' или '.', это присваивание. Иначе - вызов процедуры.
            if self.lookahead(1).type in (TokenType.ASSIGN, TokenType.LBRACKET, TokenType.DOT):
                 return self.assignment_statement()
            else:
                 return self.subroutine_call_statement()
        elif current.type == TokenType.ВЫВОД: return self.print_statement()
        elif current.type == TokenType.ВВОД: return self.input_statement()
        elif current.type == TokenType.ЕСЛИ: return self.if_statement()
        elif current.type == TokenType.НЦ: return self.loop_statement()
        else:
            raise ParserError("Неожиданный оператор", current)

    def subroutine_call_statement(self):
        call_node = self.factor()
        if not isinstance(call_node, SubroutineCall):
            raise ParserError("Ожидался вызов процедуры", call_node.token if hasattr(call_node, 'token') else self.current_token())
        return call_node
        
    def assignment_statement(self):
        left = self.factor() # левая часть может быть сложной: a.b[i]
        self.eat(TokenType.ASSIGN)
        right = self.logical_or_expr()
        return Assign(left, right)

    def print_statement(self):
        token = self.eat(TokenType.ВЫВОД)
        file_node = None
        if self.tokens[self.pos].type == TokenType.ID and self.lookahead(1).type == TokenType.COMMA:
            file_node = Var(self.eat(TokenType.ID))
            self.eat(TokenType.COMMA)
        items = []
        if self.current_token().type in (TokenType.КОН, TokenType.EOF, TokenType.ИНАЧЕ, TokenType.ВСЕ, TokenType.КЦ):
            return Print(items, file_node, token)
        while True:
            expr_node = self.logical_or_expr()
            format_spec_node = None
            if self.current_token().type == TokenType.COLON:
                self.eat(TokenType.COLON)
                width_node = self.expr()
                precision_node = None
                if self.current_token().type == TokenType.COLON:
                    self.eat(TokenType.COLON)
                    precision_node = self.expr()
                format_spec_node = FormatSpec(width_node, precision_node)
            items.append((expr_node, format_spec_node))
            if self.current_token().type != TokenType.COMMA: break
            self.eat(TokenType.COMMA)
        return Print(items, file_node, token)

    def input_statement(self):
        token = self.eat(TokenType.ВВОД)
        file_node = None
        if self.tokens[self.pos].type == TokenType.ID and self.lookahead(1).type == TokenType.COMMA:
            file_node = Var(self.eat(TokenType.ID))
            self.eat(TokenType.COMMA)
        var_nodes = [Var(self.eat(TokenType.ID))]
        while self.current_token().type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            var_nodes.append(Var(self.eat(TokenType.ID)))
        return Input(var_nodes, file_node, token)

    def if_statement(self):
        token = self.eat(TokenType.ЕСЛИ)
        condition = self.logical_or_expr()
        self.eat(TokenType.ТО)
        then_block = self.statement_list(stop_tokens=[TokenType.ИНАЧЕ, TokenType.ВСЕ])
        else_block = None
        if self.current_token().type == TokenType.ИНАЧЕ:
            self.eat(TokenType.ИНАЧЕ)
            else_block = self.statement_list(stop_tokens=[TokenType.ВСЕ])
        self.eat(TokenType.ВСЕ)
        return IfNode(condition, then_block, else_block, token)

    def loop_statement(self):
        nc_token = self.eat(TokenType.НЦ)
        if self.current_token().type == TokenType.ДЛЯ:
            self.eat(TokenType.ДЛЯ)
            var_node = Var(self.eat(TokenType.ID))
            self.eat(TokenType.ОТ)
            start_val = self.logical_or_expr()
            self.eat(TokenType.ДО)
            end_val = self.logical_or_expr()
            body = self.statement_list(stop_tokens=[TokenType.КЦ])
            self.eat(TokenType.КЦ)
            return ForNode(var_node, start_val, end_val, body, nc_token)
        elif self.current_token().type == TokenType.ПОКА:
            пока_token = self.eat(TokenType.ПОКА)
            condition = self.logical_or_expr()
            body = self.statement_list(stop_tokens=[TokenType.КЦ])
            self.eat(TokenType.КЦ)
            return WhileNode(condition, body, пока_token)
        else:
            raise ParserError(
                "Ожидалось «для / for» или «пока / while» после «нц / loop»",
                self.current_token(),
            )
            
    def statement_list(self, stop_tokens):
        statements = []
        while self.current_token().type not in stop_tokens:
            statement = self.statement()
            if statement: statements.append(statement)
        return statements

    # --- Разбор объявлений ---

    def formal_parameter_list(self):
        params = []
        if self.current_token().type != TokenType.LPAREN:
             type_node = self._parse_type_specifier()
             var_node = Var(self.eat(TokenType.ID))
             params.append(Param(var_node, type_node))
             while self.current_token().type == TokenType.COMMA:
                 self.eat(TokenType.COMMA)
                 type_node = self._parse_type_specifier()
                 var_node = Var(self.eat(TokenType.ID))
                 params.append(Param(var_node, type_node))
             return params

        self.eat(TokenType.LPAREN)
        if self.current_token().type == TokenType.RPAREN:
            self.eat(TokenType.RPAREN)
            return params
        
        type_node = self._parse_type_specifier()
        var_node = Var(self.eat(TokenType.ID))
        params.append(Param(var_node, type_node))
        while self.current_token().type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            type_node = self._parse_type_specifier()
            var_node = Var(self.eat(TokenType.ID))
            params.append(Param(var_node, type_node))
        self.eat(TokenType.RPAREN)
        return params

    def _parse_type_specifier(self):
        is_array = False
        if self.current_token().type == TokenType.ТАБ:
            self.eat(TokenType.ТАБ)
            is_array = True
        
        type_token = self.current_token()
        allowed_types = (TokenType.ЦЕЛ, TokenType.ВЕЩ, TokenType.ЛОГ, TokenType.ЛИТ, TokenType.ФАЙЛ, TokenType.СЛОВАРЬ)
        if type_token.type in allowed_types:
            type_node = Type(self.eat(type_token.type))
        elif type_token.type == TokenType.ID:
            type_node = CustomType(self.eat(TokenType.ID))
        else:
            raise ParserError(
                "Ожидался спецификатор типа (цел/int, вещ/real, лит/str, лог/bool, таб/tab, файл/file, словарь/dict)",
                type_token,
            )
        type_node.is_array = is_array
        return type_node

    def const_declaration(self):
        self.eat(TokenType.КОНСТ)
        var_node = Var(self.eat(TokenType.ID))
        self.eat(TokenType.EQ)
        expr = self.logical_or_expr()
        return ConstDecl(var_node, expr)

    def var_declaration(self):
        type_node = self._parse_type_specifier()
        declarations = []
        var_token = self.eat(TokenType.ID)
        if self.current_token().type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            start_idx = self.expr()
            self.eat(TokenType.COLON)
            end_idx = self.expr()
            self.eat(TokenType.RBRACKET)
            declarations.append(ArrayDecl(Var(var_token), type_node, start_idx, end_idx))
        else:
            declarations.append(VarDecl(Var(var_token), type_node))
            while self.current_token().type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                var_token = self.eat(TokenType.ID)
                declarations.append(VarDecl(Var(var_token), type_node))
        return declarations

    def declaration(self):
        if self.current_token().type == TokenType.КОНСТ:
            return [self.const_declaration()]
        # Проверяем, является ли ID названием типа, а не переменной
        elif self.current_token().type == TokenType.ID:
             # Это может быть объявление переменной пользовательского типа
             return self.var_declaration()
        else: # Все остальные типы
            return self.var_declaration()

    def _is_custom_type_decl(self) -> bool:
        """ID ID — объявление переменной пользовательского типа (имя_типа имя_переменной)."""
        return (
            self.current_token().type == TokenType.ID
            and self.lookahead(1).type == TokenType.ID
        )

    def _starts_var_or_const_decl(self) -> bool:
        tok = self.current_token().type
        if tok in self._VAR_DECL_START:
            return True
        return self._is_custom_type_decl()

    def _starts_declaration(self) -> bool:
        """Можно ли начать объявление в текущей позиции тела блока."""
        tok = self.current_token().type
        if tok in (TokenType.ЗАПИСЬ, TokenType.ПЕРЕЧ):
            return True
        return self._starts_var_or_const_decl()

    def _parse_one_declaration(self):
        """Разбирает одно объявление (запись, переч, конст, переменные, массив)."""
        if self.current_token().type == TokenType.ЗАПИСЬ:
            return [self.record_declaration()]
        if self.current_token().type == TokenType.ПЕРЕЧ:
            return [self.enum_declaration()]
        return self.declaration()

    def _parse_pre_begin_decls(self):
        """Объявления между заголовком подпрограммы и ключевым словом «нач» (Pascal-style)."""
        declarations = []
        while self.current_token().type != TokenType.НАЧ:
            if not self._starts_declaration():
                raise ParserError(
                    "Ожидалось объявление перед «нач / begin»",
                    self.current_token(),
                    context=self._token_context(),
                )
            declarations.extend(self._parse_one_declaration())
        return declarations

    def _parse_body(self):
        """
        Тело между «нач» и «кон»: последовательность объявлений и операторов.

        Правило различения: ID + (':=' | '(' | '[' | '.') → оператор;
        ID + ID → объявление пользовательского типа; ключевые слова типов → объявление.
        """
        declarations = []
        statements = []
        while self.current_token().type != TokenType.КОН:
            if self._starts_declaration():
                declarations.extend(self._parse_one_declaration())
            else:
                statements.append(self.statement())
        return declarations, statements

    def block(self):
        declarations = self._parse_pre_begin_decls()
        self.eat(TokenType.НАЧ)
        body_decls, statements = self._parse_body()
        declarations.extend(body_decls)
        self.eat(TokenType.КОН)
        return Block(declarations, statements)
        
    def subroutine_declaration(self):
        self.eat(TokenType.АЛГ)
        name_token = self.eat(TokenType.ID)
        params = []
        return_var_decl = None

        # Поддержка синтаксиса со скобками: алг Имя(арг ...; рез ...)
        if self.current_token().type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            while self.current_token().type != TokenType.RPAREN:
                if self.current_token().type == TokenType.АРГ:
                    self.eat(TokenType.АРГ)
                    # Используем существующий метод, он корректно распарсит список типов и имен
                    # так как точки с запятой игнорируются лексером, а запятых может и не быть
                    params.extend(self.formal_parameter_list())
                elif self.current_token().type == TokenType.РЕЗ:
                    self.eat(TokenType.РЕЗ)
                    # declaration возвращает список [VarDecl, ...], берем первый
                    # Обычно там "тип имя", что соответствует var_declaration
                    decls = self.declaration()
                    if decls:
                        return_var_decl = decls[0]
                else:
                    # Если встретили что-то неожиданное внутри скобок (не АРГ и не РЕЗ), 
                    # возможно это параметры без ключевого слова АРГ? 
                    # Пока считаем, что структура строгая. Если нет, можно попробовать распарсить как параметры.
                    # Для надежности, если это типы данных, считаем параметрами.
                    # Но лучше следовать явному синтаксису. Если зациклится - вылетит по EOF или ошибке типа.
                    if self.current_token().type in (TokenType.ЦЕЛ, TokenType.ВЕЩ, TokenType.ЛОГ, TokenType.ЛИТ, TokenType.ТАБ, TokenType.ФАЙЛ, TokenType.СЛОВАРЬ):
                         params.extend(self.formal_parameter_list())
                    else:
                         # Чтобы не было вечного цикла, если токен непонятный
                         break
            self.eat(TokenType.RPAREN)
        
        # Поддержка старого синтаксиса без скобок вокруг всего блока
        else:
            if self.current_token().type == TokenType.АРГ:
                self.eat(TokenType.АРГ)
                params = self.formal_parameter_list()
            
            if self.current_token().type == TokenType.РЕЗ:
                self.eat(TokenType.РЕЗ)
                return_var_decl = self.declaration()[0]
        
        block_node = self.block()

        if return_var_decl:
            return FuncDecl(name_token, params, return_var_decl, block_node)
        else:
            return ProcDecl(name_token, params, block_node)
            
    def record_declaration(self):
        self.eat(TokenType.ЗАПИСЬ)
        name_token = self.eat(TokenType.ID)
        self.eat(TokenType.НАЧ)
        fields = []
        while self.current_token().type != TokenType.КОН:
            fields.extend(self.declaration())
        self.eat(TokenType.КОН)
        return RecordDecl(name_token, fields)

    def enum_declaration(self):
        self.eat(TokenType.ПЕРЕЧ)
        name_token = self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)
        members = [self.eat(TokenType.ID)]
        while self.current_token().type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            members.append(self.eat(TokenType.ID))
        self.eat(TokenType.RPAREN)
        return EnumDecl(name_token, members)

    def program_element(self):
        current = self.current_token()
        if current.type == TokenType.ИСПОЛЬЗОВАТЬ:
            self.eat(TokenType.ИСПОЛЬЗОВАТЬ)
            filepath_token = self.eat(TokenType.STRING)
            return UseNode(filepath_token)
        elif current.type == TokenType.АЛГ:
            return self.subroutine_declaration()
        elif current.type == TokenType.ЗАПИСЬ:
            return self.record_declaration()
        elif current.type == TokenType.ПЕРЕЧ:
            return self.enum_declaration()
        elif current.type == TokenType.КОНСТ:
            return self.const_declaration()
        else:
            raise ParserError(
                "Ожидалось объявление: алг/proc, запись/rec, переч/enum, конст/const или использовать/import",
                current,
            )

    def parse(self):
        declarations = []
        while self.current_token().type != TokenType.EOF:
            declarations.append(self.program_element())
        return Program(declarations)