import itertools
import os
import unittest

import pronto
from pronto.relationship import Relationship, RelationshipData

from .utils import DATADIR


class TestRelationship(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ms = pronto.Ontology(os.path.join(DATADIR, "ms.obo.xz"))

    def test_properties(self):
        """Assert the data stored in data layer can be accessed in the view.
        """
        for r in RelationshipData.__slots__:
            self.assertTrue(hasattr(Relationship, r), f"no property for {r}")
