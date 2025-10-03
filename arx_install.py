from arx_lib.helpers import debug_print

import os, sys, subprocess, shutil, platform, webbrowser
from typing import Optional

is_windows : bool = os.name == 'nt'

file_dir : str = os.path.dirname(os.path.realpath(__file__))
frozen_dir = os.path.dirname(sys.executable)
executable_dir : str = os.path.dirname(os.path.realpath(__file__))
if getattr(sys, 'frozen', False):
    executable_dir = os.path.dirname(sys.executable)
os.chdir(executable_dir)

venv_dir : str = os.path.join(executable_dir, '.venv')

def check_lib(lib: str) -> None:
    venv_python : str = os.path.join(venv_dir, 'Scripts' if is_windows else 'bin', 'python')
    command : list[str] = [venv_python, '-c', f'import {lib}']
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f'Make sure ({lib}) is installed and in your Python environment.')

def system_install() -> None:
    if is_windows:
        chocolatey_path : Optional[str] = shutil.which('choco')
        if chocolatey_path:
            print('(choco) found. Using for install')
        else:
            raise EnvironmentError('Make sure (choco) is installed and on your PATH.')
        subprocess.run([chocolatey_path, 'install', 'llvm', '-y'], check=True)
        subprocess.run([chocolatey_path, 'install', 'mingw', '-y'], check=True)
        print('(system) (success)')
    else:
        packages : list[str] = ['llvm', 'clang', 'gcc']
        apt_path : Optional[str] = shutil.which('apt')
        dnf_path : Optional[str] = shutil.which('dnf')
        pacman_path : Optional[str] = shutil.which('pacman')
        if apt_path:
            print('(apt) found. Using for install')
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y'] + packages, check=True)
        elif dnf_path:
            print('(dnf) found. Using for install')
            subprocess.run(['sudo', 'dnf', 'install', '-y'] + packages, check=True)
        elif pacman_path:
            print('(pacman) found. Using for install')
            subprocess.run(['sudo', 'pacman', '-Syu', '--noconfirm'] + packages, check=True)
        else:
            raise EnvironmentError('Unsupported Linux distribution. Install (llvm) & (clang) & (gcc-libs) & (llvm-libs) manually.')
        print('(system) [info] (gcc-libs) & (llvm-libs) may need to be installed.')
        print('(system) (success)')

def environment_install() -> None:
    if not os.path.exists(venv_dir):
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
        print(f'(environment) at [ {venv_dir} ]')

    pip_path : str = os.path.join(venv_dir, 'Scripts' if is_windows else 'bin', 'pip')
    requirements_path : str = os.path.join(executable_dir, 'requirements.txt')
    if os.path.exists(requirements_path):
        subprocess.run([pip_path, 'install', '-r', requirements_path], check=True)
        print('(environment) (success)')
    else:
        raise FileNotFoundError(f'Requirements file not found at [ {requirements_path} ]')

def install_arx() -> None:
    if '--system' in sys.argv:
        print('[system]')
        system_install()
        return
    elif '--environment' in sys.argv:
        print('[environment]')
        environment_install()
        return

    print('[ 1/2 ] (system)')
    system_install()
    print('[ 2/2 ] (environment)')
    environment_install()
    print('(install) (success)')

def check_environment() -> None:
    llc_path : Optional[str] = shutil.which('llc')
    gcc_path : Optional[str] = shutil.which('gcc')
    if (not llc_path):
        print('Make sure (llc) is installed and on your PATH.')
    if (not gcc_path):
        print('Make sure (gcc) is installed and on your PATH.')
    check_lib('llvmlite')
    check_lib('sly')
    print('(check) Check completed check for warnings output above.')


if __name__ == '__main__':
    if '-i' in sys.argv:
        install_arx()
    elif '-c' in sys.argv:
        check_environment()
    else:
        print('Arguments for (arx-install)')
        print('-i  (Both for system and environment) (Must be used or -c)')
        print('--system      (Just system packages)')
        print('--environment (Just venv)')
        print('-c  (Checks install)')
    
