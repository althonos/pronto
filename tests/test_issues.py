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
        self.assertEqual(str(ont['ONT0:ROOT']), "Term('ONT0:ROOT', name='°')")
