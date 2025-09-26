from arx_lib.lexer import ArtemisLexer
from arx_lib.parser import ArtemisParser
from arx_lib.compiler import ArtemisCompiler
from arx_lib.data_classes import ArtemisData
from arx_lib.helpers import debug_print

import os, sys, subprocess, shutil, platform
from typing import List, Tuple, Set, Dict, Optional

is_windows : bool = os.name == 'nt'

def build(file_in:str, executable_dir:str) -> None:
    with open(file_in) as f:
        file_contents : str = f.read()

    map_paths : Set[str] = set()
    map_paths.add(os.path.join(executable_dir, 'c_map'))

    compiler_data : ArtemisData = ArtemisData(map_paths)

    compiler : ArtemisCompiler = ArtemisCompiler(compiler_data)
    module : str = compiler.compile_exec(file_in)


    llc_path : Optional[str] = shutil.which('llc')
    gcc_path : Optional[str] = shutil.which('gcc')

    if (not llc_path):
        raise EnvironmentError('Make sure (llc) is installed and on your PATH.')
    if (not gcc_path):
        raise EnvironmentError('Make sure (gcc) is installed and on your PATH.')

    os.makedirs(os.path.join(executable_dir, 'build'), exist_ok=True)
    os.makedirs(os.path.join(executable_dir, 'out'), exist_ok=True)

    object_extension : str = '.obj' if is_windows else '.o'
    out_ll : str = os.path.join(executable_dir, 'build', os.path.basename(file_in).rsplit('.', 1)[0] + '.ll')
    out_o : str = out_ll.rsplit('.', 1)[0] + object_extension
    with open(out_ll, 'w') as f:
        f.write(module)
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
    print(f'Built at [ {out_executable} ]')