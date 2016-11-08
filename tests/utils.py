import os
import pip
import sys


# if os.getcwd().endswith("pronto"):
#     os.chdir("tests")

def ciskip(func):
    if "CI" in os.environ and os.environ["CI"].lower()=="true":
        def _pass(*args, **kwargs):
            pass
        return _pass
    else:
        return func

def py2skip(func):
    if sys.version_info[0]==3:
        return func
    else:
        def _pass(*args, **kwargs):
            pass
        return _pass
