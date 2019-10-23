import unittest
import warnings

import pronto


class TestLiteralPropertyValue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_repr(self):
        pv = pronto.LiteralPropertyValue("IAO:0000112", "an example")
        self.assertEqual(repr(pv), "LiteralPropertyValue('IAO:0000112', 'an example')")
        pv2 = pronto.LiteralPropertyValue(
            "creation_date", "2018-09-21T16:43:39Z", "xsd:dateTime"
        )
        self.assertEqual(
            repr(pv2),
            "LiteralPropertyValue('creation_date', '2018-09-21T16:43:39Z', datatype='xsd:dateTime')",
        )


class TestResourcePropertyValue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_repr(self):
        pv = pronto.ResourcePropertyValue("IAO:0000114", "IAO:0000122")
        self.assertEqual(
            repr(pv), "ResourcePropertyValue('IAO:0000114', 'IAO:0000122')"
        )
