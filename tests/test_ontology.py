# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function

### DEPS
import six
import unittest
import io
import re
import sys
import contextlib
import os
import shutil
import gzip
import os.path as op
import warnings
import textwrap

from . import utils
import pronto


### TESTS
class TestProntoOntology(unittest.TestCase):

    class NamelessFile(object):
        def __init__(self, f):
            self._f = f
        def readline(self):
            return self._f.readline()
        def seek(self, *args, **kwargs):
            return self._f.seek(*args, **kwargs)
        def readable(self):
            return True
        def seekable(self):
            return True
        def read(self, *args, **kwargs):
            return self._f.read(*args, **kwargs)
        def __iter__(self):
            return self
        def __next__(self):
            return next(self._f)
        def next(self):
            return self.__next__()

    if six.PY2:
        def assertRegex(self, text, expected_regex, msg=None):
            return self.assertRegexpMatches(text, expected_regex, msg)

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
            file = six.moves.StringIO()
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

    def test_ims_consistency(self):
        """Assert several runs on the same file give the same output.

        See [https://github.com/althonos/pronto/issues/4]
        Thanks to @winni-genp for issue reporting.
        """
        obo = pronto.Ontology(os.path.join(utils.DATADIR, "imagingMS.obo.gz"), False)
        expected_keys = set(obo.terms.keys())
        for _ in six.moves.range(self.consistency_span):
            tmp_obo = pronto.Ontology(os.path.join(utils.DATADIR, "imagingMS.obo.gz"), False)
            self.assertEqual(set(tmp_obo.terms.keys()), expected_keys)
        self.check_ontology(obo)

    def test_remote_obogz_parsing(self):
        """Test the behaviour of pronto when parsing remote gzipped files.

        On Python2, this should raise a NotImplementedError (as
        urllib2.urlopen does not implement :obj:`io.StringIO` methods,
        gzip.GzipFile cannot handle on-the-fly decoding of data).

        On Python3, this should actually produce a proper ontology.
        """
        hpo_url = "http://localhost:8080/hpo.obo.gz"
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
            with self.assertRaises(io.UnsupportedOperation):
                gzipped = pronto.Ontology(hpo_url, parser='OwlXMLTargetParser')

    def test_unicode_in_term_names(self):
        """Test if unicode characters in term names work.

        See [https://github.com/althonos/pronto/issues/6]
        Thanks to @owen-jones-gen for issue reporting.
        """
        ontology = pronto.Ontology("tests/resources/owen-jones-gen.obo")
        with utils.mock.patch('sys.stdout', new=six.moves.StringIO()) as output:
            for term in ontology:
                print(term)
                print(term.obo)
            print()
            print(ontology.obo)

            expected_regex = re.compile(textwrap.dedent(r"""
                <ONT0:ROOT: °>
                \[Term\]
                id: ONT0:ROOT
                name: °

                date: \d{2}:\d{2}:\d{4} \d{2}:\d{2}
                auto-generated-by: pronto v\d+\.\d+\.\d+

                \[Term\]
                id: ONT0:ROOT
                name: °
                """
            ).strip())
            output.seek(0)
            self.assertRegex(output.read().strip(), expected_regex)

        self.check_ontology(ontology)

    def test_exportable_headerless_ontology(self):
        """Test if a headerless ontology can be exported

        See [https://github.com/althonos/pronto/issues/5]
        Thanks to @winni-genp for issue reporting.
        """
        obo = pronto.Ontology("tests/resources/winni-genp.obo")
        self.check_ontology(obo)

    def test_with_custom_typedef(self):
        """Try to import an obo ontology containing custom typedefs
        """
        obo = pronto.Ontology("tests/resources/elo.obo")
        self.check_ontology(obo)

        self.assertIn("has_written", pronto.Relationship._instances)
        self.assertIn(pronto.Relationship("written_by"), pronto.Relationship._instances.values())
        self.assertIn(pronto.Relationship('written_by'), obo['ELO:0130001'].relations)
        self.assertIn(pronto.Relationship('has_written'), obo['ELO:0330001'].relations)

    def test_obo_export(self):
        hpo = pronto.Ontology("tests/resources/hpo.obo.gz")
        self.assertEqual(
            hpo['HP:0000003'].obo.strip(),
            textwrap.dedent("""
            [Term]
            id: HP:0000003
            name: Multicystic kidney dysplasia
            alt_id: HP:0004715
            def: "Multicystic dysplasia of the kidney is characterized by multiple cysts of varying size in the kidney and the absence of a normal pelvicaliceal system. The condition is associated with ureteral or ureteropelvic atresia, and the affected kidney is nonfunctional." [HPO:curators]
            comment: Multicystic kidney dysplasia is the result of abnormal fetal renal development in which the affected kidney is replaced by multiple cysts and has little or no residual function. The vast majority of multicystic kidneys are unilateral. Multicystic kidney can be diagnosed on prenatal ultrasound.
            synonym: "Multicystic dysplastic kidney" EXACT []
            synonym: "Multicystic kidneys" EXACT []
            synonym: "Multicystic renal dysplasia" EXACT []
            xref: MSH:D021782
            xref: SNOMEDCT_US:204962002
            xref: SNOMEDCT_US:82525005
            xref: UMLS:C3714581
            is_a: HP:0000107 ! Renal cyst""").strip()
        )

    def test_obo_stream_import(self):
        # Check with a named stream
        with open("tests/resources/elo.obo", 'rb') as stream:
            elo = pronto.Ontology(stream)
            self.assertFalse(stream.closed)
            self.assertEqual(elo.path, "tests/resources/elo.obo")
        self.check_ontology(elo)

        patch_object = utils.mock.patch.object
        PropertyMock = utils.mock.PropertyMock

        # Check with a nameless stream
        with open("tests/resources/elo.obo", 'rb') as stream:
            elo = pronto.Ontology(self.NamelessFile(stream))
            self.assertFalse(stream.closed)
            self.assertIs(elo.path, None)
        self.check_ontology(elo)

    def test_owl_stream_import(self):
        # Check with a named stream
        with open("tests/resources/nmrCV.owl", 'rb') as stream:
            nmr = pronto.Ontology(stream)
            self.assertFalse(stream.closed)
            self.assertEqual(nmr.path, 'tests/resources/nmrCV.owl')
        self.check_ontology(nmr)

        # Check with a nameless stream
        with open("tests/resources/nmrCV.owl", 'rb') as stream:
            nmr = pronto.Ontology(self.NamelessFile(stream))
            self.assertFalse(stream.closed)
            self.assertIs(nmr.path, None)
        self.check_ontology(nmr)




class TestProntoLocalOntology(TestProntoOntology):

    def test_local_owl_noimports(self):
        """Try to import a local owl ontology without its imports
        """
        owl = pronto.Ontology("tests/resources/cl.ont.gz", False)
        self.check_ontology(owl)

    def test_local_obo_noimports(self):
        """Try to import a local obo ontology without its imports
        """
        obo = pronto.Ontology("tests/resources/cmo.obo", False)
        self.check_ontology(obo)

    def test_local_owl_imports(self):
        """Try to import a local owl ontology with its imports
        """
        owl = pronto.Ontology("tests/resources/cl.ont.gz")
        self.check_ontology(owl)

    def test_local_obo_imports(self):
        """Try to import a local owl ontology with its imports
        """
        obo = pronto.Ontology("tests/resources/cmo.obo")
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
