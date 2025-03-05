import os

import fastobo

from ..utils.meta import typechecked
from ._fastobo import FastoboParser
from .base import BaseParser


class OboParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        start = 3 if buffer.startswith((b'\xef\xbb\xbf', b'\xbf\xbb\xef')) else 0
        return buffer.lstrip().startswith((b"format-version:", b"[Term", b"[Typedef"), start)

    def parse_from(self, handle, threads=None):
        # Load the OBO document through an iterator using fastobo
        doc = fastobo.iter(handle, ordered=True)

        # Extract metadata from the OBO header
        with typechecked.disabled():
            self.ont.metadata = self.extract_metadata(doc.header())

        # Resolve imported dependencies
        self.ont.imports.update(
            self.process_imports(
                self.ont.metadata.imports,
                self.ont.import_depth,
                os.path.dirname(self.ont.path or str()),
                self.ont.timeout,
                threads=threads,
            )
        )

        # Merge lineage cache from imports
        self.import_lineage()

        # Extract frames from the current document.
        with typechecked.disabled():
            try:
                with self.pool(threads) as pool:
                    pool.map(self.extract_entity, doc)
            except SyntaxError as s:
                location = self.ont.path, s.lineno, s.offset, s.text
                raise SyntaxError(s.args[0], location) from None

        # Update lineage cache with symmetric of `subClassOf`
        self.symmetrize_lineage()
