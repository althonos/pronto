# coding: utf-8

import fastobo
import typing
from operator import attrgetter
from typing import Optional, Iterable

from .xref import Xref
from .utils.meta import roundrepr
from .utils.impl import set


class Definition(str):
    """A human-readable text definition of an entity.

    Definitions are human-readable descriptions of an entity in the ontology
    graph, with some optional cross-references to support the definition.

    Example:
        Simply create a `Definition` instance by giving it a string::

        >>> def1 = pronto.Definition('a structural anomaly')

        Additional cross-references can be passed as arguments, or added later
        to the ``xrefs`` attribute of the `Definition`:

        >>> def2 = pronto.Definition('...', xrefs={pronto.Xref('MGI:Anna')})
        >>> def2.xrefs.add(pronto.Xref('ORCID:0000-0002-3947-4444'))

    Caution:
        A `Definition` compare only based on its textual value, independently
        of the `Xref` it may contains:

        >>> def2 == pronto.Definition('...')
        True

    Note:
        Some ontologies use the xrefs of a description to attribute the
        authorship of that definition:

        >>> cio = pronto.Ontology("http://purl.obolibrary.org/obo/cio.obo")
        >>> sorted(cio['CIO:0000011'].definition.xrefs)
        [Xref('Bgee:fbb')]

        The common usecase however is to refer to the source of a definition
        using persistent identifiers like ISBN book numbers or PubMed IDs.

        >>> pl = pronto.Ontology("http://purl.obolibrary.org/obo/plana.obo")
        >>> sorted(pl['PLANA:0007518'].definition.xrefs)
        [Xref('ISBN:0-71677033-4'), Xref('PMID:4853064')]

    """

    xrefs: typing.Set[Xref]

    __slots__ = ("__weakref__", "xrefs")

    @classmethod
    def _from_ast(cls, clause: fastobo.term.DefClause):
        return cls(clause.definition, set(map(Xref._from_ast, clause.xrefs)))

    def _to_ast(self) -> fastobo.term.DefClause:
        xrefs = [Xref._to_ast(x) for x in sorted(self.xrefs)]
        return fastobo.term.DefClause(str(self), xrefs)

    def __new__(cls, text: str, xrefs=None) -> 'Definition':
        return super().__new__(cls, text)

    def __init__(self, text: str, xrefs: Optional[Iterable[Xref]] = None) -> None:
        self.xrefs = set(xrefs) if xrefs is not None else set()

    def __repr__(self):
        return roundrepr.make("Definition", str(self), xrefs=(self.xrefs, set()))
