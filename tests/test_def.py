# coding: utf-8

import unittest

import pronto



class TestDefinition(unittest.TestCase):

    def test_repr(self):
        d1 = pronto.Definition("something")
        self.assertEqual(repr(d1), "Definition('something')")
        d2 = pronto.Definition("something", xrefs={pronto.Xref("Bgee:fbb")})
        self.assertEqual(repr(d2), "Definition('something', xrefs={Xref('Bgee:fbb')})")
