import unittest
import warnings

import pronto
from pronto import SynonymType


class TestSynonymType(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def assertHashEqual(self, x, y):
        self.assertEqual(
            hash(x),
            hash(y),
            "hash({!r}) != hash({!r})".format(x, y)
        )

    def test_init_invalid_scope(self):
        with self.assertRaises(ValueError):
            _s = SynonymType(id="other", description="", scope="INVALID")

    def test_eq(self):
        # self == self
        s1 = SynonymType("other", "")
        self.assertEqual(s1, s1)
        # self == other if self.id == other.id
        s2 = SynonymType("other", "something else")
        self.assertEqual(s1, s2)
        # self != anything not a synonym type
        self.assertNotEqual(s1, 1)

    def test_lt(self):
        self.assertLess(SynonymType("a", "a"), SynonymType("b", "b"))
        self.assertLess(SynonymType("a", "a"), SynonymType("a", "b"))
        with self.assertRaises(TypeError):
            SynonymType("a", "a") < 2

    def test_hash(self):
        s1 = SynonymType("other", "")
        s2 = SynonymType("other", "something else")
        self.assertEqual(hash(s1), hash(s2), )


class TestSynonym(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_scope_invalid(self):
        ont = pronto.Ontology()
        term = ont.create_term("TEST:001")
        syn = term.add_synonym("something", scope="EXACT")
        with self.assertRaises(ValueError):
            syn.scope = "NONSENSE"

    def test_type(self):
        ont = pronto.Ontology()
        ty1 = pronto.SynonymType("declared", "a declared synonym type")
        ont.metadata.synonymtypedefs.add(ty1)
        term = ont.create_term("TEST:001")
        term.add_synonym("something", type=ty1)

    def test_type_undeclared(self):
        ont = pronto.Ontology()
        t1 = pronto.SynonymType("undeclared", "an undeclared synonym type")
        term = ont.create_term("TEST:001")
        with self.assertRaises(ValueError):
            term.add_synonym("something", type=t1)

    def test_type_setter(self):
        ont = pronto.Ontology()
        ty1 = pronto.SynonymType("declared", "a declared synonym type")
        ont.metadata.synonymtypedefs.add(ty1)
        term = ont.create_term("TEST:001")
        syn1 = term.add_synonym("something")
        self.assertIsNone(syn1.type)
        syn1.type = ty1
        self.assertEqual(syn1.type, ty1)

    def test_type_setter_undeclared(self):
        ont = pronto.Ontology()
        ty1 = pronto.SynonymType("undeclared", "an undeclared synonym type")
        term = ont.create_term("TEST:001")
        syn1 = term.add_synonym("something")
        self.assertIsNone(syn1.type)
        with self.assertRaises(ValueError):
            syn1.type = ty1
