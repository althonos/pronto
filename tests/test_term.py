import itertools
import os
import unittest

import pronto
from pronto.term import Term, _TermData

from .utils import DATADIR



class TestTerm(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ms = pronto.Ontology(os.path.join(DATADIR, "ms.obo.xz"))

    def test_properties(self):
        """Assert the data stored in `_TermData` can be accessed in `Term`.
        """
        for t in _TermData.__slots__:
            self.assertTrue(hasattr(Term, t), f"no property for {t}")

    def test_subclasses(self):
        """Assert `subclasses` does not yield the same `Term` several times.
        """
        term = self.ms['MS:1003025']
        self.assertSetEqual(
            {sup.id for sup in term.subclasses()},
            {'MS:1003025', 'MS:1003026', 'MS:1003027', 'MS:1003021', 'MS:1003022'},
        )

    def test_subclasses_uniqueness(self):
        for term in itertools.islice(self.ms.terms(), 10):
            subclasses = list(term.subclasses())
            self.assertCountEqual(subclasses, set(subclasses))

    def test_superclasses(self):
        """Assert `superclasses` does not yield the same `Term` several times.
        """
        term = self.ms['MS:1000200']
        self.assertSetEqual(
            {sup.id for sup in term.superclasses()},
            {'MS:1000200', 'MS:1000123', 'MS:1000489', 'MS:1000031'},
        )

    def test_superclasses_uniqueness(self):
        for term in self.ms.terms():
            superclasses = list(term.superclasses())
            self.assertCountEqual(superclasses, set(superclasses))
