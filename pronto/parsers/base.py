import abc
import os
import typing
import urllib.parse

if typing.TYPE_CHECKING:
    from ..ontology import Ontology


class BaseParser(abc.ABC):

    def __init__(self, ont: 'Ontology'):
        self.ont = ont

    @classmethod
    @abc.abstractmethod
    def can_parse(cls, path: str, buffer: bytes):
        """Return `True` if this parser type can parse the given handle.
        """
        return NotImplemented

    @abc.abstractmethod
    def parse_from(self, handle: typing.BinaryIO):
        return NotImplemented

    def process_imports(self):

        basepath = os.path.dirname(self.ont.path or "")

        if self.ont.import_depth != 0:
            for ref in self.ont.metadata.imports:
                s = urllib.parse.urlparse(ref).scheme
                if s in {"ftp", "http", "https"} or os.path.exists(ref):
                    url = ref
                else:
                    for ext in ["", ".obo", ".json", ".owl"]:
                        if os.path.exists(os.path.join(basepath, f"{ref}{ext}")):
                            url = os.path.join(basepath, f"{ref}{ext}")
                            break
                    else:
                        if not os.path.splitext(ref)[1]:
                            ref = f"{ref}.obo"
                        url = f"http://purl.obolibrary.org/obo/{ref}"

                self.ont.imports[ref] = type(self.ont)(
                    url,
                    max(self.ont.import_depth-1, 0),
                    self.ont.timeout,
                )
