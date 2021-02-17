import io
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

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_repr_new(self):
        ont = pronto.Ontology()
        self.assertEqual(repr(ont), "Ontology()")

    def test_repr_path(self):
        path = os.path.join(DATADIR, "pato.obo")
        ont = pronto.Ontology(path)
        self.assertEqual(repr(ont), "Ontology({!r})".format(path))

    def test_repr_path_with_import_depth(self):
        path = os.path.join(DATADIR, "pato.obo")
        ont = pronto.Ontology(path, import_depth=1)
        self.assertEqual(repr(ont), "Ontology({!r}, import_depth=1)".format(path))

    def test_repr_file(self):
        path = os.path.join(DATADIR, "pato.obo")
        with open(path, "rb") as src:
            ont = pronto.Ontology(src)
        self.assertEqual(repr(ont), "Ontology({!r})".format(path))

    def test_repr_file_handle(self):
        path = os.path.join(DATADIR, "pato.obo")
        with open(path, "rb") as src:
            handle = io.BytesIO(src.read())
        ont = pronto.Ontology(handle)
        self.assertEqual(repr(ont), "Ontology({!r})".format(handle))

    def test_threads_invalid(self):
        hp = os.path.join(DATADIR, "hp.obo")
        self.assertRaises(ValueError, pronto.Ontology, hp, threads=-1)
        self.assertRaises(ValueError, pronto.Ontology, hp, threads=0)

    def test_indexing_relationship_warning(self):
        ont = pronto.Ontology()
        ont.create_relationship("brother_of")
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertRaises(DeprecationWarning, ont.__getitem__, "brother_of")


class TestOntologyLineage(unittest.TestCase):
    def test_edit_term(self):
        ont = pronto.Ontology()
        self.assertEqual(ont._terms.lineage, {})

        t1 = ont.create_term("TST:001")
        self.assertEqual(ont._terms.lineage, {t1.id: Lineage()})

        t2 = ont.create_term("TST:002")
        self.assertEqual(ont._terms.lineage, {t1.id: Lineage(), t2.id: Lineage()})

        t2.superclasses().add(t1)
        self.assertEqual(ont._terms.lineage, {
            t1.id: Lineage(sub={t2.id}),
            t2.id: Lineage(sup={t1.id})
        })

        t2.superclasses().clear()
        self.assertEqual(ont._terms.lineage, {t1.id: Lineage(), t2.id: Lineage()})

    def test_edit_relationship(self):
        ont = pronto.Ontology()
        self.assertEqual(ont._relationships.lineage, {})

        r1 = ont.create_relationship("rel_one")
        self.assertEqual(ont._relationships.lineage, {r1.id: Lineage()})

        r2 = ont.create_relationship("rel_two")
        self.assertEqual(ont._relationships.lineage, {r1.id: Lineage(), r2.id: Lineage()})

        r2.superproperties().add(r1)
        self.assertEqual(ont._relationships.lineage, {
            r1.id: Lineage(sub={r2.id}),
            r2.id: Lineage(sup={r1.id})
        })

        r2.superproperties().clear()
        self.assertEqual(ont._relationships.lineage, {r1.id: Lineage(), r2.id: Lineage()})


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
