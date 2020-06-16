import os
import sys
import pickle
import unittest
import warnings

import pronto
from pronto.logic.lineage import Lineage

from .utils import DATADIR


class TestOntology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        warnings.simplefilter('ignore', category=UnicodeWarning)
        warnings.simplefilter('ignore', category=ResourceWarning)
        with open(os.path.join(DATADIR, "ms.obo"), "rb") as f:
            cls.ms = pronto.Ontology(f)

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_inheritance_caching(self):
        ont = pronto.Ontology()
        self.assertEqual(ont._inheritance, {})

        t1 = ont.create_term("TST:001")
        self.assertEqual(ont._inheritance, {t1.id: Lineage()})

        t2 = ont.create_term("TST:002")
        self.assertEqual(ont._inheritance, {t1.id: Lineage(), t2.id: Lineage()})

        t2.superclasses().add(t1)
        self.assertEqual(ont._inheritance, {
            t1.id: Lineage(sub={t2.id}),
            t2.id: Lineage(sup={t1.id})
        })

        t2.superclasses().clear()
        self.assertEqual(ont._inheritance, {t1.id: Lineage(), t2.id: Lineage()})


class TestPickling(object):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        warnings.simplefilter('ignore', category=UnicodeWarning)
        with open(os.path.join(DATADIR, "ms.obo"), "rb") as f:
            cls.ms = pronto.Ontology(cls.file)

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    # ------------------------------------------------------------------------

    def _test_memory_pickling(self, protocol):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        t1.name = "first name"

        pickled = pickle.dumps(ont, protocol=protocol)
        unpickled = pickle.loads(pickled)

        self.assertEqual(ont.keys(), unpickled.keys())
        self.assertEqual(ont["TST:001"], unpickled["TST:001"])
        self.assertEqual(ont["TST:001"].name, unpickled["TST:001"].name)

    def test_memory_pickling_3(self):
        self._test_memory_pickling(3)

    def test_memory_pickling_4(self):
        self._test_memory_pickling(4)

    @unittest.skipIf(sys.version_info < (3, 8), "protocol 5 requires Python 3.8+")
    def test_memory_pickling_5(self):
        self._test_memory_pickling(5)

    # ------------------------------------------------------------------------

    def _test_file_pickling(self, protocol):
        pickled = pickle.dumps(self.ms, protocol=protocol)
        unpickled = pickle.loads(pickled)
        self.assertEqual(self.ms.keys(), unpickled.keys())
        for key in self.ms.keys():
            term_ms, term_pickled = self.ms[key]._data(), unpickled[key]._data()
            for attr in term_ms.__annotations__:
                attr_ms = getattr(term_ms, attr)
                attr_pickled = getattr(term_pickled, attr)
                self.assertEqual(attr_ms, attr_pickled)

    def test_file_pickling_3(self):
        self._test_file_pickling(3)

    def test_file_pickling_4(self):
        self._test_file_pickling(4)

    @unittest.skipIf(sys.version_info < (3, 8), "protocol 5 requires Python 3.8+")
    def test_file_pickling_5(self):
        self._test_file_pickling(5)
