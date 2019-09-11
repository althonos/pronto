
import datetime
import typing
import weakref
from typing import Any, Dict, List, Optional, Set, Tuple

import fastobo

from .definition import Definition
from .synonym import Synonym
from .xref import Xref

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class _RelationshipData(object):

    id: str
    anonymous: bool
    name: Optional[str]
    namespace: Optional[str]
    alternate_ids: Set[str]
    definition: Optional[Definition]
    comment: Optional[str]
    subsets: Set[str]
    synonyms: Set[Synonym]
    xrefs: Set[Xref]
    annotations: Dict[str, List[str]]
    domain: Optional[str]
    range: Optional[str]
    builtin: bool
    holds_over_chain: Set[Tuple[str]]
    antisymmetric: bool
    cyclic: bool
    reflexive: bool
    symmetric: bool
    transitive: bool
    functional: bool
    inverse_functional: bool
    intersection_of: Set[str]
    union_of: Set[str]
    equivalent_to: Set[str]
    disjoint_from: Set[str]
    inverse_of: Optional[str]
    transitive_over: Set[str]
    equivalent_to_chain: Set[Tuple[str]]
    disjoint_over: Set[str]
    relationships: Dict[str, Set[str]]
    obsolete: bool
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    replaced_by: Set[str]
    consider: Set[str]
    expand_assertion_to: Any  # TODO
    expand_expression_to: Any  # TODO
    metadata_tag: bool
    class_level: bool

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    def __init__(self, id, builtin=False):
        self.id = id
        self.builtin = builtin


class Relationship(object):

    def __init__(self, ontology, reldata):
        self._ontology = weakref.ref(ontology)
        self._reldata = weakref.ref(reldata)

    @classmethod
    def _from_ast(cls, frame: fastobo.term.TermFrame, ontology: 'Ontology'):

            ontology._relationships[str(frame.id)] = rshipdata = _RelationshipData(str(frame.id))
            rship = cls(ontology, rshipdata)

            # union_of = set()
            # intersection_of = set()

            # for clause in frame:
            #     raise ValueError(f"unexpected clause: {clause}")

            # if len(union_of) == 1:
            #     raise ValueError("'union_of' cannot have a cardinality of 1")
            # termdata.union_of = union_of
            # if len(intersection_of) == 1:
            #     raise ValueError("'intersection_of' cannot have a cardinality of 1")
            # termdata.intersection_of = intersection_of

            return rship
