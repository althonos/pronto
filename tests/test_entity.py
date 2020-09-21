import abc
import gzip
import io
import contextlib
import os
import re
import shutil
import sys
import textwrap
import unittest
import warnings
from unittest import mock

import pronto
from pronto.entity import EntitySet

from . import utils


class _TestEntitySet(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def create_entity(self, ont):
        return NotImplemented

    def setUp(self):
        self.ont = ont = pronto.Ontology()
        self.t1 = self.create_entity(ont, "TST:001")
        self.t2 = self.create_entity(ont, "TST:002")
        self.t3 = self.create_entity(ont, "TST:003")
        self.t4 = self.create_entity(ont, "TST:004")

    def test_contains(self):
        s = EntitySet({self.t1, self.t2})
        self.assertIn(self.t1, s)
        self.assertIn(self.t2, s)
        self.assertNotIn(self.t3, s)
        self.assertIn(self.ont[self.t1.id], s)
        self.assertIn(self.ont[self.t2.id], s)
        self.assertNotIn(self.ont[self.t3.id], s)

    @unittest.skipUnless(__debug__, "no type checking in optimized mode")
    def test_init_typechecked(self):
        self.assertRaises(TypeError, EntitySet, {1, 2})
        self.assertRaises(TypeError, EntitySet, {"a", "b"})
        self.assertRaises(TypeError, EntitySet, {self.t1, "a"})

    def test_add_empty(self):
        s1 = EntitySet()
        self.assertEqual(len(s1), 0)

        s1.add(self.t1)
        s1.add(self.t2)
        self.assertEqual(len(s1), 2)

        self.assertIn(s1.pop(), {self.t1, self.t2})
        self.assertIn(s1.pop(), {self.t1, self.t2})

    def test_and(self):
        s1 = EntitySet((self.t2, self.t1))
        s = s1 & EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t2.id])
        self.assertIsNot(s._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s = s2 & {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t2.id])
        self.assertIsNot(s._ontology, None)

        s3 = EntitySet()
        s = s3 & {}
        self.assertEqual(sorted(s.ids), [])
        self.assertIs(s._ontology, None)

    def test_or(self):
        s1 = EntitySet((self.t2, self.t1))
        s = s1 | EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s = s2 | {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s3 = EntitySet()
        s = s3 | EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s4 = EntitySet()
        s = s4 | {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

    def test_sub(self):
        s1 = EntitySet((self.t2, self.t1))
        s = s1 - EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t1.id])
        self.assertIsNot(s._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s = s2 - {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t1.id])
        self.assertIsNot(s._ontology, None)

        s3 = EntitySet()
        s = s3 - EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [])
        self.assertIs(s._ontology, None)

        s4 = EntitySet()
        s = s4 - {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [])
        self.assertIs(s._ontology, None)

    def test_xor(self):
        s1 = EntitySet((self.t2, self.t1))
        s = s1 ^ EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s = s2 ^ {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s3 = EntitySet()
        s = s3 ^ EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s4 = EntitySet({self.t2, self.t3})
        s = s4 ^ s4
        self.assertEqual(sorted(s.ids), [])
        self.assertIs(s._ontology, None)

    def test_inplace_and(self):
        s1 = EntitySet((self.t2, self.t1))
        s1 &= EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s1.ids), [self.t2.id])
        self.assertIsNot(s1._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s2 &= {self.t2, self.t3}
        self.assertEqual(sorted(s2.ids), [self.t2.id])
        self.assertIsNot(s2._ontology, None)

        s3 = EntitySet()
        s3 &= {}
        self.assertEqual(sorted(s3.ids), [])
        self.assertIs(s3._ontology, None)

    def test_inplace_or(self):
        s1 = EntitySet((self.t2, self.t1))
        s1 |= EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s1.ids), [self.t1.id, self.t2.id, self.t3.id])
        self.assertIsNot(s1._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s2 |= {self.t2, self.t3}
        self.assertEqual(sorted(s2.ids), [self.t1.id, self.t2.id, self.t3.id])
        self.assertIsNot(s2._ontology, None)

        s3 = EntitySet()
        s3 |= EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s3.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s3._ontology, None)

        s4 = EntitySet()
        s4 |= {self.t2, self.t3}
        self.assertEqual(sorted(s4.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s4._ontology, None)

    def test_inplace_xor(self):
        s1 = EntitySet((self.t2, self.t1))
        s = s1 ^ EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s = s2 ^ {self.t2, self.t3}
        self.assertEqual(sorted(s.ids), [self.t1.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s3 = EntitySet()
        s = s3 ^ EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s.ids), [self.t2.id, self.t3.id])
        self.assertIsNot(s._ontology, None)

        s4 = EntitySet({self.t2, self.t3})
        s = s4 ^ s4
        self.assertEqual(sorted(s.ids), [])
        self.assertIs(s._ontology, None)

    def test_inplace_sub(self):
        s1 = EntitySet((self.t2, self.t1))
        s1 -= EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s1.ids), [self.t1.id])
        self.assertIsNot(s1._ontology, None)

        s2 = EntitySet((self.t2, self.t1))
        s2 -= {self.t2, self.t3}
        self.assertEqual(sorted(s2.ids), [self.t1.id])
        self.assertIsNot(s2._ontology, None)

        s3 = EntitySet()
        s3 -= EntitySet((self.t2, self.t3))
        self.assertEqual(sorted(s3.ids), [])
        self.assertIs(s3._ontology, None)

        s4 = EntitySet()
        s4 -= {self.t2, self.t3}
        self.assertEqual(sorted(s4.ids), [])
        self.assertIs(s4._ontology, None)


class TestAlternateIDs(unittest.TestCase):

    def test_length(self):
        path = os.path.join(utils.DATADIR, "hp.obo")
        hp = pronto.Ontology(path, import_depth=0, threads=1)
        self.assertEqual(len(hp["HP:0009882"].alternate_ids), 10)
