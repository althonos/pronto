# coding: utf-8

import sys
import six
import os
import unittest
import warnings

from . import utils
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


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
