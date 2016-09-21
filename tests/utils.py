import os
import pip
import sys


if os.getcwd().endswith("pronto"):
    os.chdir("tests")

def require(*packages):

    for package in packages:
        try:
            if not isinstance(package, str):
                import_name, install_name = package
            else:
                import_name = install_name = package
            __import__(import_name)
        except ImportError:
            cmd = ['install', install_name]
            if not hasattr(sys, 'real_prefix'):
                cmd.append('--user')
            pip.main(cmd)

def ciskip(func):

    if "CI" in os.environ and os.environ["CI"]=="true":
        def _pass(*args, **kwargs):
            pass
        return _pass
    else:
        return func


def vprint(*args, **kwargs):
    if '-v' in sys.argv:
        print(*args, **kwargs)
