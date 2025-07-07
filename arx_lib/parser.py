from sly import Parser
from .lexer import ArtemisLexer
from .helpers import ArtemisParserLogger

class ArtemisParser(Parser):
    tokens = ArtemisLexer.tokens
    log = ArtemisParserLogger()

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )

    def __init__(self):
        self.using_modules = []

    # Entry point
    @_('using_directive_list function_list')
    def program(self, p):
        return ('program', p.using_directive_list, p.function_list)

    # ----- USING DIRECTIVES -----
    @_('USING ID')
    def using_directive(self, p):
        self.using_modules.append(p.ID)
        return ('using', p.ID)

    @_('using_directive using_directive_list')
    def using_directive_list(self, p):
        return [p.using_directive] + p.using_directive_list

    @_('using_directive')
    def using_directive_list(self, p):
        return [p.using_directive]

    # ----- FUNCTION DECLARATIONS -----
    @_('function function_list')
    def function_list(self, p):
        return [p.function] + p.function_list

    @_('function')
    def function_list(self, p):
        return [p.function]
    
    @_('INT ID LPAREN RPAREN LBRACE statements RBRACE')
    def function(self, p):
        return ('function', p.ID, [], p.statements, 'int')
    
    @_('INT ID LPAREN param_list RPAREN LBRACE statements RBRACE')
    def function(self, p):
        return ('function', p.ID, p.param_list, p.statements, 'int')
    
    # ----- PARAMETERS -----
    @_('param COMMA param_list')
    def param_list(self, p):
        return [p.param] + p.param_list

    @_('param')
    def param_list(self, p):
        return [p.param]

    @_('INT ID')
    def param(self, p):
        return ('param', 'int', p.ID)

    @_('STRING ID')
    def param(self, p):
        return ('param', 'str', p.ID)

    @_('BOOL ID')
    def param(self, p):
        return ('param', 'bool', p.ID)

    # ----- STATEMENTS -----
    @_('statements statement')
    def statements(self, p):
        return p.statements + [p.statement]

    @_('')
    def statements(self, p):
        return []

    @_('expression')
    def statement(self, p):
        return ('expression', p.expression)

    @_('RETURN expression')
    def statement(self, p):
        return ('return', p.expression)
    
    # -- IF / ELSE IF / ELSE CHAIN --

    @_('IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain')
    def statement(self, p):
        return ('if_chain', [(p.expression, p.statements)] + p.elseif_chain)

    @_('ELSE IF LPAREN expression RPAREN LBRACE statements RBRACE elseif_chain')
    def elseif_chain(self, p):
        return [(p.expression, p.statements)] + p.elseif_chain

    @_('ELSE LBRACE statements RBRACE')
    def elseif_chain(self, p):
        return [(None, p.statements)]

    @_('')
    def elseif_chain(self, p):
        return []
    
    # ----- FOR -----
    @_('FOR LPAREN type ID IN ID RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('for_in', p.type, p.ID0, p.ID1, p.statements)

    # ----- OPS -----
    @_('expression PLUS expression')
    def expression(self, p):
        return ('binop', '+', p.expression0, p.expression1)

    @_('expression MINUS expression')
    def expression(self, p):
        return ('binop', '-', p.expression0, p.expression1)

    @_('expression TIMES expression')
    def expression(self, p):
        return ('binop', '*', p.expression0, p.expression1)

    @_('expression DIVIDE expression')
    def expression(self, p):
        return ('binop', '/', p.expression0, p.expression1)
    
    @_('expression EQEQ expression')
    def expression(self, p):
        return ('binop', '==', p.expression0, p.expression1)
    
    @_('expression NOTEQ expression')
    def expression(self, p):
        return ('binop', '!=', p.expression0, p.expression1)
    
    @_('expression LTEQ expression')
    def expression(self, p):
        return ('binop', '<=', p.expression0, p.expression1)
    
    @_('expression GTEQ expression')
    def expression(self, p):
        return ('binop', '>=', p.expression0, p.expression1)
    
    @_('expression GT expression')
    def expression(self, p):
        return ('binop', '>', p.expression0, p.expression1)
    
    @_('expression LT expression')
    def expression(self, p):
        return ('binop', '<', p.expression0, p.expression1)


    # ----- EXPRESSIONS -----
    @_('type ID ASSIGN expression')
    def statement(self, p):
        return ('declare', p.type, p.ID, p.expression)
    
    @_('LIST COLON type ID ASSIGN expression')
    def statement(self, p):
        return ('declare_list', p.type, p.ID, p.expression)

    @_('function_call')
    def expression(self, p):
        return p.function_call

    @_('ID DOT ID LPAREN args RPAREN')
    def function_call(self, p):
        return ('call_method', p.ID0, p.ID1, p.args)

    @_('ID LPAREN args RPAREN')
    def function_call(self, p):
        return ('call', p.ID, p.args)

    @_('STRING')
    def expression(self, p):
        return ('string', p.STRING)

    @_('NUMBER')
    def expression(self, p):
        return ('int', p.NUMBER)
    
    @_('TRUE')
    def expression(self, p):
        return ('bool', True)

    @_('FALSE')
    def expression(self, p):
        return ('bool', False)
    
    # ----- TYPES -----
    @_('INT')
    def type(self, p):
        return 'int'
    
    @_('BOOL')
    def type(self, p):
        return 'bool'
    
    @_('FLOAT')
    def type(self, p):
        return 'float'
    
    @_('STR')
    def type(self, p):
        return 'string'
    
    @_('LBRACKET list_elements RBRACKET')
    def expression(self, p):
        return ('list_literal', p.list_elements)

    @_('expression COMMA list_elements')
    def list_elements(self, p):
        return [p.expression] + p.list_elements

    @_('expression')
    def list_elements(self, p):
        return [p.expression]

    # ----- FUNCTION ARGUMENTS -----
    @_('')
    def args(self, p):
        return []

    @_('expression')
    def args(self, p):
        return [p.expression]

    @_('args COMMA expression')
    def args(self, p):
        return p.args + [p.expression]
    
    @_('ID')
    def expression(self, p):
        return ('var', p.ID)
