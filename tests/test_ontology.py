# coding: utf-8

### DEPS
import utils
utils.require(('yaml', 'PyYAML'), 'six')

import six
import yaml
import unittest
import io
import sys
import os.path as op
import warnings
import textwrap

# Make sure we're using the local pronto library
sys.path.insert(0, op.dirname(op.dirname(op.dirname(op.abspath(__file__)))))
import pronto


### TESTS
class ProntoUnicodeHandlingTest(unittest.TestCase):
    
    def setUp(self):
        sys.__stdout__.flush()
        sys.stdout = six.StringIO()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_unicode_in_names(self):
        ontology = pronto.Ontology("resources/owen-jones-gen.obo")
        for term in ontology:
            print(term)
            print(term.obo)
        print(ontology.obo)

        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read().strip(), 
                         textwrap.dedent("""
                                         <ONT0:ROOT: °>
                                         [Term]
                                         id: ONT0:ROOT
                                         name: °
                                         [Term]
                                         id: ONT0:ROOT
                                         name: °
                                         """).strip())

class ProntoConsistencyTest(unittest.TestCase):

    def setUp(self):
        self.obo = pronto.Ontology("resources/cmo.obo", False)
        self.consistency_span = 100

    def test_obo_redundancy(self):
        for x in range(self.consistency_span):
            tmp_obo = pronto.Ontology("resources/cmo.obo", False)
            self.assertEqual(tmp_obo.terms.keys(), self.obo.terms.keys())

class ProntoOntologyTest(unittest.TestCase):

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

class ProntoLocalOntologyTest(ProntoOntologyTest):

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

class ProntoRemoteOntologyTest(ProntoOntologyTest):

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

class ProntoAberOwlTest(ProntoOntologyTest):
    pass

class ProntoOboFoundryTest(ProntoOntologyTest):

    @classmethod
    @utils.ciskip
    def register_tests(cls):
        """Register tests for each ontology of the obofoundry"""

        foundry_url = "http://www.obofoundry.org/registry/ontologies.yml"
        foundry_rq = six.moves.urllib.request.urlopen(foundry_url)
        foundry_yaml = yaml.load(foundry_rq)

        products = ( o['products'] for o in foundry_yaml['ontologies'] if 'product' in o )
        for product in products:
            cls.add_test(product)


    @classmethod
    def add_test(cls, product):
        """Add test for each product found in the obofoundry yaml file"""

                             #CRASH       #INF. WAIT
        if product["id"] in ("chebi.obo", "dideo.owl"):
            return

        url, name = product["ontology_purl"], product["id"]

        def _foundry_noimports(self):
            onto = pronto.Ontology(url, False)
            self.check_ontology(onto)

        def _foundry_imports(self):
            onto = pronto.Ontology(url)
            self.check_ontology(onto)

        setattr(cls, "test_{}_foundry_noimports".format(name), _foundry_noimports)
        setattr(cls, "test_{}_foundry_imports".format(name),   _foundry_imports)



### RUN
if __name__=="__main__":

    print(pronto)

    ProntoOboFoundryTest.register_tests()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        unittest.main()
