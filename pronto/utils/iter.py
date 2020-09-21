from collections.abc import Sized
from typing import Generic, Iterator, TypeVar

__all__ = ["SizedIterator"]
S = TypeVar("S")
T = TypeVar("T")


class SizedIterator(Generic[T], Iterator[T], Sized):
    """A wrapper for iterators which length is known in advance."""

    def __init__(self, it: Iterator[T], length: int):
        self._it = it
        self._length = length

    def __len__(self) -> int:
        return self._length

    def __length_hint__(self) -> int:
        return self._length

    def __iter__(self: S) -> S:
        return self

    def __next__(self) -> T:
        val = next(self._it)
        self._length -= 1
        return val
