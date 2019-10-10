import abc
import io
import os
import operator
import typing
import urllib.parse
from typing import BinaryIO, ClassVar

import fastobo

from ..metadata import Metadata
from ..ontology import Ontology
from ..synonym import SynonymData
from ..term import Term, TermData
from ..xref import Xref
from ..pv import PropertyValue, LiteralPropertyValue, ResourcePropertyValue

from ._fastobo import FastoboSerializer
from .base import BaseSerializer



class OboJSONSerializer(FastoboSerializer, BaseSerializer):

    format = "json"

    def dump(self, file):
        doc = self._to_obodoc(self.ont)
        fastobo.dump_graph(doc, file)
