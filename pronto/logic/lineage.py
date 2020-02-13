from typing import AbstractSet

from ..utils.impl import set
from ..utils.meta import roundrepr


@roundrepr
class Lineage(object):
    """An internal type to store the superclasses and subclasses of a term.

    Used in `Ontology` to cache subclassing relationships between terms since
    only the superclassing relationships are explicitly declared in source
    documents.
    """

    __slots__ = ("sub", "sup")

    def __init__(self, sub: AbstractSet[str] = None, sup: AbstractSet[str] = None):
        self.sub: AbstractSet[str] = sub or set()
        self.sup: AbstractSet[str] = sup or set()

    def __eq__(self, other):
        if isinstance(other, Lineage):
            return self.sub == other.sub and self.sup == other.sup
        return False
