from arx_lib.helpers import debug_print
from arx_lib.builder import build

version_string : str = '[2025.09.11]'

import os, sys, subprocess, shutil, platform
from typing import List, Tuple, Set, Dict, Optional

is_windows : bool = os.name == 'nt'

file_dir : str = os.path.dirname(os.path.realpath(__file__))
frozen_dir = os.path.dirname(sys.executable)
executable_dir : str = os.path.dirname(os.path.realpath(__file__))
if getattr(sys, 'frozen', False):
    executable_dir = os.path.dirname(sys.executable)
os.chdir(executable_dir)

def check_environment() -> None:
    llc_path : Optional[str] = shutil.which('llc')
    gcc_path : Optional[str] = shutil.which('gcc')
    if (not llc_path):
        print('Make sure (llc) is installed and on your PATH.')
        return
    if (not gcc_path):
        print('Make sure (gcc) is installed and on your PATH.')
        return
    if (not llc_path) and (not gcc_path):
        raise EnvironmentError('Make sure (llc) and (gcc) are installed and on your PATH.')
    print('Both (llc) and (gcc) were found in PATH')


if __name__ == '__main__':
    print('Artemis (ARX)')
    print('(Vendetta-chan Studios) 2025')
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'version':
                print(version_string)
                print('Python', platform.python_version())
                exit(0)
            case 'insight':
                tokei_path : Optional[str] = shutil.which('tokei')
                if (not tokei_path):
                    raise EnvironmentError('Make sure (tokei) is installed and on your PATH.')
                subprocess.run([tokei_path, file_dir])
                exit(0)
            case 'environment':
                check_environment()
                exit(0)
            case 'build':
                if len(sys.argv) > 2:
                    if os.path.isfile(sys.argv[2]):
                        print(f'Building [{os.path.basename(sys.argv[2])}]')
                        build(sys.argv[2], executable_dir)
                        exit(0)
                    else:
                        raise FileNotFoundError(f'Input file not found at [ {sys.argv[2]} ]')
            case 'install':
                if is_windows:
                    chocolatey_path : Optional[str] = shutil.which('choco')
                    if (not chocolatey_path):
                        raise EnvironmentError('Make sure (choco) is installed and on your PATH.')
                    subprocess.run([chocolatey_path, 'install', 'llvm', '-y'], check=True)
                    subprocess.run([chocolatey_path, 'install', 'mingw', '-y'], check=True)
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
                    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', os.path.abspath('requirements.txt')], check=True)
                    print('Windows install success')
                else:
                    print('Linux not implemented')
                exit(0)
        
    print('Usage for (arx)')
    print('- arx version')
    print('- arx environment')
    print('- arx install')
    print('- arx build <input.arx>')
    print('- arx insight')