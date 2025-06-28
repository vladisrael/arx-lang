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
        return ('function', p.ID, p.statements)

    # ----- STATEMENTS -----
    @_('statements statement')
    def statements(self, p):
        return p.statements + [p.statement]

    @_('')
    def statements(self, p):
        return []

    @_('expr')
    def statement(self, p):
        return ('expr', p.expr)

    @_('RETURN expr')
    def statement(self, p):
        return ('return', p.expr)

    # ----- OPS -----
    @_('expr PLUS expr')
    def expr(self, p):
        return ('binop', '+', p.expr0, p.expr1)

    @_('expr MINUS expr')
    def expr(self, p):
        return ('binop', '-', p.expr0, p.expr1)

    @_('expr TIMES expr')
    def expr(self, p):
        return ('binop', '*', p.expr0, p.expr1)

    @_('expr DIVIDE expr')
    def expr(self, p):
        return ('binop', '/', p.expr0, p.expr1)


    # ----- EXPRESSIONS -----
    @_('type ID ASSIGN expr')
    def statement(self, p):
        return ('declare', p.type, p.ID, p.expr)

    @_('function_call')
    def expr(self, p):
        return p.function_call

    @_('ID DOT ID LPAREN args RPAREN')
    def function_call(self, p):
        return ('call_method', p.ID0, p.ID1, p.args)

    @_('ID LPAREN args RPAREN')
    def function_call(self, p):
        return ('call', p.ID, p.args)

    @_('STRING')
    def expr(self, p):
        return ('string', p.STRING)

    @_('NUMBER')
    def expr(self, p):
        return ('int', p.NUMBER)
    
    @_('TRUE')
    def expr(self, p):
        return ('bool', True)

    @_('FALSE')
    def expr(self, p):
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

    # ----- FUNCTION ARGUMENTS -----
    @_('')
    def args(self, p):
        return []

    @_('expr')
    def args(self, p):
        return [p.expr]

    @_('args COMMA expr')
    def args(self, p):
        return p.args + [p.expr]
    
    @_('ID')
    def expr(self, p):
        return ('var', p.ID)
