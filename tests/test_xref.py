# coding: utf-8

import unittest

import fastobo
import pronto


class TestXref(unittest.TestCase):

    def setUp(self):
        self.x1 = pronto.Xref("PMC:5392374")
        self.x2 = pronto.Xref("PMC:5392374")
        self.x3 = pronto.Xref("PMC:5706746")

    def test_repr(self):
        x1 = pronto.Xref("PMC:5392374")
        self.assertEqual(repr(x1), "Xref('PMC:5392374')")

    def test_eq(self):
        self.assertTrue(self.x1 == self.x2)
        self.assertFalse(self.x1 == self.x3)
        self.assertFalse(self.x1 == 1)

    def test_ne(self):
        self.assertFalse(self.x1 != self.x2)
        self.assertTrue(self.x1 != self.x3)
        self.assertTrue(self.x1 != 1)

    def test_lt(self):
        self.assertFalse(self.x1 < self.x2)
        self.assertTrue(self.x1 < self.x3)
        with self.assertRaises(TypeError):
            self.x1 < 1

    def test_le(self):
        self.assertTrue(self.x1 <= self.x2)
        self.assertTrue(self.x1 <= self.x3)
        with self.assertRaises(TypeError):
            self.x1 <= 1

    def test_gt(self):
        self.assertFalse(self.x2 > self.x2)
        self.assertTrue(self.x3 > self.x1)
        with self.assertRaises(TypeError):
            self.x1 > 1

    def test_ge(self):
        self.assertTrue(self.x1 >= self.x2)
        self.assertTrue(self.x3 >= self.x1)
        with self.assertRaises(TypeError):
            self.x1 >= 1

    def test_init(self):
        with self.assertRaises(ValueError):
            pronto.Xref("PMC SOMETHING")
        if __debug__:
            with self.assertRaises(TypeError):
                pronto.Xref(1)
            with self.assertRaises(TypeError):
                pronto.Xref("PMC:5392374", 1)

    def test_from_ast(self):
        ast1 = fastobo.xref.Xref(fastobo.id.parse("GO:0099545"))
        x1 = pronto.Xref._from_ast(ast1)
        self.assertEqual(x1.id, "GO:0099545")
        self.assertIs(x1.description, None)

        ast2 = fastobo.xref.Xref(fastobo.id.parse("GO:0099545"), "positive regulation of granuloma formation")
        x2 = pronto.Xref._from_ast(ast2)
        self.assertEqual(x2.id, "GO:0099545")
        self.assertEqual(x2.description, "positive regulation of granuloma formation")
