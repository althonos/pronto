
import datetime
import typing
import weakref
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

import fastobo

from .entity import Entity
from .definition import Definition
from .synonym import Synonym
from .xref import Xref
from .pv import PropertyValue

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
    asymmetric: bool
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

    def __init__(
        self,
        id: str,
        anonymous: bool = False,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        alternate_ids: Set[str] = None,
        definition: Optional[Definition] = None,
        comment: Optional[str] = None,
        subsets: Optional[Set[str]] = None,
        synonyms: Optional[Set[Synonym]] = None,
        xrefs: Optional[Set[Xref]] = None,
        annotations: Optional[Dict[str, List[str]]] = None,
        domain: Optional[str] = None,
        range: Optional[str] = None,
        builtin: bool = False,
        holds_over_chain: Optional[Set[Tuple[str]]] = None,
        antisymmetric: bool = False,
        cyclic: bool = False,
        reflexive: bool = False,
        asymmetric: bool = False,
        symmetric: bool = False,
        transitive: bool = False,
        functional: bool = False,
        inverse_functional: bool = False,
        intersection_of: Optional[Set[str]] = None,
        union_of: Optional[Set[str]] = None,
        equivalent_to: Optional[Set[str]] = None,
        disjoint_from: Optional[Set[str]] = None,
        inverse_of: Optional[str] = None,
        transitive_over: Optional[Set[str]] = None,
        equivalent_to_chain: Optional[Set[Tuple[str]]] = None,
        disjoint_over: Optional[Set[str]] = None,
        relationships: Optional[Dict[str, Set[str]]] = None,
        obsolete: bool = False,
        created_by: Optional[str] = None,
        creation_date: Optional[datetime.datetime] = None,
        replaced_by: Optional[Set[str]] = None,
        consider: Optional[Set[str]] = None,
        expand_assertion_to: Any = None, # TODO
        expand_expression_to: Any = None, # TODO
        metadata_tag: bool = False,
        class_level: bool = False,
    ):
        self.id = id
        self.anonymous = anonymous
        self.name = name
        self.namespace = namespace
        self.alternate_ids = alternate_ids or set()
        self.definition = definition
        self.comment = comment
        self.subsets = subsets or set()
        self.synonyms = synonyms or set()
        self.xrefs = xrefs or set()
        self.annotations = annotations or dict()
        self.domain = domain
        self.range = range
        self.builtin = builtin
        self.holds_over_chain = holds_over_chain or set()
        self.antisymmetric = antisymmetric
        self.cyclic = cyclic
        self.reflexive = reflexive
        self.asymmetric = asymmetric
        self.symmetric = symmetric
        self.transitive = transitive
        self.functional = functional
        self.inverse_functional = inverse_functional
        self.intersection_of = intersection_of or set()
        self.union_of = union_of or set()
        self.equivalent_to = equivalent_to or set()
        self.disjoint_from = disjoint_from or set()
        self.inverse_of = inverse_of
        self.transitive_over = transitive_over or set()
        self.equivalent_to_chain = equivalent_to_chain or set()
        self.disjoint_over = disjoint_over or set()
        self.relationships = relationships or dict()
        self.obsolete = obsolete
        self.created_by = created_by
        self.creation_date = creation_date
        self.replaced_by = replaced_by or set()
        self.consider = consider or set()
        self.expand_assertion_to = expand_assertion_to
        self.expand_expression_to = expand_expression_to
        self.metadata_tag = metadata_tag
        self.class_level = class_level


