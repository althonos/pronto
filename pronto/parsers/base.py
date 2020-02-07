import abc
import os
import typing
import urllib.parse
from typing import Dict, Set

from ..ontology import Ontology


class BaseParser(abc.ABC):
    def __init__(self, ont: Ontology):
        self.ont: Ontology = ont

    @classmethod
    @abc.abstractmethod
    def can_parse(cls, path: str, buffer: bytes) -> bool:
        """Return `True` if this parser type can parse the given handle.
        """
        return NotImplemented

    @abc.abstractmethod
    def parse_from(self, handle: typing.BinaryIO) -> None:
        return NotImplemented

    @classmethod
    def process_imports(
        cls,
        imports: Set[str],
        import_depth: int = -1,
        basepath: str = "",
        timeout: int = 5,
    ) -> Dict[str, Ontology]:
        # check we did not reach the maximum import depth
        resolved: Dict[str, Ontology] = {}
        if import_depth == 0:
            return resolved

        # process each import
        for ref in imports:
            s = urllib.parse.urlparse(ref).scheme
            if s in {"ftp", "http", "https"} or os.path.exists(ref):
                url = ref
            else:
                for ext in ["", ".obo", ".json", ".owl"]:
                    if os.path.exists(os.path.join(basepath, f"{ref}{ext}")):
                        url = os.path.join(basepath, f"{ref}{ext}")
                        break
                else:
                    id_ = f"{ref}.obo" if not os.path.splitext(ref)[1] else ref
                    url = f"http://purl.obolibrary.org/obo/{id_}"
            resolved[ref] = Ontology(url, max(import_depth - 1, 0), timeout)

        # return the resolved imports
        return resolved
