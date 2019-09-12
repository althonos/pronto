# coding: utf-8
from __future__ import absolute_import

import unittest
import os
import six
import sys
import warnings
import shutil

from . import utils
import pronto


build_main = utils.try_import("sphinx.cmd.build:build_main", None)


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
    def register_tests(cls):
        """Register tests for most sphinx builders"""
        for builder in ('html', 'json', 'man', 'xml'):
            cls.add_test(builder)

    @classmethod
    def add_test(cls, builder):

        @unittest.skipUnless(build_main, "Sphinx is not available")
        def _test(self):
            with utils.mock.patch('sys.stderr', six.moves.StringIO()) as stderr:
                with utils.mock.patch('sys.stdout', six.moves.StringIO()) as stdout:
                    self.assertEquals(0, build_main([
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

    TestProntoDocumentation.register_tests()
    tests.addTests(loader.loadTestsFromTestCase(TestProntoDocumentation))
    return tests
