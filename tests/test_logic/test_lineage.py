import io
import operator
import os
import unittest
import warnings
import xml.etree.ElementTree as etree

import pronto
from pronto.logic import lineage


class TestLineage(unittest.TestCase):

    def test_eq(self):
        self.assertEqual(lineage.Lineage(), lineage.Lineage())
        self.assertEqual(lineage.Lineage(sub={"a"}), lineage.Lineage(sub={"a"}))
        self.assertNotEqual(lineage.Lineage(sub={"a"}), lineage.Lineage(sub={"b"}))
        self.assertNotEqual(lineage.Lineage(), object())


class TestSubclassesIterator(unittest.TestCase):

    def test_empty(self):
        self.assertListEqual(list(lineage.SubclassesIterator().to_set()), [])
        self.assertListEqual(list(lineage.SubclassesIterator()), [])
        self.assertEqual(operator.length_hint(lineage.SubclassesIterator()), 0)


class TestSuperclassesIterator(unittest.TestCase):

    def test_empty(self):
        self.assertListEqual(list(lineage.SuperclassesIterator()), [])
        self.assertListEqual(list(lineage.SuperclassesIterator().to_set()), [])
        self.assertEqual(operator.length_hint(lineage.SuperclassesIterator()), 0)
