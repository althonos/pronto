# coding: utf-8
from __future__ import absolute_import

### DEPS
import six
import unittest
import io
import sys
import os.path as op
import warnings
import textwrap

try:
    from unittest import mock
except ImportError:
    import mock

from . import utils


# Make sure we're using the local pronto library
sys.path.insert(0, op.dirname(op.dirname(op.abspath(__file__))))
import pronto


### TESTS
class TestProntoUnicodeHandling(unittest.TestCase):

    def test_unicode_in_names(self):
        self.ontology = pronto.Ontology("resources/owen-jones-gen.obo")
        with mock.patch('sys.stdout', new=six.moves.StringIO()) as self.output:
            for term in self.ontology:
                print(term)
                print(term.obo)
            print(self.ontology.obo)

        self.assertEqual(self.output.getvalue().strip(),
                         textwrap.dedent("""
                                         <ONT0:ROOT: °>
                                         [Term]
                                         id: ONT0:ROOT
                                         name: °
                                         [Term]
                                         id: ONT0:ROOT
                                         name: °
                                         """).strip())

class TestProntoConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.obo = pronto.Ontology("resources/cmo.obo", False)
        cls.expected_keys = set(cls.obo.terms.keys())
        cls.consistency_span = 10

    def test_cmo_consistency(self):
        for x in range(self.consistency_span):
            tmp_obo = pronto.Ontology("resources/cmo.obo", False)
            self.assertEqual(set(tmp_obo.terms.keys()), self.expected_keys)

class TestProntoOntology(unittest.TestCase):

    def assert_loaded(self, ontology):

        # check if not empty
        self.assertNotEqual(len(ontology), 0)

        # check if succesfully crosslinked
        for term in ontology:
            for l in term.relations.values():
                for other in l:
                    self.assertIsInstance(other, pronto.Term)

    @utils.py2skip
    def assert_exportable(self, ontology):
        try:
            file = io.StringIO()
            file.write(ontology.obo)
        except BaseException as e:
            self.fail("export failed: {}".format(e))

    def assert_mergeable(self, ontology):
        try:
            other = pronto.Ontology()
            other.merge(ontology)
        except BaseException as e:
            self.fail("merge failed: {}".format(e))
        self.assertEqual(len(other), len(ontology))

    def check_ontology(self, ontology):
        self.assert_loaded(ontology)
        self.assert_exportable(ontology)
        self.assert_mergeable(ontology)

class TestProntoLocalOntology(TestProntoOntology):

    def test_owl_noimports(self):
        owl = pronto.Ontology("resources/cl.ont", False)
        self.check_ontology(owl)

    def test_obo_noimports(self):
        obo = pronto.Ontology("resources/cmo.obo", False)
        self.check_ontology(obo)

    def test_owl_imports(self):
        owl = pronto.Ontology("resources/cl.ont")
        self.check_ontology(owl)

    def test_obo_imports(self):
        obo = pronto.Ontology("resources/cmo.obo")
        self.check_ontology(obo)

    def test_winni_genp(self):
        obo = pronto.Ontology("resources/winni-genp.obo")
        self.check_ontology(obo)

    def test_with_custom_typedef(self):
        obo = pronto.Ontology("resources/elo.obo")
        self.check_ontology(obo)

        self.assertIn("has_written", pronto.Relationship._instances)
        self.assertIn(pronto.Relationship("written_by"), pronto.Relationship._instances.values())
        self.assertIn(pronto.Relationship('written_by'), obo['ELO:0130001'].relations)
        self.assertIn(pronto.Relationship('has_written'), obo['ELO:0330001'].relations)

class TestProntoRemoteOntology(TestProntoOntology):

    def test_obo_noimports(self):
        obo = pronto.Ontology("http://purl.obolibrary.org/obo/pdumdv.obo", False)
        self.check_ontology(obo)

    def test_owl_noimports(self):
        owl = pronto.Ontology("http://aber-owl.net/onts/FLU_63.ont", False)
        self.check_ontology(owl)

    def test_obo_imports(self):
        obo = pronto.Ontology("http://purl.obolibrary.org/obo/doid.obo")
        self.check_ontology(obo)

    def test_owl_imports(self):
        owl = pronto.Ontology("http://purl.obolibrary.org/obo/xao.owl")
        self.check_ontology(owl)

class TestProntoAberOwl(TestProntoOntology):
    pass
