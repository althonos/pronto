import os
import multiprocessing.pool

import fastobo

from ..logic.lineage import Lineage
from .base import BaseParser
from ._fastobo import FastoboParser


class OboParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith((b"format-version:", b"[Term", b"[Typedef"))

    def parse_from(self, handle, threads=None):
        # Load the OBO document through an iterator using fastobo
        doc = fastobo.iter(handle, ordered=True)

        # Extract metadata from the OBO header and resolve imports
        self.ont.metadata = self.extract_metadata(doc.header())
        self.ont.imports.update(
            self.process_imports(
                self.ont.metadata.imports,
                self.ont.import_depth,
                os.path.dirname(self.ont.path or str()),
                self.ont.timeout,
            )
        )

        # Merge inheritance cache from imports
        for dep in self.ont.imports.values():
            for id, lineage in dep._inheritance.items():
                self.ont._inheritance.setdefault(id, Lineage())
                self.ont._inheritance[id].sup.update(lineage.sup)
                self.ont._inheritance[id].sub.update(lineage.sub)

        # Extract frames from the current document.
        try:
            with multiprocessing.pool.ThreadPool(threads) as pool:
                pool.map(self.extract_entity, doc)
        except SyntaxError as s:
            location = self.ont.path, s.lineno, s.offset, s.text
            raise SyntaxError(s.args[0], location) from None

        # Update inheritance cache
        self.symmetrize_inheritance()
