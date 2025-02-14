from typing import BinaryIO

import fastobo

from ._fastobo import FastoboSerializer
from .base import BaseSerializer


class RdfXMLSerializer(FastoboSerializer, BaseSerializer):

    format = "rdf"

    def dump(self, file: BinaryIO):
        doc = self._to_obodoc(self.ont)
        fastobo.dump_owl(doc, file, format="rdf")
