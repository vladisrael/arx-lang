from sly import Parser
from sly.lex import Token
from .lexer import ArtemisLexer
from .helpers import ArtemisParserLogger
from typing import Set

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
    def program(self, p):
        return ('program', p.using_directive_list, p.function_list)

    # ----- USING DIRECTIVES -----
    @_('USING ID') # type: ignore[name-defined]
    def using_directive(self, p):
        self.using_modules.append(p.ID)
        return ('using', p.ID)

    @_('using_directive using_directive_list') # type: ignore[name-defined]
    def using_directive_list(self, p):
        return [p.using_directive] + p.using_directive_list

    @_('using_directive') # type: ignore[name-defined]
    def using_directive_list(self, p):
        return [p.using_directive]

    # ----- FUNCTION DECLARATIONS -----
    @_('function function_list') # type: ignore[name-defined]
    def function_list(self, p):
        return [p.function] + p.function_list

    @_('function') # type: ignore[name-defined]
    def function_list(self, p):
        return [p.function]
    
    @_('type ID LPAREN RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def function(self, p):
        return ('function', p.ID, [], p.statements, p.type)
    
    @_('type ID LPAREN param_list RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def function(self, p):
        return ('function', p.ID, p.param_list, p.statements, p.type)
    
    # ----- PARAMETERS -----
    @_('param COMMA param_list') # type: ignore[name-defined]
    def param_list(self, p):
        return [p.param] + p.param_list

    @_('param') # type: ignore[name-defined]
    def param_list(self, p):
        return [p.param]

    @_('INT ID') # type: ignore[name-defined]
    def param(self, p):
        return ('param', 'int', p.ID)

    @_('STR ID') # type: ignore[name-defined]
    def param(self, p):
        return ('param', 'str', p.ID)

    @_('BOOL ID') # type: ignore[name-defined]
    def param(self, p):
        return ('param', 'bool', p.ID)

    # ----- STATEMENTS -----
    @_('statements statement') # type: ignore[name-defined]
    def statements(self, p):
        return p.statements + [p.statement]

    @_('') # type: ignore[name-defined]
    def statements(self, p):
        return []

    @_('expression') # type: ignore[name-defined]
    def statement(self, p):
        return ('expression', p.expression)

    @_('RETURN expression') # type: ignore[name-defined]
    def statement(self, p):
        return ('return', p.expression)
    
    @_('RETURN') # type: ignore[name-defined]
    def statement(self, p):
        return ('return_void',)
    
    # -- IF / ELSE IF / ELSE CHAIN --

    @_('IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain') # type: ignore[name-defined]
    def statement(self, p):
        return ('if_chain', [(p.expression, p.statements)] + p.elseif_chain)

    @_('ELSE IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain') # type: ignore[name-defined]
    def elseif_chain(self, p):
        return [(p.expression, p.statements)] + p.elseif_chain

    @_('ELSE LBRACE statements RBRACE') # type: ignore[name-defined]
    def elseif_chain(self, p):
        return [(None, p.statements)]

    @_('') # type: ignore[name-defined]
    def elseif_chain(self, p):
        return []
    
    # ----- FOR -----
    @_('FOR LPAREN type ID IN ID RPAREN LBRACE statements RBRACE') # type: ignore[name-defined]
    def statement(self, p):
        return ('for_in', p.type, p.ID0, p.ID1, p.statements)

    # ----- OPS -----
    @_('expression PLUS expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '+', p.expression0, p.expression1)

    @_('expression MINUS expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '-', p.expression0, p.expression1)

    @_('expression TIMES expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '*', p.expression0, p.expression1)

    @_('expression DIVIDE expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '/', p.expression0, p.expression1)
    
    @_('expression EQEQ expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '==', p.expression0, p.expression1)
    
    @_('expression NOTEQ expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '!=', p.expression0, p.expression1)
    
    @_('expression LTEQ expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '<=', p.expression0, p.expression1)
    
    @_('expression GTEQ expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '>=', p.expression0, p.expression1)
    
    @_('expression GT expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '>', p.expression0, p.expression1)
    
    @_('expression LT expression') # type: ignore[name-defined]
    def expression(self, p):
        return ('binop', '<', p.expression0, p.expression1)

    # ----- TYPES -----
    @_('INT') # type: ignore[name-defined]
    def type(self, p):
        return 'int'
    
    @_('BOOL') # type: ignore[name-defined]
    def type(self, p):
        return 'bool'
    
    @_('FLOAT') # type: ignore[name-defined]
    def type(self, p):
        return 'float'
    
    @_('STR') # type: ignore[name-defined]
    def type(self, p):
        return 'string'

    @_('VOID') # type: ignore[name-defined]
    def type(self, p):
        return 'void'
    
    # ----- EXPRESSIONS -----
    @_('type ID ASSIGN expression') # type: ignore[name-defined]
    def statement(self, p):
        return ('declare', p.type, p.ID, p.expression)
    
    @_('LIST COLON type ID ASSIGN expression') # type: ignore[name-defined]
    def statement(self, p):
        return ('declare_list', p.type, p.ID, p.expression)
    
    @_('BREAK') # type: ignore[name-defined]
    def statement(self, p):
        return ('break',)

    @_('CONTINUE') # type: ignore[name-defined]
    def statement(self, p):
        return ('continue',)

    @_('function_call') # type: ignore[name-defined]
    def expression(self, p):
        return p.function_call

    @_('ID DOT ID LPAREN args RPAREN') # type: ignore[name-defined]
    def function_call(self, p):
        return ('call_method', p.ID0, p.ID1, p.args)

    @_('ID LPAREN args RPAREN') # type: ignore[name-defined]
    def function_call(self, p):
        return ('call', p.ID, p.args)

    @_('STRING') # type: ignore[name-defined]
    def expression(self, p):
        return ('string', p.STRING)

    @_('NUMBER') # type: ignore[name-defined]
    def expression(self, p):
        return ('int', p.NUMBER)
    
    @_('TRUE') # type: ignore[name-defined]
    def expression(self, p):
        return ('bool', True)

    @_('FALSE') # type: ignore[name-defined]
    def expression(self, p):
        return ('bool', False)
    
    # ----- LISTS -----
    
    @_('LBRACKET list_elements RBRACKET') # type: ignore[name-defined]
    def expression(self, p):
        return ('list_literal', p.list_elements)

    @_('expression COMMA list_elements') # type: ignore[name-defined]
    def list_elements(self, p):
        return [p.expression] + p.list_elements

    @_('expression') # type: ignore[name-defined]
    def list_elements(self, p):
        return [p.expression]

    # ----- FUNCTION ARGUMENTS -----
    @_('') # type: ignore[name-defined]
    def args(self, p):
        return []

    @_('expression') # type: ignore[name-defined]
    def args(self, p):
        return [p.expression]

    @_('args COMMA expression') # type: ignore[name-defined]
    def args(self, p):
        return p.args + [p.expression]
    
    @_('ID') # type: ignore[name-defined]
    def expression(self, p):
        return ('var', p.ID)
