# coding: utf-8
"""
Test doctest contained tests in every file of the module.
"""

import os
import sys
import unittest
import doctest
import shutil

import pronto

MODULE_TYPE = type(sys)
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')



def _load_tests_from_module(tests, module, globs, setUp, tearDown):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module)):
        if isinstance(attr, MODULE_TYPE):
            tests.addTests(doctest.DocTestSuite(attr, globs=globs, setUp=setUp, tearDown=tearDown))
    return tests

def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""

    def _setUp(self):
        """setUp method used by the DocTestSuite"""
        self._rundir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run')
        os.mkdir(self._rundir)

    def _tearDown(self):
        """tearDown method used by the DocTestSuite"""
        shutil.rmtree(self._rundir)

    globs = {
        # ontologies
        'nmr': pronto.Ontology('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl', False),
        'ms':  pronto.Ontology('https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo'),
        'uo':  pronto.Ontology(os.path.join(RESOURCES_DIR, "uo.obo"), False),
        'cl':  pronto.Ontology(os.path.join(RESOURCES_DIR, "cl.ont"), False),

        # classes
        'Relationship': pronto.relationship.Relationship,
        'Ontology':     pronto.ontology.Ontology,
        'Term':         pronto.term.Term,
        'TermList':     pronto.term.TermList,
    }

    tests = _load_tests_from_module(tests, pronto, globs, _setUp, _tearDown)   
    return tests

