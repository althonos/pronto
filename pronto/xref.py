# coding: utf-8

import functools
import typing

import fastobo

from .utils.repr import roundrepr


@roundrepr
class Xref(object):
    """A cross-reference to another document or resource.

    Cross-references (xrefs for short) can be used to back-up definitions of
    entities, synonyms, or to link ontological entities to other resources
    they may have been derived from.

    Example:
        A cross-reference in the Mammalian Phenotype ontology linking a term
        to some related Web resource:

        >>> mp = pronto.Ontology("http://purl.obolibrary.org/obo/mp.obo")
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

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    @classmethod
    def _from_ast(cls, xref: fastobo.xref.Xref) -> 'Xref':
        return cls(str(xref.id), xref.desc)

    def _to_ast(self) -> fastobo.xref.Xref:
        return fastobo.xref.Xref(fastobo.id.parse(self.id), self.description)

    def __init__(self, id: str, description: typing.Optional[str] = None):
        """Create a new cross-reference.

        Arguments:
            id (str): the identifier of the cross-reference, either as a URL,
                a prefixed identifier, or an unprefixed identifier.
            description (str or None): a human-readable description of the
                cross-reference, or `None`.
        """
        if __debug__:
            if not isinstance(id, str):
                raise TypeError(f"'id' must be str, not {type(id).__name__}")
            if description is not None and not isinstance(description, str):
                msg = "'description' must be str or None, not {}"
                raise TypeError(msg.format(type(description).__name__))
        # check the id is valid using fastobo
        self.id: str = str(fastobo.id.parse(id))
        self.description = description

    def __eq__(self, other):
        if isinstance(other, Xref):
            return self.id == other.id
        return False

    def __gt__(self, other):
        if isinstance(other, Xref):
            return self.id > other.id
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Xref):
            return self.id >= other.id
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Xref):
            return self.id < other.id
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Xref):
            return self.id <= other.id
        return NotImplemented

    def __hash__(self):
        return hash(self.id)
