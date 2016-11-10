# coding: utf-8
"""
Test doctest contained tests in every file of the module.
"""

import os
import sys
import doctest
import shutil
import re
import warnings
import os.path as op


# Make sure we're using the local pronto library
sys.path.insert(0, op.dirname(op.dirname(op.abspath(__file__))))
import pronto

MODULE_TYPE = type(sys)
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


class IgnoreUnicodeChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        if sys.version_info[0] > 2:
            want = re.sub("u'(.*?)'", "'\\1'", want)
            want = re.sub('u"(.*?)"', '"\\1"', want)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


def _load_tests_from_module(tests, module, globs, setUp, tearDown):
    """Load tests from module, iterating through submodules"""
    for attr in (getattr(module, x) for x in dir(module) if not x.startswith('_')):
        if isinstance(attr, MODULE_TYPE):
            tests.addTests(doctest.DocTestSuite(attr, globs=globs,
                setUp=setUp, tearDown=tearDown, checker=IgnoreUnicodeChecker()))
    return tests

def load_tests(loader, tests, ignore):
    """load_test function used by unittest to find the doctests"""

    def _setUp(self):
        """setUp method used by the DocTestSuite"""
        self._starting_dir = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._rundir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'run')
        os.mkdir(self._rundir)

    def _tearDown(self):
        """tearDown method used by the DocTestSuite"""
        os.chdir(self._starting_dir)
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



def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
