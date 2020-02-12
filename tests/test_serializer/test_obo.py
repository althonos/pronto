import io
import unittest
import warnings
import xml.etree.ElementTree as etree

import pronto

from .base import TestSerializer


class TestOboSerializer(TestSerializer, unittest.TestCase):

    format = "obo"

    def test_metadata_auto_generated_by(self):
        self.assertRoundtrip(
            f"""
            format-version: 1.4
            auto-generated-by: pronto v{pronto.__version__}
            """
        )

    def test_metadata_date(self):
        self.assertRoundtrip(
            """
            format-version: 1.4
            date: 28:01:2020 10:29
            """
        )

    def test_metadata_namespace_id_rule(self):
        self.assertRoundtrip(
            """
            format-version: 1.4
            namespace-id-rule: * MS:$sequence(7,0,9999999)$
            """
        )

    def test_metadata_owl_axioms(self):
        self.assertRoundtrip(
            """
            format-version: 1.4
            owl-axioms: AnnotationAssertion(<http://www.geneontology.org/formats/oboInOwl#hasOBONamespace> <http://purl.obolibrary.org/obo/MS_1000393> \\"MS\\"^^xsd:string)
            """
        )

    def test_metadata_saved_by(self):
        self.assertRoundtrip(
            """
            format-version: 1.4
            saved-by: Martin Larralde
            """
        )

    def test_metadata_unreserved(self):
        self.assertRoundtrip(
            """
            format-version: 1.4
            unreserved-thing: very much unreserved
            """
        )

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

    def test_term_comment(self):
        self.assertRoundtrip(
            """
            format-version: 1.4

            [Term]
            id: TST:001
            comment: This is a very important comment.
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
