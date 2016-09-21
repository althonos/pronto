### DEPS
import utils
utils.require(('yaml', 'PyYAML'), 'six')

import six
import yaml
import unittest
import io
import warnings

import pronto



### TESTS
class ProntoOntologyTest(unittest.TestCase):

    def assert_loaded(self, ontology):

        # check if not empty
        self.assertNotEqual(len(ontology), 0)

        # check if succesfully crosslinked
        for term in ontology:
            for r,l in six.iteritems(term.relations):
                for other in l:
                    self.assertIsInstance(other, pronto.Term)

    def assert_exportable(self, ontology):
        try:
            file = io.StringIO()
            file.write(ontology.obo)
        except Error as e:
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

        foundry_url = "http://www.obofoundry.org/registry/ontologies.yml"
        foundry_rq = six.moves.urllib.request.urlopen(foundry_url)
        foundry_yaml = yaml.load(foundry_rq)

        for o in foundry_yaml['ontologies']:
            if 'products' in o:
                for product in o['products']:

                    def _foundry_noimports(self):
                        onto = pronto.Ontology(product['ontology_purl'], False)
                        self.check_ontology(onto)

                    def _foundry_imports(self):
                        onto = pronto.Ontology(product['ontology_purl'])
                        self.check_ontology(onto)

                    cls.add_test(product['id'].replace(".", "_"), _foundry_noimports, _foundry_imports)

    @classmethod
    @utils.ciskip
    def add_test(cls, name, callable_noimports, callable_imports):
        #print('Registering tests for', name)
        setattr(cls, "test_{}_foundry_noimports".format(name), callable_noimports)
        setattr(cls, "test_{}_foundry_imports".format(name), callable_imports)



### RUN
if __name__=="__main__":

    ProntoOboFoundryTest.register_tests()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        unittest.main()
