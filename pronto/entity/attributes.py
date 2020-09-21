import typing
from typing import Iterable, Iterator

from ..utils.meta import typechecked
from . import Entity, EntitySet

if typing.TYPE_CHECKING:
    from ..relationship import Relationship

_E = typing.TypeVar("_E", bound="Entity")
_S = typing.TypeVar("_S", bound="EntitySet")


class AlternateIDs(typing.MutableSet[str], typing.Generic[_E]):
    """A dedicated mutable set to manage the alternate IDs of an entity.

    Editing the alternate IDs of an entity also allows retrieving it in the
    source ontology using its alternate IDs.

    Example:
        >>> ont = pronto.Ontology()
        >>> t1 = ont.create_term("TST:001")
        >>> ont["ALT:001"]
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        KeyError: 'ALT:001'
        >>> t1.alternate_ids.add("ALT:001")
        >>> ont["ALT:001"]
        Term('TST:001')

    """

    def __init__(self, entity: _E):
        self._inner = entity._data().alternate_ids
        self._entity = entity
        self._ontology = entity._ontology()

    def __contains__(self, item: object) -> bool:
        return item in self._inner

    def __len__(self) -> int:
        return len(self._inner)

    def __iter__(self) -> Iterator[str]:
        return iter(self._inner)

    def __repr__(self):
        return f"{type(self).__name__}({self._inner})"

    @typechecked()
    def add(self, id: str):
        if id in self._ontology:
            entity = self._ontology[id]
            raise ValueError(f"identifier already in use: {id} ({entity})")
        self._inner.add(id)
        self._entity._data_getter(self._ontology).aliases[id] = self._entity._data()

    @typechecked()
    def discard(self, item: str):
        self._inner.discard(item)
        del self._entity._data_getter(self._ontology).aliases[item]

    def clear(self):
        for id_ in self._inner:
            del self._entity._data_getter(self._ontology).aliases[id_]
        self._inner.clear()

    def pop(self) -> str:
        id_ = self.pop()
        del self._entity._data_getter(self._ontology).aliases[id_]
        return id_

    def update(self, items: Iterable[str]):
        for item in items:
            self.add(item)


class Relationships(typing.MutableMapping["Relationship", _S], typing.Generic[_E, _S]):
    """A dedicated mutable mapping to manage the relationships of an entity."""

    def __init__(self, entity: _E):
        self._inner = entity._data().relationships
        self._entity = entity
        self._ontology = entity._ontology()

    def __getitem__(self, item: "Relationship") -> _S:
        if item.id not in self._inner:
            raise KeyError(item)
        s = self._entity._Set()
        s._ids = self._inner[item.id]
        s._ontology = self._ontology
        return s

    def __delitem__(self, item: "Relationship"):
        if item.id not in self._inner:
            raise KeyError(item)
        del self._inner[item.id]

    def __len__(self) -> int:
        return len(self._inner)

    def __iter__(self) -> Iterator["Relationship"]:
        from ..relationship import Relationship

        return (self._ontology.get_relationship(id_) for id_ in self._inner)

    def __setitem__(self, key: "Relationship", entities: Iterable[_E]):
        if key._ontology() is not self._ontology:
            raise ValueError("cannot use a relationship from a different ontology")
        self._inner[key.id] = {entity.id for entity in entities}
