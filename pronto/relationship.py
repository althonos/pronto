import datetime
import operator
import typing
from dataclasses import field
from typing import Dict, Iterable, FrozenSet, Optional, Set, Tuple, Iterator

from .definition import Definition
from .entity import Entity, EntityData, EntitySet
from .logic import SubpropertiesIterator, SuperpropertiesIterator
from .logic.lineage import SubpropertiesHandler, SuperpropertiesHandler
from .pv import PropertyValue
from .synonym import SynonymData
from .utils.meta import typechecked, dataclass
from .xref import Xref

if typing.TYPE_CHECKING:
    from .ontology import Ontology
    from .term import Term


__all__ = ["Relationship", "RelationshipData", "RelationshipSet"]


@dataclass(init=True, slots=True, weakref_slot=True)
class RelationshipData(EntityData):
    """Internal data storage of `Relationship` information."""

    domain: Optional[str] = field(default=None)
    range: Optional[str] = field(default=None)
    holds_over_chain: Set[Tuple[str, str]] = field(default_factory=set)
    antisymmetric: bool = field(default=False)
    cyclic: bool = field(default=False)
    reflexive: bool = field(default=False)
    asymmetric: bool = field(default=False)
    symmetric: bool = field(default=False)
    transitive: bool = field(default=False)
    functional: bool = field(default=False)
    inverse_functional: bool = field(default=False)
    intersection_of: Set[str] = field(default_factory=set)
    inverse_of: Optional[str] = field(default=None)
    transitive_over: Set[str] = field(default_factory=set)
    equivalent_to_chain: Set[Tuple[str, str]] = field(default_factory=set)
    disjoint_over: Set[str] = field(default_factory=set)
    expand_assertion_to: Set[Definition] = field(default_factory=set)
    expand_expression_to: Set[Definition] = field(default_factory=set)
    metadata_tag: bool = field(default=False)
    class_level: bool = field(default=False)


