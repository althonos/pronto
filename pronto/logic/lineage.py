import abc
import collections
import typing
import warnings
from typing import AbstractSet, Deque, Dict, Iterator, Iterable, Optional, Set, Tuple

from ..utils.meta import roundrepr

if typing.TYPE_CHECKING:
    from ..term import Term, TermSet
    from ..relationship import Relationship
    from ..ontology import Ontology


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
    __hash__ = None



class LineageHandler(Iterable["Term"]):

    def __init__(self, term: "Term", distance: Optional[int], with_self: Optional[int]):
        self.term = term
        self.distance = distance
        self.with_self = with_self
        # TODO: API compatibilty with previous iterator (remove for v3.0.0)
        self._it = None

    def __next__(self):
        if self._it is None:
            warnings.warn(
                "`Term.subclasses()` and `Term.superclasses()` will not return"
                "iterator in next major version, but iterables. Update your "
                "code to use `iter(...)` if needed.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            self._it = iter(self)
        return next(self._it)

    def to_set(self):
        return iter(self).to_set()

    def _add(self, subclass: "Term", superclass: "Term"):
        if superclass._ontology() is not subclass._ontology():
            raise ValueError("cannot use `Term` instances from different ontologies")
        cache = subclass._ontology()._inheritance
        cache[subclass.id].sup.add(superclass.id)
        cache[superclass.id].sub.add(subclass.id)

    def _remove(self, subclass: "Term", superclass: "Term"):
        if superclass._ontology() is not subclass._ontology():
            raise ValueError("cannot use `Term` instances from different ontologies")
        cache = subclass._ontology()._inheritance
        cache[subclass.id].sup.remove(superclass.id)
        cache[superclass.id].sub.remove(subclass.id)


class SuperclassesHandler(LineageHandler):

    def __iter__(self):
        return SuperclassesIterator(
            self.term,
            distance=self.distance,
            with_self=self.with_self
        )

    def add(self, superclass: "Term"):
        self._add(subclass=self.term, superclass=superclass)

    def remove(self, superclass: "Term"):
        self._remove(subclass=self.term, superclass=superclass)

    def clear(self):
        cache = self.term._ontology()._inheritance
        for subclass in cache[self.term.id].sup:
            cache[subclass].sub.remove(self.term.id)
        cache[self.term.id].sup.clear()


class SubclassesHandler(LineageHandler):

    def __iter__(self):
        return SubclassesIterator(
            self.term,
            distance=self.distance,
            with_self=self.with_self
        )

    def add(self, subclass: "Term"):
        self._add(superclass=self.term, subclass=subclass)

    def remove(self, subclass: "Term"):
        self._remove(superclass=self.term, subclass=subclass)

    def clear(self):
        cache = self.term._ontology()._inheritance
        for superclass in cache[self.term.id].sub:
            cache[superclass].sup.remove(self.term.id)
        cache[self.term.id].sub.clear()



class LineageIterator(Iterator["Term"]):

    _distmax: float
    _maxlen: int
    _ontology: "Ontology"
    _linked: Set[str]
    _done: Set[str]
    _frontier: Deque[Tuple[str, int]]
    _queue: Deque[str]

    # ---

    @abc.abstractmethod
    def _get_neighbors(self, node: str) -> Set[str]:
        return NotImplemented  # type: ignore

    # ---

    def __init__(
        self, *terms: "Term", distance: Optional[int] = None, with_self: bool = True
    ) -> None:

        self._distmax = float("inf") if distance is None else distance

        # if not term is given, `__next__` will raise `StopIterator` on
        # the first call without ever accessing `self._ontology`, so it's
        # safe not to initialise it here in that case.
        if terms:
            self._ontology = ont = terms[0]._ontology()
            self._maxlen = len(ont.terms())

        self._linked: Set[str] = set()
        self._done: Set[str] = set()
        self._frontier: Deque[Tuple[str, int]] = collections.deque()
        self._queue: Deque[str] = collections.deque()

        for term in terms:
            self._frontier.append((term.id, 0))
            self._linked.add(term.id)
            if with_self:
                self._queue.append(term.id)

    def __iter__(self) -> "LineageIterator":
        return self

    def __length_hint__(self) -> int:
        """Return an estimate of the number of remaining entities to yield.
        """
        if self._queue or self._frontier:
            return self._maxlen - len(self._linked) + len(self._queue)
        else:
            return 0

    def __next__(self) -> "Term":
        while self._frontier or self._queue:
            # Return any element currently queued
            if self._queue:
                return self._ontology.get_term(self._queue.popleft())
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


class SubclassesIterator(LineageIterator):
    """An iterator over the subclasses of one or several `~pronto.Term`.
    """

    def _get_neighbors(self, node: str) -> Set[str]:
        return self._ontology._inheritance.get(node, Lineage()).sub


class SuperclassesIterator(LineageIterator):
    """An iterator over the superclasses of one or several `~pronto.Term`.
    """

    def _get_neighbors(self, node: str) -> Set[str]:
        return self._ontology._inheritance.get(node, Lineage()).sup
