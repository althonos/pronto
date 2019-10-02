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
import pronto.parsers

from . import utils


def _load_tests_from_module(tests, module, globs, setUp=None, tearDown=None):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith("_")):
        if isinstance(attr, types.ModuleType):
            suite = doctest.DocTestSuite(attr, globs, setUp=setUp, tearDown=tearDown)
            tests.addTests(suite)
    return tests


def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""

    def setUp(self):
        warnings.simplefilter("ignore")
        self.rundir = os.getcwd()
        self.datadir = os.path.realpath(os.path.join(__file__, "..", "data"))
        os.chdir(self.datadir)

    def tearDown(self):
        os.chdir(self.rundir)
        warnings.simplefilter(warnings.defaultaction)

    globs = {"pronto": pronto}
    if not sys.argv[0].endswith("green"):
        tests = _load_tests_from_module(tests, pronto, globs, setUp, tearDown)
        tests = _load_tests_from_module(tests, pronto.utils, globs, setUp, tearDown)
        tests = _load_tests_from_module(tests, pronto.parsers, globs, setUp, tearDown)
    return tests
