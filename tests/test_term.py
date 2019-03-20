# coding: utf-8
from __future__ import absolute_import
from __future__ import print_function

### DEPS
import copy
import six
import unittest
import io
import re
import sys
import contextlib
import os
import shutil
import gzip
import os.path as op
import warnings
import textwrap

from . import utils
import pronto

from pprint import pprint


### TESTS
class TestProntoTerm(unittest.TestCase):

    def test_deepcopy_eq(self):

        obo = pronto.Ontology("http://purl.obolibrary.org/obo/doid.obo")

        term = obo['DOID:0001816']
        term_copy = copy.deepcopy(term)
        self.assertEqual(term, term_copy)

        term_copy_copy = copy.deepcopy(term_copy)
        self.assertEqual(term, term_copy_copy)
