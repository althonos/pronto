import datetime
import operator
import typing
import weakref
from typing import AbstractSet, Any, Dict, FrozenSet, Iterable, Iterator, Optional, Set

from ..definition import Definition
from ..pv import PropertyValue
from ..synonym import Synonym, SynonymData, SynonymType
from ..utils.meta import roundrepr, typechecked
from ..xref import Xref

if typing.TYPE_CHECKING:
    from ..ontology import _DataGraph, Ontology
    from ..relationship import Relationship
    from .attributes import Relationships

__all__ = ["EntityData", "Entity", "EntitySet"]
_D = typing.TypeVar("_D", bound="EntityData")
_E = typing.TypeVar("_E", bound="Entity")
_S = typing.TypeVar("_S", bound="EntitySet")


class EntityData:

    id: str
    alternate_ids: Set[str]
    annotations: Set[PropertyValue]
    anonymous: bool
    builtin: bool
    comment: Optional[str]
    consider: Set[str]
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    disjoint_from: Set[str]
    definition: Optional[Definition]
    equivalent_to: Set[str]
    name: Optional[str]
    namespace: Optional[str]
    obsolete: bool
    relationships: Dict[str, Set[str]]
    replaced_by: Set[str]
    subsets: Set[str]
    synonyms: Set[SynonymData]
    union_of: Set[str]
    xrefs: Set[Xref]

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602


