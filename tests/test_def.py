# coding: utf-8

import unittest
import warnings

import pronto


class TestDefinition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_repr(self):
        d1 = pronto.Definition("something")
        self.assertEqual(repr(d1), "Definition('something')")
        d2 = pronto.Definition("something", xrefs={pronto.Xref("Bgee:fbb")})
        self.assertEqual(repr(d2), "Definition('something', xrefs={Xref('Bgee:fbb')})")
