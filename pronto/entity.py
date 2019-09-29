import collections.abc
import datetime
import weakref
import typing
from typing import Any, Callable, Optional, FrozenSet

from .definition import Definition
from .synonym import Synonym
from .pv import PropertyValue
from .xref import Xref
from .utils.meta import roundrepr
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
    def alternate_ids(self, ids: FrozenSet[str]):
        if __debug__:
            msg = "'alternate_ids' must be a set of str, not {}"
            if not isinstance(ids, collections.abc.FrozenSet):
                raise TypeError(msg.format(type(ids).__name__))
            for x in (x for x in ids if isinstance(x, str)):
                raise TypeError(msg.format(type(x).__name__))
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
    def builtin(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'builtin' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
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
    def created_by(self, value: Optional[str]):
        if __debug__:
            if value is not None and not isinstance(value, str):
                msg = "'created_by' must be str or None, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._data().created_by = value

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        return self._data().creation_date

    @creation_date.setter
    def creation_date(self, value: Optional[datetime.datetime]):
        if __debug__:
            if value is not None and not isinstance(value, datetime.datetime):
                msg = "'creation_date' must be datetime or None, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._data().creation_date = value

    @property
    def definition(self) -> Optional[Definition]:
        return self._data().definition

    @definition.setter
    def definition(self, definition: Optional[Definition]):
        if __debug__:
            if definition is not None and not isinstance(definition, Definition):
                msg = "'definition' must be a Definition, not {}"
                raise TypeError(msg.format(type(definition).__name__))
        self._data().definition = definition

    @property
    def equivalent_to(self) -> FrozenSet[str]:
        return frozenset(self._data().equivalent_to)

    @equivalent_to.setter
    def equivalent_to(self, equivalent_to: FrozenSet[str]):
        if __debug__:
            msg = "'equivalent_to' must be a set of str, not {}"
            if not isinstance(equivalent_to, collections.abc.Set):
                raise TypeError(msg.format(type(equivalent_to).__name__))
            for x in (x for x in equivalent_to if not isinstance(x, str)):
                raise TypeError(msg.format(type(x).__name__))
        self._data().equivalent_to = set(equivalent_to)

    @property
    def id(self):
        return self._data().id

    @id.setter
    def id(self, value):
        raise RuntimeError("cannot set `id` of entities directly")

    @property
    def name(self) -> Optional[str]:
        return self._data().name

    @name.setter
    def name(self, value: Optional[str]):
        if __debug__:
            if value is not None and not isinstance(value, str):
                msg = "'name' must be str or None, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._data().name = value

    @property
    def namespace(self) -> Optional[str]:
        return self._data().namespace

    @namespace.setter
    def namespace(self, ns: Optional[str]):
        if __debug__:
            if ns is not None and not isinstance(ns, str):
                msg = "'namespace' must be str or None, not {}"
                raise TypeError(msg.format(type(ns).__name__))
        self._data().namespace = ns

    @property
    def obsolete(self) -> bool:
        return self._data().obsolete

    @obsolete.setter
    def obsolete(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'obsolete' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._data().obsolete = value

    @property
    def subsets(self) -> FrozenSet[str]:
        return frozenset(self._data().subsets)

    @subsets.setter
    def subsets(self, subsets: FrozenSet[str]):
        if __debug__:
            msg = "'subsets' must be a set of str, not {}"
            if not isinstance(subsets, collections.abc.Set):
                raise TypeError(msg.format(type(subsets).__name__))
            for x in (x for x in subsets if not isinstance(x, str)):
                raise TypeError(msg.format(type(x).__name__))
        for subset in subsets:
            subsetdefs = self._ontology().metadata.subsetdefs
            if not any(subset == subsetdef.id for subsetdef in subsetdefs):
                raise ValueError(f"undeclared subset: {subset!r}")
        self._data().subsets = set(subsets)

    @property
    def synonyms(self) -> FrozenSet[Synonym]:
        ontology, termdata = self._ontology(), self._data()
        return frozenset(Synonym(ontology, s) for s in termdata.synonyms)

    @synonyms.setter
    def synonyms(self, synonyms: FrozenSet[Synonym]):
        if __debug__:
            msg = "'synonyms' must be a set of Synonym, not {}"
            if not isinstance(synonyms, collections.abc.Set):
                raise TypeError(msg.format(type(synonyms).__name__))
            for x in (x for x in synonyms if not isinstance(x, Synonym)):
                raise TypeError(msg.format(type(x).__name__))
        self._data().synonyms = set(synonyms)

    @property
    def xrefs(self) -> FrozenSet[Xref]:
        return frozenset(self._data().xrefs)

    @xrefs.setter
    def xrefs(self, xrefs: FrozenSet[Xref]):
        if __debug__:
            msg = "'xrefs' must be a set of Xref, not {}"
            if not isinstance(xrefs, collections.abc.Set):
                raise TypeError(msg.format(type(xrefs).__name__))
            for x in (x for x in xrefs if not isinstance(x, Xref)):
                raise TypeError(msg.format(type(x).__name__))
        self._data().xrefs = set(xrefs)
