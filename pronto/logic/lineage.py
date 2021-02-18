import abc
import collections
import typing
import warnings
from typing import AbstractSet, Deque, Dict, Optional, Set, Tuple, cast

from ..utils.meta import roundrepr

if typing.TYPE_CHECKING:
    from ..entity import Entity
    from ..term import Term, TermSet, TermData
    from ..relationship import Relationship, RelationshipData, RelationshipSet
    from ..ontology import Ontology, _DataGraph


_E = typing.TypeVar("_E", bound="Entity")

# --- Storage ----------------------------------------------------------------


@roundrepr
class Lineage(object):
    """An internal type to store the superclasses and subclasses of a term.

    Used in `Ontology` to cache subclassing relationships between terms since
    only the superclassing relationships are explicitly declared in source
    documents.
    """

    __slots__ = ("sub", "sup")

    def __init__(
        self,
        sub: Optional[AbstractSet[str]] = None,
        sup: Optional[AbstractSet[str]] = None,
    ):
        self.sub: Set[str] = set(sub) if sub is not None else set()  # type: ignore
        self.sup: Set[str] = set(sup) if sup is not None else set()  # type: ignore

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Lineage):
            return self.sub == other.sub and self.sup == other.sup
        return False

    # `Lineage` is mutable so this is the explicit way to tell it's unhashable
    # (see https://docs.python.org/3/reference/datamodel.html#object.__hash__)
    __hash__ = None  # type: ignore


# --- Abstract handlers ------------------------------------------------------


