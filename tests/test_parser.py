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
            m,t,i = parser.parse(handle)
        finally:
            handle.close()
        return m,t,i



@six.add_metaclass(abc.ABCMeta)
class TestProntoOwlParser(object):

    parser = None
    imp = platform.python_implementation()

    # ----------------------------------------
    # Test importing file with inline comments
    # ----------------------------------------

    @unittest.skipIf(utils.lxml_etree is None, 'lxml unavailable')
    def test_inline_comment_lxml(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.lxml_etree):
                tree_m, tree_t, tree_i = self._parse(
                    pronto.parser.owl.OwlXMLTreeParser(),
                    os.path.join(self.resources_dir, 'obi-small.owl'),
                )
        except Exception as e:
            self.fail(e)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_inline_comment_cElementTree(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
                tree_m, tree_t, tree_i = self._parse(
                    pronto.parser.owl.OwlXMLTreeParser(),
                    os.path.join(self.resources_dir, 'obi-small.owl'),
                )
        except Exception as e:
            self.fail(e)

    def test_inline_comment_ElementTree(self):
        try:
            with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
                tree_m, tree_t, tree_i = self._parse(
                    pronto.parser.owl.OwlXMLTreeParser(),
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
            m,t,i = self._parse(
                self.parser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_with_xml_cElementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
            m,t,i = self._parse(
                self.parser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
            m,t,i = self._parse(
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
            m,t,i = self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    @unittest.skipIf(utils.cxml_etree is None, 'cElementTree unavailable')
    def test_with_xml_cElementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.cxml_etree):
            m,t,i =  self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",

            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", utils.xml_etree):
            m,t,i = self._parse(
                self.parser(),
                "http://localhost:8080/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)


class TestProntoOwlTargetParser(TestProntoOwlParser, TestProntoParser):
    parser = pronto.parser.owl.OwlXMLTargetParser


class TestProntoOwlTreeParser(TestProntoOwlParser, TestProntoParser):
    parser = pronto.parser.owl.OwlXMLTreeParser


class TestProntoOwlUnicity(TestProntoParser):

    def test_parser_unicity(self):
        tree_m, tree_t, tree_i  = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )
        target_m, target_t, target_i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont.gz'),
            )

        #print(target_i)
        #print(target_m)
        #tree_cl = pronto.Ontology(os.path.join(self.resources_dir, 'cl.ont.gz'), 'OwlXMLTreeParser')
        #target_cl = pronto.Ontology(os.path.join(self.resources_dir, 'cl.ont.gz'), 'OwlXMLTargetParser')

        self.assertEqual(set(tree_t.keys()), set(target_t.keys()))
        self.assertEqual(set(tree_m.keys()), set(target_m.keys()))

        #FEAT# Acceptance test for althonos/pronto#7
        #self.assertEqual(tree_i, target_i)

        # for tid in tree_t:
        #     tree_term = tree_t[tid]
        #     target_term = target_t[tid]
        #     self.assertEqual(tree_term.id, target_term.id)
        #     self.assertEqual(tree_term.name, target_term.name)
        #     self.assertEqual(tree_term.desc, target_term.desc)
        #     self.assertEqual(tree_term.relations.keys(), target_term.relations.keys())
        #     self.assertEqual(tree_term.synonyms, target_term.synonyms)




def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
