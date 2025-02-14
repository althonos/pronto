from typing import BinaryIO

import fastobo

from ._fastobo import FastoboSerializer
from .base import BaseSerializer


class OwlXMLSerializer(FastoboSerializer, BaseSerializer):

    format = "owx"

    def dump(self, file: BinaryIO):
        doc = self._to_obodoc(self.ont)
        fastobo.dump_owl(doc, file, format="owx")