class Entity(typing.Generic[_D, _S]):
    """An entity in the ontology graph.

    With respects to the OBO semantics, an `Entity` is either a term or a
    relationship in the ontology graph. Any entity has a unique identifier as
    well as some common properties.
    """

    if __debug__ or typing.TYPE_CHECKING:

        __data: "weakref.ReferenceType[_D]"
        __slots__: Iterable[str] = ()

        def __init__(self, ontology: "Ontology", data: "_D"):
            self.__data = weakref.ref(data)
            self.__id = data.id
            self.__ontology = ontology

        def _data(self) -> "EntityData":
            rdata = self.__data()
            if rdata is None:
                raise RuntimeError("internal data was deallocated")
            return rdata

    else:

        __slots__: Iterable[str] = ("_data",)  # type: ignore

        def __init__(self, ontology: "Ontology", data: "_D"):
            self._data = weakref.ref(data)  # type: ignore
            self.__ontology = ontology
            self.__id = data.id

    _Set: typing.ClassVar[typing.Type[_S]] = NotImplemented
    _data_getter: typing.Callable[["Ontology"], "_DataGraph"] = NotImplemented

    # --- Private helpers ----------------------------------------------------

    def _ontology(self) -> "Ontology":
        return self.__ontology

    # --- Magic Methods ------------------------------------------------------

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Entity):
            return self.id == other.id
        return False

    def __lt__(self, other):
        if isinstance(other, Entity):
            return self.id < other.id
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Entity):
            return self.id <= other.id
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Entity):
            return self.id > other.id
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Entity):
            return self.id >= other.id
        return NotImplemented

    def __hash__(self):
        return hash((self.id))

    def __repr__(self):
        return roundrepr.make(type(self).__name__, self.id, name=(self.name, None))

    # --- Data descriptors ---------------------------------------------------

    @property
    def alternate_ids(self) -> Set[str]:
        """`set` of `str`: A set of alternate IDs for this entity."""
        return self._data().alternate_ids

    @alternate_ids.setter  # type: ignore
    def alternate_ids(self, ids: Iterable[str]):
        self._data().alternate_ids = set(ids)

    @property
    def annotations(self) -> Set[PropertyValue]:
        """`set` of `PropertyValue`: Annotations relevant to the entity."""
        return self._data().annotations

    @annotations.setter
    def annotations(self, value: Iterable[PropertyValue]) -> None:
        self._data().annotations = set(value)

    @property
    def anonymous(self) -> bool:
        """`bool`: Whether or not the entity has an anonymous id.

        Semantics of anonymous entities are the same as B-Nodes in RDF.
        """
        return self._data().anonymous

    @anonymous.setter
    def anonymous(self, value: bool):
        self._data().anonymous = value

    @property
    def builtin(self) -> bool:
        """`bool`: Whether or not the entity is built-in to the OBO format.

        ``pronto`` uses this tag on the ``is_a`` relationship, which is the
        axiomatic to the OBO language but treated as a relationship in the
        library.
        """
        return self._data().builtin

    @builtin.setter  # type: ignore
    @typechecked(property=True)
    def builtin(self, value: bool):
        self._data().builtin = value

    @property
    def comment(self) -> Optional[str]:
        """`str` or `None`: A comment about the current entity.

        Comments in ``comment`` clauses are guaranteed to be conserved by OBO
        parsers and serializers, unlike bang comments. A non `None` `comment`
        is semantically equivalent to a ``rdfs:comment`` in OWL2. When parsing
        from OWL, several RDF comments will be merged together into a single
        ``comment`` clause spanning over multiple lines.
        """
        return self._data().comment

    @comment.setter
    def comment(self, value: Optional[str]):
        self._data().comment = value

    @property
    def consider(self) -> _S:
        """`EntitySet`: A set of potential substitutes for an obsolete term.

        An obsolete entity can provide one or more entities which may be
        appropriate substitutes, but needs to be looked at carefully by a
        human expert before the replacement is done.

        See Also:
            `~Entity.replaced_by`, which provides a set of entities suitable
            for automatic replacement.

        """
        s = self._Set()
        s._ids = self._data().consider
        s._ontology = self._ontology()
        return s

    @consider.setter
    def consider(self, consider: Iterable[_E]) -> None:
        if isinstance(consider, EntitySet):
            data = consider._ids
        else:
            data = {entity.id for entity in consider}
        self._data().consider = data

    @property
    def created_by(self) -> Optional[str]:
        """`str` or `None`: The name of the creator of the entity, if any.

        This property gets translated to a ``dc:creator`` annotation in OWL2,
        which has very broad semantics. Some OBO ontologies may instead use
        other annotation properties such as the ones found in `Information
        Interchange Ontology <http://www.obofoundry.org/ontology/iao.html>`_,
        which can be accessed in the `annotations` attribute of the entity,
        if any.
        """
        return self._data().created_by

    @created_by.setter  # type: ignore
    @typechecked(property=True)
    def created_by(self, value: Optional[str]):
        self._data().created_by = value

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        """`~datetime.datetime` or `None`: The date the entity was created."""
        return self._data().creation_date

    @creation_date.setter  # type: ignore
    @typechecked(property=True)
    def creation_date(self, value: Optional[datetime.datetime]):
        self._data().creation_date = value

    @property
    def definition(self) -> Optional[Definition]:
        """`Definition` or `None`: The definition of the current entity.

        Definitions in OBO are intended to be human-readable text describing
        the entity, with some additional cross-references if possible.

        Example:
            >>> hp = pronto.Ontology.from_obo_library("hp.obo")
            >>> term = hp["HP:0009882"]
            >>> term.name
            'Short distal phalanx of finger'
            >>> str(term.definition)
            'Short distance from the end of the finger to the most distal...'
            >>> sorted(term.definition.xrefs)
            [Xref('HPO:probinson'), Xref('PMID:19125433')]

        """
        return self._data().definition

    @definition.setter  # type: ignore
    @typechecked(property=True)
    def definition(self, definition: Optional[Definition]):
        self._data().definition = definition

    @property
    def disjoint_from(self) -> _S:
        """`EntitySet`: The entities declared as disjoint from this entity.

        Two entities are disjoint if they have no instances in common. Two
        entities that are disjoint cannot share any subentities, but the
        opposite is not always true.
        """
        s = self._Set()
        s._ids = self._data().disjoint_from
        s._ontology = self._ontology()
        return s

    @disjoint_from.setter
    def disjoint_from(self, disjoint: Iterable[_E]):
        if isinstance(disjoint, EntitySet):
            data = disjoint._ids
        else:
            data = {entity.id for entity in disjoint}
        self._data().disjoint_from = data

    @property
    def equivalent_to(self) -> _S:
        """`EntitySet`: The entities declared as equivalent to this entity."""
        s = self._Set()
        s._ids = self._data().equivalent_to
        s._ontology = self._ontology()
        return s

    @equivalent_to.setter
    def equivalent_to(self, entities: Iterable[_E]):
        if isinstance(entities, EntitySet):
            data = entities._ids
        else:
            data = {entity.id for entity in entities}
        self._data().equivalent_to = data

    @property
    def id(self) -> str:
        """`str`: The OBO identifier of the entity.

        Identifiers can be either prefixed (e.g. ``MS:1000031``), unprefixed
        (e.g. ``part_of``) or given as plain URLs. Identifiers cannot be
        edited.
        """
        return self.__id

    @property
    def name(self) -> Optional[str]:
        """`str` or `None`: The name of the entity.

        Names are formally equivalent to ``rdf:label`` in OWL2. The OBO format
        version 1.4 made names optional to improve OWL interoperability, as
        labels are optional in OWL.
        """
        return self._data().name

    @name.setter  # type: ignore
    @typechecked(property=True)
    def name(self, value: Optional[str]):
        self._data().name = value

    @property
    def namespace(self) -> Optional[str]:
        """`str` or `None`: The namespace this entity is defined in."""
        return self._data().namespace

    @namespace.setter  # type: ignore
    @typechecked(property=True)
    def namespace(self, ns: Optional[str]):
        self._data().namespace = ns

    @property
    def obsolete(self) -> bool:
        """`bool`: Whether or not the entity is obsolete.

        Hint:
            All OBO entities can be made obsolete through a boolean flag, and
            map to one or several replacements. When querying an obsolete
            entity, ``pronto`` will **not** attempt to perform any kind of
            replacement itself ::

                >>> ms = pronto.Ontology.from_obo_library("ms.obo")
                >>> term = ms["MS:1001414"]
                >>> term
                Term('MS:1001414', name='MGF scans')
                >>> term.obsolete
                True

            To always get the up-to-date, non-obsolete entity, you could use
            the following snippet, going through a term replacement if there
            is no ambiguity ::

                >>> while term.obsolete:
                ...     if len(term.replaced_by) != 1:
                ...         raise ValueError(f"no replacement for {term.id}")
                ...     term = term.replaced_by.pop()
                >>> term
                Term('MS:1000797', name='peak list scans')

        See Also:
            `~.Entity.consider` and `~Entity.replaced_by`, storing some
            replacement options for an obsolete entity.

        """
        return self._data().obsolete

    @obsolete.setter  # type: ignore
    @typechecked(property=True)
    def obsolete(self, value: bool):
        self._data().obsolete = value

    @property
    def relationships(self: _E) -> "Relationships[_E, _S]":
        from .attributes import Relationships

        return Relationships(self)

    @relationships.setter
    def relationships(self, rels: typing.Mapping["Relationship", Iterable[_E]]):
        self._data().relationships = {
            relation.id: set(entity.id for entity in entities)
            for relation, entities in rels.items()
        }

    @property
    def replaced_by(self) -> _S:
        """`EntitySet`: A set of of replacements for an obsolete term.

        An obsolete entity can provide one or more replacement that can
        safely be used to automatically reassign instances to non-obsolete
        classes.

        See Also:
            `~Entity.consider`, which provides a set of entities suitable
            for replacement but requiring expert curation.

        """
        s = self._Set()
        s._ids = self._data().replaced_by
        s._ontology = self._ontology()
        return s

    @replaced_by.setter
    def replaced_by(self, replacements: Iterable[_E]) -> None:
        if isinstance(replacements, EntitySet):
            data = replacements._ids
        else:
            data = set(entity.id for entity in replacements)
        self._data().replaced_by = data

    @property
    def subsets(self) -> FrozenSet[str]:
        """`frozenset` of `str`: The subsets containing this entity."""
        return frozenset(self._data().subsets)

    @subsets.setter  # type: ignore
    @typechecked(property=True)
    def subsets(self, subsets: FrozenSet[str]):
        declared = set(s.name for s in self._ontology().metadata.subsetdefs)
        for subset in subsets:
            if subset not in declared:
                raise ValueError(f"undeclared subset: {subset!r}")
        self._data().subsets = set(subsets)

    @property
    def synonyms(self) -> FrozenSet[Synonym]:
        """`frozenset` of `Synonym`: A set of synonyms for this entity."""
        ontology, termdata = self._ontology(), self._data()
        return frozenset(Synonym(ontology, s) for s in termdata.synonyms)

    @synonyms.setter  # type: ignore
    @typechecked(property=True)
    def synonyms(self, synonyms: Iterable[Synonym]):
        self._data().synonyms = {syn._data() for syn in synonyms}

    @property
    def union_of(self) -> _S:
        s = self._Set()
        s._ids = self._data().union_of
        s._ontology = self._ontology()
        return s

    @union_of.setter
    def union_of(self, union_of: Iterable[_E]) -> None:
        if isinstance(union_of, EntitySet):
            data = union_of._ids
        else:
            data = set()
            for entity in union_of:
                if not isinstance(entity, Entity):
                    ty = type(entity).__name__
                    raise TypeError(f"expected `Entity`, found {ty}")
                data.add(entity.id)
        if len(data) == 1:
            raise ValueError("'union_of' cannot have a cardinality of 1")
        self._data().union_of = data

    @property
    def xrefs(self) -> FrozenSet[Xref]:
        """`frozenset` of `Xref`: A set of database cross-references.

        Xrefs can be used to describe an analogous entity in another
        vocabulary, such as a database or a semantic knowledge base.
        """
        return frozenset(self._data().xrefs)

    @xrefs.setter  # type: ignore
    @typechecked(property=True)
    def xrefs(self, xrefs: FrozenSet[Xref]):
        self._data().xrefs = set(xrefs)

    # --- Convenience methods ------------------------------------------------

    def add_synonym(
        self,
        description: str,
        scope: Optional[str] = None,
        type: Optional[SynonymType] = None,
        xrefs: Optional[Iterable[Xref]] = None,
    ) -> Synonym:
        """Add a new synonym to the current entity.

        Arguments:
            description (`str`): The alternate definition of the entity, or a
                related human-readable synonym.
            scope (`str` or `None`): An optional synonym scope. Must be either
                **EXACT**, **RELATED**, **BROAD** or **NARROW** if given.
            type (`~pronto.SynonymType` or `None`): An optional synonym type.
                Must be declared in the header of the current ontology.
            xrefs (iterable of `Xref`, or `None`): A collections of database
                cross-references backing the origin of the synonym.

        Raises:
            ValueError: when given an invalid synonym type or scope.

        Returns:
            `~pronto.Synonym`: A new synonym for the terms. The synonym is
            already added to the `Entity.synonyms` collection.

        """
        # check the type is declared in the current ontology
        if type is None:
            type_id: Optional[str] = None
        else:
            try:
                type_id = self._ontology().get_synonym_type(type.id).id
            except KeyError as ke:
                raise ValueError(f"undeclared synonym type {type.id!r}") from ke

        data = SynonymData(description, scope, type_id, xrefs=xrefs)
        self._data().synonyms.add(data)
        return Synonym(self._ontology(), data)


