import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock

TESTDIR = os.path.dirname(os.path.abspath(__file__))
MAINDIR = os.path.dirname(TESTDIR)
DOCSDIR = os.path.join(MAINDIR, "docs")

