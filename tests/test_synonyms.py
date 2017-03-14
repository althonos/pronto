# coding: utf-8
from __future__ import absolute_import

### DEPS
import six
import unittest
import io
import sys
import contextlib
import os
import shutil
import gzip
import os.path as op
import warnings
import textwrap

from . import utils
import pronto.synonym


class TestProntoSynonymType(unittest.TestCase):

    def assertOk(self, synonymtype, scope):
        self.assertEqual(synonymtype.desc, 'British spelling')
        self.assertEqual(synonymtype.name, 'UK_SPELLING')
        self.assertEqual(synonymtype.scope, scope)
        self.assertIn(synonymtype.name, pronto.synonym.SynonymType._instances)

    def test_new_synonymtype_from_obo_header_with_scope(self):
        synonymtype = pronto.synonym.SynonymType.from_obo_header(
            'UK_SPELLING "British spelling" EXACT'
        )
        self.assertOk(synonymtype, "EXACT")

    def test_new_synonymtype_from_obo_header_without_scope(self):
        synonymtype = pronto.synonym.SynonymType.from_obo_header(
            'UK_SPELLING "British spelling"'
        )
        self.assertOk(synonymtype, None)

    def test_new_synonymtype_with_scope(self):
        synonymtype = pronto.synonym.SynonymType(
            'UK_SPELLING', 'British spelling', 'EXACT',
        )
        self.assertOk(synonymtype, "EXACT")

    def test_new_synonymtype_without_scope(self):
        synonymtype = pronto.synonym.SynonymType(
            'UK_SPELLING', 'British spelling',
        )
        self.assertOk(synonymtype, None)

    def test_fail_wrong_scope(self):
        with self.assertRaises(ValueError) as ctx:
            pronto.synonym.SynonymType(
            'UK_SPELLING', 'British spelling', 'UNEXISTING_SCOPE',
        )
        self.assertEqual(str(ctx.exception), "scope must be 'NARROW'"
                         ", 'BROAD', 'EXACT', 'RELATED' or None")

    def test_obo_with_scope(self):
        obo_header = 'UK_SPELLING "British spelling" EXACT'
        synonymtype = pronto.synonym.SynonymType.from_obo_header(obo_header)
        self.assertEqual(synonymtype.obo, "synonymtypedef: {}".format(obo_header))

    def test_obo_without_scope(self):
        obo_header = 'UK_SPELLING "British spelling"'
        synonymtype = pronto.synonym.SynonymType.from_obo_header(obo_header)
        self.assertEqual(synonymtype.obo, "synonymtypedef: {}".format(obo_header))


class TestProntoSynonym(unittest.TestCase):

    def tearDown(self):
        pronto.synonym.SynonymType._instances.clear()

    def assertOk(self, synonym, scope, synonymtype=None):
        self.assertEqual(synonym.desc, "The other white meat")
        self.assertEqual(synonym.scope, scope)
        self.assertEqual(synonym.xref, ['MEAT:00324', 'BACONBASE:03021'])
        if synonymtype is not None:
            self.assertEqual(synonym.syn_type, synonymtype)

    def test_new_synonym_from_obo_header_with_scope_with_syntype(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan')
        synonym = pronto.synonym.Synonym.from_obo_header(
            '"The other white meat" EXACT MARKETING_SLOGAN [MEAT:00324, BACONBASE:03021]'
        )
        self.assertOk(synonym, "EXACT", synonymtype)

    def test_new_synonym_from_obo_header_without_scope_with_syntype(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan')
        synonym = pronto.synonym.Synonym.from_obo_header(
            '"The other white meat" MARKETING_SLOGAN [MEAT:00324, BACONBASE:03021]'
        )
        self.assertOk(synonym, "RELATED", synonymtype)

    def test_new_synonym_with_scope_with_syntype(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan')
        synonym = pronto.synonym.Synonym(
            "The other white meat", "BROAD", "MARKETING_SLOGAN", ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "BROAD", synonymtype)

    def test_new_synonym_without_scope_with_syntype(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan')
        synonym = pronto.synonym.Synonym(
            "The other white meat", None, "MARKETING_SLOGAN", ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "RELATED", synonymtype)

    def test_new_synonym_from_obo_header_with_scope_without_syntype(self):
        synonym = pronto.synonym.Synonym.from_obo_header(
            '"The other white meat" EXACT [MEAT:00324, BACONBASE:03021]'
        )
        self.assertOk(synonym, "EXACT")

    def test_new_synonym_from_obo_header_without_scope_without_syntype(self):
        synonym = pronto.synonym.Synonym.from_obo_header(
            '"The other white meat" [MEAT:00324, BACONBASE:03021]'
        )
        self.assertOk(synonym, "RELATED")

    def test_new_synonym_with_scope_without_syntype(self):
        synonym = pronto.synonym.Synonym(
            "The other white meat", "BROAD", None, ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "BROAD")

    def test_new_synonym_without_scope_without_syntype(self):
        synonym = pronto.synonym.Synonym(
            "The other white meat", None, None, ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "RELATED")

    def test_new_synonym_inherit_scope_from_syn_type(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan', "EXACT")
        synonym = pronto.synonym.Synonym(
            "The other white meat", None, "MARKETING_SLOGAN", ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "EXACT", synonymtype)

    def test_new_synonym_force_scope_from_syn_type(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan', "EXACT")
        synonym = pronto.synonym.Synonym(
            "The other white meat", "BROAD", "MARKETING_SLOGAN", ["MEAT:00324", "BACONBASE:03021"],
        )
        self.assertOk(synonym, "EXACT", synonymtype)

    def test_fail_wrong_scope(self):
        synonymtype = pronto.synonym.SynonymType("MARKETING_SLOGAN", 'marketing slogan')
        with self.assertRaises(ValueError) as ctx:
            synonym = pronto.synonym.Synonym(
                "The other white meat", "WRONG", "MARKETING_SLOGAN", ["MEAT:00324", "BACONBASE:03021"],
        )

    def test_fail_undefined_syn_type(self):
        with self.assertRaises(ValueError) as ctx:
            synonym = pronto.synonym.Synonym(
                "The other white meat", "BROAD", "WRONG_TYPE", ["MEAT:00324", "BACONBASE:03021"],
        )
