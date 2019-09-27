import contextlib
import datetime
import itertools
import io
import typing
import os
import urllib.parse
from typing import BinaryIO, Dict, Iterator, Mapping, Optional, Union

import contexter
import fastobo
import requests

from . import relationship
from .term import Term, _TermData
from .synonym import SynonymType
from .relationship import Relationship, _RelationshipData
from .metadata import Metadata
from .utils.io import decompress, get_handle, get_location
from .utils.iter import SizedIterator
from .utils.repr import make_repr
from .utils.set import set
from .parsers import BaseParser


class Ontology(Mapping[str, Union[Term, Relationship]]):
    """An ontology.
    """

    session: requests.Session
    import_depth: int
    timeout: int
    imports: Dict[str, 'Ontology']

    def __init__(
        self,
        handle: Union[BinaryIO, str, None] = None,
        import_depth: int = -1,
        timeout: int = 2,
        session: Optional[requests.Session] = None,
    ):
        with contexter.Contexter() as ctx:
            self._default_session = session is None
            self.session = session or (ctx << requests.Session())
            self.import_depth = import_depth
            self.timeout = timeout
            self.imports = dict()

            self._terms: Dict[str, _TermData] = {}
            self._relationships: Dict[str, _RelationshipData] = {}

            # Creating an ontology from scratch is supported
            if handle is None:
                self.metadata = Metadata()
                self.path = self.handle = None
                return

            # Get the path and the handle from arguments
            if isinstance(handle, str):
                self.path: str = handle
                self.handle = ctx << get_handle(handle, self.session, timeout)
                _handle = ctx << decompress(self.handle)
            elif hasattr(handle, 'read'):
                self.path: str = get_location(handle)
                self.handle = handle
                _handle = decompress(self.handle)
            else:
                raise TypeError(f"could not parse ontology from {handle!r}")

            # Parse the ontology using the appropriate parser
            buffer = _handle.peek(io.DEFAULT_BUFFER_SIZE)
            for cls in BaseParser.__subclasses__():
                if cls.can_parse(typing.cast(str, self.path), buffer):
                    cls(self).parse_from(_handle)
                    break
            else:
                raise ValueError(f"could not find a parser to parse {handle!r}")

    def __len__(self) -> int:
        return len(self._terms) + len(self._relationships) + sum(map(len, self.imports))

    def __iter__(self) -> SizedIterator[str]:
        terms, relationships = self.terms(), self.relationships()
        return SizedIterator(
            (entity.id for entity in itertools.chain(terms, relationships)),
            length=len(terms) + len(relationships),
        )

    def __contains__(self, item: str) -> bool:
        return any(item in i for i in self.imports.values()) \
            or item in self._terms \
            or item in self._relationships \
            or item in relationship._BUILTINS

    def __getitem__(self, id: str) -> Union[Term, Relationship]:
        """Get any entity in the ontology graph with the given identifier.
        """
        try:
            return self.get_relationship(id)
        except KeyError:
            pass
        try:
            return self.get_term(id)
        except KeyError:
            pass
        raise KeyError(f"could not find entity: {id}")

    def __repr__(self):
        args = (self.path,) if self.path is not None else ()
        kwargs = {"timeout": (self.timeout, 2)}
        if self.import_depth > 0:
            kwargs["import_depth"] = (self.import_depth, -1)
        if not self._default_session:
            kwargs["session"] = (self.session, None)
        return make_repr("Ontology", *args, **kwargs)

    # ------------------------------------------------------------------------

    def terms(self) -> SizedIterator[Term]:
        """Iterate over the terms of the ontology graph.
        """
        return SizedIterator(
            itertools.chain(
                (
                    Term(self, t._data())
                    for ref in self.imports.values()
                    for t in ref.terms()
                ),
                (
                    Term(self, t) for t in self._terms.values()
                ),
            ),
            length=(
                sum(len(r.terms()) for r in self.imports.values())
                + len(self._terms)
            ),
        )

    def relationships(self) -> SizedIterator[Relationship]:
        """Iterate over the relationships of the ontology graph.

        Builtin ontologies (``is_a`` and ``has_subclass``) are not part of the
        returned sequence.
        """
        return SizedIterator(
            itertools.chain(
                (
                    Relationship(self, r._data())
                    for ref in self.imports.values()
                    for r in ref.relationships()
                ),
                (
                    self.get_relationship(r) for r in self._relationships
                ),
            ),
            length=(
                sum(len(r.relationships()) for r in self.imports.values())
                + len(self._relationships)
            ),
        )

    def create_term(self, id: str) -> Term:
        """Create a new term with the given identifier.

        Raises:
            ValueError: if the provided ``id`` already identifies an entity
                in the ontology graph.

        """
        with contextlib.suppress(KeyError):
            raise ValueError(f"identifier already in use: {id} ({self[id]})")
        self._terms[id] = termdata = _TermData(id)
        return Term(self, termdata)

    def create_relationship(self, id: str) -> Relationship:
        """Create a new relationship with the given identifier.

        Raises:
            ValueError: if the provided ``id`` already identifies an entity
                in the ontology graph.

        """
        if id in self._relationships or id in relationship._BUILTINS:
            raise ValueError(f"identifier already in use: {id}")
        self._relationships[id] = reldata = _RelationshipData(id)
        return Relationship(self, reldata)

    def get_term(self, id: str) -> Term:
        """Get a term in the ontology graph from the given identifier.

        Raises:
            KeyError: if the provided ``id`` cannot be found in the terms of
                the ontology graph.

        """
        for dep in self.imports.values():
            with contextlib.suppress(KeyError):
                return Term(self, dep.get_term(id)._data())
        return Term(self, self._terms[id])

    def get_relationship(self, id: str) -> Relationship:
        """Get a relationship in the ontology graph from the given identifier.

        Builtin ontologies (``is_a`` and ``has_subclass``) can be accessed
        with this method.

        Raises:
            KeyError: if the provided ``id`` cannot be found in the
                relationships of the ontology graph.

        """
        if id in relationship._BUILTINS:
            return Relationship(self, relationship._BUILTINS[id])
        for dep in self.imports.values():
            with contextlib.suppress(KeyError):
                return Relationship(self, dep.get_relationship(id)._data())
        return Relationship(self, self._relationships[id])
