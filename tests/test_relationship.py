import itertools
import os
import unittest
import warnings

import pronto
from pronto.relationship import Relationship, RelationshipData

from .utils import DATADIR
from .test_entity import _TestEntitySet


class TestRelationship(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_properties(self):
        """Assert the data stored in data layer can be accessed in the view.
        """
        for r in RelationshipData.__slots__:
            self.assertTrue(hasattr(Relationship, r), f"no property for {r}")

    def test_superproperties(self):
        ont = pronto.Ontology()
        friend_of = ont.create_relationship("friend_of")
        best_friend_of = ont.create_relationship("best_friend_of")
        best_friend_of.superproperties().add(friend_of)
        self.assertIn(friend_of, sorted(best_friend_of.superproperties()))

    def test_subproperties(self):
        ont = pronto.Ontology()
        best_friend_of = ont.create_relationship("best_friend_of")
        friend_of = ont.create_relationship("friend_of")
        friend_of.subproperties().add(best_friend_of)
        self.assertIn(best_friend_of, sorted(friend_of.subproperties()))


class TestRelationshipSet(_TestEntitySet, unittest.TestCase):

    def create_entity(self, ont, id):
        return ont.create_relationship(id)
