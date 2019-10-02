import fastobo

from .base import BaseParser
from ._fastobo import FastoboParser
from ..metadata import Metadata
from ..term import Term
from ..relationship import Relationship


class OboJsonParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b"{")

    def parse_from(self, handle):
        # Load the OBO graph into a syntax tree using fastobo
        doc = fastobo.load_graph(handle)

        # Extract metadata from the graph metadata and resolve imports
        self.ont.metadata = self._extract_metadata(doc.header)
        self.process_imports()

        # Extract frames from the current document.
        try:
            for frame in doc:
                if isinstance(frame, fastobo.term.TermFrame):
                    self._extract_term(frame)
                elif isinstance(frame, fastobo.typedef.TypedefFrame):
                    self._extract_relationship(frame)
        except SyntaxError as s:
            location = self.ont.path, s.lineno, s.offset, s.text
            raise SyntaxError(s.args[0], location) from None
