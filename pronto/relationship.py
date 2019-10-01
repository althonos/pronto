import datetime
import typing
import warnings
import weakref
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Set, Tuple

import fastobo
import frozendict

from .entity import Entity, EntityData
from .definition import Definition
from .synonym import Synonym, _SynonymData
from .xref import Xref
from .pv import PropertyValue
from .utils.impl import set
from .utils.meta import typechecked
from .utils.warnings import NotImplementedWarning

if typing.TYPE_CHECKING:
    from .ontology import Ontology
    from .term import Term


class _RelationshipData(EntityData):

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
    annotations: Set[PropertyValue]
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

    __slots__ = tuple(__annotations__)  # noqa: E0602

    def __init__(
        self,
        id: str,
        anonymous: bool = False,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        alternate_ids: Optional[Set[str]] = None,
        definition: Optional[Definition] = None,
        comment: Optional[str] = None,
        subsets: Optional[Set[str]] = None,
        synonyms: Optional[Set[Synonym]] = None,
        xrefs: Optional[Set[Xref]] = None,
        annotations: Optional[Set[PropertyValue]] = None,
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
        expand_assertion_to: Optional[Set[Definition]] = None,
        expand_expression_to: Optional[Set[Definition]] = None,
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
        self.annotations = annotations or set()
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
        self.expand_assertion_to = expand_assertion_to or set()
        self.expand_expression_to = expand_expression_to or set()
        self.metadata_tag = metadata_tag
        self.class_level = class_level


class Relationship(Entity):

    def __init__(self, ontology: 'Ontology', reldata: '_RelationshipData'):
        """Instantiate a new `Relationship`.

        Important:
            Do not use directly, as this API does some black magic to reduce
            memory usage and improve consistency in the data model. Use
            `Ontology.create_relationship` or `Ontology.get_relationship`
            depending on your needs to obtain a `Relationship` instance.
        """
        super().__init__(ontology, reldata)

    @classmethod
    def _from_ast(cls, frame: fastobo.typedef.TypedefFrame, ontology: 'Ontology'):

        rship = ontology.create_relationship(str(frame.id))
        rshipdata = rship._data()

        union_of = set()
        intersection_of = set()

        def copy(src, dst=None, cb=None):
            cb = cb or (lambda x: x)
            dst = dst or src
            return lambda c: setattr(rshipdata, dst, cb(getattr(c, src)))

        def add(src, dst=None, cb=None):
            cb = cb or (lambda x: x)
            dst = dst or src
            return lambda c: getattr(rshipdata, dst).add(cb(getattr(c, src)))

        def todo():
            return lambda c: warnings.warn(f"cannot process `{c}`", NotImplementedWarning, stacklevel=3)

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
                lambda c: setattr(rshipdata, "domain", str(c.domain)),
            fastobo.typedef.EquivalentToChainClause: todo(),
            fastobo.typedef.EquivalentToClause: add("typedef", "equivalent_to", cb=str),
            fastobo.typedef.ExpandAssertionToClause: (lambda c:
                rshipdata.expand_assertion_to.add(Definition._from_ast(c))
            ),
            fastobo.typedef.ExpandExpressionToClause: (lambda c:
                rshipdata.expand_expression_to.add(Definition._from_ast(c))
            ),
            fastobo.typedef.HoldsOverChainClause: (lambda c:
                rshipdata.holds_over_chain.add((str(c.first), str(c.last)))
            ),
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
            fastobo.typedef.RangeClause:
                lambda c: setattr(rshipdata, "range", str(c.range)),
            fastobo.typedef.RelationshipClause: todo(),
            fastobo.typedef.ReplacedByClause: add("typedef", "replaced_by", cb=str),
            fastobo.typedef.SubsetClause: add("subset", "subsets", cb=str),
            fastobo.typedef.SynonymClause:
                lambda c: rshipdata.synonyms.add(_SynonymData._from_ast(c.synonym)),
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

    if typing.TYPE_CHECKING:

        def _data(self) -> '_RelationshipData':
            return typing.cast('_RelationshipData', super()._data())

    # --- Data descriptors ---------------------------------------------------

    @property
    def antisymmetric(self) -> bool:
        return self._data().antisymmetric

    @antisymmetric.setter
    @typechecked(property=True)
    def antisymmetric(self, value: bool) -> None:
        self._data().antisymmetric = value

    @property
    def asymmetric(self) -> bool:
        return self._data().asymmetric

    @asymmetric.setter
    @typechecked(property=True)
    def asymmetric(self, value: bool) -> None:
        self._data().asymmetric = value

    @property
    def class_level(self) -> bool:
        return self._data().class_level

    @class_level.setter
    @typechecked(property=True)
    def class_level(self, value: bool) -> None:
        self._data().class_level = value

    @property
    def consider(self) -> FrozenSet['Relationship']:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(r) for r in rdata.consider)

    @property
    def cyclic(self) -> bool:
        return self._data().cyclic

    @property
    def disjoint_from(self) -> FrozenSet['Relationship']:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(t) for t in rdata.disjoint_from)

    @property
    def disjoint_over(self) -> FrozenSet['Relationship']:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(t) for t in rdata.disjoint_over)

    @property
    def domain(self) -> Optional['Term']:
        rshipdata, ontology = self._data(), self._ontology()
        if rshipdata.domain is not None:
            return ontology.get_term(rshipdata.domain)
        return None

    @domain.setter
    #@typechecked(property=True)
    def domain(self, value: Optional['Term']) -> None:
        rshipdata, ontology = self._data(), self._ontology()
        if value is not None:
            try:
                ontology.get_term(value.id)
            except KeyError:
                raise ValueError(f"{value} is not a term in {ontology}")
        rshipdata.domain = value.id if value is not None else None

    @property
    def domain(self) -> Optional['Term']:
        dom, ontology = self._data().domain, self._ontology()
        return ontology.get_term(dom) if dom is not None else None

    @domain.setter
    def domain(self, value: Optional['Term']):
        if value is not None:
            try:
                self._ontology().get_term(value.id)
            except KeyError:
                raise ValueError(f"{value} is not a term in {self._ontology()}")
        self._data().domain = value.id if value is not None else None

    @property
    def equivalent_to_chain(self) -> FrozenSet[Tuple['Relationship', 'Relationship']]:
        return frozenset({
            tuple(map(self._ontology().get_relationship, chain))
            for chain in self._data().equivalent_to_chain
        })

    @property
    def expand_assertion_to(self) -> FrozenSet[Definition]:
        return frozenset(self._data().expand_assertion_to)

    @property
    def expand_expression_to(self) -> FrozenSet[Definition]:
        return frozenset(self._data().expand_expression_to)

    @property
    def functional(self) -> bool:
        return self._data().functional

    @functional.setter
    @typechecked(property=True)
    def functional(self, value: bool) -> None:
        self._data().functional = value

    @property
    def inverse_functional(self) -> bool:
        return self._data().inverse_functional

    @inverse_functional.setter
    @typechecked(property=True)
    def inverse_functional(self, value: bool) -> None:
        self._data().inverse_functional = value

    @property
    def metadata_tag(self) -> bool:
        return self._data().metadata_tag

    @metadata_tag.setter
    @typechecked(property=True)
    def metadata_tag(self, value: bool):
        self._data().metadata_tag = value

    @property
    def relationships(self) -> Mapping['Relationship', FrozenSet['Relationship']]:
        ont, reldata = self._ontology(), self._data()
        return frozendict.frozendict({
            ont.get_relationship(rel): frozenset(
                ont.get_relationship(rel)
                for rel in rels
            )
            for rel, rels in reldata.relationships.items()
        })

    @property
    def holds_over_chain(self) -> FrozenSet[Tuple['Relationship', 'Relationship']]:
        ont: 'Ontology' = self._ontology()
        data: '_RelationshipData' = self._data()
        return frozenset({
            tuple(map(ont.get_term, chain))
            for chain in data.holds_over_chain
        })

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
    def intersection_of(self) -> FrozenSet['Relationship']:
        ont, reldata = self._ontology(), self._data()
        return frozenset({
            ont.get_relationship(r) for r in reldata.intersection_of
        })

    @property
    def range(self) -> Optional['Term']:
        range, ont = self._data().range, self._ontology()
        return ont.get_term(range) if range is not None else None

    @range.setter
    def range(self, value: Optional['Term']):
        if value is not None:
            try:
                self._ontology().get_term(value.id)
            except KeyError:
                raise ValueError(f"{value} is not in {self._ontology()}")
        self._data().range = value.id if value is not None else None

    @property
    def reflexive(self) -> bool:
        return self._data().reflexive

    @reflexive.setter
    @typechecked(property=True)
    def reflexive(self, value: bool):
        self._data().reflexive = value

    @property
    def replaced_by(self) -> FrozenSet['Relationship']:
        ont, data = self._ontology(), self._data()
        return frozenset({ont.get_relationship(r) for r in data.replaced_by})

    @property
    def symmetric(self) -> bool:
        return self._data().symmetric

    @symmetric.setter
    @typechecked(property=True)
    def symmetric(self, value: bool):
        self._data().symmetric = value

    @property
    def transitive(self) -> bool:
        return self._data().transitive

    @transitive.setter
    @typechecked(property=True)
    def transitive(self, value: bool):
        self._data().transitive = value

    @property
    def transitive_over(self) -> FrozenSet['Relationship']:
        ont, reldata = self._ontology(), self._data()
        return frozenset(ont.get_relationship(x) for x in reldata.transitive_over)

    @property
    def union_of(self) -> FrozenSet['Relationship']:
        data, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(r) for r in data.union_of)


_BUILTINS = {
    "is_a": _RelationshipData(
        id = "is_a",
        anonymous = False,
        name = "is a",
        namespace = None,
        alternate_ids = None,
        definition = Definition(
            "A subclassing relationship between one term and another",
            xrefs=set({Xref("http://owlcollab.github.io/oboformat/doc/GO.format.obo-1_4.html")}),
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
}
