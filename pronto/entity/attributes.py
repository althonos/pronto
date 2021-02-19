import typing
from typing import Iterable, Iterator

from ..utils.meta import typechecked
from . import Entity, EntitySet

if typing.TYPE_CHECKING:
    from ..relationship import Relationship

_E = typing.TypeVar("_E", bound=Entity)
_S = typing.TypeVar("_S", bound=EntitySet)


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
