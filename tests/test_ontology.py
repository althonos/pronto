# coding: utf-8 from __future__ import absolute_import

### DEPS
import six
import unittest
import io
import sys
import contextlib
import os
import shutil
import gzip
import os.path as op
import warnings
import textwrap

from . import utils

if os.getcwd().endswith("pronto"):
    os.chdir("tests")

# Make sure we're using the local pronto library
sys.path.insert(0, utils.MAINDIR)
import pronto


### TESTS
class TestProntoOntology(unittest.TestCase):

    def assert_loaded(self, ontology):

        # check if not empty
        self.assertNotEqual(len(ontology), 0)

        # check if succesfully crosslinked
        for term in ontology:
            for l in term.relations.values():
                for other in l:
                    self.assertIsInstance(other, pronto.Term)

    def assert_exportable(self, ontology):
        try:
            file = six.StringIO()
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





class TestProntoFeatures(TestProntoOntology):

    @classmethod
    def setUpClass(cls):
        cls.consistency_span = 10
        cls._rundir = os.path.join(os.getcwd(), 'run')
        os.mkdir(cls._rundir)

        ims_url = "https://github.com/beny/imzml/raw/master/data/imagingMS.obo"
        with open(os.path.join(cls._rundir, 'imagingMS.obo'), 'wb') as out_file:
            with contextlib.closing(six.moves.urllib.request.urlopen(ims_url)) as con:
                while True:
                    chunk = con.read(1024)
                    if not chunk:
                        break
                    out_file.write(chunk)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._rundir)

    def test_ims_consistency(self):
        """Assert several runs on the same file give the same output.

        See [https://github.com/althonos/pronto/issues/4]
        Thanks to @winni-genp for issue reporting.
        """
        obo = pronto.Ontology(os.path.join(self._rundir, "imagingMS.obo"), False)
        expected_keys = set(obo.terms.keys())
        for _ in six.moves.range(self.consistency_span):
            tmp_obo = pronto.Ontology(os.path.join(self._rundir, "imagingMS.obo"), False)
            self.assertEqual(set(tmp_obo.terms.keys()), expected_keys)
        self.check_ontology(obo)

    def test_remote_obogz_parsing(self):
        """Test the behaviour of pronto when parsing remote gzipped files.

        On Python2, this should raise a NotImplementedError (as
        urllib2.urlopen does not implement :obj:`io.StringIO` methods,
        gzip.GzipFile cannot handle on-the-fly decoding of data).

        On Python3, this should actually produce a proper ontology.
        """
        hpo_url = "https://github.com/Bioconductor-mirror/gwascat/"\
                      "raw/master/inst/obo/hpo.obo.gz"
        if six.PY3:
            gzipped = pronto.Ontology(hpo_url)
            expected_keys = {
                x.decode('utf-8').strip().split(': ')[-1]
                    for x in gzip.GzipFile(
                        fileobj=six.moves.urllib.request.urlopen(hpo_url)
                    )
                        if x.startswith(b'id: ')
            }
            self.assertEqual(expected_keys, set(gzipped.terms.keys()))
            self.check_ontology(gzipped)
        else:
            with self.assertRaises(NotImplementedError):
                gzipped = pronto.Ontology(hpo_url, parser='OwlXMLTargetParser')

    def test_unicode_in_term_names(self):
        """Test if unicode characters in term names work.

        See [https://github.com/althonos/pronto/issues/6]
        Thanks to @owen-jones-gen for issue reporting.
        """
        ontology = pronto.Ontology("resources/owen-jones-gen.obo")
        with utils.mock.patch('sys.stdout', new=six.moves.StringIO()) as output:
            for term in ontology:
                print(term)
                print(term.obo)
            print(ontology.obo)

            self.assertEqual(output.getvalue().strip(),
                             textwrap.dedent("""
                                             <ONT0:ROOT: °>
                                             [Term]
                                             id: ONT0:ROOT
                                             name: °
                                             [Term]
                                             id: ONT0:ROOT
                                             name: °
                                             """).strip())

        self.check_ontology(ontology)

    def test_exportable_headerless_ontology(self):
        """Test if a headerless ontology can be exported

        See [https://github.com/althonos/pronto/issues/5]
        Thanks to @winni-genp for issue reporting.
        """
        obo = pronto.Ontology("resources/winni-genp.obo")
        self.check_ontology(obo)

    def test_with_custom_typedef(self):
        """Try to import an obo ontology containing custom typedefs
        """
        obo = pronto.Ontology("resources/elo.obo")
        self.check_ontology(obo)

        self.assertIn("has_written", pronto.Relationship._instances)
        self.assertIn(pronto.Relationship("written_by"), pronto.Relationship._instances.values())
        self.assertIn(pronto.Relationship('written_by'), obo['ELO:0130001'].relations)
        self.assertIn(pronto.Relationship('has_written'), obo['ELO:0330001'].relations)


class TestProntoLocalOntology(TestProntoOntology):

    def test_local_owl_noimports(self):
        """Try to import a local owl ontology without its imports
        """
        owl = pronto.Ontology("resources/cl.ont", False)
        self.check_ontology(owl)

    def test_local_obo_noimports(self):
        """Try to import a local obo ontology without its imports
        """
        obo = pronto.Ontology("resources/cmo.obo", False)
        self.check_ontology(obo)

    def test_local_owl_imports(self):
        """Try to import a local owl ontology with its imports
        """
        owl = pronto.Ontology("resources/cl.ont")
        self.check_ontology(owl)

    def test_local_obo_imports(self):
        """Try to import a local owl ontology with its imports
        """
        obo = pronto.Ontology("resources/cmo.obo")
        self.check_ontology(obo)


class TestProntoRemoteOntology(TestProntoOntology):

    def test_remote_obo_noimports(self):
        """Try to import a remote obo ontology without its imports
        """
        obo = pronto.Ontology("http://purl.obolibrary.org/obo/pdumdv.obo", False)
        self.check_ontology(obo)

    def test_remote_owl_noimports(self):
        """Try to import a remote owl ontology without its imports
        """
        owl = pronto.Ontology("https://www.ebi.ac.uk/ols/ontologies/flu/download", False, parser="OwlXMLTreeParser")
        self.check_ontology(owl)

    def test_remote_obo_imports(self):
        """Try to import a remote obo ontology with its imports
        """
        obo = pronto.Ontology("http://purl.obolibrary.org/obo/doid.obo")
        self.check_ontology(obo)

    def test_remote_owl_imports(self):
        """Try to import a remote owl ontology with its imports
        """
        owl = pronto.Ontology("ftp://ftp.xenbase.org/pub/XenopusAnatomyOntology/xenopus_anatomy.owl")
        self.check_ontology(owl)


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
