# coding: utf-8

import fastobo
import typing
from operator import attrgetter

from .xref import Xref
from .utils.repr import make_repr


class Definition(str):
    """The definition of a term or a relationship, backed by some xrefs.
    """

    xrefs: typing.Set[Xref]

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    @classmethod
    def _from_ast(cls, clause: fastobo.term.DefClause):
        return cls(clause.definition, set(map(Xref._from_ast, clause.xrefs)))

    def _to_ast(self) -> fastobo.term.DefClause:
        xrefs = [
            Xref._to_ast(x)
            for x in sorted(self.xrefs, key=attrgetter("id", "description"))
        ]
        return fastobo.term.DefClause(str(self), xrefs)

    def __new__(cls, text, xrefs=None):
        return super(Definition, cls).__new__(cls, text)

    def __init__(self, text, xrefs=None):
        self.xrefs = xrefs or set()

    def __repr__(self):
        return make_repr("Definition", str(self), xrefs=(self.xrefs, set()))
