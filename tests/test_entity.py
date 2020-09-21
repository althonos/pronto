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


class TestEntityCollections(unittest.TestCase):

    def test_alternate_ids_length(self):
        path = os.path.join(utils.DATADIR, "hp.obo")
        hp = pronto.Ontology(path, import_depth=0, threads=1)
        self.assertEqual(len(hp["HP:0009882"].alternate_ids), 10)
