from sly import Lexer

class ArtemisLexer(Lexer):
    # Set of token names
    tokens = {
        FLAG, MANAGED, MANUAL, USING,
        INT, FLOAT, LIST, STR, ANY, VOID, CLASS, SELF, BOOL,
        TRUE, FALSE,
        ID, NUMBER, FLOATNUM, STRING,
        EQEQ, NOTEQ, LTEQ, GTEQ, LT, GT,
        PLUS, MINUS, TIMES, DIVIDE,
        ASSIGN, COLON, COMMA, IF, ELSE, FOR, IN,
        LBRACE, RBRACE, LPAREN, RPAREN, LBRACKET, RBRACKET, DOT, RETURN,
    }

    # String containing ignored characters between tokens
    ignore = ' \t'

    ignore_comment = r'//.*'


    # Track line numbers for error reporting
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    # Operators and punctuation
    EQEQ = r'=='
    NOTEQ = r'!='
    LTEQ = r'<='
    GTEQ = r'>='
    LT   = r'<'
    GT   = r'>'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    ASSIGN = r'='
    COLON = r':'
    COMMA = r','
    DOT = r'\.'

    LBRACE = r'\{'
    RBRACE = r'\}'
    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACKET = r'\['
    RBRACKET = r'\]'

    # Identifiers (variable names, function names, types except keywords)
    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def ID(self, t):
        keywords = {
            'flag' : 'FLAG',
            'managed' : 'MANAGED',
            'manual' : 'MANUAL',
            'using' : 'USING',
            'int' : 'INT',
            'float' : 'FLOAT',
            'string' : 'STR',
            'list' : 'LIST',
            'any' : 'ANY',
            'void' : 'VOID',
            'class' : 'CLASS',
            'self' : 'SELF',
            'true' : 'TRUE',
            'false' : 'FALSE',
            'return' : 'RETURN',
            'bool' : 'BOOL',
            'if' : 'IF',
            'else' : 'ELSE',
            'for' : 'FOR',
            'in' : 'IN'
        }
        t.type = keywords.get(t.value, 'ID')
        return t

    # Numbers: float
    @_(r'\d+\.\d+')
    def FLOATNUM(self, t):
        t.value = float(t.value)
        return t

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r"'([^\\']|\\.)*'")
    def STRING(self, t):
        raw = t.value[1:-1]  # Strip the single quotes
        # Decode escape sequences: \n, \t, \\, etc.
        t.value = bytes(raw, 'utf-8').decode('unicode_escape')
        return t

    # Error handling
    def error(self, t):
        print(f'Illegal character {t.value[0]!r} at line {self.lineno}')
        self.index += 1

