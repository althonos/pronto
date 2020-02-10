import unittest
import warnings

import pronto


class _SetupMixin(object):

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')
        cls.rpv1 = pronto.ResourcePropertyValue("IAO:0000114", "IAO:0000122")
        cls.rpv2 = pronto.ResourcePropertyValue("IAO:0000114", "IAO:0000122")
        cls.rpv3 = pronto.ResourcePropertyValue("IAO:0000114", "IAO:0000124")
        cls.lpv1 = pronto.LiteralPropertyValue("IAO:0000114", "unknown")
        cls.lpv2 = pronto.LiteralPropertyValue("IAO:0000114", "unknown")
        cls.lpv3 = pronto.LiteralPropertyValue("IAO:0000114", "other")
        cls.lpv4 = pronto.LiteralPropertyValue("IAO:0000112", "an example")
        cls.lpv5 = pronto.LiteralPropertyValue(
            "creation_date", "2018-09-21T16:43:39Z", "xsd:dateTime"
        )
        cls.lpv6 = pronto.LiteralPropertyValue(
            "creation_date", "2018-09-21T16:43:39Z", "xsd:string"
        )
        cls.lpv7 = pronto.LiteralPropertyValue(
            "IAO:0000427", "true", "xsd:boolean"
        )

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)


class TestLiteralPropertyValue(_SetupMixin, unittest.TestCase):

    def test_eq_self(self):
        self.assertEqual(self.lpv1, self.lpv1)
        self.assertEqual(self.lpv3, self.lpv3)

    def test_eq_literal_identical(self):
        self.assertEqual(self.lpv1, self.lpv2)
        self.assertIsNot(self.lpv1, self.lpv2)

    def test_eq_literal_different(self):
        self.assertNotEqual(self.lpv1, self.lpv3)
        self.assertNotEqual(self.lpv1, self.lpv4)
        self.assertNotEqual(self.lpv5, self.lpv6)

    def test_eq_resource_same_property(self):
        self.assertNotEqual(self.lpv5, self.rpv1)
        self.assertNotEqual(self.lpv5, self.rpv3)

    def test_eq_resource_different(self):
        self.assertNotEqual(self.lpv1, self.rpv1)

    def test_lt_literal_identical(self):
        self.assertFalse(self.lpv1 < self.lpv1)
        self.assertFalse(self.lpv1 < self.lpv2)

    def test_lt_literal_different(self):
        self.assertTrue(self.lpv4 < self.lpv1)
        self.assertTrue(self.lpv3 < self.lpv1)

    def test_lt_type_error(self):
        with self.assertRaises(TypeError):
            self.lpv1 < 1

    def test_lt_resource_identical(self):
        self.assertFalse(self.lpv1 < self.rpv1)

    def test_hash_identical(self):
        self.assertEqual(hash(self.lpv1), hash(self.lpv2))

    def test_hash_different(self):
        self.assertNotEqual(hash(self.lpv1), hash(self.lpv3))

    def test_repr(self):
        self.assertEqual(repr(self.lpv4), "LiteralPropertyValue('IAO:0000112', 'an example')")
        self.assertEqual(
            repr(self.lpv5),
            "LiteralPropertyValue('creation_date', '2018-09-21T16:43:39Z', datatype='xsd:dateTime')",
        )


class TestResourcePropertyValue(_SetupMixin, unittest.TestCase):

    def test_eq_self(self):
        self.assertEqual(self.rpv1, self.rpv1)
        self.assertEqual(self.rpv2, self.rpv2)

    def test_eq_other(self):
        self.assertNotEqual(self.rpv1, object())
        self.assertNotEqual(self.rpv1, 1)

    def test_eq_resource_identical(self):
        self.assertEqual(self.rpv1, self.rpv2)
        self.assertIsNot(self.rpv1, self.rpv2)

    def test_eq_resource_different(self):
        self.assertNotEqual(self.rpv1, self.rpv3)
        self.assertNotEqual(self.rpv2, self.rpv3)

    def test_eq_literal_different(self):
        self.assertNotEqual(self.rpv1, self.lpv1)
        self.assertNotEqual(self.rpv3, self.lpv1)

    def test_eq_literal_same_property(self):
        self.assertNotEqual(self.rpv1, self.lpv5)
        self.assertNotEqual(self.rpv3, self.lpv5)

    def test_hash_identical(self):
        self.assertEqual(hash(self.rpv1), hash(self.rpv2))

    def test_hash_different(self):
        self.assertNotEqual(hash(self.rpv1), hash(self.rpv3))

    def test_lt_resource_identical(self):
        self.assertFalse(self.rpv1 < self.rpv1)
        self.assertFalse(self.rpv1 < self.rpv2)

    def test_lt_resource_different(self):
        self.assertTrue(self.rpv1 < self.rpv3)

    def test_lt_literal_identical(self):
        self.assertFalse(self.rpv1 < self.lpv1)

    def test_lt_literal_different(self):
        self.assertTrue(self.rpv1 < self.lpv7)

    def test_lt_type_error(self):
        with self.assertRaises(TypeError):
            self.rpv1 < 1

    def test_repr(self):
        self.assertEqual(
            repr(self.rpv1),
            "ResourcePropertyValue('IAO:0000114', 'IAO:0000122')"
        )
