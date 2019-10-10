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


class BaseSerializer(abc.ABC):

    format: ClassVar[str] = NotImplemented

    def __init__(self, ont: "Ontology"):
        self.ont = ont

    @abc.abstractmethod
    def dump(self, file: BinaryIO, encoding: str = "utf-8") -> None:
        return NotImplemented

    def dumps(self) -> str:
        s = io.BytesIO()
        self.dump(s)
        return s.getvalue().decode('utf-8')
