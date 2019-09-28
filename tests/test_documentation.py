# coding: utf-8
from __future__ import absolute_import

import unittest
import os
import six
import sys
import warnings
import shutil
from unittest import mock

from . import utils
import pronto


build_main = utils.try_import("sphinx.cmd.build:build_main", None)


class TestProntoDocumentation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.build_dir = os.path.join(utils.TESTDIR, "run", "build")
        cls.source_dir = os.path.join(utils.DOCSDIR, "source")
        os.makedirs(os.path.join(utils.TESTDIR, "run"), exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(utils.TESTDIR, "run"))

    def assertBuilds(self, format):
        with mock.patch('sys.stderr', six.moves.StringIO()) as stderr:
            with mock.patch('sys.stdout', six.moves.StringIO()) as stdout:
                self.assertEquals(0, build_main([
                    "-b{}".format(format),
                    "-d{}".format(os.path.join(self.build_dir, 'doctrees')),
                    self.source_dir,
                    os.path.join(self.build_dir, format)]),
                    "sphinx exited with non-zero return code",
                )

    def test_html(self):
        self.assertBuilds("html")

    def test_json(self):
        self.assertBuilds("json")

    def test_man(self):
        self.assertBuilds("man")

    def test_xml(self):
        self.assertBuilds("xml")


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
