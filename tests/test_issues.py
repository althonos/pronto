import unittest
import io
import re
import sys
import contextlib
import os
import shutil
import gzip
import os.path
import warnings
import textwrap
from unittest import mock

from . import utils
import pronto


class TestIssues(unittest.TestCase):

    CONSISTENCY_SPAN = 10

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
