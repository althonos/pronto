import itertools
import os
import unittest
import warnings

import pronto
from pronto.term import Term, TermData, TermSet

from .utils import DATADIR
from .test_entity import _TestEntitySet


class TestTerm(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        warnings.simplefilter('ignore', category=UnicodeWarning)
        cls.ms = pronto.Ontology(os.path.join(DATADIR, "ms.obo"))

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def setUp(self):
        self.ont = ont = pronto.Ontology()
        self.t1 = ont.create_term("TST:001")
        self.t2 = ont.create_term("TST:002")
        self.t3 = ont.create_term("TST:003")
        self.t4 = ont.create_term("TST:004")
        self.has_part = ont.create_relationship("has_part")

    def test_annotations(self):
        ontology = pronto.Ontology()
        term = ontology.create_term("TST:001")
        term.annotations = {
            pronto.LiteralPropertyValue("http://purl.org/dc/terms/creator", "Martin Larralde")
        }

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
        self.t2.superclasses().add(self.t1)
        self.t3.superclasses().add(self.t1)
        self.t4.superclasses().add(self.t2)
        self.t4.superclasses().add(self.t3)
        self.assertEqual(
            sorted(self.t4.superclasses(with_self=False)),
            [self.t1, self.t2, self.t3]
        )

    def test_superclasses(self):
        term = self.ms["MS:1000200"]
        self.assertSetEqual(
            {sup.id for sup in term.superclasses(with_self=False)},
            {"MS:1000123", "MS:1000489", "MS:1000031"},
        )

    def test_consider(self):
        self.assertEqual(self.t1.consider, TermSet())
        self.t1.consider = {self.t2}
        self.assertEqual(self.t1.consider, TermSet({self.t2}))
        self.t1.consider.clear()
        self.assertEqual(self.t1.consider, TermSet())

    def test_disjoint_from(self):
        self.assertEqual(self.t1.disjoint_from, TermSet())
        self.t1.disjoint_from = {self.t2}
        self.assertEqual(self.t1.disjoint_from, TermSet({self.t2}))

    def test_intersection_of(self):
        self.assertEqual(self.t1.intersection_of, TermSet())
        self.t1.intersection_of = {self.t2, self.t3}
        self.assertEqual(self.t1.intersection_of, {self.t2, self.t3})
        self.t1.intersection_of = {self.t2, (self.has_part, self.t3)}
        self.assertEqual(self.t1.intersection_of, {self.t2, (self.has_part, self.t3)})

    def test_intersection_of_type_error(self):
        with self.assertRaises(TypeError):
            self.t1.intersection_of = {0}

    def test_union_of(self):
        self.t1.union_of = {self.t2, self.t3}
        self.assertEqual(self.t1.union_of, TermSet({self.t2, self.t3}))
        self.assertEqual(self.t1._data().union_of, {self.t2.id, self.t3.id})

    @unittest.skipUnless(__debug__, "no type checking in optimized mode")
    def test_union_of_typechecked(self):
        with self.assertRaises(TypeError):
            self.t1.union_of = 1
        with self.assertRaises(TypeError):
            self.t1.union_of = { 1 }

    def test_union_of_cardinality(self):
        with self.assertRaises(ValueError):
            self.t2.union_of = { self.t1 }

    def test_replaced_by(self):
        self.assertEqual(sorted(self.t1.replaced_by.ids), [])

        self.t1.replaced_by.add(self.t2)
        self.assertEqual(sorted(self.t1.replaced_by.ids), [self.t2.id])
        self.assertEqual(sorted(self.ont[self.t1.id].replaced_by.ids), [self.t2.id])

        self.t1.replaced_by.add(self.t3)
        self.assertEqual(sorted(self.t1.replaced_by.ids), [self.t2.id, self.t3.id])
        self.assertEqual(sorted(self.ont[self.t1.id].replaced_by.ids), [self.t2.id, self.t3.id])

    def test_repr(self):
        self.assertEqual(repr(self.t1), f"Term({self.t1.id!r})")
        self.t1.name = "test"
        self.assertEqual(repr(self.t1), f"Term({self.t1.id!r}, name={self.t1.name!r})")


class TestTermSet(_TestEntitySet, unittest.TestCase):

    def create_entity(self, ont, id):
        return ont.create_term(id)

    def test_subclasses_uniqueness(self):
        self.t2.superclasses().add(self.t1)
        self.t3.superclasses().add(self.t2)

        self.assertEqual(
            self.t1.subclasses().to_set().ids, {self.t1.id, self.t2.id, self.t3.id}
        )
        self.assertEqual(
            self.t2.subclasses().to_set().ids, {self.t2.id, self.t3.id}
        )
        self.assertEqual(
            self.t3.subclasses().to_set().ids, {self.t3.id}
        )

        s = pronto.TermSet({self.t1, self.t2})
        self.assertEqual(
            sorted(t.id for t in s.subclasses(with_self=False)),
            [self.t3.id]
        )
        self.assertEqual(
            sorted(t.id for t in s.subclasses(with_self=True)),
            [self.t1.id, self.t2.id, self.t3.id]
        )

    def test_superclasses_uniqueness(self):
        self.t2.superclasses().add(self.t1)
        self.t3.superclasses().add(self.t1)
        self.t3.superclasses().add(self.t2)

        s = pronto.TermSet({self.t2, self.t3})
        self.assertEqual(
            sorted(t.id for t in s.superclasses(with_self=False)),
            [self.t1.id]
        )
        self.assertEqual(
            sorted(t.id for t in s.superclasses(with_self=True)),
            [self.t1.id, self.t2.id, self.t3.id]
        )

    def test_repr(self):
        s1 = TermSet({self.t1})
        self.assertEqual(repr(s1), f"TermSet({{Term({self.t1.id!r})}})")

        s2 = TermSet({self.t1, self.t2})
        self.assertIn(
            repr(s2),
            [
                f"TermSet({{Term({self.t1.id!r}), Term({self.t2.id!r})}})",
                f"TermSet({{Term({self.t2.id!r}), Term({self.t1.id!r})}})"
            ]
        )
