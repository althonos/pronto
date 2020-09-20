# coding: utf-8
from __future__ import absolute_import

import io
import unittest
import os
import sys
import warnings
import shutil
from unittest import mock

from . import utils
import pronto


build_main = utils.try_import("sphinx.cmd.build:build_main", None)
within_ci = os.getenv("CI", "false") == "true"


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
        with mock.patch("sys.stderr", io.StringIO()) as stderr:
            with mock.patch("sys.stdout", io.StringIO()) as stdout:
                res = build_main(
                    [
                        "-b{}".format(format),
                        "-d{}".format(os.path.join(self.build_dir, "doctrees")),
                        self.source_dir,
                        os.path.join(self.build_dir, format),
                    ]
                )
        if res != 0:
            print(stdout.getvalue())
            print(stderr.getvalue())
        self.assertEqual(res, 0, "sphinx exited with non-zero exit code")

    @unittest.skipUnless(build_main, "sphinx not available")
    @unittest.skipUnless(within_ci, "only build docs in CI")
    def test_html(self):
        self.assertBuilds("html")

    @unittest.skipUnless(build_main, "sphinx not available")
    @unittest.skipUnless(within_ci, "only build docs in CI")
    def test_json(self):
        self.assertBuilds("json")

    @unittest.skipUnless(build_main, "sphinx not available")
    @unittest.skipUnless(within_ci, "only build docs in CI")
    def test_xml(self):
        self.assertBuilds("xml")


def setUpModule():
    warnings.simplefilter("ignore")


def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
