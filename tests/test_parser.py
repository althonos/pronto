# coding: utf-8
import sys
import six
import os
import time
import functools
import unittest
import importlib
import warnings

from .utils import mock

# Make sure we're using the local pronto library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pronto



class TestProntoParser(unittest.TestCase):

    def setUp(self):
        self.resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

    def _check(self, m,t,i, *args, **kwargs):
        #FEAT# Store internals as utf-8
        #self._check_utf8(m,t,i)
        if 'exp_len' in kwargs:
            self._check_len(t, kwargs['exp_len'])

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

class TestProntoOwlTargetParser(TestProntoOwlParser):

    def test_with_lxml_etree(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_lxml_etree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_cElementTree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i =  self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",

            )
        self._check(m,t,i, exp_len=685)

class TestProntoOwlTreeParser(TestProntoOwlParser):

    def test_with_lxml_etree(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
            )
        self._check(m,t,i, exp_len=2348)

    def test_with_lxml_etree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_elementTree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)

    def test_with_xml_cElementTree_remote(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            m,t,i = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            )
        self._check(m,t,i, exp_len=685)


def setUpModule():
    warnings.simplefilter('ignore')

def tearDownModule():
    warnings.simplefilter(warnings.defaultaction)
