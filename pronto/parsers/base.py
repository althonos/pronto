import abc
import os
import typing
import urllib.parse
from typing import Dict, Optional, Set

from ..logic.lineage import Lineage
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
    def parse_from(self, handle: typing.BinaryIO, threads: Optional[int] = None) -> None:
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

    def symmetrize_inheritance(self):
        for t in self.ont.terms():
            self.ont._inheritance.setdefault(t.id, Lineage())
        for subclass, lineage in self.ont._inheritance.items():
            for superclass in lineage.sup:
                self.ont._inheritance[superclass].sub.add(subclass)

    def import_inheritance(self):
        for dep in self.ont.imports.values():
            for id, lineage in dep._inheritance.items():
                self.ont._inheritance.setdefault(id, Lineage())
                self.ont._inheritance[id].sup.update(lineage.sup)
                self.ont._inheritance[id].sub.update(lineage.sub)
