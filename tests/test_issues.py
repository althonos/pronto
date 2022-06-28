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
            warnings.simplefilter('ignore', DeprecationWarning)
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
        self.assertNotIn("HP:0001198", hp)
        self.assertIn("HP:0001198", hp["HP:0009882"].alternate_ids)

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

    def test_rdfxml_aliased_typedef(self):
        warnings.simplefilter("ignore")
        path = os.path.join(__file__, "..", "data", "go-basic.owl")
        go_basic = pronto.Ontology(os.path.realpath(path))
        self.assertIn("regulates", go_basic.relationships())
        self.assertIn("negatively_regulates", go_basic.relationships())
        self.assertIn(
            go_basic.get_relationship("regulates"),
            go_basic.get_relationship("negatively_regulates").superproperties().to_set(),
        )

    def test_idspaces_serialization(self):
       ont = pronto.Ontology()
       ont.metadata.idspaces["RHEA"] = ("http://identifier.org/rhea/", None)
       try:
           obo = ont.dumps()
       except Exception as err:
           self.fail("serialization failed with {}".format(err))

    def test_metadata_tag_serialization(self):
        """Assert relationships which are metadata tag serialize properly.

        See `#164 <https://github.com/althonos/pronto/issues/164>`_.
        """
        ont = pronto.Ontology()
        r = ont.create_relationship("TST:001")
        r.metadata_tag = True
        text = ont.dumps()
        self.assertEqual(
            text.strip(),
            textwrap.dedent("""
            format-version: 1.4

            [Typedef]
            id: TST:001
            is_metadata_tag: true
            """).strip()
        )

    def test_relationship_chains(self):
        ont = pronto.Ontology()
        r1 = ont.create_relationship("r1")
        r2 = ont.create_relationship("r2")
        r3 = ont.create_relationship("r3")
        r3.holds_over_chain = { (r1, r2) }
        r3.equivalent_to_chain = { (r1, r2) }
        ont.dumps()

    def test_class_level_clause(self):
        ont = pronto.Ontology()
        r1 = ont.create_relationship("r1")
        r1.class_level = True
        ont.dumps()
