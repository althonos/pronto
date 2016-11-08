# coding: utf-8
import sys
import six
import os
import time
import functools
import unittest
import contextlib
import importlib
import gzip

try:
    from unittest import mock
except ImportError:
    import mock

# Make sure we're using the local pronto library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pronto


class TestOwlParserUtils(unittest.TestCase):

    def test_get_id_from_url(self):

        test_values = {
            'http://purl.obolibrary.org/obo/IAO_0000115': 'IAO:0000115',
            'http://purl.obolibrary.org/obo/CL_0002420': 'CL:0002420',
            'http://purl.obolibrary.org/obo/UBERON_0001278': 'UBERON:0001278',
            'http://nmrML.org/nmrCV#NMR:1000001': 'NMR:1000001',
        }

        for k,v in six.iteritems(test_values):
            self.assertEqual(pronto.parser.owl.OwlXMLParser._get_id_from_url(k), v)


class TestOwlParser(unittest.TestCase):

    def setUp(self):
        self.resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        self.lxml_etree = importlib.import_module("lxml.etree")
        self.xml_etree = importlib.import_module("xml.etree.ElementTree")
        self.cxml_etree = importlib.import_module("xml.etree.cElementTree")

    def _parse(self, parser, path, expected_len):

        if path.startswith(('http', 'ftp')):
            handler = six.moves.urllib.request.urlopen
        else:
            handler = functools.partial(open, mode='rb')

        with contextlib.closing(handler(path)) as file:
            t1 = time.time()
            m,t,i = parser.parse(file)
            t2 = time.time()

        self.assertEqual(len(t), expected_len)
        return t2-t1


class TestOwlTargetParser(TestOwlParser):

    def test_with_lxml_etree(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )

    def test_lxml_etree_remote(self):
        dt = self._parse(
            pronto.parser.owl.OwlXMLTargetParser(),
            "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            685,
        )

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
                685,
            )

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTargetParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
                685,
            )


class TestOwlTreeParser(TestOwlParser):

    def test_with_lxml_etree(self):
        with mock.patch("pronto.parser.owl.etree", self.lxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )
            self.assertGreater(dt, 0)

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )
        self.assertGreater(dt, 0)

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                os.path.join(self.resources_dir, 'cl.ont'),
                2348,
            )
        self.assertGreater(dt, 0)

    def test_lxml_etree_remote(self):
        dt = self._parse(
            pronto.parser.owl.OwlXMLTreeParser(),
            "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
            685,
        )

    def test_with_xml_elementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.cxml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
                685,
            )

    def test_with_xml_cElementTree(self):
        with mock.patch("pronto.parser.owl.etree", self.xml_etree):
            dt = self._parse(
                pronto.parser.owl.OwlXMLTreeParser(),
                "http://nmrml.org/cv/v1.0.rc1/nmrCV.owl",
                685,
            )



# class TestProntoOboParser(unittest.TestCase):

#     def test_obo_parser(self):
#         pass
