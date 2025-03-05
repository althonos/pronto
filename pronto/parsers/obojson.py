import os

import fastobo

from ..logic.lineage import Lineage
from ..utils.meta import typechecked
from ._fastobo import FastoboParser
from .base import BaseParser


class OboJSONParser(FastoboParser, BaseParser):
    @classmethod
    def can_parse(cls, path, buffer):
        start = 3 if buffer.startswith((b'\xef\xbb\xbf', b'\xbf\xbb\xef')) else 0
        return buffer.lstrip().startswith(b"{", start)

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

        # Merge lineage cache from imports
        self.import_lineage()

        # Extract frames from the current document.
        with typechecked.disabled():
            try:
                with self.pool(threads) as pool:
                    pool.map(self.extract_entity, doc)
            except SyntaxError as err:
                location = self.ont.path, err.lineno, err.offset, err.text
                raise SyntaxError(err.args[0], location) from None

            # OBOJSON can define classes implicitly using only `is_a` properties
            # mapping to unresolved identifiers: in this case, we create the
            # term ourselves
            for lineage in list(self.ont._terms.lineage.values()):
                for superclass in lineage.sup.difference(self.ont._terms.lineage):
                    self.ont.create_term(superclass)

        # Update lineage cache
        self.symmetrize_lineage()
