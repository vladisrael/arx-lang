import sys

class ArtemisParserLogger(object):
    def __init__(self):
        self.f = sys.stderr

    def debug(self, msg, *args, **kwargs):
        if '--debug' in sys.argv:
            self.f.write((msg % args) + '\n')

    info = debug

    def warning(self, msg, *args, **kwargs):
        if '--debug' in sys.argv:
            self.f.write('WARNING: ' + (msg % args) + '\n')

    def error(self, msg, *args, **kwargs):
        self.f.write('ERROR: ' + (msg % args) + '\n')

    critical = debug

def debug_print(*values:object) -> None:
    if '--debug' in sys.argv:
        print(*values)
