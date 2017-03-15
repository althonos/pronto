# coding: utf-8
from __future__ import absolute_import

import unittest
import os
import six
import sys
import warnings
import shutil

try:
    import sphinx
except ImportError:
    sphinx = None

from . import utils
import pronto


### TESTS ###
class TestProntoDocumentation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.build_dir = os.path.join(utils.TESTDIR, "run", "build")
        cls.source_dir = os.path.join(utils.DOCSDIR, "source")
        os.mkdir(os.path.join(utils.TESTDIR, "run"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(utils.TESTDIR, "run"))

    @classmethod
    @unittest.skipUnless(sys.version[:3] in {'3.6', '2.7'},
        "Python {} cannot run Sphinx".format(sys.version[:3]))
    def register_tests(cls):
        """Register tests for most sphinx builders"""
        for builder in ('html', 'latexpdf', 'json', 'man', 'xml'):
            cls.add_test(builder)

    @classmethod
    def add_test(cls, builder):
        def _test(self):
            with utils.mock.patch('sys.stderr', six.moves.StringIO()) as stderr:
                with utils.mock.patch('sys.stdout', six.moves.StringIO()) as stdout:
                    self.assertEquals(0, sphinx.build_main([
                        "-b{}".format(builder),
                        "-d{}".format(os.path.join(self.build_dir, 'doctrees')),
                        self.source_dir,
                        os.path.join(self.build_dir, builder)])
                    )
        setattr(cls, "test_{}".format(builder), _test)


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    #TestProntoDocumentation.register_tests()
    suite.addTests(loader.loadTestsFromTestCase(TestProntoDocumentation))
    return suite
