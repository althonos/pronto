import unittest

import pronto.pv



class TestLiteralPropertyValue(unittest.TestCase):

    def test_repr(self):
        pv = pronto.pv.LiteralPropertyValue("IAO:0000112", "an example")
        self.assertEqual(
            repr(pv),
            "LiteralPropertyValue('IAO:0000112', 'an example')"
        )
        pv2 = pronto.pv.LiteralPropertyValue("creation_date", "2018-09-21T16:43:39Z", "xsd:dateTime")
        self.assertEqual(
            repr(pv2),
            "LiteralPropertyValue('creation_date', '2018-09-21T16:43:39Z', datatype='xsd:dateTime')"
        )



class TestResourcePropertyValue(unittest.TestCase):

    def test_repr(self):
        pv = pronto.pv.ResourcePropertyValue("IAO:0000114", "IAO:0000122")
        self.assertEqual(repr(pv), "ResourcePropertyValue('IAO:0000114', 'IAO:0000122')")
