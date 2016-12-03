# coding: utf-8
import sys
import six
import os
import time
import functools
import unittest
import importlib
import warnings
import platform

from . import utils

# Make sure we're using the local pronto library
sys.path.insert(0, utils.MAINDIR)
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



class TestProntoOwlParser(TestProntoParser):

    def setUp(self):
        super(TestProntoOwlParser, self).setUp()
        self.lxml_etree = importlib.import_module("lxml.etree")
        self.xml_etree = importlib.import_module("xml.etree.ElementTree")
        self.cxml_etree = importlib.import_module("xml.etree.cElementTree")

    @staticmethod
    def _parse(parser, path):
        if path.startswith(('http', 'ftp')):
            handle = six.moves.urllib.request.urlopen(path)
        else:
            handle = open(path, 'rb')
        try:
            m,t,i = parser.parse(handle)
        finally:
            handle.close()
        return m,t,i


class TestProntoOwlUnicity(TestProntoOwlParser):

    def test_parser_unicity(self):
        tree_m, tree_t, tree_i  = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        target_m, target_t, target_i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )

        print(target_i)
        print(target_m)
        #tree_cl = pronto.Ontology(os.path.join(self.resources_dir, 'cl.ont'), 'OwlXMLTreeParser')
        #target_cl = pronto.Ontology(os.path.join(self.resources_dir, 'cl.ont'), 'OwlXMLTargetParser')

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



class TestProntoOwlTargetParser(TestProntoOwlParser):

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run lxml with {}'.format(platform.python_implementation()))
    def test_with_lxml_etree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run cElementTree with {}'.format(platform.python_implementation()))
    def test_with_xml_cElementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run lxml with {}'.format(platform.python_implementation()))
    def test_with_lxml_etree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run cElementTree with {}'.format(platform.python_implementation()))
    def test_with_xml_cElementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i =  self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",

            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

class TestProntoOwlTreeParser(TestProntoOwlParser):


    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run lxml with {}'.format(platform.python_implementation()))
    def test_with_lxml_etree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run cElementTree with {}'.format(platform.python_implementation()))
    def test_with_xml_cElementTree(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run lxml with {}'.format(platform.python_implementation()))
    def test_with_lxml_etree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    @unittest.skipIf(platform.python_implementation()!="CPython",
        'cannot run cElementTree with {}'.format(platform.python_implementation()))
    def test_with_xml_cElementTree_remote(self):
        with utils.mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
