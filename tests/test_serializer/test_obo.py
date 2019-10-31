import io
import unittest
import warnings
import xml.etree.ElementTree as etree

import pronto

from .base import TestSerializer


class TestOboSerializer(TestSerializer, unittest.TestCase):

    format = "obo"

    def test_term_anonymous(self):
        self.assertRoundtrip(
            """
            format-version: 1.4

            [Term]
            id: TST:001
            is_anonymous: true
            """
        )

    def test_term_builtin(self):
        self.assertRoundtrip(
            """
            format-version: 1.4

            [Term]
            id: TST:001
            builtin: true
            """
        )

    def test_term_consider(self):
        self.assertRoundtrip(
            """
            format-version: 1.4

            [Term]
            id: TST:001

            [Term]
            id: TST:002
            consider: TST:001
            """
        )

    def test_term_intersection_of(self):
        self.assertRoundtrip(
            """
            format-version: 1.4

            [Term]
            id: TST:001

            [Term]
            id: TST:002

            [Term]
            id: TST:003
            intersection_of: TST:001
            intersection_of: part_of TST:002

            [Typedef]
            id: part_of
            """
        )
