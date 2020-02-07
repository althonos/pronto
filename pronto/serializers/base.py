import abc
import io
import typing
from typing import BinaryIO, ClassVar

from ..ontology import Ontology


class BaseSerializer(abc.ABC):

    format: ClassVar[str] = NotImplemented

    def __init__(self, ont: Ontology):
        self.ont = ont

    @abc.abstractmethod
    def dump(self, file: BinaryIO) -> None:
        return NotImplemented

    def dumps(self) -> str:
        s = io.BytesIO()
        self.dump(s)
        return s.getvalue().decode("utf-8")
