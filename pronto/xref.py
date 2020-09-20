"""Cross-reference object definition.
"""

import typing

import fastobo

from .utils.meta import roundrepr, typechecked


__all__ = ["Xref"]


@roundrepr
class Xref(object):
    """A cross-reference to another document or resource.

    Cross-references (xrefs for short) can be used to back-up definitions of
    entities, synonyms, or to link ontological entities to other resources
    they may have been derived from. Although originally intended to provide
    links to databases, cross-references in OBO ontologies gained additional
    purposes, such as helping for header macros expansion, or being used to
    alias external relationships with local unprefixed IDs.

    The OBO format version 1.4 expects references to be proper OBO identifiers
    that can be translated to actual IRIs, which is a breaking change from the
    previous format. Therefore, cross-references are encouraged to be given as
    plain IRIs or as prefixed IDs using an ID from the IDspace mapping defined
    in the header.

    Example:
        A cross-reference in the Mammalian Phenotype ontology linking a term
        to some related Web resource:

        >>> mp = pronto.Ontology.from_obo_library("mp.obo")
        >>> mp["MP:0030151"].name
        'abnormal buccinator muscle morphology'
        >>> mp["MP:0030151"].xrefs
        frozenset({Xref('https://en.wikipedia.org/wiki/Buccinator_muscle')})

    Caution:
        `Xref` instances compare only using their identifiers; this means it
        is not possible to have several cross-references with the same
        identifier and different descriptions in the same set.

    Todo:
        Make sure to resolve header macros for xrefs expansion (such as
        ``treat-xrefs-as-is_a``) when creating an ontology, or provide a
        method on `~pronto.Ontology` doing so when called.

    """

    id: str
    description: typing.Optional[str]

    __slots__ = ("__weakref__", "id", "description")  # noqa: E0602

    @typechecked()
    def __init__(self, id: str, description: typing.Optional[str] = None):
        """Create a new cross-reference.

        Arguments:
            id (str): the identifier of the cross-reference, either as a URL,
                a prefixed identifier, or an unprefixed identifier.
            description (str or None): a human-readable description of the
                cross-reference, if any.

        """
        # check the id is valid using fastobo
        if not fastobo.id.is_valid(id):
            raise ValueError("invalid identifier: {}".format(id))

        self.id: str = id
        self.description = description

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Xref):
            return self.id == other.id
        return False

    def __gt__(self, other: object) -> bool:
        if isinstance(other, Xref):
            return self.id > other.id
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Xref):
            return self.id >= other.id
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Xref):
            return self.id < other.id
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, Xref):
            return self.id <= other.id
        return NotImplemented

    def __hash__(self):
        return hash(self.id)
