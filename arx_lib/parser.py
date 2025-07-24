from sly import Parser
from sly.lex import Token
from .lexer import ArtemisLexer
from .helpers import ArtemisParserLogger
from typing import Set, Any

class ArtemisParser(Parser):
    tokens : Set[str] = ArtemisLexer.tokens
    log : ArtemisParserLogger = ArtemisParserLogger()

    precedence : tuple = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )

    def __init__(self) -> None:
        self.using_modules = []

    @_('using_directive_list function_list') # type: ignore[name-defined]
    def program(self, p) -> tuple:
        return ('program', p.using_directive_list, p.function_list)

    # ----- USING DIRECTIVES -----
    @_('USING ID') # type: ignore[name-defined]
    def using_directive(self, p) -> tuple:
        self.using_modules.append(p.ID)
        return ('using', p.ID)

    @_('using_directive using_directive_list') # type: ignore[name-defined]
    def using_directive_list(self, p) -> list:
        return [p.using_directive] + p.using_directive_list

    @_('using_directive') # type: ignore[name-defined]
    def using_directive_list(self, p) -> list:
        return [p.using_directive]

    # ----- FUNCTION DECLARATIONS -----
    @_('function function_list') # type: ignore[name-defined]
    def function_list(self, p) -> list:
        return [p.function] + p.function_list

    @_('function') # type: ignore[name-defined]
    def function_list(self, p) -> list:
        return [p.function]
    
    @_('type ID LPAREN RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def function(self, p) -> tuple:
        return ('function', p.ID, [], p.statements, p.type)
    
    @_('type ID LPAREN param_list RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def function(self, p) -> tuple:
        return ('function', p.ID, p.param_list, p.statements, p.type)
    
    # ----- PARAMETERS -----
    @_('param COMMA param_list') # type: ignore[name-defined]
    def param_list(self, p) -> list:
        return [p.param] + p.param_list

    @_('param') # type: ignore[name-defined]
    def param_list(self, p) -> list:
        return [p.param]

    @_('INT ID') # type: ignore[name-defined]
    def param(self, p) -> tuple:
        return ('param', 'int', p.ID)

    @_('STR ID') # type: ignore[name-defined]
    def param(self, p) -> tuple:
        return ('param', 'str', p.ID)

    @_('BOOL ID') # type: ignore[name-defined]
    def param(self, p) -> tuple:
        return ('param', 'bool', p.ID)

    # ----- STATEMENTS -----
    @_('statements statement') # type: ignore[name-defined]
    def statements(self, p) -> list:
        return p.statements + [p.statement]

    @_('') # type: ignore[name-defined]
    def statements(self, p) -> list:
        return []

    @_('expression') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('expression', p.expression)

    @_('RETURN expression') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('return', p.expression)
    
    @_('RETURN') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('return_void',)
    
    # -- IF / ELSE IF / ELSE CHAIN --

    @_('IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('if_chain', [(p.expression, p.statements)] + p.elseif_chain)

    @_('ELSE IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain') # type: ignore[name-defined]
    def elseif_chain(self, p) -> list:
        return [(p.expression, p.statements)] + p.elseif_chain

    @_('ELSE LBRACE statements RBRACE') # type: ignore[name-defined]
    def elseif_chain(self, p) -> list:
        return [(None, p.statements)]

    @_('') # type: ignore[name-defined]
    def elseif_chain(self, p) -> list:
        return []
    
    # ----- FOR -----
    @_('FOR LPAREN type ID IN ID RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('for_in', p.type, p.ID0, p.ID1, p.statements)

    # ----- WHILE -----
    @_('WHILE LPAREN expression RPAREN LBRACE statements RBRACE')  # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('while', p.expression, p.statements)

    # ----- OPS -----
    @_('expression PLUS expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '+', p.expression0, p.expression1)

    @_('expression MINUS expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '-', p.expression0, p.expression1)

    @_('expression TIMES expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '*', p.expression0, p.expression1)

    @_('expression DIVIDE expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '/', p.expression0, p.expression1)
    
    @_('expression EQEQ expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '==', p.expression0, p.expression1)
    
    @_('expression NOTEQ expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '!=', p.expression0, p.expression1)
    
    @_('expression LTEQ expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '<=', p.expression0, p.expression1)
    
    @_('expression GTEQ expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '>=', p.expression0, p.expression1)
    
    @_('expression GT expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '>', p.expression0, p.expression1)
    
    @_('expression LT expression') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('binop', '<', p.expression0, p.expression1)

    # ----- TYPES -----
    @_('INT') # type: ignore[name-defined]
    def type(self, p) -> str:
        return 'int'
    
    @_('BOOL') # type: ignore[name-defined]
    def type(self, p) -> str:
        return 'bool'
    
    @_('FLOAT') # type: ignore[name-defined]
    def type(self, p) -> str:
        return 'float'
    
    @_('STR') # type: ignore[name-defined]
    def type(self, p) -> str:
        return 'string'

    @_('VOID') # type: ignore[name-defined]
    def type(self, p) -> str:
        return 'void'
    
    # ----- EXPRESSIONS -----
    @_('type ID ASSIGN expression') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('declare', p.type, p.ID, p.expression)
    
    @_('ID ASSIGN expression')  # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('assign', p.ID, p.expression)
    
    @_('LIST COLON type ID ASSIGN expression') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('declare_list', p.type, p.ID, p.expression)
    
    @_('BREAK') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('break',)

    @_('CONTINUE') # type: ignore[name-defined]
    def statement(self, p) -> tuple:
        return ('continue',)

    @_('function_call') # type: ignore[name-defined]
    def expression(self, p) -> Any:
        return p.function_call

    @_('ID DOT ID LPAREN args RPAREN') # type: ignore[name-defined]
    def function_call(self, p) -> tuple:
        return ('call_method', p.ID0, p.ID1, p.args)

    @_('ID LPAREN args RPAREN') # type: ignore[name-defined]
    def function_call(self, p) -> tuple:
        return ('call', p.ID, p.args)

    @_('STRING') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('string', p.STRING)

    @_('NUMBER') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('int', p.NUMBER)
    
    @_('TRUE') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('bool', True)

    @_('FALSE') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('bool', False)
    
    # ----- LISTS -----
    
    @_('LBRACKET list_elements RBRACKET') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('list_literal', p.list_elements)

    @_('expression COMMA list_elements') # type: ignore[name-defined]
    def list_elements(self, p) -> list:
        return [p.expression] + p.list_elements

    @_('expression') # type: ignore[name-defined]
    def list_elements(self, p) -> list:
        return [p.expression]

    # ----- FUNCTION ARGUMENTS -----
    @_('') # type: ignore[name-defined]
    def args(self, p) -> list:
        return []

    @_('expression') # type: ignore[name-defined]
    def args(self, p) -> list:
        return [p.expression]

    @_('args COMMA expression') # type: ignore[name-defined]
    def args(self, p) -> list:
        return p.args + [p.expression]
    
    @_('ID') # type: ignore[name-defined]
    def expression(self, p) -> tuple:
        return ('var', p.ID)
    
    @_('LPAREN expression RPAREN') # type: ignore[name-defined]
    def expression(self, p) -> list:
        return p.expression
