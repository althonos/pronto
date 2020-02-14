import collections
import typing
from typing import Deque, Dict, Iterator, Optional, Set, Tuple, List

from ..utils.impl import set

if typing.TYPE_CHECKING:
    from ..term import Term, TermSet
    from ..relationship import Relationship
    from ..ontology import Ontology


class SuperclassesIterator(Iterator["Term"]):
    """An iterator over the superclasses of one or several `~pronto.Term`.

    Todo:
        * Rewrite directly using superclassing cache like `SubclassesIterator`
          and maybe refactor common parts of the code.
    """

    def __init__(
        self, *terms: "Term", distance: Optional[int] = None, with_self: bool = True,
    ) -> None:
        self._distmax: float = float("inf") if distance is None else distance
        self._ontology = ont = terms[0]._ontology

        self._sup: Set[Term] = set()
        self._done: Set[Term] = set()
        self._frontier: Deque[Tuple[Term, int]] = collections.deque()
        self._queue: Deque[Term] = collections.deque()

        for term in terms:
            self._frontier.append((term, 0))
            self._sup.add(term)
            if with_self:
                self._queue.append(term)

    def __iter__(self) -> "SuperclassesIterator":
        return self

    def __next__(self) -> "Term":
        is_a: Relationship = self._ontology().get_relationship("is_a")
        while self._frontier or self._queue:
            # Return any element currently queued
            if self._queue:
                return self._queue.popleft()
            # Get the next node in the frontier
            node, distance = self._frontier.popleft()
            self._done.add(node)
            # Process its neighbors if they are not too far
            neighbors: Set[Term] = set(node.relationships.get(is_a, ()))
            if neighbors and distance < self._distmax:
                for node in sorted(neighbors - self._done):
                    self._frontier.append((node, distance + 1))
                for neighbor in sorted(neighbors - self._sup):
                    self._sup.add(neighbor)
                    self._queue.append(neighbor)
        # Stop iteration if no more elements to process
        raise StopIteration

    def to_set(self) -> "TermSet":
        """Collect all superclasses into a `~pronto.TermSet`.
        """
        from ..term import TermSet

        return TermSet(self)
