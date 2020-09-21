import io
from typing import BinaryIO, ClassVar

from ..relationship import Relationship, RelationshipData
from ..term import Term, TermData
from ._fastobo import FastoboSerializer
from .base import BaseSerializer


class OboSerializer(FastoboSerializer, BaseSerializer):

    format = "obo"

    def dump(self, file):
        writer = io.TextIOWrapper(file)
        try:
            # dump the header
            if self.ont.metadata:
                header = self._to_header_frame(self.ont.metadata)
                file.write(str(header).encode("utf-8"))
                if self.ont._terms.entities or self.ont._relationships.entities:
                    file.write(b"\n")
            # dump terms
            if self.ont._terms.entities:
                for i, id in enumerate(sorted(self.ont._terms.entities)):
                    data = self.ont._terms.entities[id]
                    frame = self._to_term_frame(Term(self.ont, data))
                    file.write(str(frame).encode("utf-8"))
                    if (
                        i < len(self.ont._terms.entities) - 1
                        or self.ont._relationships.entities
                    ):
                        file.write(b"\n")
            # dump typedefs
            if self.ont._relationships.entities:
                for i, id in enumerate(sorted(self.ont._relationships.entities)):
                    data = self.ont._relationships.entities[id]
                    frame = self._to_typedef_frame(Relationship(self.ont, data))
                    file.write(str(frame).encode("utf-8"))
                    if i < len(self.ont._relationships.entities) - 1:
                        file.write(b"\n")
        finally:
            writer.detach()