class EntitySet(typing.Generic[_E], typing.MutableSet[_E]):
    """A specialized mutable set to store `Entity` instances."""

    # --- Magic methods ------------------------------------------------------

    def __init__(self, entities: Optional[Iterable[_E]] = None) -> None:
        self._ids: Set[str] = set()
        self._ontology: "Optional[Ontology]" = None

        for entity in entities if entities is not None else ():
            if __debug__ and not isinstance(entity, Entity):
                err_msg = "'entities' must be iterable of Entity, not {}"
                raise TypeError(err_msg.format(type(entity).__name__))
            if self._ontology is None:
                self._ontology = entity._ontology()
            if self._ontology is not entity._ontology():
                raise ValueError("entities do not originate from the same ontology")
            self._ids.add(entity.id)

    def __contains__(self, other: object):
        if isinstance(other, Entity):
            return other.id in self._ids
        return False

    def __iter__(self) -> Iterator[_E]:
        return map(lambda t: self._ontology[t], iter(self._ids))  # type: ignore

    def __len__(self):
        return len(self._ids)

    def __repr__(self):
        ontology = self._ontology
        elements = (repr(ontology[id_]) for id_ in self._ids)
        return f"{type(self).__name__}({{{', '.join(elements)}}})"

    def __iand__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            self._ids &= other._ids
        else:
            super().__iand__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __and__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            s = type(self)()
            s._ids = self._ids.__and__(other._ids)
            s._ontology = self._ontology if s._ids else None
        else:
            s = type(self)(super().__and__(other))
        return s

    def __ior__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if not isinstance(other, EntitySet):
            other = type(self)(other)
        self._ids |= other._ids
        self._ontology = self._ontology or other._ontology
        return self

    def __or__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            s = type(self)()
            s._ids = self._ids.__or__(other._ids)
            s._ontology = self._ontology or other._ontology
        else:
            s = type(self)(super().__or__(other))
        return s

    def __isub__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            self._ids -= other._ids
        else:
            super().__isub__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __sub__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            s = type(self)()
            s._ids = self._ids.__sub__(other._ids)
            s._ontology = self._ontology
        else:
            s = type(self)(super().__sub__(other))
        return s

    def __ixor__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            self._ids ^= other._ids
            self._ontology = self._ontology or other._ontology
        else:
            super().__ixor__(other)
        if not self._ids:
            self._ontology = None
        return self

    def __xor__(self, other: AbstractSet[_E]) -> "EntitySet[_E]":
        if isinstance(other, EntitySet):
            s = type(self)()
            s._ids = self._ids.__xor__(other._ids)
            s._ontology = self._ontology or other._ontology
        else:
            s = type(self)(super().__xor__(other))
        if not s._ids:
            s._ontology = None
        return s

    # --- Methods ------------------------------------------------------------

    def add(self, entity: _E) -> None:
        if self._ontology is None:
            self._ontology = entity._ontology()
        elif self._ontology is not entity._ontology():
            raise ValueError("cannot use `Entity` instances from different `Ontology`")
        self._ids.add(entity.id)

    def clear(self) -> None:
        self._ids.clear()
        self._ontology = None

    def discard(self, entity: _E) -> None:
        self._ids.discard(entity.id)

    def pop(self) -> _E:
        id_ = self._ids.pop()
        entity = self._ontology[id_]  # type: ignore
        if not self._ids:
            self._ontology = None
        return entity  # type: ignore

    def remove(self, entity: _E):
        if self._ontology is not None and self._ontology is not entity._ontology():
            raise ValueError("cannot use `Entity` instances from different `Ontology`")
        self._ids.remove(entity.id)

    # --- Attributes ---------------------------------------------------------

    @property
    def ids(self) -> FrozenSet[str]:
        return frozenset(map(operator.attrgetter("id"), iter(self)))

    @property
    def alternate_ids(self) -> FrozenSet[str]:
        return frozenset(id for entity in self for id in entity.alternate_ids)

    @property
    def names(self) -> FrozenSet[str]:
        return frozenset(map(operator.attrgetter("name"), iter(self)))
