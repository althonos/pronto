import unittest
import io
import os
import warnings

import pronto


### DEPS

if os.getcwd().endswith("pronto"):
    os.chdir("tests")

def require(*packages):
    import sys, pip
    for package in packages:
        try:
            if not isinstance(package, str):
                import_name, install_name = package
            else:
                import_name = install_name = package
            __import__(import_name)
        except ImportError:
            cmd = ['install', install_name]
            if not hasattr(sys, 'real_prefix'):
                cmd.append('--user')
            pip.main(cmd)


require(('yaml', 'PyYAML'), 'six')

import six
import yaml



def ciskip(func):

    if "CI" in os.environ and os.environ["CI"]=="true":
        def _pass(*args, **kwargs):
            pass
        return _pass
    else:
        return func





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

        # check

    def assert_exportable(self, ontology):
        file = io.StringIO()
        file.write(ontology.obo)

    def check_ontology(self, ontology):
        for name,method in six.iteritems(self.__dict__):
            if name.startswith("assert_"):
                method(self, ontology)


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
    def register_tests(cls):

        foundry_url = "http://www.obofoundry.org/registry/ontologies.yml"
        print("Reaching", foundry_url, "...")

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
    @ciskip
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
