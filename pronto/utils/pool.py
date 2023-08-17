import typing
from typing import Callable, Iterable, List

try:
    from multiprocessing.pool import ThreadPool as _ThreadPool
except ImportError:
    _ThreadPool = None  # type: ignore


_T = typing.TypeVar("_T")
_U = typing.TypeVar("_U")


class ThreadPool(object):

    def __init__(self, threads: int = 0):
        self.threads = threads
        self.pool = None if _ThreadPool is None else _ThreadPool(self.threads)

    def __enter__(self) -> "Pool":
        if self.pool is not None:
            self.pool.__enter__()
        return self

    def __exit__(self, exc_val, exc_ty, tb):
        if self.pool is not None:
            return self.pool.__exit__(exc_val, exc_ty, tb)
        return False

    def map(self, func: Callable[[_T], _U], items: Iterable[_T]) -> List[_U]:
        if self.pool is None:
            return list(map(func, items))
        else:
            return self.pool.map(func, items)