class LineageHandler(typing.Generic[_E], typing.Iterable[_E]):
    def __init__(
        self, entity: _E, distance: Optional[int] = None, with_self: bool = False
    ):
        self.entity = entity
        self.distance = distance
        self.with_self = with_self
        # TODO: API compatibilty with previous iterator (remove for v3.0.0)
        self._it: typing.Optional[typing.Iterator[_E]] = None

    def __next__(self) -> _E:
        if self._it is None:
            ty = type(self.entity).__name__
            warnings.warn(
                f"`{ty}.subclasses()` and `{ty}.superclasses()` will not "
                "return iterators in next major version, but iterables. "
                "Update your code to use `iter(...)` if needed.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            self._it = iter(self)
        return next(cast(typing.Iterator[_E], self._it))

    def _add(self, subclass: _E, superclass: _E):
        if superclass._ontology() is not subclass._ontology():
            ty = type(subclass).__name__
            raise ValueError(f"cannot use `{ty}` instances from different ontologies")
        lineage = self._get_data().lineage
        lineage[subclass.id].sup.add(superclass.id)
        lineage[superclass.id].sub.add(subclass.id)

    def _remove(self, subclass: _E, superclass: _E):
        if superclass._ontology() is not subclass._ontology():
            ty = type(subclass).__name__
            raise ValueError(f"cannot use `{ty}` instances from different ontologies")
        lineage = self._get_data().lineage
        lineage[subclass.id].sup.remove(superclass.id)
        lineage[superclass.id].sub.remove(subclass.id)

    @abc.abstractmethod
    def __iter__(self) -> "LineageIterator[_E]":
        return NotImplemented

    @abc.abstractmethod
    def _get_data(self) -> "_DataGraph":
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def add(self, other: _E) -> None:
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def remove(self, other: _E) -> None:
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def clear(self) -> None:
        return NotImplemented  # type: ignore


class TermHandler(LineageHandler["Term"]):
    @abc.abstractmethod
    def __iter__(self) -> "TermIterator":
        return NotImplemented

    def _get_data(self) -> "_DataGraph[TermData]":
        return self.entity._ontology()._terms

    def to_set(self) -> "TermSet":
        return self.__iter__().to_set()


class RelationshipHandler(LineageHandler["Relationship"]):
    @abc.abstractmethod
    def __iter__(self) -> "RelationshipIterator":
        return NotImplemented

    def _get_data(self) -> "_DataGraph[RelationshipData]":
        return self.entity._ontology()._relationships

    def to_set(self) -> "RelationshipSet":
        return self.__iter__().to_set()


class SuperentitiesHandler(LineageHandler):
    @abc.abstractmethod
    def __iter__(self) -> "SuperentitiesIterator":
        return NotImplemented

    def add(self, superclass: _E):
        self._add(subclass=self.entity, superclass=superclass)

    def remove(self, superclass: _E):
        self._remove(subclass=self.entity, superclass=superclass)

    def clear(self):
        lineage = self._get_data().lineage
        for subclass in lineage[self.entity.id].sup:
            lineage[subclass].sub.remove(self.entity.id)
        lineage[self.entity.id].sup.clear()


class SubentitiesHandler(LineageHandler):
    @abc.abstractmethod
    def __iter__(self) -> "SubentitiesIterator":
        return NotImplemented

    def add(self, subclass: _E):
        self._add(superclass=self.entity, subclass=subclass)

    def remove(self, subclass: _E):
        self._remove(superclass=self.entity, subclass=subclass)

    def clear(self):
        lineage = self._get_data().lineage
        for superclass in lineage[self.entity.id].sub:
            lineage[superclass].sup.remove(self.entity.id)
        lineage[self.entity.id].sub.clear()


# --- Concrete handlers ------------------------------------------------------


class SubclassesHandler(SubentitiesHandler, TermHandler):
    def __iter__(self) -> "SubclassesIterator":
        return SubclassesIterator(
            self.entity, distance=self.distance, with_self=self.with_self
        )


class SubpropertiesHandler(SubentitiesHandler, RelationshipHandler):
    def __iter__(self) -> "SubpropertiesIterator":
        return SubpropertiesIterator(
            self.entity, distance=self.distance, with_self=self.with_self
        )


class SuperclassesHandler(SuperentitiesHandler, TermHandler):
    def __iter__(self) -> "SuperclassesIterator":
        return SuperclassesIterator(
            self.entity, distance=self.distance, with_self=self.with_self
        )


class SuperpropertiesHandler(SuperentitiesHandler, RelationshipHandler):
    def __iter__(self) -> "SuperpropertiesIterator":
        return SuperpropertiesIterator(
            self.entity, distance=self.distance, with_self=self.with_self
        )


# --- Abstract iterators -----------------------------------------------------


class LineageIterator(typing.Generic[_E], typing.Iterator[_E]):

    _distmax: float
    _ontology: "Ontology"
    _linked: Set[str]
    _done: Set[str]
    _frontier: Deque[Tuple[str, int]]
    _queue: Deque[str]

    # ---

    @abc.abstractmethod
    def _get_data(self) -> "_DataGraph":
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def _get_neighbors(self, node: str) -> Set[str]:
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def _get_entity(self, node: str) -> _E:
        return NotImplemented  # type: ignore

    @abc.abstractmethod
    def _maxlen(self) -> int:
        return NotImplemented  # type: ignore

    # ---

    def __init__(
        self, *entities: _E, distance: Optional[int] = None, with_self: bool = True
    ) -> None:

        self._distmax = float("inf") if distance is None else distance

        # if not term is given, `__next__` will raise `StopIterator` on
        # the first call without ever accessing `self._ontology`, so it's
        # safe not to initialise it here in that case.
        if entities:
            self._ontology = ont = entities[0]._ontology()

        self._linked: Set[str] = set()
        self._done: Set[str] = set()
        self._frontier: Deque[Tuple[str, int]] = collections.deque()
        self._queue: Deque[str] = collections.deque()

        for entity in entities:
            self._frontier.append((entity.id, 0))
            self._linked.add(entity.id)
            if with_self:
                self._queue.append(entity.id)

    def __iter__(self) -> "LineageIterator[_E]":
        return self

    def __length_hint__(self) -> int:
        """Return an estimate of the number of remaining entities to yield."""
        if self._queue or self._frontier:
            return self._maxlen() - len(self._linked) + len(self._queue)
        else:
            return 0

    def __next__(self) -> "_E":
        while self._frontier or self._queue:
            # Return any element currently queued
            if self._queue:
                return self._get_entity(self._queue.popleft())
            # Get the next node in the frontier
            node, distance = self._frontier.popleft()
            self._done.add(node)
            # Process its neighbors if they are not too far
            neighbors: Set[str] = set(self._get_neighbors(node))
            if neighbors and distance < self._distmax:
                for node in sorted(neighbors.difference(self._done)):
                    self._frontier.append((node, distance + 1))
                for neighbor in sorted(neighbors.difference(self._linked)):
                    self._linked.add(neighbor)
                    self._queue.append(neighbor)
        # Stop iteration if no more elements to process
        raise StopIteration


class TermIterator(LineageIterator["Term"]):
    def _maxlen(self):
        return len(self._ontology.terms())

    def _get_entity(self, id):
        return self._ontology.get_term(id)

    def _get_data(self):
        return self._ontology._terms

    def to_set(self) -> "TermSet":
        """Collect all classes into a `~pronto.TermSet`.

        Hint:
            This method is useful to query an ontology using a method chaining
            syntax, for instance::

            >>> cio = pronto.Ontology("cio.obo")
            >>> sorted(cio['CIO:0000034'].subclasses().to_set().ids)
            ['CIO:0000034', 'CIO:0000035', 'CIO:0000036']

        """
        from ..term import TermSet

        return TermSet(self)


class RelationshipIterator(LineageIterator["Relationship"]):
    def _maxlen(self):
        return len(self._ontology.relationships())

    def _get_entity(self, id):
        return self._ontology.get_relationship(id)

    def _get_data(self):
        return self._ontology._relationships

    def to_set(self) -> "RelationshipSet":
        """Collect all relationshisp into a `~pronto.RelationshipSet`.

        Hint:
            This method is useful to query an ontology using a method chaining
            syntax.

        """
        from ..relationship import RelationshipSet

        return RelationshipSet(self)


class SubentitiesIterator(LineageIterator):
    def _get_neighbors(self, node: str) -> Set[str]:
        return self._get_data().lineage.get(node, Lineage()).sub


class SuperentitiesIterator(LineageIterator):
    def _get_neighbors(self, node: str) -> Set[str]:
        return self._get_data().lineage.get(node, Lineage()).sup


# --- Concrete iterators -----------------------------------------------------


class SubclassesIterator(SubentitiesIterator, TermIterator):
    """An iterator over the subclasses of one or several `~pronto.Term`."""


class SuperclassesIterator(SuperentitiesIterator, TermIterator):
    """An iterator over the superclasses of one or several `~pronto.Term`."""


class SubpropertiesIterator(SubentitiesIterator, RelationshipIterator):
    """An iterator over the subproperties of one or several `~pronto.Relationship`."""


class SuperpropertiesIterator(SuperentitiesIterator, RelationshipIterator):
    """An iterator over the superproperties of one or several `~pronto.Relationship`."""
