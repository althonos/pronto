import io
from typing import BinaryIO, ClassVar

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
                if self.ont._terms or self.ont._relationships:
                    file.write(b"\n")
            # dump terms
            if self.ont._terms:
                for i, (id, data) in enumerate(self.ont._terms.items()):
                    frame = self._to_term_frame(data)
                    file.write(str(frame).encode("utf-8"))
                    if i < len(self.ont._terms) - 1 or self.ont._relationships:
                        file.write(b"\n")
            # dump typedefs
            if self.ont._relationships:
                for i, (id, data) in enumerate(self.ont._relationships.items()):
                    frame = self._to_typedef_frame(data)
                    file.write(str(frame).encode("utf-8"))
                    if i < len(self.ont._relationships) - 1:
                        file.write(b"\n")
        finally:
            writer.detach()
