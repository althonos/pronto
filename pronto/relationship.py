import datetime
import typing
from typing import Dict, FrozenSet, Mapping, Optional, Set, Tuple

import frozendict

from .entity import Entity, EntityData
from .definition import Definition
from .synonym import SynonymData
from .xref import Xref
from .pv import PropertyValue
from .utils.impl import set
from .utils.meta import typechecked

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class RelationshipData(EntityData):
    """Internal data storage of `Relationship` information.
    """

    id: str
    anonymous: bool
    name: Optional[str]
    namespace: Optional[str]
    alternate_ids: Set[str]
    definition: Optional[Definition]
    comment: Optional[str]
    subsets: Set[str]
    synonyms: Set[SynonymData]
    xrefs: Set[Xref]
    annotations: Set[PropertyValue]
    domain: Optional[str]
    range: Optional[str]
    builtin: bool
    holds_over_chain: Set[Tuple[str, str]]
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
    equivalent_to_chain: Set[Tuple[str, str]]
    disjoint_over: Set[str]
    relationships: Dict[str, Set[str]]
    obsolete: bool
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    replaced_by: Set[str]
    consider: Set[str]
    expand_assertion_to: Set[Definition]
    expand_expression_to: Set[Definition]
    metadata_tag: bool
    class_level: bool

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

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
        synonyms: Optional[Set[SynonymData]] = None,
        xrefs: Optional[Set[Xref]] = None,
        annotations: Optional[Set[PropertyValue]] = None,
        domain: Optional[str] = None,
        range: Optional[str] = None,
        builtin: bool = False,
        holds_over_chain: Optional[Set[Tuple[str, str]]] = None,
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
        equivalent_to_chain: Optional[Set[Tuple[str, str]]] = None,
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
    """A relationship, constitute the edges of the ontology graph.

    Also sometimes referede as typedefs, relationship types, properties or
    predicates. Formally equivalent to a property (either ``ObjectProperty``
    or ``AnnotationProperty``) in OWL2.
    """

    if typing.TYPE_CHECKING:

        def __init__(self, ontology: "Ontology", reldata: "RelationshipData"):
            super().__init__(ontology, reldata)

        def _data(self) -> "RelationshipData":
            return typing.cast("RelationshipData", super()._data())

    # --- Data descriptors ---------------------------------------------------

    @property
    def antisymmetric(self) -> bool:
        """`bool`: whether this relationship is anti-symmetric.
        """
        return self._data().antisymmetric

    @antisymmetric.setter
    @typechecked(property=True)
    def antisymmetric(self, value: bool) -> None:
        self._data().antisymmetric = value

    @property
    def asymmetric(self) -> bool:
        """`bool`: whether this relationship is asymmetric.
        """
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
    def consider(self) -> FrozenSet["Relationship"]:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(r) for r in rdata.consider)

    @property
    def cyclic(self) -> bool:
        return self._data().cyclic

    @property
    def disjoint_from(self) -> FrozenSet["Relationship"]:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(t) for t in rdata.disjoint_from)

    @property
    def disjoint_over(self) -> FrozenSet["Relationship"]:
        rdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(t) for t in rdata.disjoint_over)

    @property
    def domain(self) -> Optional["Term"]:
        rshipdata, ontology = self._data(), self._ontology()
        if rshipdata.domain is not None:
            return ontology.get_term(rshipdata.domain)
        return None

    @domain.setter
    # @typechecked(property=True)
    def domain(self, value: Optional["Term"]) -> None:
        rshipdata, ontology = self._data(), self._ontology()
        if value is not None:
            try:
                ontology.get_term(value.id)
            except KeyError:
                raise ValueError(f"{value} is not a term in {ontology}")
        rshipdata.domain = value.id if value is not None else None

    @property
    def equivalent_to_chain(self) -> FrozenSet[Tuple["Relationship", "Relationship"]]:
        return frozenset(
            {
                tuple(map(self._ontology().get_relationship, chain))
                for chain in self._data().equivalent_to_chain
            }
        )

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
    def relationships(self) -> Mapping["Relationship", FrozenSet["Relationship"]]:
        ont, reldata = self._ontology(), self._data()
        return frozendict.frozendict(
            {
                ont.get_relationship(rel): frozenset(
                    ont.get_relationship(rel) for rel in rels
                )
                for rel, rels in reldata.relationships.items()
            }
        )

    @property
    def holds_over_chain(self) -> FrozenSet[Tuple["Relationship", "Relationship"]]:
        ont: "Ontology" = self._ontology()
        data: "RelationshipData" = self._data()
        return frozenset(
            {tuple(map(ont.get_term, chain)) for chain in data.holds_over_chain}
        )

    @property
    def inverse_of(self) -> Optional["Relationship"]:
        ont, reldata = self._ontology(), self._data()
        if reldata.inverse_of is not None:
            return ont.get_relationship(reldata.inverse_of)
        return None

    @inverse_of.setter
    def inverse_of(self, value: Optional["Relationship"]):
        self._data().inverse_of = None if value is None else value.id

    @property
    def intersection_of(self) -> FrozenSet["Relationship"]:
        ont, reldata = self._ontology(), self._data()
        return frozenset({ont.get_relationship(r) for r in reldata.intersection_of})

    @property
    def range(self) -> Optional["Term"]:
        range, ont = self._data().range, self._ontology()
        return ont.get_term(range) if range is not None else None

    @range.setter
    def range(self, value: Optional["Term"]):
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
    def replaced_by(self) -> FrozenSet["Relationship"]:
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
    def transitive_over(self) -> FrozenSet["Relationship"]:
        ont, reldata = self._ontology(), self._data()
        return frozenset(ont.get_relationship(x) for x in reldata.transitive_over)

    @property
    def union_of(self) -> FrozenSet["Relationship"]:
        data, ont = self._data(), self._ontology()
        return frozenset(ont.get_relationship(r) for r in data.union_of)


_BUILTINS = {
    "is_a": RelationshipData(
        id="is_a",
        anonymous=False,
        name="is a",
        namespace=None,
        alternate_ids=None,
        definition=Definition(
            "A subclassing relationship between one term and another",
            xrefs=set(
                {
                    Xref(
                        "http://owlcollab.github.io/oboformat/doc/GO.format.obo-1_4.html"
                    )
                }
            ),
        ),
        comment=None,
        subsets=None,
        synonyms=None,
        xrefs=None,
        annotations=None,
        domain=None,
        range=None,
        builtin=True,
        holds_over_chain=None,
        antisymmetric=True,
        cyclic=True,
        reflexive=True,
        asymmetric=False,
        symmetric=False,
        transitive=True,
        functional=False,
        inverse_functional=False,
        intersection_of=None,
        union_of=None,
        equivalent_to=None,
        disjoint_from=None,
        inverse_of=None,
        transitive_over=None,
        equivalent_to_chain=None,
        disjoint_over=None,
        relationships=None,
        obsolete=False,
        created_by=None,
        creation_date=None,
        replaced_by=None,
        consider=None,
        expand_assertion_to=None,  # TODO
        expand_expression_to=None,  # TODO
        metadata_tag=False,
        class_level=True,
    )
}
