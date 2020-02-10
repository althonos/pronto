import os

import fastobo

from .base import BaseParser
from ._fastobo import FastoboParser


class OboJSONParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b"{")

    def parse_from(self, handle):
        # Load the OBO graph into a syntax tree using fastobo
        doc = fastobo.load_graph(handle)

        # Extract metadata from the graph metadata and resolve imports
        self.ont.metadata = self.extract_metadata(doc.header)
        self.ont.imports.update(
            self.process_imports(
                self.ont.metadata.imports,
                self.ont.import_depth,
                os.path.dirname(self.ont.path or str()),
                self.ont.timeout,
            )
        )

        # Extract frames from the current document.
        try:
            for frame in doc:
                if isinstance(frame, fastobo.term.TermFrame):
                    self.enrich_term(frame)
                elif isinstance(frame, fastobo.typedef.TypedefFrame):
                    self.enrich_relationship(frame)
        except SyntaxError as err:
            location = self.ont.path, err.lineno, err.offset, err.text
            raise SyntaxError(err.args[0], location) from None
