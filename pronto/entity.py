import collections.abc
import datetime
import weakref
import typing
from typing import Any, Callable, Optional, FrozenSet

from .definition import Definition
from .synonym import Synonym
from .pv import PropertyValue
from .xref import Xref
from .utils.meta import roundrepr, typechecked
from .utils.impl import set

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class EntityData():
    __slots__ = ("__weakref__",)


class Entity():
    """An entity in the ontology graph.

    With respects to the OBO semantics, an `Entity` is either a term or a
    relationship in the ontology graph. Any entity has a unique identifier as
    well as some common properties.
    """

    if typing.TYPE_CHECKING:

        __ontology: 'weakref.ReferenceType[Ontology]'
        __data: 'weakref.ReferenceType[EntityData]'

        __slots__ = ("__weakref__", "__ontology", "__data")

        def __init__(self, ontology: 'Ontology', data: 'EntityData'):
            self.__ontology = weakref.ref(ontology)
            self.__data = weakref.ref(data)

        def _data(self) -> 'EntityData':
            rdata = self.__data()
            if rdata is None:
                raise RuntimeError("entity data was deallocated")
            return rdata

        def _ontology(self) -> 'Ontology':
            ontology = self.__ontology()
            if ontology is None:
                raise RuntimeError("referenced ontology was deallocated")
            return ontology

    else:

        def __init__(self, ontology: 'Ontology', data: 'EntityData'):
            self._ontology = weakref.ref(ontology)
            self._data = weakref.ref(data)


    # --- Magic Methods ------------------------------------------------------

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        return False

    def __lt__(self, other):
        if isinstance(other, Entity):
            return self.id < other.id
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Entity):
            return self.id <= other.id
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Entity):
            return self.id > other.id
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Entity):
            return self.id >= other.id
        return NotImplemented

    def __hash__(self):
        return hash((self.id))

    def __repr__(self):
        return roundrepr.make(type(self).__name__, self.id, name=(self.name, None))

    # --- Data descriptors ---------------------------------------------------

    @property
    def alternate_ids(self) -> FrozenSet[str]:
        return frozenset(self._data().alternate_ids)

    @alternate_ids.setter
    @typechecked(property=True)
    def alternate_ids(self, ids: FrozenSet[str]):
        self._data().alternate_ids = set(ids)

    @property
    def annotations(self) -> FrozenSet[PropertyValue]:
        return frozenset(self._data().annotations)

    @property
    def anonymous(self) -> bool:
        return self._data().anonymous

    @anonymous.setter
    def anonymous(self, value: bool):
        self._data().anonymous = value

    @property
    def builtin(self) -> bool:
        return self._data().builtin

    @builtin.setter
    @typechecked(property=True)
    def builtin(self, value: bool):
        self._data().builtin = value

    @property
    def comment(self) -> Optional[str]:
        return self._data().comment

    @comment.setter
    def comment(self, value: Optional[str]):
        self._data().comment = value

    @property
    def created_by(self) -> Optional[str]:
        return self._data().created_by

    @created_by.setter
    @typechecked(property=True)
    def created_by(self, value: Optional[str]):
        self._data().created_by = value

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        return self._data().creation_date

    @creation_date.setter
    @typechecked(property=True)
    def creation_date(self, value: Optional[datetime.datetime]):
        self._data().creation_date = value

    @property
    def definition(self) -> Optional[Definition]:
        return self._data().definition

    @definition.setter
    @typechecked(property=True)
    def definition(self, definition: Optional[Definition]):
        self._data().definition = definition

    @property
    def equivalent_to(self) -> FrozenSet[str]:
        return frozenset(self._data().equivalent_to)

    @equivalent_to.setter
    def equivalent_to(self, equivalent_to: FrozenSet[str]):
        self._data().equivalent_to = set(equivalent_to)

    @property
    def id(self):
        return self._data().id

    @property
    def name(self) -> Optional[str]:
        return self._data().name

    @name.setter
    @typechecked(property=True)
    def name(self, value: Optional[str]):
        self._data().name = value

    @property
    def namespace(self) -> Optional[str]:
        return self._data().namespace

    @namespace.setter
    @typechecked(property=True)
    def namespace(self, ns: Optional[str]):
        self._data().namespace = ns

    @property
    def obsolete(self) -> bool:
        return self._data().obsolete

    @obsolete.setter
    @typechecked(property=True)
    def obsolete(self, value: bool):
        self._data().obsolete = value

    @property
    def subsets(self) -> FrozenSet[str]:
        return frozenset(self._data().subsets)

    @subsets.setter
    @typechecked(property=True)
    def subsets(self, subsets: FrozenSet[str]):
        declared = set(s.id for s in self._ontology().metadata.subsetdefs)
        for subset in subsets:
            if subset not in declared:
                raise ValueError(f"undeclared subset: {subset!r}")
        self._data().subsets = set(subsets)

    @property
    def synonyms(self) -> FrozenSet[Synonym]:
        ontology, termdata = self._ontology(), self._data()
        return frozenset(Synonym(ontology, s) for s in termdata.synonyms)

    @synonyms.setter
    @typechecked(property=True)
    def synonyms(self, synonyms: FrozenSet[Synonym]):
        self._data().synonyms = set(synonyms)

    @property
    def xrefs(self) -> FrozenSet[Xref]:
        return frozenset(self._data().xrefs)

    @xrefs.setter
    @typechecked(property=True)
    def xrefs(self, xrefs: FrozenSet[Xref]):
        self._data().xrefs = set(xrefs)
