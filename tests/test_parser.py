# coding: utf-8
import sys
import six
import abc
import os
import time
import functools
import unittest
import importlib
import warnings
import platform
import gzip

from . import utils
import pronto


class TestProntoParser(unittest.TestCase):

    def setUp(self):
        self.resources_dir = os.path.join(utils.TESTDIR, "resources")

    def _check(self, m,t,i, *args, **kwargs):
        #FEAT# Store internals as utf-8
        #self._check_utf8(m,t,i)

        if 'exp_len' in kwargs:
            self._check_len(t, kwargs['exp_len'])

        for term in six.itervalues(t):
            self._check_synonyms(term)

    def _check_synonyms(self, term):
        """Check that each Term synonym is stored as Synonym object
        """
        for s in term.synonyms:
            self.assertIsInstance(s, pronto.synonym.Synonym)

    def _check_utf8(self, m, t, i):
        """Check that inner properties are stored as utf-8
        """
        for term in six.itervalues(t):
            # six.text_type is str in Py3, unicode in Py2
            self.assertIsInstance(term.id, six.text_type)
            self.assertIsInstance(term.name, six.text_type)
            self.assertIsInstance(term.desc, six.text_type)

        for importpath in i:
            self.assertIsInstance(importpath, six.text_type)

        for k,v in six.iteritems(m):
            self.assertIsInstance(k, six.text_type)
            for x in v:
                self.assertIsInstance(x, six.text_type)

    def _check_len(self, t, exp_len):
        """Check the terms dict length matches the expected length
        """
        self.assertEqual(len(t), exp_len)

    @staticmethod
    def _parse(parser, path):
        if path.startswith(('http', 'ftp')):
            handle = six.moves.urllib.request.urlopen(path)
        elif path.endswith('.gz'):
            handle = gzip.GzipFile(path)
        else:
            handle = open(path, 'rb')
        try:
            m,t,i,tpd = parser.parse(handle)
        finally:
            handle.close()
        return m,t,i,tpd


class TestProntoOboParser(TestProntoParser):
    parser = pronto.parser.obo.OboParser

    def test_inline_comment(self):
        m, t, i, _ = self._parse(
            self.parser(), os.path.join(self.resources_dir, 'krassowski.obo')
        )

        self.assertEqual(t['CVCL_KA96'].other['xref'][0], "NCBI_TaxID:10090")
        self.assertEqual(m['format-version'][0], '1.2')
        self.assertEqual(t['CVCL_KA96'].other['subset'][0], "Hybridoma")


@six.add_metaclass(abc.ABCMeta)
class _TestProntoOwlParser(object):

    parser = None
    imp = platform.python_implementation()

    # ----------------------------------------
    # Test importing file with inline comments
    # ----------------------------------------

    @unittest.skipIf(utils.lxml_etree is None, 'lxml unavailable')
    def test_inline_comment_lxml(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.lxml_etree):
                tree_m, tree_t, tree_i, tpd = self._parse(
                    pronto.parser.owl.OwlXMLParser(),
                    os.path.join(self.resources_dir, 'obi-small.owl'),
                )
        except Exception as e:
            self.fail(e)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_inline_comment_cElementTree(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
                tree_m, tree_t, tree_i, tpd = self._parse(
                    pronto.parser.owl.OwlXMLParser(),
                    os.path.join(self.resources_dir, 'obi-small.owl'),
                )
        except Exception as e:
            self.fail(e)

    def test_inline_comment_ElementTree(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
                tree_m, tree_t, tree_i, tpd = self._parse(
                    pronto.parser.owl.OwlXMLParser(),
                    os.path.join(self.resources_dir, 'obi-small.owl'),
                )
        except Exception as e:
            self.fail(e)

    # -----------------------------------
    # Test importing from "local" source
    # -----------------------------------

    @unittest.skipIf(utils.lxml_etree is None, 'lxml unavailable')
    def test_with_lxml_etree(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.lxml_etree):
            m,t,i, tpd = self._parse(
                self.parser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_with_xml_cElementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
            m,t,i, tpd = self._parse(
                self.parser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
            m,t,i, tpd = self._parse(
                self.parser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        self._check(m,t,i, exp_len=2348)

    # -----------------------------------
    # Test importing from "remote" source
    # -----------------------------------

    @unittest.skipIf(utils.lxml_etree is None, 'lxml unavailable')
    def test_with_lxml_etree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.lxml_etree):
            m,t,i, tpd = self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_with_xml_cElementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
            m,t,i, tpd =  self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",

            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
            m,t,i, tpd = self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)


class TestOwlXMLParser(_TestProntoOwlParser, TestProntoParser):
    parser = pronto.parser.owl.OwlXMLParser


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
