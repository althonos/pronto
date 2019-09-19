# coding: utf-8

import functools
import typing
import weakref
from typing import Optional, Set

import fastobo

from .xref import Xref
from .utils.repr import make_repr, roundrepr

if typing.TYPE_CHECKING:
    from .ontology import Ontology

@functools.total_ordering
@roundrepr
class SynonymType(object):

    id: str
    description: str
    scope: Optional[str]

    __slots__ = ("__weakref__",) + tuple(__annotations__)

    def __init__(self, id: str, description: str, scope: Optional[str]=None):
        if scope is not None:
            if scope not in {'EXACT', 'RELATED', 'BROAD', 'NARROW'}:
                raise ValueError(f"invalid synonym scope: {scope}")
        self.id = id
        self.description = description
        self.scope = scope

    def __eq__(self, other):
        if not isinstance(other, _SynonymData):
            return False
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__slots__[1:]
        )

    def __lt__(self, other):
        if not isinstance(other, _SynonymData):
            return NotImplemented
        if self.scope is not None and other.scope is not None:
            return (self.id, self.description, self.scope) < (other.id, other.description, other.scope)
        else:
            return (self.id, self.description) < (other.id, other.description)

    def __hash__(self):
        return hash((self.id, self.description, self.scope))


@functools.total_ordering
@roundrepr
class _SynonymData(object):

    description: str
    scope: Optional[str]
    type: Optional[str]
    xrefs: Set[Xref]

    __slots__ = ("__weakref__",) + tuple(__annotations__)

    def __eq__(self, other):
        if not isinstance(other, _SynonymData):
            return False
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__slots__[1:]
        )

    def __lt__(self, other):
        if not isinstance(other, _SynonymData):
            return NotImplemented
        if self.type is not None and other.type is not None:
            return (self.description, self.scope, self.type, frozenset(self.xrefs)) \
                 < (self.description, self.scope, other.type, frozenset(other.xrefs))
        else:
            return (self.description, self.scope, frozenset(self.xrefs)) \
                 < (self.description, self.scope, frozenset(other.xrefs))

    def __hash__(self):
        return hash((self.description, self.scope, self.type, frozenset(self.xrefs)))

    def __init__(
        self,
        description: str,
        scope: Optional[str]=None,
        type: Optional[str]=None,
        xrefs: Set[Xref]=None
    ):
        self.description = description
        self.scope = scope
        self.type = type
        self.xrefs = xrefs or set()

    @classmethod
    def _from_ast(cls, syn: fastobo.syn.Synonym):
        xrefs =  {Xref._from_ast(x) for x in syn.xrefs}
        type_ = str(syn.type) if syn.type is not None else None
        return cls(syn.desc, syn.scope, type_, xrefs)

    def _to_ast(self) -> fastobo.syn.Synonym:
        return fastobo.syn.Synonym(
            self.description,
            self.scope,
            fastobo.id.parse(self.type) if self.type is not None else None,
            map(Xref._to_ast, self.xrefs),
        )


@functools.total_ordering
class Synonym(object):

    _ontology: 'weakref.ReferenceType[Ontology]'
    _syndata: 'weakref.ReferenceType[_SynonymData]'

    def _to_ast(self):
        return self._syndata()._to_ast()

    def __init__(self, ontology: 'Ontology', syndata: '_SynonymData'):
        if syndata.type is not None:
            synonyms = ontology.metadata.synonymtypedefs
            if not any(s.id == syndata.type for s in synonyms):
                raise ValueError(f"undeclared synonym type: {syndata.type}")

        self._ontology = weakref.ref(ontology)
        self._syndata = weakref.ref(syndata)

    def __eq__(self, other):
        if isinstance(other, Synonym):
            return self._syndata() == other._syndata()
        return False

    def __lt__(self, other):
        if not isinstance(other, Synonym):
            return False
        return self._syndata().__lt__(other._syndata())

    def __hash__(self):
        return hash(self._syndata())

    def __repr__(self):
        return make_repr(
            "Synonym",
            self.description,
            scope=(self.scope, None),
            type=(self.type, None),
            xrefs=(self.xrefs, set()),
        )

    @property
    def description(self) -> str:
        return self._syndata().description

    @description.setter
    def description(self, description: str):
        if __debug__:
            if not isinstance(description, str):
                msg = "'description' must be str, not {}"
                raise TypeError(msg.format(type(description).__name__))
        self._syndata().description = description

    @property
    def type(self) -> Optional[SynonymType]:
        ontology, syndata = self._ontology(), self._syndata()
        if syndata.type is not None:
            return ontology.metadata.synonymtypedefs[syndata.type]
        return None

    @type.setter
    def type(self, type_: Optional[SynonymType]):
        if __debug__:
            if type_ is not None and not isinstance(type, SynonymType):
                msg = "'type' must be SynonymType or None, not {}"
                raise TypeError(msg.format(type(type_).__name__))
        synonyms = self._ontology().metadata.synonymtypedefs
        if type is not None and type_.id not in synonyms:
            raise ValueError(f"undeclared synonym type: {type_.id}")
        self._syndata().type = type_.id if type_ is not None else None

    @property
    def scope(self) -> Optional[str]:
        return self._syndata().scope

    @scope.setter
    def scope(self, scope: str):
        if __debug__:
            if scope is not None and not isinstance(scope, str):
                msg = "'scope' must be str or None, not {}"
                raise TypeError(msg.format(type(scope).__name__))
        if scope not in {'EXACT', 'RELATED', 'BROAD', 'NARROW'}:
            raise ValueError(f"invalid synonym scope: {scope}")
        self._syndata().scope = scope

    @property
    def xrefs(self):
        return self._syndata().xrefs
