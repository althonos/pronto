import os
import multiprocessing.pool

import fastobo

from ..logic.lineage import Lineage
from ..utils.meta import typechecked
from .base import BaseParser
from ._fastobo import FastoboParser


class OboParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith((b"format-version:", b"[Term", b"[Typedef"))

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

        # Merge inheritance cache from imports
        self.import_inheritance()

        # Extract frames from the current document.
        with typechecked.disabled():
            try:
                with multiprocessing.pool.ThreadPool(threads) as pool:
                    pool.map(self.extract_entity, doc)
            except SyntaxError as s:
                location = self.ont.path, s.lineno, s.offset, s.text
                raise SyntaxError(s.args[0], location) from None

        # Update inheritance cache with symmetric of `subClassOf`
        self.symmetrize_inheritance()
