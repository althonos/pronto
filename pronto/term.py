import collections.abc
import datetime
import itertools
import typing
import queue
from typing import (
    Callable,
    Deque,
    Dict,
    Iterator,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Union,
    FrozenSet,
)

import frozendict
import networkx

from . import relationship
from .entity import Entity, EntityData
from .definition import Definition
from .xref import Xref
from .synonym import Synonym, SynonymData
from .relationship import Relationship
from .pv import PropertyValue, ResourcePropertyValue, LiteralPropertyValue
from .utils.impl import set
from .utils.meta import typechecked

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class TermData(EntityData):  # noqa: R0902, R0903
    """Internal data storage of `Term` information.
    """

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
    union_of: Set[str]
    disjoint_from: Set[str]
    relationships: Dict[str, Set[str]]
    obsolete: bool
    replaced_by: Set[str]
    consider: Set[str]
    builtin: bool
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    equivalent_to: Set[str]
    annotations: Set[PropertyValue]

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


class Term(Entity):
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

    # --- Methods ------------------------------------------------------------

    def objects(self, r: Relationship) -> Iterator["Term"]:
        """Iterate over the terms ``t`` verifying ``self · r · t``.

        Example:
            >>> go = pronto.Ontology.from_obo_library("go.obo")
            >>> go['GO:0048870']
            Term('GO:0048870', name='cell motility')
            >>> list(go['GO:0048870'].objects(go['part_of']))
            [Term('GO:0051674', name='localization of cell')]

        Todo:
            Make `Term.objects` take in account ``holds_over_chain`` and
            ``transitive_over`` values of the relationship it is building an
            iterator with.

        """

        if r._data() is relationship._BUILTINS["is_a"]:
            return self.superclasses()

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

    def superclasses(self, distance: Optional[int] = None) -> Iterator["Term"]:
        """Get an iterator over the superclasses of this `Term`.

        In order to follow the semantics of ``rdf:subClassOf``, which in turn
        respects the mathematical inclusion of subset inclusion, ``is_a`` is
        defined as a transitive relationship, hence ``has_subclass`` is also
        transitive by closure property. Therefore ``self`` is always yielded
        first when calling this method.

        Arguments:
            distance (int, optional): The maximum distance between this node
                and the yielded superclass (`0` for the term itself, `1` for
                its immediate superclasses, etc.). Use `None` to explore
                transitively the entire directed graph.

        Yields:
            `Term`: Superclasses of the selected term, breadth-first. The
            first element is always the term itself, use `itertools.islice`
            to skip it.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> sup = ms['MS:1000143'].superclasses()
            >>> next(sup)
            Term('MS:1000143', name='API 150EX')
            >>> next(sup)
            Term('MS:1000121', name='SCIEX instrument model')
            >>> next(sup)
            Term('MS:1000031', name='instrument model')

        Note:
            The time complexity for this algorithm is in :math:`O(n)`, where
            :math:`n` is the number of terms in the source ontology.

        See Also:
            The `RDF Schema 1.1 <https://www.w3.org/TR/rdf-schema/>`_
            specification, defining the ``rdfs:subClassOf`` property, which
            the ``is_a`` relationship is translated to in OWL2 language.

        """
        distmax: float = distance if distance is not None else float("+inf")
        is_a: Relationship = self._ontology().get_relationship("is_a")

        # Search objects terms
        sup: Set[Term] = set()
        done: Set[Term] = set()
        frontier: Deque[Tuple[Term, int]] = collections.deque()

        # RDF semantics state that self is a subclass of self
        frontier.append((self, 0))
        sup.add(self)
        yield self

        # Explore the graph
        while frontier:
            node, distance = frontier.popleft()
            neighbors: Set[Term] = set(node.relationships.get(is_a, ()))
            if distance < distmax:
                for node in sorted(neighbors - done):
                    frontier.append((node, distance + 1))
                for neighbor in sorted(neighbors - sup):
                    sup.add(neighbor)
                    yield neighbor
            done.add(node)

    def subclasses(self, distance: Optional[int] = None) -> Iterator["Term"]:
        """Get an iterator over the subclasses of this `Term`.

        Yields:
            `Term`: Subclasses of the selected term, breadth-first. The first
            element is always the term itself, use `itertools.islice` to skip
            it.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> sub = ms['MS:1000031'].subclasses()
            >>> next(sub)
            Term('MS:1000031', name='instrument model')
            >>> next(sub)
            Term('MS:1000121', name='SCIEX instrument model')
            >>> next(sub)
            Term('MS:1000122', name='Bruker Daltonics instrument model')

        Note:
            This method has a runtime of :math:`O(n^2)` where :math:`n` is the
            number of terms in the source ontology in the worst case. This is
            due to the fact that OBO and OWL only explicit *superclassing*
            relationship, so we have to build the graph of *subclasses* from
            the knowledge graph. By caching the graph however, this can be
            reduced to an :math:`O(n)` operation.

        """
        ont: "Ontology" = self._ontology()
        distmax: float = distance if distance is not None else float("+inf")

        # use the subclassing cache from the `Ontology` or build it ourselves
        graph: Optional[Dict[str, Set[str]]] = ont._subclassing_cache
        if graph is None:
            is_a: Relationship = ont.get_relationship("is_a")
            graph = dict()
            for t in ont.terms():
                for t2 in t.relationships.get(is_a, []):
                    graph.setdefault(t2.id, set()).add(t.id)
            ont._subclassing_cache = graph

        # Search objects terms
        sub: Set[str] = set()
        done: Set[str] = set()
        frontier: Deque[Tuple[str, int]] = collections.deque()

        # RDF semantics state that self is a subclass of self
        frontier.append((self.id, 0))
        sub.add(self.id)
        yield self

        # Explore the graph
        while frontier:
            node, distance = frontier.popleft()
            done.add(node)
            try:
                neighbors: Set[str] = graph[node]
                if distance < distmax:
                    for node in sorted(neighbors - done):
                        frontier.append((node, distance + 1))
                    for neighbor in sorted(neighbors - sub):
                        sub.add(neighbor)
                        yield ont.get_term(neighbor)
            except KeyError:
                pass

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
        """
        ont = self._ontology()
        is_a = ont.get_relationship("is_a")
        for t in self._ontology().terms():
            if self in t.relationships.get(is_a, {}):
                return False
        return True

    # --- Attributes ---------------------------------------------------------

    @property
    def disjoint_from(self) -> FrozenSet["Term"]:
        """The terms declared as disjoint from this term.

        Two terms are disjoint if they have no instances or subclasses in
        common.
        """
        ontology, termdata = self._ontology(), self._data()
        return frozenset({ontology.get_term(id) for id in termdata.disjoint_from})

    @disjoint_from.setter
    @typechecked(property=True)
    def disjoint_from(self, terms: FrozenSet["Term"]):
        self._data().disjoint_from = set(term.id for term in terms)

    @property
    def intersection_of(
        self
    ) -> FrozenSet[Union["Term", Tuple[Relationship, "Term"]]]:
        """The terms or term relationships this term is an intersection of.
        """
        ont, termdata = self._ontology(), self._data()
        intersection_of: List[Union["Term", Tuple[Relationship, "Term"]]] = []
        for item in termdata.intersection_of:
            if len(item) == 2:
                r, t = item
                intersection_of.append((ont.get_relationship(r), ont.get_term(t)))
            else:
                intersection_of.append(ont.get_term(typing.cast(str, item)))
        return frozenset(intersection_of)

    @property
    def relationships(self) -> Mapping[Relationship, FrozenSet["Term"]]:
        ont, termdata = self._ontology(), self._data()
        return frozendict.frozendict(
            {
                Relationship(ont, ont.get_relationship(rel)._data()): frozenset(
                    Term(ont, ont.get_term(term)._data()) for term in terms
                )
                for rel, terms in termdata.relationships.items()
            }
        )

    @relationships.setter
    def relationships(self, r: Mapping[Relationship, Iterable["Term"]]):
        self._data().relationships = {
            relation.id: set(t.id for t in terms) for relation, terms in r.items()
        }

    @property
    def replaced_by(self) -> FrozenSet["Term"]:
        ontology, termdata = self._ontology(), self._data()
        return frozenset({ontology.get_term(t) for t in termdata.replaced_by})

    @property
    def union_of(self) -> FrozenSet["Term"]:
        termdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_term(t) for t in termdata.union_of)

    @union_of.setter
    @typechecked(property=True)
    def union_of(self, union_of: FrozenSet["Term"]):
        if len(union_of) == 1:
            raise ValueError("'union_of' cannot have a cardinality of 1")
        self._data().union_of = set(term.id for term in union_of)

    @property
    def consider(self) -> FrozenSet["Term"]:
        termdata, ont = self._data(), self._ontology()
        return frozenset(ont.get_term(t) for t in termdata.consider)
