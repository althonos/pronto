# coding: utf-8

import sys
import six
import os
import unittest
import warnings

from .utils import mock, py2skip, ciskip

# Make sure we're using the local pronto library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pronto


class TestProntoUtils(unittest.TestCase):

    def test_output_str(self):
        """Test function output_str provided by pronto.utils
        """
        @pronto.utils.output_str
        def unicode_returning_function():
            """This function returns str in Py3 and unicode in Py2"""
            return six.u("abc")

        self.assertIsInstance(unicode_returning_function(), str)

    def test_unique_everseen(self):
        """Test function unique_everseen provided by pronto.utils
        """
        self.assertEqual(['a', 'b', 'c', 'd'], list(pronto.utils.unique_everseen("aaaabbbcccaaadd")))

    def test_owlparser_get_id_from_url(self):
        """Test method _get_id_from_url of pronto.parser.owl.OwlXMLParser
        """
        test_values = {
            'http://purl.obolibrary.org/obo/IAO_0000115': 'IAO:0000115',
            'http://purl.obolibrary.org/obo/CL_0002420': 'CL:0002420',
            'http://purl.obolibrary.org/obo/UBERON_0001278': 'UBERON:0001278',
            'http://nmrML.org/nmrCV#NMR:1000001': 'NMR:1000001',
        }
        for k,v in six.iteritems(test_values):
            self.assertEqual(pronto.parser.owl.OwlXMLParser._get_id_from_url(k), v)


class TestTestUtils(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter('ignore')

    def tearDown(self):
        warnings.simplefilter('default')

    def test_ciskip(self):
        """Test the ciskip function of the tests.utils module

        If there is an environment variable called CI with value true
        (as defined in a CI build environment), then the decorated function
        will not even be declared, and a mock function will be created and
        called instead.
        """
        for v,r in ('true', list('test')), ('false', list('estt')):
            with mock.patch.dict('os.environ', {'CI': v}):
                @ciskip
                def sort(l):
                    l.sort()
                l = list("test")
                sort(l)
                self.assertEqual(l, r)

    def test_py2skip(self):
        """Test the py2skip function of the tests.utils module

        If the python version is not 3, then the decorated function
        will not even be declared, and a mock function will be created and
        called instead.
        """
        for v,r in ((2,7,12), list('test')), ((3,5,2), list('estt')):
            with mock.patch('sys.version_info', v):
                @py2skip
                def sort(l):
                    l.sort()
                l = list("test")
                sort(l)
                self.assertEqual(l, r)


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
