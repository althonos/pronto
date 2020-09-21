import typing
from typing import Iterable, Optional

from .utils.meta import roundrepr
from .xref import Xref

__all__ = ["Definition"]


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

        The text content of the definition can be accessed by casting the
        definition object to a plain string:

        >>> str(def1)
        'a structural anomaly'

    Caution:
        A `Definition` compare only based on its textual value, independently
        of the `Xref` it may contains:

        >>> def2 == pronto.Definition('...')
        True

    Note:
        Some ontologies use the xrefs of a description to attribute the
        authorship of that definition:

        >>> cio = pronto.Ontology.from_obo_library("cio.obo")
        >>> sorted(cio['CIO:0000011'].definition.xrefs)
        [Xref('Bgee:fbb')]

        The common usecase however is to refer to the source of a definition
        using persistent identifiers like ISBN book numbers or PubMed IDs.

        >>> pl = pronto.Ontology.from_obo_library("plana.obo")
        >>> sorted(pl['PLANA:0007518'].definition.xrefs)
        [Xref('ISBN:0-71677033-4'), Xref('PMID:4853064')]

    """

    xrefs: typing.Set[Xref]

    __slots__ = ("__weakref__", "xrefs")

    def __new__(cls, text: str, xrefs=None) -> "Definition":
        return super().__new__(cls, text)  # type: ignore

    def __init__(self, text: str, xrefs: Optional[Iterable[Xref]] = None) -> None:
        self.xrefs = set(xrefs) if xrefs is not None else set()

    def __repr__(self) -> str:
        return roundrepr.make("Definition", str(self), xrefs=(self.xrefs, set()))
