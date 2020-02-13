import itertools
import os
import unittest
import warnings

import pronto
from pronto.term import Term, TermData, TermSet
from pronto.logic.lineage import Lineage

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

    def test_inheritance_caching(self):
        ont = pronto.Ontology()
        self.assertEqual(ont._inheritance, {})

        t1 = ont.create_term("TST:001")
        self.assertEqual(ont._inheritance, {t1.id: Lineage()})

        t2 = ont.create_term("TST:002")
        self.assertEqual(ont._inheritance, {t1.id: Lineage(), t2.id: Lineage()})

        t2.relationships = { ont["is_a"]: [t1] }
        self.assertEqual(ont._inheritance, {
            t1.id: Lineage(sub={t2.id}),
            t2.id: Lineage(sup={t1.id})
        })

        t2.relationships = {}
        self.assertEqual(ont._inheritance, {t1.id: Lineage(), t2.id: Lineage()})
