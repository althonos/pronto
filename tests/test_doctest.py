# coding: utf-8
"""Test doctest contained tests in every file of the module.
"""

import configparser
import doctest
import importlib
import os
import pkgutil
import re
import sys
import shutil
import types
import warnings
from unittest import mock

import pronto
import pronto.parsers

from . import utils

def get_packages():
    parser = configparser.ConfigParser()
    cfg_path = os.path.realpath(os.path.join(__file__, '..', '..', 'setup.cfg'))
    parser.read(cfg_path)
    return parser.get('options', 'packages').split()

def _load_tests_from_module(tests, module, globs, setUp=None, tearDown=None):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith("_")):
        if isinstance(attr, types.ModuleType) and attr.__name__.startswith("pronto"):
            suite = doctest.DocTestSuite(attr, globs, setUp=setUp, tearDown=tearDown, optionflags=+doctest.ELLIPSIS)
            tests.addTests(suite)
    return tests


def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""

    def setUp(self):
        warnings.simplefilter("ignore")
        self.rundir = os.getcwd()
        self.datadir = os.path.realpath(os.path.join(__file__, "..", "data"))
        os.chdir(self.datadir)

        Ontology = pronto.Ontology
        _from_obo_library = Ontology.from_obo_library
        _cache = {}

        def from_obo_library(name):
            if name not in _cache:
                if os.path.exists(os.path.join(utils.DATADIR, name)):
                    _cache[name] = Ontology(os.path.join(utils.DATADIR, name), threads=1)
                else:
                    _cache[name] = _from_obo_library(name)
            return _cache[name]

        self.m = mock.patch("pronto.Ontology.from_obo_library", from_obo_library)
        self.m.__enter__()

    def tearDown(self):
        self.m.__exit__(None, None, None)
        os.chdir(self.rundir)
        warnings.simplefilter(warnings.defaultaction)

    # doctests are not compatible with `green`, so we may want to bail out
    # early if `green` is running the tests
    if sys.argv[0].endswith("green"):
        return tests

    # recursively traverse all library submodules and load tests from them
    packages = [None, pronto]
    for pkg in iter(packages.pop, None):
        for (_, subpkgname, subispkg) in pkgutil.walk_packages(pkg.__path__):
            # import the submodule and add it to the tests
            module = importlib.import_module(".".join([pkg.__name__, subpkgname]))
            globs = dict(pronto=pronto, **module.__dict__)
            tests.addTests(
                doctest.DocTestSuite(
                    module,
                    globs=globs,
                    setUp=setUp,
                    tearDown=tearDown,
                    optionflags=+doctest.ELLIPSIS,
                )
            )
            # if the submodule is a package, we need to process its submodules
            # as well, so we add it to the package queue
            if subispkg and subpkgname != "tests":
                packages.append(module)

    return tests