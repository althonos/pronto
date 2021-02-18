import abc
import functools
import multiprocessing.pool
import operator
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
        """Return `True` if this parser type can parse the given handle."""
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def parse_from(
        self, handle: typing.BinaryIO, threads: Optional[int] = None
    ) -> None:
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
        return Ontology(url, max(import_depth - 1, -1), timeout)

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
            timeout=timeout,
        )
        with multiprocessing.pool.ThreadPool(threads) as pool:
            return dict(pool.map(lambda i: (i, process(i)), imports))

    _entities = {
        "Term": operator.attrgetter("terms", "_terms"),
        "Relationship": operator.attrgetter("relationships", "_relationships"),
    }

    def symmetrize_lineage(self):
        for getter in self._entities.values():
            entities, graphdata = getter(self.ont)
            for entity in entities():
                graphdata.lineage.setdefault(entity.id, Lineage())
            for subentity, lineage in graphdata.lineage.items():
                for superentity in lineage.sup:
                    graphdata.lineage[superentity].sub.add(subentity)

    def import_lineage(self):
        for getter in self._entities.values():
            entities, graphdata = getter(self.ont)
            for dep in self.ont.imports.values():
                dep_entities, dep_graphdata = getter(dep)
                for entity in dep_entities():
                    graphdata.lineage[entity.id] = Lineage()
                for id, lineage in dep_graphdata.lineage.items():
                    graphdata.lineage[id].sup.update(lineage.sup)
                    graphdata.lineage[id].sub.update(lineage.sub)
