from arx_lib.lexer import ArtemisLexer
from arx_lib.parser import ArtemisParser
from arx_lib.compiler import ArtemisCompiler
from arx_lib.data_classes import ArtemisData
from arx_lib.helpers import debug_print

version_string : str = '[alpha]'

import os, sys, subprocess, shutil, platform
from typing import List, Tuple, Set, Dict, Optional


file_dir : str = os.path.dirname(os.path.realpath(__file__))
frozen_dir = os.path.dirname(sys.executable)
executable_dir : str = os.path.dirname(os.path.realpath(__file__))
if getattr(sys, 'frozen', False):
    executable_dir = os.path.dirname(sys.executable)
os.chdir(executable_dir)

def build(file_in:str) -> None:
    with open(file_in) as f:
        file_contents : str = f.read()

    map_paths : Set[str] = set()
    map_paths.add(os.path.join(executable_dir, 'c_map'))

    compiler_data : ArtemisData = ArtemisData(map_paths)

    lexer : ArtemisLexer = ArtemisLexer()
    parser : ArtemisParser = ArtemisParser()

    tokens : list = list(lexer.tokenize(file_contents))
    debug_print(tokens)

    ast : tuple = parser.parse(iter(tokens))
    if not ast:
        raise RuntimeError('Parsing failed')
    debug_print(ast)

    using_modules : tuple = [mod[1] for mod in ast[1]]
    debug_print(using_modules)
    functions : tuple = ast[2]

    compiler : ArtemisCompiler = ArtemisCompiler(compiler_data)
    compiler.load_extern_modules(using_modules)

    for fn in functions:
        if fn[0] == 'function':
            compiler.compile_function(fn[1], fn[2], fn[3], fn[4])

    compiler.add_c_main()

    is_windows : bool = os.name == 'nt'
    llc_path : Optional[str] = shutil.which('llc')
    gcc_path : Optional[str] = shutil.which('gcc')

    if (not llc_path):
        raise EnvironmentError('Make sure (llc) are installed and on your PATH.')
    if (not gcc_path):
        raise EnvironmentError('Make sure (gcc) are installed and on your PATH.')

    os.makedirs(os.path.join(executable_dir, 'build'), exist_ok=True)
    os.makedirs(os.path.join(executable_dir, 'out'), exist_ok=True)

    object_extension : str = '.obj' if is_windows else '.o'
    out_ll : str = os.path.join(executable_dir, 'build', os.path.basename(file_in).rsplit('.', 1)[0] + '.ll')
    out_o : str = out_ll.rsplit('.', 1)[0] + object_extension
    with open(out_ll, 'w') as f:
        f.write(str(compiler.module))
    debug_print('[llc]')
    subprocess.run([llc_path, out_ll, '-filetype=obj', '-o', out_o])
    
    final_command : List[str] = [gcc_path, out_o]
    total_libs : int = len(compiler.extern_c) + 1
    for i, c_lib in enumerate(compiler.extern_c):
        print(f'[ {i + 1}/{total_libs} ]' + ' [lib] (' + c_lib + ')')
        subprocess.run([gcc_path, '-c', '-o', os.path.join(executable_dir, 'build', c_lib + object_extension), os.path.join(executable_dir, 'c_lib', c_lib + '.c')])
        final_command.append(
            os.path.join(executable_dir, 'build', c_lib + object_extension)
        )
    print(f'[ {total_libs}/{total_libs} ]' + ' [main]')
    out_executable : str = os.path.join(executable_dir, 'out', os.path.basename(file_in).rsplit('.', 1)[0] + ('.exe' if is_windows else ''))
    subprocess.run(final_command + ['-o', out_executable])
    print('Built at: ' + out_executable)

if __name__ == '__main__':
    print('Artemis (ARX)')
    print('(Vendetta-chan Studios) 2025')
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'version':
                print(version_string)
                print('Python', platform.python_version())
                exit(0)          
            case 'dependencies':
                llc_path : Optional[str] = shutil.which('llc')
                gcc_path : Optional[str] = shutil.which('gcc')
                if (not llc_path):
                    raise EnvironmentError('Make sure (llc) are installed and on your PATH.')
                if (not gcc_path):
                    raise EnvironmentError('Make sure (gcc) are installed and on your PATH.')
                print('Both (llc) and (gcc) were found in PATH')
                exit(0)
            case 'build':
                if len(sys.argv) > 2:
                    if os.path.isfile(sys.argv[2]):
                        print('Building ' + sys.argv[2])
                        build(sys.argv[2])
                        exit(0)
                    else:
                        raise FileNotFoundError(f'Input file not found at: {sys.argv[2]}')
        
    print('Usage for (arx)')
    print('- arx version')
    print('- arx build <input.arx>')