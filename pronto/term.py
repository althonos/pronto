import collections.abc
import datetime
import itertools
import operator
import typing
import warnings
from typing import (
    AbstractSet,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Union,
)

from . import relationship
from .definition import Definition
from .entity import Entity, EntityData, EntitySet
from .logic import SubclassesIterator, SuperclassesIterator
from .logic.lineage import SubclassesHandler, SuperclassesHandler
from .pv import PropertyValue
from .relationship import Relationship
from .synonym import SynonymData
from .utils.meta import typechecked
from .utils.warnings import NotImplementedWarning
from .xref import Xref

if typing.TYPE_CHECKING:
    from .ontology import Ontology


__all__ = ["TermData", "Term", "TermSet"]


class TermData(EntityData):  # noqa: R0902, R0903
    """Internal data storage of `Term` information."""

    id: str
    anonymous: bool
    name: Optional[str]
    alternate_ids: Set[str]
    definition: Optional[Definition]
    comment: Optional[str]
    synonyms: Set[SynonymData]
    subsets: Set[str]
    namespace: Optional[str]
    xrefs: Set[Xref]
    intersection_of: Set[Union[str, Tuple[str, str]]]
    obsolete: bool
    builtin: bool
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    annotations: Set[PropertyValue]

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

    __slots__ = tuple(__annotations__)  # noqa: E0602

    def __init__(
        self,
        id,
        anonymous=False,
        name=None,
        alternate_ids=None,
        definition=None,
        comment=None,
        synonyms=None,
        subsets=None,
        namespace=None,
        xrefs=None,
        intersection_of=None,
        union_of=None,
        disjoint_from=None,
        relationships=None,
        obsolete=False,
        replaced_by=None,
        consider=None,
        builtin=False,
        created_by=None,
        creation_date=None,
        equivalent_to=None,
        annotations=None,
    ):
        self.id = id
        self.anonymous = anonymous
        self.name = name
        self.alternate_ids = alternate_ids or set()
        self.definition = definition
        self.comment = comment
        self.synonyms = synonyms or set()
        self.subsets = subsets or set()
        self.namespace = namespace or None
        self.xrefs = xrefs or set()
        self.intersection_of = intersection_of or set()
        self.union_of = union_of or set()
        self.disjoint_from = disjoint_from or set()
        self.relationships = relationships or dict()
        self.obsolete = obsolete
        self.replaced_by = replaced_by or set()
        self.consider = consider or set()
        self.builtin = builtin
        self.created_by = created_by
        self.creation_date = creation_date
        self.equivalent_to = equivalent_to or set()
        self.annotations = annotations or set()


