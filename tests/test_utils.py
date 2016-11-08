# coding: utf-8

import sys
import six
import os
import time
import functools
import unittest
import contextlib
import importlib
import gzip
import warnings

try:
    from unittest import mock
except ImportError:
    import mock

# Make sure we're using the local pronto library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pronto


class TestProntoOwlParserUtils(unittest.TestCase):
    """Test utils provided by pronto.parser.owl.OwlParser
    """

    def test_get_id_from_url(self):

        test_values = {
            'http://purl.obolibrary.org/obo/IAO_0000115': 'IAO:0000115',
            'http://purl.obolibrary.org/obo/CL_0002420': 'CL:0002420',
            'http://purl.obolibrary.org/obo/UBERON_0001278': 'UBERON:0001278',
            'http://nmrML.org/nmrCV#NMR:1000001': 'NMR:1000001',
        }

        for k,v in six.iteritems(test_values):
            self.assertEqual(pronto.parser.owl.OwlXMLParser._get_id_from_url(k), v)


class TestProntoUtils(unittest.TestCase):

    def test_output_bytes(self):

        @pronto.utils.output_bytes
        def unicode_returning_function():
            """This function returns str in Py3 and unicode in Py2"""
            return u"abc"

        self.assertIsInstance(unicode_returning_function(), str)

    def test_unique_everseen(self):
        self.assertEqual(['a', 'b', 'c', 'd'], list(pronto.utils.unique_everseen("aaaabbbcccaaadd")))


class TestTestUtils(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter('ignore')

    def tearDown(self):
        warnings.simplefilter('default')

    def test_ciskip(self):
        from .utils import ciskip
        for v,r in ('true', list('test')), ('false', list('estt')):
            with mock.patch.dict('os.environ', {'CI': v}):
                @ciskip
                def sort(l):
                    l.sort()
                l = list("test")
                sort(l)
                self.assertEqual(l, r)

    def test_py2skip(self):
        from .utils import py2skip
        for v,r in ((2,7,12), list('test')), ((3,5,2), list('estt')):
            with mock.patch('sys.version_info', v):
                @py2skip
                def sort(l):
                    l.sort()
                l = list("test")
                sort(l)
                self.assertEqual(l, r)
