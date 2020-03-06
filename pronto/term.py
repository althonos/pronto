import collections.abc
import datetime
import itertools
import operator
import typing
from typing import (
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
    MutableSet,
    AbstractSet,
)

import frozendict
import networkx

from . import relationship
from .entity import Entity, EntityData
from .definition import Definition
from .xref import Xref
from .synonym import SynonymData
from .relationship import Relationship
from .pv import PropertyValue
from .logic import SubclassesIterator, SuperclassesIterator
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

    def superclasses(
        self, distance: Optional[int] = None, with_self: bool = True,
    ) -> Iterator["Term"]:
        """Get an iterator over the superclasses of this `Term`.

        In order to follow the semantics of ``rdf:subClassOf``, which in turn
        respects the mathematical inclusion of subset inclusion, ``is_a`` is
        defined as a transitive relationship, hence ``has_subclass`` is also
        transitive by closure property.

        Arguments:
            distance (int, optional): The maximum distance between this term
                and the yielded superclass (`0` for the term itself, `1` for
                its immediate superclasses, etc.). Use `None` to explore
                transitively the entire directed graph.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is transitive, so this is enabled
                by default, but in most practical cases only the distinct
                subclasses are desired.

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
        return SuperclassesIterator(self, distance=distance, with_self=with_self)

    def subclasses(
        self, distance: Optional[int] = None, with_self: bool = True,
    ) -> SubclassesIterator:
        """Get an iterator over the subclasses of this `Term`.

        Arguments:
            distance (int, optional): The maximum distance between this term
                and the yielded subclass (`0` for the term itself, `1` for
                its immediate children, etc.). Use `None` to explore the
                entire directed graph transitively.
            with_self (bool): Whether or not to include the current term in
                the terms being yielded. RDF semantics state that the
                ``rdfs:subClassOf`` property is transitive, so this is enabled
                by default, but in most practical cases only the distinct
                subclasses are desired.

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

        Hint:
            Use the ``to_set`` method of the returned iterator to efficiently
            collect all subclasses into a `TermSet`.

        Note:
            This method has a runtime of :math:`O(n^2)` where :math:`n` is the
            number of terms in the source ontology in the worst case. This is
            due to the fact that OBO and OWL only explicit *superclassing*
            relationship, so we have to build the graph of *subclasses* from
            the knowledge graph. By caching the graph however, this can be
            reduced to an :math:`O(n)` operation.

        """
        return SubclassesIterator(self, distance=distance, with_self=with_self)

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
        return not self._ontology()._inheritance[self.id].sub

    # --- Attributes ---------------------------------------------------------

    @property
    def disjoint_from(self) -> "TermSet":
        """The terms declared as disjoint from this term.

        Two terms are disjoint if they have no instances or subclasses in
        common.
        """
        s = TermSet()
        s._ids = self._data().disjoint_from
        s._ontology = self._ontology()
        return s

    @disjoint_from.setter
    def disjoint_from(self, terms: Iterable["Term"]):
        self._data().disjoint_from = set(term.id for term in terms)

    @property
    def equivalent_to(self) -> FrozenSet[str]:
        """The terms declared as equivalent to this term.
        """
        s = TermSet()
        s._ids = self._data().equivalent_to
        s._ontology = self._ontology()
        return s

    @equivalent_to.setter
    def equivalent_to(self, terms:  Iterable["Term"]):
        self._data().equivalent_to = set(equivalent_to.id for term in terms)

    @property
    def intersection_of(self) -> FrozenSet[Union["Term", Tuple[Relationship, "Term"]]]:
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

    @intersection_of.setter
    def intersection_of(
        self, intersection_of: Iterable[Union["Term", Tuple[Relationship, "Term"]]]
    ):
        data = set()
        for item in intersection_of:
            if isinstance(item, Term):
                data.add(item.id)
            elif isinstance(item, collections.abc.Collection) and len(item) == 2:
                rel, term = item
                data.add((rel.id, term.id))
            else:
                msg = "expected iterable of `Term` or `Relationship`, `Term` couple, found: {}"
                raise TypeError(msg.format(type(item).__name__))
        self._data().intersection_of = data

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
        self._data().relationships = relationships = {
            relation.id: set(t.id for t in terms) for relation, terms in r.items()
        }

        ## FIXME: Maybe wrap in a single function
        cache = self._ontology()._inheritance
        previous_super = cache[self.id].sup
        new_super = relationships.get("is_a", set())
        for removed in previous_super - new_super:
            cache[removed].sub.remove(self.id)
        for added in new_super - previous_super:
            cache[added].sub.add(self.id)
        cache[self.id].sup.clear()
        cache[self.id].sup.update(new_super)

    @property
    def replaced_by(self) -> "TermSet":
        s = TermSet()
        s._ids = self._data().replaced_by
        s._ontology = self._ontology()
        return s

    @replaced_by.setter
    def replaced_by(self, replaced_by: Iterable["Term"]) -> None:
        if isinstance(replaced_by, TermSet):
            data = replaced_by._ids
        else:
            data = set(term.id for term in replaced_by)
        self._data().replaced_by = data

    @property
    def union_of(self) -> "TermSet":
        s = TermSet()
        s._ids = self._data().union_of
        s._ontology = self._ontology()
        return s

    @union_of.setter
    def union_of(self, union_of: Iterable["Term"]) -> None:
        if isinstance(union_of, TermSet):
            data = union_of._ids
        else:
            data = set()
            for term in union_of:
                if isinstance(term, Term):
                    data.add(term.id)
                else:
                    raise TypeError(f"expected Term, found {type(term).__name__}")
        if len(data) == 1:
            raise ValueError("'union_of' cannot have a cardinality of 1")
        self._data().union_of = data

    @property
    def consider(self) -> "TermSet":
        s = TermSet()
        s._ids = self._data().consider
        s._ontology = self._ontology()
        return s

    @consider.setter
    def consider(self, consider: Iterable["Term"]) -> None:
        if isinstance(consider, TermSet):
            data = consider._ids
        else:
            data = set(term.id for term in consider)
        self._data().consider = data


class TermSet(MutableSet[Term]):
    """A specialized mutable set to store `Term` instances.
    """

    def __init__(self, terms: Optional[Iterable[Term]] = None) -> None:
        self._ids: Set[str] = set()
        self._ontology: "Optional[Ontology]" = None

        for term in terms if terms is not None else ():
            if __debug__ and not isinstance(term, Term):
                err_msg = "'terms' must be iterable of Term, not {}"
                raise TypeError(err_msg.format(type(term).__name__))
            if self._ontology is None:
                self._ontology = term._ontology()
            if self._ontology is not term._ontology():
                raise ValueError("terms do not originate from the same ontology")
            self._ids.add(term.id)

    def __contains__(self, other: object):
        if isinstance(other, Term):
            return other.id in self._ids
        return False

    def __iter__(self) -> Iterator[Term]:
        return map(lambda t: self._ontology.get_term(t), iter(self._ids))

    def __len__(self):
        return len(self._ids)

    def __repr__(self):
        ontology = self._ontology
        elements = (ontology[id_].__repr__() for id_ in self._ids)
        return f"{type(self).__name__}({{{', '.join(elements)}}})"

    def __iand__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            self._ids &= other._ids
        else:
            super().__iand__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __and__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            s = TermSet()
            s._ids = self._ids.__and__(other._ids)
            s._ontology = self._ontology if s._ids else None
        else:
            s = TermSet(super().__and__(other))
        return s

    def __ior__(self, other: AbstractSet[Term]) -> "TermSet":
        if not isinstance(other, TermSet):
            other = TermSet(other)
        self._ids |= other._ids
        self._ontology = self._ontology or other._ontology
        return self

    def __or__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            s = TermSet()
            s._ids = self._ids.__or__(other._ids)
            s._ontology = self._ontology
        else:
            s = TermSet(super().__or__(other))
        return s

    def __isub__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            self._ids -= other._ids
        else:
            super().__isub__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __sub__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            s = TermSet()
            s._ids = self._ids.__sub__(other._ids)
            s._ontology = self._ontology
        else:
            s = TermSet(super().__sub__(other))
        return s

    def __ixor__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            self._ids ^= other._ids
        else:
            super().__ixor__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __xor__(self, other: AbstractSet[Term]) -> "TermSet":
        if isinstance(other, TermSet):
            s = TermSet()
            s._ids = self._ids.__xor__(other._ids)
        else:
            s = TermSet(super().__xor__(other))
        if not s._ids:
            s._ontology = None
        return s

    @typechecked()
    def add(self, term: Term) -> None:
        self._ids.add(term.id)

    def clear(self) -> None:
        self._ids.clear()
        self._ontology = None

    @typechecked()
    def discard(self, term: Term) -> None:
        self._ids.discard(term.id)

    def pop(self) -> Term:
        return self._ontology.get_term(self._ids.pop())

    @typechecked()
    def remove(self, term: Term):
        self._ids.remove(term.id)

    # --- Attributes ---------------------------------------------------------

    @property
    def ids(self) -> FrozenSet[str]:
        return frozenset(map(operator.attrgetter("id"), iter(self)))

    @property
    def alternate_ids(self) -> FrozenSet[str]:
        return frozenset(id for term in self for id in term.alternate_ids)

    @property
    def names(self) -> FrozenSet[str]:
        return frozenset(map(operator.attrgetter("name"), iter(self)))

    def subclasses(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SubclassesIterator:
        """Get an iterator over the subclasses of all terms in the set.
        """
        return SubclassesIterator(*self, distance=distance, with_self=with_self)

    def superclasses(
        self, distance: Optional[int] = None, with_self: bool = True
    ) -> SubclassesIterator:
        """Get an iterator over the superclasses of all terms in the set.

        Example:
            >>> ms = pronto.Ontology("ms.obo")
            >>> s = pronto.TermSet({ms['MS:1000122'], ms['MS:1000124']})
            >>> s.superclasses(with_self=False).to_set().ids
            frozenset({'MS:1000031'})
            >>> ms["MS:1000031"]
            Term('MS:1000031', name='instrument model')
        """
        return SuperclassesIterator(*self, distance=distance, with_self=with_self)