class TermSet(EntitySet["Term"]):
    """A specialized mutable set to store `Term` instances."""

    # --- Methods ------------------------------------------------------------

    def subclasses(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SubclassesIterator:
        """Get an iterator over the subclasses of all terms in the set.

        Caution:
            Contrary to `pronto.Term.subclasses`, this method **does not**
            return a handler that lets you edit the subclasses directly.
            Adding a new subclass to all the members of the set must be
            done explicitly.

        """
        return SubclassesIterator(*self, distance=distance, with_self=with_self)

    def superclasses(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SuperclassesIterator:
        """Get an iterator over the superclasses of all terms in the set.

        Caution:
            Contrary to `pronto.Term.superclasses`, this method **does not**
            return a handler that lets you edit the superclasses directly.
            Adding a new superclass to all the members of the set must be
            done explicitly.

        Example:
            >>> ms = pronto.Ontology("ms.obo")
            >>> s = pronto.TermSet({ms['MS:1000122'], ms['MS:1000124']})
            >>> s.superclasses(with_self=False).to_set().ids
            frozenset({'MS:1000031'})
            >>> ms["MS:1000031"]
            Term('MS:1000031', name='instrument model')

        """
        return SuperclassesIterator(*self, distance=distance, with_self=with_self)


class Term(Entity["TermData", "TermSet"]):
    """A term, corresponding to a node in the ontology graph.

    Formally a `Term` frame is equivalent to an ``owl:Class`` declaration in
    OWL2 language. However, some constructs may not be possible to express in
    both OBO and OWL2.

    `Term` should not be manually instantiated, but obtained from an existing
    `Ontology` instance, using either the `~Ontology.create_term` or the
    `~Ontology.get_term` method.
    """

    if typing.TYPE_CHECKING:

        def __init__(self, ontology: "Ontology", termdata: "TermData"):
            super().__init__(ontology, termdata)

        def _data(self) -> "TermData":
            return typing.cast("TermData", super()._data())

    # --- Associated type variables ------------------------------------------

    _Set = TermSet
    _data_getter = operator.attrgetter("_terms")

    # --- Methods ------------------------------------------------------------

    def objects(self, r: Relationship) -> Iterator["Term"]:
        """Iterate over the terms ``t`` verifying ``self · r · t``.

        Example:
            >>> go = pronto.Ontology.from_obo_library("go.obo")
            >>> go['GO:0048870']
            Term('GO:0048870', name='cell motility')
            >>> list(go['GO:0048870'].objects(go.get_relationship('part_of')))
            [Term('GO:0051674', name='localization of cell')]

        Todo:
            Make `Term.objects` take in account ``holds_over_chain`` and
            ``transitive_over`` values of the relationship it is building an
            iterator with.

        """
        # delegate import of NetworkX
        import networkx

        if r._data() is relationship._BUILTINS["is_a"]:
            warnings.warn(
                "using the `is_a` relationship with `Term.objects` will not be "
                "supported in future versions, use `Term.superclasses` instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return self.superclasses()

        warnings.warn(
            "`Term.objects` is not semantically correct, most of the logic "
            "rules have not been implemented. Consider using an actual "
            "reasoner instead.",
            category=NotImplementedWarning,
            stacklevel=2
        )

        g = networkx.MultiDiGraph()
        ont = self._ontology()

        # Build the graph
        for t in ont.terms():
            g.add_node(t.id)
            for (rel, terms) in t.relationships.items():
                for t2 in terms:
                    g.add_edge(t.id, t2.id, key=rel.id)
                    if rel.symmetric:
                        g.add_edge(t2.id, t.id, key=rel.id)
                    elif rel.inverse_of is not None:
                        g.add_edge(t2.id, t.id, key=rel.inverse_of.id)

        # Search objects terms
        red, done = set(), set()
        is_red = red.__contains__
        frontier = {self.id}

        # Initial connected components
        if r.reflexive:
            red.add(self.id)
            yield self
        for other in g.neighbors(self.id):
            if r.id in g.get_edge_data(self.id, other):
                red.add(other)
                yield ont.get_term(other)

        # Explore the graph
        while frontier:
            node = frontier.pop()
            frontier.update(n for n in g.neighbors(node) if n not in done)
            if is_red(node) and r.transitive:
                for other in itertools.filterfalse(is_red, g.neighbors(node)):
                    if r.id in g.get_edge_data(node, other):
                        red.add(other)
                        yield ont.get_term(other)
            done.add(node)

    def superclasses(
        self,
        distance: Optional[int] = None,
        with_self: bool = True,
    ) -> "SuperclassesHandler":
        """Get an handle over the superclasses of this `Term`.

        In order to follow the semantics of ``rdf:subClassOf``, which in turn
        respects the mathematical definition of subset inclusion, ``is_a`` is
        defined as a reflexive relationship, and so is its inverse
        relationship.

        Arguments:
            distance (int, optional): The maximum distance between this term
                and the yielded superclass (`0` for the term itself, `1` for
                its immediate superclasses, etc.). Use `None` to explore
                transitively the entire directed graph.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is reflexive, so this is enabled
                by default, but in most practical cases only the distinct
                subclasses are desired.

        Yields:
            `Term`: Superclasses of the selected term, breadth-first. The
            first element is always the term itself, use `itertools.islice`
            to skip it.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> sup = iter(ms['MS:1000143'].superclasses())
            >>> next(sup)
            Term('MS:1000143', name='API 150EX')
            >>> next(sup)
            Term('MS:1000121', name='SCIEX instrument model')
            >>> next(sup)
            Term('MS:1000031', name='instrument model')

        Note:
            The time complexity for this algorithm is in :math:`O(n)`, where
            :math:`n` is the number of subclasses of initial term.

        See Also:
            The `RDF Schema 1.1 <https://www.w3.org/TR/rdf-schema/>`_
            specification, defining the ``rdfs:subClassOf`` property, which
            the ``is_a`` relationship is translated to in OWL2 language.

        """
        return SuperclassesHandler(self, distance=distance, with_self=with_self)

    def subclasses(
        self,
        distance: Optional[int] = None,
        with_self: bool = True,
    ) -> "SubclassesHandler":
        """Get an handle over the subclasses of this `Term`.

        Arguments:
            distance (int, optional): The maximum distance between this term
                and the yielded subclass (`0` for the term itself, `1` for
                its immediate children, etc.). Use `None` to explore the
                entire directed graph transitively.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is reflexive, so this is enabled
                by default, but in most practical cases only the distinct
                subclasses are desired.

        Yields:
            `Term`: Subclasses of the selected term, breadth-first. The first
            element is always the term itself, use `itertools.islice` to skip
            it.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> sub = iter(ms['MS:1000031'].subclasses())
            >>> next(sub)
            Term('MS:1000031', name='instrument model')
            >>> next(sub)
            Term('MS:1000121', name='SCIEX instrument model')
            >>> next(sub)
            Term('MS:1000122', name='Bruker Daltonics instrument model')

        Hint:
            Use the ``to_set`` method of the returned iterator to efficiently
            collect all subclasses into a `TermSet`.

        Note:
            This method has a runtime that is :math:`O(n)` where :math:`n` is
            the number of subclasses of the initial term. While OBO and OWL
            only explicit the *superclassing* relationship (equivalent to the
            ``rdfs:subClassOf`` property in RDF), we can build a cache that
            stores the edges of the resulting knowledge graph in an index
            accessible by both endpoints of each edge.

        """
        return SubclassesHandler(self, distance=distance, with_self=with_self)

    def is_leaf(self) -> bool:
        """Check whether the term is a leaf in the ontology.

        We define leaves as nodes in the ontology which do not have subclasses
        since the subclassing relationship is directed and can be used to
        create a DAG of all the terms in the ontology.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> ms['MS:1000031'].is_leaf()   # instrument model
            False
            >>> ms['MS:1001792'].is_leaf()   # Xevo TQ-S
            True

        Note:
            This method has a runtime of :math:`O(1)` as `Ontology` objects
            internally cache the subclasses of each term.

        """
        return not self._ontology()._terms.lineage[self.id].sub

    # --- Attributes ---------------------------------------------------------

    @property
    def intersection_of(self) -> FrozenSet[Union["Term", Tuple[Relationship, "Term"]]]:
        """`frozenset`: The terms this term is an intersection of."""
        ont, termdata = self._ontology(), self._data()
        intersection_of: List[Union["Term", Tuple[Relationship, "Term"]]] = []
        for item in termdata.intersection_of:
            if isinstance(item, str):
                intersection_of.append(ont.get_term(typing.cast(str, item)))
            else:
                r, t = item
                intersection_of.append((ont.get_relationship(r), ont.get_term(t)))
        return frozenset(intersection_of)

    @intersection_of.setter
    def intersection_of(
        self, intersection_of: Iterable[Union["Term", Tuple[Relationship, "Term"]]]
    ):
        data = set()
        for item in intersection_of:
            if isinstance(item, Term):
                data.add(item.id)
            elif isinstance(item, collections.abc.Collection) and len(item) == 2:
                rel, term = item  # type: ignore
                data.add((rel.id, term.id))  # type: ignore
            else:
                msg = "expected iterable of `Term` or `Relationship`, `Term` couple, found: {}"
                raise TypeError(msg.format(type(item).__name__))
        self._data().intersection_of = data
