import typing
from typing import TypeVar, Generic, Iterator, Sized


T = TypeVar('T')


class SizedIterator(Iterator[T], Sized, Generic[T]):

    def __init__(self, it: Iterator[T], length: int):
        self._it = it
        self._length = length

    def __len__(self) -> int:
        return self._length

    def __length_hint__(self) -> int:
        return self._length

    def __iter__(self) -> 'SizedIterator[T]':
        return self

    def __next__(self) -> T:
        val = next(self._it)
        self._length -= 1
        return val
