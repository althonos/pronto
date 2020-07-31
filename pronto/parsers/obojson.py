import os
import multiprocessing.pool

import fastobo

from ..logic.lineage import Lineage
from ..utils.meta import typechecked
from .base import BaseParser
from ._fastobo import FastoboParser


class OboJSONParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b"{")

    def parse_from(self, handle, threads=None):
        # Load the OBO graph into a syntax tree using fastobo
        doc = fastobo.load_graph(handle).compact_ids()

        # Extract metadata from the OBO header
        with typechecked.disabled():
            self.ont.metadata = self.extract_metadata(doc.header)

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
            except SyntaxError as err:
                location = self.ont.path, err.lineno, err.offset, err.text
                raise SyntaxError(err.args[0], location) from None

            # OBOJSON can define classes implicitly using only `is_a` properties
            # mapping to unresolved identifiers: in this case, we create the
            # term ourselves
            for lineage in list(self.ont._inheritance.values()):
                for superclass in lineage.sup.difference(self.ont._inheritance):
                    self.ont.create_term(superclass)

        # Update inheritance cache
        self.symmetrize_inheritance()
