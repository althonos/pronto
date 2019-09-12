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


def _load_tests_from_module(tests, module, globs, setUp, tearDown):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith('_')):
        if isinstance(attr, types.ModuleType):
            suite = doctest.DocTestSuite(attr, globs=globs, setUp=setUp, tearDown=tearDown)
            tests.addTests(suite)
    return tests


def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""

    def _setUp(self):
        self._starting_dir = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._rundir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run')
        os.mkdir(self._rundir)

    def _tearDown(self):
        os.chdir(self._starting_dir)
        shutil.rmtree(self._rundir)

    globs = {
        'Relationship': pronto.Relationship,
        'Ontology':     pronto.Ontology,
        'Term':         pronto.Term,
    }

    if not sys.argv[0].endswith('green'):
        tests = _load_tests_from_module(tests, pronto, globs, _setUp, _tearDown)
    return tests


def setUpModule():
    warnings.simplefilter('ignore')


def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
