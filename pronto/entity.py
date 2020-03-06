import datetime
import weakref
import typing
from typing import Any, Dict, Iterable, Optional, Set, FrozenSet

from .definition import Definition
from .synonym import Synonym, SynonymData, SynonymType
from .pv import PropertyValue
from .xref import Xref
from .utils.meta import roundrepr, typechecked
from .utils.impl import set

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class EntityData:

    id: str
    alternate_ids: Set[str]
    annotations: Set[PropertyValue]
    anonymous: bool
    builtin: bool
    comment: Optional[str]
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    definition: Optional[Definition]
    equivalent_to: Set[str]
    name: Optional[str]
    namespace: Optional[str]
    obsolete: bool
    subsets: Set[str]
    synonyms: Set[SynonymData]
    xrefs: Set[Xref]

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602


class Entity:
    """An entity in the ontology graph.

    With respects to the OBO semantics, an `Entity` is either a term or a
    relationship in the ontology graph. Any entity has a unique identifier as
    well as some common properties.
    """

    if __debug__ or typing.TYPE_CHECKING:

        __data: "weakref.ReferenceType[EntityData]"
        __slots__: Iterable[str] = ("__weakref__",)

        def __init__(self, ontology: "Ontology", data: "EntityData"):
            self.__data = weakref.ref(data)
            self.__id = data.id
            self.__ontology = ontology

        def _data(self) -> "EntityData":
            rdata = self.__data()
            if __debug__ and rdata is None:
                raise RuntimeError("internal data was deallocated")
            return rdata

    else:

        __slots__: Iterable[str] = ("__weakref__", "_data")

        def __init__(self, ontology: "Ontology", data: "EntityData"):
            self._data = weakref.ref(data)
            self.__ontology = ontology
            self.__id = data.id

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
    def alternate_ids(self) -> FrozenSet[str]:
        """`frozenset` of `str`: A set of alternate IDs for this entity.
        """
        return frozenset(self._data().alternate_ids)

    @alternate_ids.setter
    @typechecked(property=True)
    def alternate_ids(self, ids: FrozenSet[str]):
        self._data().alternate_ids = set(ids)

    @property
    def annotations(self) -> FrozenSet[PropertyValue]:
        """`frozenset` of `PropertyValue`: Annotations relevant to the entity.
        """
        return frozenset(self._data().annotations)

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

    @builtin.setter
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
    def created_by(self) -> Optional[str]:
        """`str` or `None`: the name of the creator of the entity, if any.

        This property gets translated to a ``dc:creator`` annotation in OWL2,
        which has very broad semantics. Some OBO ontologies may instead use
        other annotation properties such as the ones found in `Information
        Interchange Ontology <http://www.obofoundry.org/ontology/iao.html>`_,
        which can be accessed in the `annotations` attribute of the entity,
        if any.
        """
        return self._data().created_by

    @created_by.setter
    @typechecked(property=True)
    def created_by(self, value: Optional[str]):
        self._data().created_by = value

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        """`~datetime.datetime` or None: the date the entity was created.
        """
        return self._data().creation_date

    @creation_date.setter
    @typechecked(property=True)
    def creation_date(self, value: Optional[datetime.datetime]):
        self._data().creation_date = value

    @property
    def definition(self) -> Optional[Definition]:
        """`str` or None: the textual definition of the current entity.

        Definitions in OBO are intended to be human-readable text describing
        the entity, with some additional cross-references if possible.
        """
        return self._data().definition

    @definition.setter
    @typechecked(property=True)
    def definition(self, definition: Optional[Definition]):
        self._data().definition = definition

    @property
    def equivalent_to(self) -> FrozenSet[str]:
        return frozenset(self._data().equivalent_to)

    @equivalent_to.setter
    def equivalent_to(self, equivalent_to: FrozenSet[str]):
        self._data().equivalent_to = set(equivalent_to)

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

    @name.setter
    @typechecked(property=True)
    def name(self, value: Optional[str]):
        self._data().name = value

    @property
    def namespace(self) -> Optional[str]:
        """`str` or `None`: the namespace this entity is defined in.
        """
        return self._data().namespace

    @namespace.setter
    @typechecked(property=True)
    def namespace(self, ns: Optional[str]):
        self._data().namespace = ns

    @property
    def obsolete(self) -> bool:
        """`bool`: whether or not the entity is obsolete.
        """
        return self._data().obsolete

    @obsolete.setter
    @typechecked(property=True)
    def obsolete(self, value: bool):
        self._data().obsolete = value

    @property
    def subsets(self) -> FrozenSet[str]:
        """`frozenset` of `str`: the subsets containing this entity.
        """
        return frozenset(self._data().subsets)

    @subsets.setter
    @typechecked(property=True)
    def subsets(self, subsets: FrozenSet[str]):
        declared = set(s.name for s in self._ontology().metadata.subsetdefs)
        for subset in subsets:
            if subset not in declared:
                raise ValueError(f"undeclared subset: {subset!r}")
        self._data().subsets = set(subsets)

    @property
    def synonyms(self) -> FrozenSet[Synonym]:
        """`frozenset` of `Synonym`: a set of synonyms for this entity.
        """
        ontology, termdata = self._ontology(), self._data()
        return frozenset(Synonym(ontology, s) for s in termdata.synonyms)

    @synonyms.setter
    @typechecked(property=True)
    def synonyms(self, synonyms: FrozenSet[Synonym]):
        self._data().synonyms = set(synonyms)

    @property
    def xrefs(self) -> FrozenSet[Xref]:
        """`frozenset` of `Xref`: a set of database cross-references.

        Xrefs can be used to describe an analogous entity in another
        vocabulary, such as a database or a semantic knowledge base.
        """
        return frozenset(self._data().xrefs)

    @xrefs.setter
    @typechecked(property=True)
    def xrefs(self, xrefs: FrozenSet[Xref]):
        self._data().xrefs = set(xrefs)

    # --- Conveniene methods -------------------------------------------------

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
        type_id = type.id if type is not None else None
        data = SynonymData(description, scope, type_id, xrefs=xrefs)
        synonym = Synonym(self._ontology(), data)
        self._data().synonyms.add(data)
        return synonym
