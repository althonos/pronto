import itertools
import os
import unittest

import pronto
from pronto.relationship import Relationship, _RelationshipData

from .utils import DATADIR



class TestRelationship(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ms = pronto.Ontology(os.path.join(DATADIR, "ms.obo.xz"))

    def test_properties(self):
        """Assert the data stored in `_TermData` can be accessed in `Term`.
        """
        for r in _RelationshipData.__slots__:
            self.assertTrue(hasattr(Relationship, r), f"no property for {r}")
