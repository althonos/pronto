import abc
import functools
import os
import typing
import urllib.parse
import multiprocessing.pool
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
    def process_import(
        cls,
        ref: str,
        import_depth: int = -1,
        basepath: str = "",
        timeout: int = 5,
    ) -> Ontology:
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
        return Ontology(url, max(import_depth-1, -1), timeout)

    @classmethod
    def process_imports(
        cls,
        imports: Set[str],
        import_depth: int = -1,
        basepath: str = "",
        timeout: int = 5,
        threads: Optional[int] = None,
    ) -> Dict[str, Ontology]:
        # check we did not reach the maximum import depth
        if import_depth == 0:
            return dict()
        process = functools.partial(
            cls.process_import,
            import_depth=import_depth,
            basepath=basepath,
            timeout=timeout
        )
        with multiprocessing.pool.ThreadPool(threads) as pool:
            return dict(pool.map(lambda i: (i, process(i)), imports))

    def symmetrize_inheritance(self):
        for t in self.ont.terms():
            self.ont._inheritance.setdefault(t.id, Lineage())
        for subclass, lineage in self.ont._inheritance.items():
            for superclass in lineage.sup:
                self.ont._inheritance[superclass].sub.add(subclass)

    def import_inheritance(self):
        for dep in self.ont.imports.values():
            for term in dep.terms():
                self.ont._inheritance[term.id] = Lineage()
        for dep in self.ont.imports.values():
            for id, lineage in dep._inheritance.items():
                self.ont._inheritance[id].sup.update(lineage.sup)
                self.ont._inheritance[id].sub.update(lineage.sub)
