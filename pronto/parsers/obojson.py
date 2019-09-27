import fastobo

from .base import BaseParser
from ..metadata import Metadata
from ..term import Term
from ..relationship import Relationship


class OboJsonParser(BaseParser):

    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b'{')

    def parse_from(self, handle):
        # Load the OBO graph into a syntax tree using fastobo
        doc = fastobo.load_graph(handle)

        # Extract metadata from the graph metadata and resolve imports
        self.ont.metadata = Metadata._from_ast(doc.header)
        self.process_imports()

        # Extract frames from the current document.
        try:
            for frame in doc:
                if isinstance(frame, fastobo.term.TermFrame):
                    Term._from_ast(frame, self.ont)
                elif isinstance(frame, fastobo.typedef.TypedefFrame):
                    Relationship._from_ast(frame, self.ont)
        except SyntaxError as s:
            location = self.ont.path, s.lineno, s.offset, s.text
            raise SyntaxError(s.args[0], location) from None
