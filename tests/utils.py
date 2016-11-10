import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock

# if os.getcwd().endswith("pronto"):
#     os.chdir("tests")

def ciskip(func):
    """Don't do anything if in CI environment
    """
    if "CI" in os.environ and os.environ["CI"].lower()=="true":
        def _pass(*args, **kwargs):
            pass
        return _pass
    else:
        return func

def py2skip(func):
    """Don't do anything if python version is not 3
    """
    if sys.version_info[0]==3:
        return func
    else:
        def _pass(*args, **kwargs):
            pass
        return _pass
