# coding: utf-8

import functools
import typing

import fastobo

from .utils.repr import roundrepr


@roundrepr
@functools.total_ordering
class Xref(object):

    id: str
    description: typing.Optional[str]

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    @classmethod
    def _from_ast(cls, xref: fastobo.xref.Xref) -> 'Xref':
        return cls(str(xref.id), xref.desc)

    def _to_ast(self) -> fastobo.xref.Xref:
        return fastobo.xref.Xref(fastobo.id.parse(self.id), self.description)

    def __init__(self, id: str, description: typing.Optional[str] = None):
        self.id: str = id
        self.description = description

    def __eq__(self, other):
        if isinstance(other, Xref):
            return self.id == other.id and self.description == other.description
        return False

    def __lt__(self, other):
        if not isinstance(other, Xref):
            return NotImplemented
        return self.id < other.id \
            or (self.id == other.id and self.description < other.description )

    def __hash__(self):
        return hash((self.id, self.description))
