import unittest
import io
import re
import sys
import contextlib
import os
import shutil
import gzip
import warnings
import textwrap
from unittest import mock

import pronto

from . import utils


# a mock implementation of `BaseParser.process_import` that uses files
# in `utils.DATADIR` instead of querying the OBO library
def process_import(ref, import_depth=-1, basepath="", timeout=5):
    ref, _ = os.path.splitext(ref)
    return pronto.Ontology(os.path.join(utils.DATADIR, f"{ref}.obo"))


class TestIssues(unittest.TestCase):

    CONSISTENCY_SPAN = 4

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter('error')

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_parser_consistency(self):
        """Assert several runs on the same file give the same output.

        See `#4 <https://github.com/althonos/pronto/issues/4>`_.
        Thanks to @winni-genp for issue reporting.
        """
        path = os.path.join(utils.DATADIR, "imagingMS.obo")
        ims = pronto.Ontology(path, import_depth=0)
        expected_keys = set(ims.keys())
        for _ in range(self.CONSISTENCY_SPAN):
            tmp_ims = pronto.Ontology(path, import_depth=0)
            self.assertEqual(set(tmp_ims.keys()), set(ims.keys()))

    def test_unicode_in_term_names(self):
        """Test if unicode characters in term names work.

        See `#6 <https://github.com/althonos/pronto/issues/6>`_.
        Thanks to @owen-jones-gen for issue reporting.
        """
        ont = pronto.Ontology(os.path.join(utils.DATADIR, "owen-jones-gen.obo"))
        self.assertEqual(str(ont["ONT0:ROOT"]), "Term('ONT0:ROOT', name='°')")

    @mock.patch("pronto.parsers.base.BaseParser.process_import", new=process_import)
    def test_nested_imports(self):
        """Check an ontology importing an ontology with imports can be opened.
        """
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UnicodeWarning)
            path = os.path.join(utils.DATADIR, "imagingMS.obo")
            ims = pronto.Ontology(path)

        self.assertIn("MS:1000031", ims)
        self.assertIn("UO:0000000", ims)

        self.assertIn("MS:1000040", ims["UO:0000000"].subclasses().to_set().ids)
        self.assertIn("UO:0000000", ims["MS:1000040"].superclasses().to_set().ids)

        self.assertEqual(ims.imports["ms"].metadata.ontology, "ms")
        self.assertEqual(ims.imports["ms"].imports["uo.obo"].metadata.ontology, "uo")

    def test_alt_id_access(self):
        path = os.path.join(utils.DATADIR, "hp.obo")
        hp = pronto.Ontology(path, import_depth=0)
        self.assertIn("HP:0001198", hp)
        self.assertEqual(hp["HP:0001198"].id, "HP:0009882")

    @mock.patch("pronto.parsers.base.BaseParser.process_import", new=process_import)
    def test_synonym_type_in_import(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UnicodeWarning)
            ont = pronto.Ontology(io.BytesIO(b"""
                format-version: 1.4
                import: hp
            """))

        ty = next(ty for ty in ont.synonym_types() if ty.id == "uk_spelling")

        t1 = ont.create_term("TST:001")
        t1.name = "color blindness"
        s1 = t1.add_synonym("colour blindness", scope="EXACT", type=ty)

        self.assertEqual(s1.type, ty)
