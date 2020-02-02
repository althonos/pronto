import itertools
import os
import unittest
import warnings

import pronto
from pronto.term import Term, TermData, TermSet

from .utils import DATADIR


class TestTerm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        warnings.simplefilter('ignore', category=UnicodeWarning)
        cls.file = open(os.path.join(DATADIR, "ms.obo"), "rb")
        cls.ms = pronto.Ontology(cls.file)

    @classmethod
    def tearDownClass(cls):
        cls.file.close()
        warnings.simplefilter(warnings.defaultaction)

    def test_add_synonym(self):
        term = self.ms["MS:1000031"]
        s = term.add_synonym('instrument type')
        self.assertIn(s, term.synonyms)

    def test_add_synonym_invalid_scope(self):
        term = self.ms["MS:1000031"]
        with self.assertRaises(ValueError):
            s = term.add_synonym('instrument type', scope="NONSENSE")

    def test_add_synonym_invalid_type(self):
        term = self.ms["MS:1000031"]
        st = pronto.SynonymType("undeclared", "an undeclared synonym type")
        with self.assertRaises(ValueError):
            s = term.add_synonym('instrument type', type=st)

    def test_properties(self):
        for t in TermData.__slots__:
            self.assertTrue(hasattr(Term, t), f"no property for {t}")

    def test_subclasses(self):
        term = self.ms["MS:1003025"]
        self.assertSetEqual(
            {sub.id for sub in term.subclasses()},
            {"MS:1003025", "MS:1003026", "MS:1003027", "MS:1003021", "MS:1003022"},
        )

    def test_subclasses_distance(self):
        term = self.ms["MS:1000031"]
        self.assertSetEqual(set(term.subclasses(0)), {term})
        self.assertSetEqual(
            {sub.id for sub in term.subclasses(1)},
            {
                "MS:1000031",
                "MS:1000490",
                "MS:1000495",
                "MS:1000122",
                "MS:1000491",
                "MS:1000488",
                "MS:1001800",
                "MS:1000121",
                "MS:1000124",
                "MS:1000483",
                "MS:1000489",
                "MS:1000126",
            },
        )

    def test_subclasses_uniqueness(self):
        for term in itertools.islice(self.ms.terms(), 10):
            subclasses = list(term.subclasses())
            self.assertCountEqual(subclasses, set(subclasses))

    def test_subclasses_without_self(self):
        term = self.ms["MS:1003025"]
        self.assertSetEqual(
            {sub.id for sub in term.subclasses(with_self=False)},
            {"MS:1003026", "MS:1003027", "MS:1003021", "MS:1003022"},
        )

    def test_superclasses(self):
        term = self.ms["MS:1000200"]
        self.assertSetEqual(
            {sup.id for sup in term.superclasses()},
            {"MS:1000200", "MS:1000123", "MS:1000489", "MS:1000031"},
        )

    def test_superclasses_distance(self):
        term = self.ms["MS:1000200"]
        scls = ["MS:1000200", "MS:1000123", "MS:1000489", "MS:1000031"]
        for i in range(len(scls)):
            self.assertSetEqual(
                {sup.id for sup in term.superclasses(i)}, set(scls[: i + 1])
            )

    def test_superclasses_uniqueness(self):
        for term in self.ms.terms():
            superclasses = list(term.superclasses())
            self.assertCountEqual(superclasses, set(superclasses))

    def test_superclasses(self):
        term = self.ms["MS:1000200"]
        self.assertSetEqual(
            {sup.id for sup in term.superclasses(with_self=False)},
            {"MS:1000123", "MS:1000489", "MS:1000031"},
        )

    @unittest.skipUnless(__debug__, "no type checking in optimized mode")
    def test_union_of_typechecked(self):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        with self.assertRaises(TypeError):
            t1.union_of = 1
        with self.assertRaises(TypeError):
            t1.union_of = { 1 }

    def test_union_of_cardinality(self):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        t2 = ont.create_term("TST:002")
        with self.assertRaises(ValueError):
            t2.union_of = { t1 }

    def test_replaced_by(self):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        t2 = ont.create_term("TST:002")
        t3 = ont.create_term("TST:003")

        self.assertEqual(sorted(t1.replaced_by.ids), [])

        t1.replaced_by.add(t2)
        self.assertEqual(sorted(t1.replaced_by.ids), ["TST:002"])
        self.assertEqual(sorted(ont["TST:001"].replaced_by.ids), ["TST:002"])

        t1.replaced_by.add(t3)
        self.assertEqual(sorted(t1.replaced_by.ids), ["TST:002", "TST:003"])
        self.assertEqual(sorted(ont["TST:001"].replaced_by.ids), ["TST:002", "TST:003"])


class TestTermSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        warnings.simplefilter('ignore', category=UnicodeWarning)
        cls.file = open(os.path.join(DATADIR, "ms.obo"), "rb")
        cls.ms = pronto.Ontology(cls.file)

    def test_inplace_and(self):
        s1 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s1 &= TermSet((self.ms['MS:1000015'], self.ms['MS:1000016']))
        self.assertEqual(sorted(s1.ids), ['MS:1000015'])
        self.assertIsNot(s1._ontology, None)

        s2 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s2 &= {self.ms['MS:1000015'], self.ms['MS:1000016']}
        self.assertEqual(sorted(s2.ids), ['MS:1000015'])
        self.assertIsNot(s2._ontology, None)

        s3 = TermSet()
        s3 &= {}
        self.assertEqual(sorted(s3.ids), [])
        self.assertIs(s3._ontology, None)

    def test_inplace_or(self):
        s1 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s1 |= TermSet((self.ms['MS:1000015'], self.ms['MS:1000016']))
        self.assertEqual(sorted(s1.ids), ['MS:1000014', 'MS:1000015', 'MS:1000016'])
        self.assertIsNot(s1._ontology, None)

        s2 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s2 |= {self.ms['MS:1000015'], self.ms['MS:1000016']}
        self.assertEqual(sorted(s2.ids), ['MS:1000014', 'MS:1000015', 'MS:1000016'])
        self.assertIsNot(s2._ontology, None)

        s3 = TermSet()
        s3 |= TermSet((self.ms['MS:1000015'], self.ms['MS:1000016']))
        self.assertEqual(sorted(s3.ids), ['MS:1000015', 'MS:1000016'])
        self.assertIsNot(s3._ontology, None)

        s4 = TermSet()
        s4 |= {self.ms['MS:1000015'], self.ms['MS:1000016']}
        self.assertEqual(sorted(s4.ids), ['MS:1000015', 'MS:1000016'])
        self.assertIsNot(s4._ontology, None)

    def test_inplace_sub(self):
        s1 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s1 -= TermSet((self.ms['MS:1000015'], self.ms['MS:1000016']))
        self.assertEqual(sorted(s1.ids), ['MS:1000014'])
        self.assertIsNot(s1._ontology, None)

        s2 = TermSet((self.ms['MS:1000015'], self.ms['MS:1000014']))
        s2 -= {self.ms['MS:1000015'], self.ms['MS:1000016']}
        self.assertEqual(sorted(s2.ids), ['MS:1000014'])
        self.assertIsNot(s2._ontology, None)

        s3 = TermSet()
        s3 -= TermSet((self.ms['MS:1000015'], self.ms['MS:1000016']))
        self.assertEqual(sorted(s3.ids), [])
        self.assertIs(s3._ontology, None)

        s4 = TermSet()
        s4 -= {self.ms['MS:1000015'], self.ms['MS:1000016']}
        self.assertEqual(sorted(s4.ids), [])
        self.assertIs(s4._ontology, None)
