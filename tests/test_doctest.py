# coding: utf-8
"""Test doctest contained tests in every file of the module.
"""

import doctest
import os
import re
import sys
import shutil
import types
import warnings

import pronto

from . import utils


def _load_tests_from_module(tests, module, globs, setUp=None, tearDown=None):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith('_')):
        if isinstance(attr, types.ModuleType):
            suite = doctest.DocTestSuite(attr, globs=globs, setUp=setUp, tearDown=tearDown)
            tests.addTests(suite)
    return tests


def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""
    globs = {'pronto': pronto}
    if not sys.argv[0].endswith('green'):
        tests = _load_tests_from_module(tests, pronto, globs)
    return tests


def setUpModule():
    warnings.simplefilter('ignore')


def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