class Relationship(Entity):

    def __init__(self, ontology, reldata):
        """Instantiate a new `Relationship`.

        Important:
            Do not use directly, as this API does some black magic to reduce
            memory usage and improve consistentcy in the data model. Use
            `Ontology.create_relationship` or `Ontology.get_relationship`
            depending on your needs to obtain a `Relationship` instance.
        """
        self._ontology = weakref.ref(ontology)
        self._data = weakref.ref(reldata)

    @classmethod
    def _from_ast(cls, frame: fastobo.typedef.TypedefFrame, ontology: 'Ontology'):

            rship = ontology.create_relationship(str(frame.id))
            rshipdata = rship._data()

            union_of = set()
            intersection_of = set()

            def copy(src, dst=None, cb=None):
                cb = cb or (lambda x: x)
                dst = dst or src
                return lambda c: setattr(rship, dst, cb(getattr(c, src)))

            def add(src, dst=None, cb=None):
                cb = cb or (lambda x: x)
                dst = dst or src
                return lambda c: getattr(rshipdata, dst).add(cb(getattr(c, src)))

            def todo():
                return lambda c: print("todo", c)

            _callbacks = {
                fastobo.typedef.AltIdClause: add("alt_id", "alternate_ids", cb=str),
                fastobo.typedef.BuiltinClause: copy("builtin"),
                fastobo.typedef.CommentClause: copy("comment"),
                fastobo.typedef.ConsiderClause: add("typedef", "consider", cb=str),
                fastobo.typedef.CreatedByClause: copy("creator", "created_by"),
                fastobo.typedef.CreationDateClause: copy("date", "creation_date"),
                fastobo.typedef.DefClause:
                    lambda c: setattr(rship, "definition", Definition._from_ast(c)),
                fastobo.typedef.DisjointFromClause:
                    add("typedef", "disjoint_from", cb=str),
                fastobo.typedef.DisjointOverClause:
                    add("typedef", "disjoint_over", cb=str),
                fastobo.typedef.DomainClause:
                    copy("domain", cb=str),
                fastobo.typedef.EquivalentToChainClause: todo(),
                fastobo.typedef.EquivalentToClause: todo(),
                fastobo.typedef.ExpandAssertionToClause: todo(),
                fastobo.typedef.ExpandExpressionToClause: todo(),
                fastobo.typedef.HoldsOverChainClause: todo(),
                fastobo.typedef.IntersectionOfClause:
                    lambda c: intersection_of.add(str(c.typedef)),
                fastobo.typedef.InverseOfClause:
                    lambda c: setattr(rshipdata, "inverse_of", str(c.typedef)),
                fastobo.typedef.IsAClause:
                    lambda c: rshipdata.relationships.setdefault("is_a", set()).add(str(c.typedef)),
                fastobo.typedef.IsAnonymousClause: copy("anonymous"),
                fastobo.typedef.IsAntiSymmetricClause: copy("antisymmetric"),
                fastobo.typedef.IsAsymmetricClause: copy("asymmetric"),
                fastobo.typedef.IsClassLevelClause: copy("class_level"),
                fastobo.typedef.IsCyclicClause: copy("cyclic"),
                fastobo.typedef.IsFunctionalClause: copy("functional"),
                fastobo.typedef.IsInverseFunctionalClause: copy("inverse_functional"),
                fastobo.typedef.IsMetadataTagClause: copy("metadata_tag"),
                fastobo.typedef.IsObsoleteClause: copy("obsolete"),
                fastobo.typedef.IsReflexiveClause: copy("reflexive"),
                fastobo.typedef.IsSymmetricClause: copy("symmetric"),
                fastobo.typedef.IsTransitiveClause: copy("transitive"),
                fastobo.typedef.NameClause: copy("name"),
                fastobo.typedef.NamespaceClause: copy("namespace", cb=str),
                fastobo.typedef.PropertyValueClause: (lambda c: (
                    rshipdata.annotations.add(
                        PropertyValue._from_ast(c.property_value)
                    )
                )),
                fastobo.typedef.RangeClause: todo(),
                fastobo.typedef.RelationshipClause: todo(),
                fastobo.typedef.ReplacedByClause: todo(),
                fastobo.typedef.SubsetClause: todo(),
                fastobo.typedef.SynonymClause: todo(),
                fastobo.typedef.TransitiveOverClause:
                    lambda c: rshipdata.transitive_over.add(str(c.typedef)),
                fastobo.typedef.UnionOfClause:
                    lambda c: union_of.add(str(c.typedef)),
                fastobo.typedef.XrefClause:
                    add("xref", "xrefs", cb=Xref._from_ast),
            }

            for clause in frame:
                try:
                    _callbacks[type(clause)](clause)
                except KeyError:
                    raise TypeError(f"unexpected type: {type(clause).__name__}")
            if len(union_of) == 1:
                raise ValueError("'union_of' cannot have a cardinality of 1")
            rshipdata.union_of = union_of
            if len(intersection_of) == 1:
                raise ValueError("'intersection_of' cannot have a cardinality of 1")
            rshipdata.intersection_of = intersection_of
            return rship

    # --- Data descriptors ---------------------------------------------------

    @property
    def metadata_tag(self) -> bool:
        return self._data().metadata_tag

    @metadata_tag.setter
    def metadata_tag(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'metadata_tag' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._data().metadata_tag = value

    @property
    def relationships(self) -> Dict['Relationship', FrozenSet['Relationship']]:
        ont, reldata = self._ontology(), self._data()
        return {
            Relationship(ont, ont.get_relationship(rel)._data()): frozenset(
                Term(ont, ont.get_relationship(rel)._data())
                for rel in rels
            )
            for rel, rels in reldata.relationships.items()
        }

    @property
    def inverse_of(self) -> Optional['Relationship']:
        ont, reldata = self._ontology(), self._data()
        if reldata.inverse_of is not None:
            return ont.get_relationship(reldata.inverse_of)
        return None

    @inverse_of.setter
    def inverse_of(self, value: Optional['Relationship']):
        self._data().inverse_of = None if value is None else value.id

    @property
    def transitive_over(self) -> FrozenSet['Relationship']:
        ont, reldata = self._ontology(), self._data()
        return frozenset(ont.get_relationship(x) for x in reldata.transitive_over)



_BUILTINS = {
    "is_a": _RelationshipData(
        id = "is_a",
        anonymous = False,
        name = "is a",
        namespace = None,
        alternate_ids = None,
        definition = Definition(
            "A subclassing relationship between one term and another",
            xrefs={Xref("http://owlcollab.github.io/oboformat/doc/GO.format.obo-1_4.html")},
        ),
        comment = None,
        subsets = None,
        synonyms = None,
        xrefs = None,
        annotations = None,
        domain = None,
        range = None,
        builtin = True,
        holds_over_chain = None,
        antisymmetric = True,
        cyclic = True,
        reflexive = True,
        asymmetric = False,
        symmetric = False,
        transitive = True,
        functional = False,
        inverse_functional = False,
        intersection_of = None,
        union_of = None,
        equivalent_to = None,
        disjoint_from = None,
        inverse_of = None,
        transitive_over = None,
        equivalent_to_chain = None,
        disjoint_over = None,
        relationships = None,
        obsolete = False,
        created_by = None,
        creation_date = None,
        replaced_by = None,
        consider = None,
        expand_assertion_to = None, # TODO
        expand_expression_to = None, # TODO
        metadata_tag = False,
        class_level = True,
    ),
    "has_subclass": _RelationshipData(
        id = "has_subclass",
        anonymous = False,
        name = "has subclass",
        namespace = None,
        alternate_ids = None,
        definition = Definition(
            "A superclassing relationship between one term and another",
        ),
        comment = None,
        subsets = None,
        synonyms = None,
        xrefs = None,
        annotations = None,
        domain = None,
        range = None,
        builtin = True,
        holds_over_chain = None,
        antisymmetric = True,
        asymmetric = False,
        cyclic = True,
        reflexive = True,
        symmetric = False,
        transitive = True,
        functional = False,
        inverse_functional = False,
        intersection_of = None,
        union_of = None,
        equivalent_to = None,
        disjoint_from = None,
        inverse_of = "is_a",
        transitive_over = None,
        equivalent_to_chain = None,
        disjoint_over = None,
        relationships = None,
        obsolete = False,
        created_by = None,
        creation_date = None,
        replaced_by = None,
        consider = None,
        expand_assertion_to = None, # TODO
        expand_expression_to = None, # TODO
        metadata_tag = False,
        class_level = True,
    )
}