class RelationshipSet(EntitySet["Relationship"]):
    """A specialized mutable set to store `Relationship` instances."""

    # --- Magic methods ------------------------------------------------------

    def __iter__(self) -> Iterator["Relationship"]:
        return map(lambda t: self._ontology.get_relationship(t), iter(self._ids))  # type: ignore

    # --- Methods ---------------------------------------------------------

    def subproperties(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SubpropertiesIterator:
        """Get an iterator over the subproperties of all relationships in the set."""
        return SubpropertiesIterator(*self, distance=distance, with_self=with_self)

    def superproperties(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SuperpropertiesIterator:
        """Get an iterator over the superproperties of all relationships in the set.

        Example:
            >>> pato = pronto.Ontology("pato.obo")
            >>> proportionality_to = pato["PATO:0001470"]
            >>> quality_mapping = pronto.RelationshipSet(
            ...     r for r in pato.relationships()
            ...     if r.domain == proportionality_to
            ... )
            >>> sorted(quality_mapping.subproperties().to_set().ids)
            ['has_dividend_entity', 'has_dividend_quality', ...

        """
        return SuperpropertiesIterator(*self, distance=distance, with_self=with_self)


class Relationship(Entity["RelationshipData", "RelationshipSet"]):
    """A relationship, constitute the edges of the ontology graph.

    Also sometimes refered as typedefs, relationship types, properties or
    predicates. Formally equivalent to a property (either ``ObjectProperty``
    or ``AnnotationProperty``) in OWL2.
    """

    if typing.TYPE_CHECKING:

        def __init__(self, ontology: "Ontology", reldata: "RelationshipData"):
            super().__init__(ontology, reldata)

        def _data(self) -> "RelationshipData":
            return typing.cast("RelationshipData", super()._data())

    # --- Associated type variables ------------------------------------------

    _Set = RelationshipSet
    _data_getter = operator.attrgetter("_relationships")

    # --- Methods ------------------------------------------------------------

    def subproperties(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> "SubpropertiesHandler":
        """Get an handle over the subproperties of this `Relationship`.

        Arguments:
            distance (int, optional): The maximum distance between this
                relationship and the yielded subproperties (`0` for the
                relationship itself, `1` for its immediate children, etc.).
                Use `None` to explore the entire directed graph transitively.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is reflexive (and therefore is
                ``rdfs:subPropertyOf`` reflexive too by transitivity), so this
                is enabled by default, but in most practical cases only the
                distinct subproperties are desired.

        """
        return SubpropertiesHandler(self, distance=distance, with_self=with_self)

    def superproperties(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> "SuperpropertiesHandler":
        """Get an handle over the superproperties of this `Relationship`.

        In order to follow the semantics of ``rdf:subPropertyOf``, which in
        turn respects the mathematical definition of subset inclusion, ``is_a``
        is defined as a transitive relationship, hence the inverse relationship
        is also transitive by closure property.

        Arguments:
            distance (int, optional): The maximum distance between this
                relationship and the yielded subperoperties (`0` for the
                relationship itself, `1` for its immediate parents, etc.).
                Use `None` to explore the entire directed graph transitively.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is transitive (and therefore is
                ``rdfs:subPropertyOf`` transitive too), so this is enabled
                by default, but in most practical cases only the distinct
                subproperties are desired.

        """
        return SuperpropertiesHandler(self, distance=distance, with_self=with_self)

    # --- Attributes ---------------------------------------------------------

    @property
    def antisymmetric(self) -> bool:
        """`bool`: Whether this relationship is anti-symmetric."""
        return self._data().antisymmetric

    @antisymmetric.setter  # type: ignore
    @typechecked(property=True)
    def antisymmetric(self, value: bool) -> None:
        self._data().antisymmetric = value

    @property
    def asymmetric(self) -> bool:
        """`bool`: Whether this relationship is asymmetric."""
        return self._data().asymmetric

    @asymmetric.setter  # type: ignore
    @typechecked(property=True)
    def asymmetric(self, value: bool) -> None:
        self._data().asymmetric = value

    @property
    def class_level(self) -> bool:
        """`bool`: Whether this relationship is applied at class level.

        This tag affects how OBO ``relationship`` tags should be translated
        in OWL2: by default, all relationship tags are taken to mean an
        all-some relation over an instance level relation. With this flag
        set to `True`, the relationship will be translated to an `owl:hasValue`
        restriction.
        """
        return self._data().class_level

    @class_level.setter  # type: ignore
    @typechecked(property=True)
    def class_level(self, value: bool) -> None:
        self._data().class_level = value

    @property
    def cyclic(self) -> bool:
        """`bool`: Whether this relationship is cyclic."""
        return self._data().cyclic

    @cyclic.setter  # type: ignore
    @typechecked(property=True)
    def cyclic(self, value: bool) -> None:
        self._data().cyclic = value

    @property
    def disjoint_over(self) -> "RelationshipSet":
        """`frozenset`: The relationships this relationships is disjoint over."""
        s = RelationshipSet()
        s._ids = self._data().disjoint_over
        s._ontology = self._ontology()
        return s

    @property
    def domain(self) -> Optional["Term"]:
        """`Term` or `None`: The domain of the relationship, if any."""
        data, ontology = self._data(), self._ontology()
        if data.domain is not None:
            return ontology.get_term(data.domain)
        return None

    @domain.setter
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

    @equivalent_to_chain.setter
    def equivalent_to_chain(self, equivalent_to_chain: Iterable[Tuple["Relationship", "Relationship"]]):
        data = self._data()
        data.equivalent_to_chain = {
            (r1.id, r2.id)
            for r1, r2 in equivalent_to_chain
        }

    @property
    def expand_assertion_to(self) -> FrozenSet[Definition]:
        return frozenset(self._data().expand_assertion_to)

    @property
    def expand_expression_to(self) -> FrozenSet[Definition]:
        return frozenset(self._data().expand_expression_to)

    @property
    def functional(self) -> bool:
        """`bool`: Whether this relationship is functional."""
        return self._data().functional

    @functional.setter  # type: ignore
    @typechecked(property=True)
    def functional(self, value: bool) -> None:
        self._data().functional = value

    @property
    def inverse_functional(self) -> bool:
        """`bool`: Whether this relationship is inverse functional."""
        return self._data().inverse_functional

    @inverse_functional.setter  # type: ignore
    @typechecked(property=True)
    def inverse_functional(self, value: bool) -> None:
        self._data().inverse_functional = value

    @property
    def metadata_tag(self) -> bool:
        """`bool`: Whether or not this relationship is a metadata tag.

        This tag affects how OBO typedefs should be translated in OWL2: by
        default, all typedef tags are translated to an `owl:ObjectProperty`.
        With this flag set to `True`, the typedef will be translated to an
        `owl:AnnotationProperty`.
        """
        return self._data().metadata_tag

    @metadata_tag.setter  # type: ignore
    @typechecked(property=True)
    def metadata_tag(self, value: bool):
        self._data().metadata_tag = value

    @property
    def holds_over_chain(self) -> FrozenSet[Tuple["Relationship", "Relationship"]]:
        """`frozenset` of `Relationship` couples: The chains this relationship holds over."""
        ont: "Ontology" = self._ontology()
        data: "RelationshipData" = self._data()
        return frozenset(
            tuple(map(ont.get_term, chain))
            for chain in data.holds_over_chain
        )

    @holds_over_chain.setter
    def holds_over_chain(self, holds_over_chain: Iterable[Tuple["Relationship", "Relationship"]]) -> None:
        data: "RelationshipData" = self._data()
        data.holds_over_chain = {
            (r1.id, r2.id)
            for r1, r2 in holds_over_chain
        }

    @property
    def inverse_of(self) -> Optional["Relationship"]:
        """`Relationship` or `None`: The inverse of this relationship, if any."""
        ont, reldata = self._ontology(), self._data()
        if reldata.inverse_of is not None:
            return ont.get_relationship(reldata.inverse_of)
        return None

    @inverse_of.setter
    def inverse_of(self, value: Optional["Relationship"]):
        self._data().inverse_of = None if value is None else value.id

    @property
    def intersection_of(self) -> "RelationshipSet":
        """`RelationshipSet`: The relations this relationship is an intersection of."""
        s = RelationshipSet()
        s._ids = self._data().intersection_of
        s._ontology = self._ontology()
        return s

    @property
    def range(self) -> Optional["Term"]:
        """`Term` or `None`: The range of the relationship, if any."""
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
        """`bool`: Whether or not the relationship is reflexive."""
        return self._data().reflexive

    @reflexive.setter  # type: ignore
    @typechecked(property=True)
    def reflexive(self, value: bool):
        self._data().reflexive = value

    @property
    def symmetric(self) -> bool:
        """`bool`: Whether or not the relationship is symmetric."""
        return self._data().symmetric

    @symmetric.setter  # type: ignore
    @typechecked(property=True)
    def symmetric(self, value: bool):
        self._data().symmetric = value

    @property
    def transitive(self) -> bool:
        """`bool`: Whether or not the relationship is transitive."""
        return self._data().transitive

    @transitive.setter  # type: ignore
    @typechecked(property=True)
    def transitive(self, value: bool):
        self._data().transitive = value

    @property
    def transitive_over(self) -> "RelationshipSet":
        """`RelationshipSet`: The relations this relationship is transitive over."""
        s = RelationshipSet()
        s._ids = self._data().transitive_over
        s._ontology = self._ontology()
        return s


# TODO: remove in v3.0.0
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
