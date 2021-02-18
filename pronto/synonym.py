# coding: utf-8

import functools
import typing
import weakref
from typing import FrozenSet, Iterable, Optional, Set

from .utils.meta import roundrepr, typechecked
from .xref import Xref

if typing.TYPE_CHECKING:
    from .ontology import Ontology


_SCOPES = frozenset({"EXACT", "RELATED", "BROAD", "NARROW", None})
__all__ = ["SynonymType", "SynonymData", "Synonym"]


@roundrepr
@functools.total_ordering
class SynonymType(object):
    """A user-defined synonym type."""

    id: str
    description: str
    scope: Optional[str]

    __slots__ = ("__weakref__", "id", "description", "scope")

    @typechecked()
    def __init__(self, id: str, description: str, scope: Optional[str] = None):
        if scope not in _SCOPES:
            raise ValueError(f"invalid synonym scope: {scope}")
        self.id = id
        self.description = description
        self.scope = scope

    def __eq__(self, other):
        if isinstance(other, SynonymType):
            return self.id == other.id
        return False

    def __lt__(self, other):
        if isinstance(other, SynonymType):
            if self.id < other.id:
                return True
            return self.id == other.id and self.description < other.description
        return NotImplemented

    def __hash__(self):
        return hash((SynonymType, self.id))


@roundrepr
@functools.total_ordering
class SynonymData(object):
    """Internal data storage of `Synonym` information."""

    description: str
    scope: Optional[str]
    type: Optional[str]
    xrefs: Set[Xref]

    __slots__ = ("__weakref__", "description", "type", "xrefs", "scope")

    def __eq__(self, other):
        if isinstance(other, SynonymData):
            return self.description == other.description and self.scope == other.scope
        return False

    def __lt__(self, other):  # FIXME?
        if not isinstance(other, SynonymData):
            return NotImplemented
        if self.type is not None and other.type is not None:
            return (self.description, self.scope, self.type, frozenset(self.xrefs)) < (
                self.description,
                self.scope,
                other.type,
                frozenset(other.xrefs),
            )
        else:
            return (self.description, self.scope, frozenset(self.xrefs)) < (
                self.description,
                self.scope,
                frozenset(other.xrefs),
            )

    def __hash__(self):
        return hash((self.description, self.scope))

    def __init__(
        self,
        description: str,
        scope: Optional[str] = None,
        type: Optional[str] = None,
        xrefs: Optional[Iterable[Xref]] = None,
    ):
        if scope not in _SCOPES:
            raise ValueError(f"invalid synonym scope: {scope}")
        self.description = description
        self.scope = scope
        self.type = type
        self.xrefs = set(xrefs) if xrefs is not None else set()


@functools.total_ordering
class Synonym(object):
    """A synonym for an entity, with respect to the OBO terminology."""

    __ontology: "Ontology"

    if typing.TYPE_CHECKING:

        __data: "weakref.ReferenceType[SynonymData]"

        def __init__(self, ontology: "Ontology", data: "SynonymData"):
            self.__data = weakref.ref(data)
            self.__ontology = ontology

        def _data(self) -> SynonymData:
            rdata = self.__data()
            if rdata is None:
                raise RuntimeError("synonym data was deallocated")
            return rdata

    else:

        __slots__: Iterable[str] = ("__weakref__", "__ontology", "_data")

        def __init__(self, ontology: "Ontology", syndata: "SynonymData"):
            if syndata.type is not None:
                if not any(t.id == syndata.type for t in ontology.synonym_types()):
                    raise ValueError(f"undeclared synonym type: {syndata.type}")
            self._data = weakref.ref(syndata)
            self.__ontology = ontology

    def __eq__(self, other: object):
        if isinstance(other, Synonym):
            return self._data() == other._data()
        return False

    def __lt__(self, other: object):
        if not isinstance(other, Synonym):
            return False
        return self._data().__lt__(other._data())

    def __hash__(self):
        return hash(self._data())

    def __repr__(self):
        return roundrepr.make(
            "Synonym",
            self.description,
            scope=(self.scope, None),
            type=(self.type, None),
            xrefs=(self.xrefs, set()),
        )

    @property
    def description(self) -> str:
        return self._data().description

    @description.setter  # type: ignore
    @typechecked(property=True)
    def description(self, description: str) -> None:
        self._data().description = description

    @property
    def type(self) -> Optional[SynonymType]:
        ontology, syndata = self.__ontology, self._data()
        if syndata.type is not None:
            return next(t for t in ontology.synonym_types() if t.id == syndata.type)
        return None

    @type.setter  # type: ignore
    @typechecked(property=True)
    def type(self, type_: Optional[SynonymType]) -> None:
        synonyms: Iterable[SynonymType] = self.__ontology.synonym_types()
        if type_ is not None and not any(type_.id == s.id for s in synonyms):
            raise ValueError(f"undeclared synonym type: {type_.id}")
        self._data().type = type_.id if type_ is not None else None

    @property
    def scope(self) -> Optional[str]:
        return self._data().scope

    @scope.setter  # type: ignore
    @typechecked(property=True)
    def scope(self, scope: Optional[str]):
        if scope not in _SCOPES:
            raise ValueError(f"invalid synonym scope: {scope}")
        self._data().scope = scope

    @property
    def xrefs(self) -> Set[Xref]:
        return self._data().xrefs

    @xrefs.setter
    def xrefs(self, xrefs: Iterable[Xref]):
        self._data().xrefs = set(xrefs)
