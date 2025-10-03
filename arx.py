from arx_lib.helpers import debug_print
from arx_lib.builder import build

version_string : str = '[2025.09.26]'

import os, sys, subprocess, shutil, platform, webbrowser
from typing import Optional

is_windows : bool = os.name == 'nt'

file_dir : str = os.path.dirname(os.path.realpath(__file__))
frozen_dir = os.path.dirname(sys.executable)
executable_dir : str = os.path.dirname(os.path.realpath(__file__))
if getattr(sys, 'frozen', False):
    executable_dir = os.path.dirname(sys.executable)
os.chdir(executable_dir)

if __name__ == '__main__':
    print('Artemis (ARX)')
    print('(Vendetta-chan Studios) 2025')
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'version':
                print(version_string)
                print('Python', platform.python_version())
                exit(0)
            case 'site':
                webbrowser.open_new_tab('https://vladimir-sama.github.io/arx-lang/')
                exit(0)
            case 'insight':
                tokei_path : Optional[str] = shutil.which('tokei')
                if (not tokei_path):
                    raise EnvironmentError('Make sure (tokei) is installed and on your PATH.')
                subprocess.run([tokei_path, file_dir])
                exit(0)
            case 'build':
                if len(sys.argv) > 2:
                    if os.path.isfile(sys.argv[2]):
                        print(f'Building [{os.path.basename(sys.argv[2])}]')
                        build(sys.argv[2], executable_dir)
                        exit(0)
                    else:
                        raise FileNotFoundError(f'Input file not found at [ {sys.argv[2]} ]')
        
    print('Usage for (arx)')
    print('- arx version')
    print('- arx build <input.arx>')
    print('- arx insight')