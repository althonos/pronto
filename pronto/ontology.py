import contextlib
import io
import itertools
import typing
import warnings
from os import PathLike, fspath
from typing import (
    BinaryIO,
    Container,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
    Sized,
    Union,
)

from . import relationship
from .entity import Entity, EntityData
from .logic.lineage import Lineage
from .metadata import Metadata
from .relationship import Relationship, RelationshipData
from .synonym import SynonymType
from .term import Term, TermData
from .utils.io import decompress, get_handle, get_location
from .utils.iter import SizedIterator
from .utils.meta import roundrepr, typechecked

__all__ = ["Ontology"]
_D = typing.TypeVar("_D", bound=EntityData)


class _DataGraph(typing.Generic[_D], typing.Mapping[str, _D]):
    """A private data storage for a type of entity.

    This class is equivalent to a graph storing nodes in the ``entities``
    attribute, and directed edges corresponding to the sub-entity
    relationship between entities in the ``lineage`` attribute.
    """

    entities: MutableMapping[str, _D]
    lineage: MutableMapping[str, Lineage]

    def __init__(self, entities=None, lineage=None):
        self.entities = entities or {}
        self.lineage = lineage or {}

    def __contains__(self, key: object) -> bool:
        return key in self.entities

    def __len__(self) -> int:
        return len(self.entities)

    def __iter__(self):
        return iter(self.entities)

    def __getitem__(self, key: str) -> _D:
        return self.entities[key]


class _OntologyTerms(Sized, Container, Iterable[Term]):
    """A convenience wrapper over the terms of an ontology."""

    def __init__(self, ontology: "Ontology") -> None:
        self.__ontology = ontology

    def __len__(self) -> int:
        return sum(len(ref.terms()) for ref in self.__ontology.imports.values()) + len(
            self.__ontology._terms.entities
        )

    def __iter__(self) -> Iterator[Term]:
        return itertools.chain(
            (
                Term(self.__ontology, t._data())
                for ref in self.__ontology.imports.values()
                for t in ref.terms()
            ),
            (
                Term(self.__ontology, tdata)
                for tdata in self.__ontology._terms.entities.values()
            ),
        )

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return (
                any(item in ref for ref in self.__ontology.imports.values())
                or item in self.__ontology._terms
            )
        return False


class _OntologyRelationships(Sized, Container, Iterable[Relationship]):
    """A convenience wrapper over the relationships of an ontology."""

    def __init__(self, ontology: "Ontology"):
        self.__ontology = ontology

    def __len__(self) -> int:
        return sum(
            len(ref.relationships()) for ref in self.__ontology.imports.values()
        ) + len(self.__ontology._relationships.entities)

    def __iter__(self) -> Iterator[Relationship]:
        return itertools.chain(
            (
                Relationship(self.__ontology, r._data())
                for ref in self.__ontology.imports.values()
                for r in ref.relationships()
            ),
            (
                Relationship(self.__ontology, rdata)
                for rdata in self.__ontology._relationships.entities.values()
            ),
        )

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return (
                any(item in ref for ref in self.__ontology.imports.values())
                or item in self.__ontology._relationships
            )
        return False


class Ontology(Mapping[str, Union[Term, Relationship]]):
    """An ontology storing terms and the relationships between them.

    Ontologies can be loaded with ``pronto`` if they are serialized in any of
    the following ontology languages and formats at the moment:

    - `Ontology Web Language 2 <https://www.w3.org/TR/owl2-overview/>`_
      in `RDF/XML format
      <https://www.w3.org/TR/2012/REC-owl2-mapping-to-rdf-20121211/>`_.
    - `Open Biomedical Ontologies 1.4
      <http://owlcollab.github.io/oboformat/doc/obo-syntax.html>`_.
    - `OBO graphs <https://github.com/geneontology/obographs>`_ in
      `JSON <http://json.org/>`_ format.

    Attributes:
        metadata (Metadata): A data structure storing the metadata about the
            current ontology, either extracted from the ``owl:Ontology`` XML
            element or from the header of the OBO file.
        timeout (int): The timeout in seconds to use when performing network
            I/O, for instance when connecting to the OBO library to download
            imports. This is kept for reference, as it is not used after the
            initialization of the ontology.
        imports (~typing.Dict[str, Ontology]): A dictionary mapping references
            found in the import section of the metadata to resolved `Ontology`
            instances.

    """

    # Public attributes
    import_depth: int
    timeout: int
    imports: Dict[str, "Ontology"]
    path: Optional[str]
    handle: Optional[BinaryIO]

    # Private attributes
    _terms: _DataGraph[TermData]
    _relationships: _DataGraph[RelationshipData]

    # --- Constructors -------------------------------------------------------

    @classmethod
    def from_obo_library(
        cls,
        slug: str,
        import_depth: int = -1,
        timeout: int = 5,
        threads: Optional[int] = None,
    ) -> "Ontology":
        """Create an `Ontology` from a file in the OBO Library.

        This is basically just a shortcut constructor to avoid typing the full
        OBO Library URL each time.

        Arguments:
            slug (str): The filename of the ontology release to download from
                the OBO Library, including the file extension (should be one
                of ``.obo``, ``.owl`` or ``.json``).
            import_depth (int): The maximum depth of imports to resolve in the
                ontology tree. *Note that the library may not behave correctly
                when not importing the complete dependency tree, so you should
                probably use the default value and import everything*.
            timeout (int): The timeout in seconds to use when performing
                network I/O, for instance when connecting to the OBO library
                to download imports.
            threads (int): The number of threads to use when parsing, for
                parsers that support multithreading. Give `None` to autodetect
                the number of CPUs on the host machine.

        Example:
            >>> apo = pronto.Ontology.from_obo_library("apo.obo")
            >>> apo.metadata.ontology
            'apo'
            >>> apo.path
            'http://purl.obolibrary.org/obo/apo.obo'

        """
        return cls(
            f"http://purl.obolibrary.org/obo/{slug}", import_depth, timeout, threads
        )

    def __init__(
        self,
        handle: Union[BinaryIO, str, PathLike, None] = None,
        import_depth: int = -1,
        timeout: int = 5,
        threads: Optional[int] = None,
    ):
        """Create a new `Ontology` instance.

        Arguments:
            handle (str, ~typing.BinaryIO, ~os.PathLike, or None): Either the
                path to a file or a binary file handle that contains a
                serialized version of the ontology. If `None` is given, an
                empty `Ontology` is returned and can be populated manually.
            import_depth (int): The maximum depth of imports to resolve in the
                ontology tree. *Note that the library may not behave correctly
                when not importing the complete dependency tree, so you should
                probably use the default value and import everything*.
            timeout (int): The timeout in seconds to use when performing
                network I/O, for instance when connecting to the OBO library
                to download imports.
            threads (int): The number of threads to use when parsing, for
                parsers that support multithreading. Give `None` to autodetect
                the number of CPUs on the host machine.

        Raises:
            TypeError: When the given ``handle`` could not be used to parse
                and ontology.
            ValueError: When the given ``handle`` contains a serialized
                ontology not supported by any of the builtin parsers.

        """
        from .parsers import BaseParser

        with contextlib.ExitStack() as ctx:
            self.import_depth = import_depth
            self.timeout = timeout
            self.imports = dict()

            # self._inheritance = dict()
            # self._terms: Dict[str, TermData] = {}
            # self._relationships: Dict[str, RelationshipData] = {}
            self._terms = _DataGraph(entities={}, lineage={})
            self._relationships = _DataGraph(entities={}, lineage={})

            # Creating an ontology from scratch is supported
            if handle is None:
                self.metadata = Metadata()
                self.path = self.handle = None
                return

            # Get the path and the handle from arguments
            if isinstance(handle, (str, PathLike)):
                self.path = handle = fspath(handle)
                self.handle = ctx.enter_context(get_handle(handle, timeout))
                _handle = ctx.enter_context(decompress(self.handle))
                _detach = False
            elif hasattr(handle, "read"):
                self.path = get_location(handle)
                self.handle = handle
                _handle = decompress(self.handle)
                _detach = True
            else:
                raise TypeError(f"could not parse ontology from {handle!r}")

            # check value of `threads`
            if threads is not None and not threads > 0:
                raise ValueError("`threads` must be None or strictly positive")

            # Parse the ontology using the appropriate parser
            buffer = _handle.peek(io.DEFAULT_BUFFER_SIZE)
            for cls in BaseParser.__subclasses__():
                if cls.can_parse(typing.cast(str, self.path), buffer):
                    cls(self).parse_from(_handle)  # type: ignore
                    break
            else:
                raise ValueError(f"could not find a parser to parse {handle!r}")

            if _detach:
                _handle.detach()

    # --- Magic Methods ------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of entities in the ontology.

        This method takes into accounts the terms and the relationships defined
        in the current ontology as well as all of its imports. To only count
        terms or relationships, use `len` on the iterator returned by the
        dedicated methods (e.g. ``len(ontology.terms())``).

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> len(ms)
            6023
            >>> len(ms.terms())
            5995

        """
        return (
            len(self._terms.entities)
            + len(self._relationships.entities)
            + sum(map(len, self.imports.values()))
        )

    def __iter__(self) -> SizedIterator[str]:
        """Yield the identifiers of all the entities part of the ontology."""
        terms, relationships = self.terms(), self.relationships()
        entities: typing.Iterable[Entity] = itertools.chain(terms, relationships)
        return SizedIterator(
            (entity.id for entity in entities),
            length=len(terms) + len(relationships),
        )

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            # TODO: remove in v3.0.0
            if item in self._relationships or item in relationship._BUILTINS:
                warnings.warn(
                    "checking if an ontology contains a relationship with "
                    "`<id> in Ontology` will not be supported in future "
                    "versions, use `<id> in Ontology.relationships()`.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                return True
            return any(item in i for i in self.imports.values()) or item in self._terms
        return False

    def __getitem__(self, id: str) -> Union[Term, Relationship]:
        """Get any entity in the ontology graph with the given identifier."""
        # TODO: remove block in v3.0.0
        try:
            entity = self.get_relationship(id)
        except KeyError:
            pass
        else:
            warnings.warn(
                "indexing an ontology to retrieve a relationship will not be "
                "supported in future versions, use `Ontology.get_relationship` "
                "directly.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return entity

        try:
            return self.get_term(id)
        except KeyError:
            pass

        raise KeyError(id)

    def __repr__(self):
        """Return a textual representation of `self` that should roundtrip."""
        if self.path is not None:
            args = (self.path,)
        elif self.handle is not None:
            args = (self.handle,)
        else:
            args = ()
        kwargs = {"timeout": (self.timeout, 5)}
        if self.import_depth > 0:
            kwargs["import_depth"] = (self.import_depth, -1)
        return roundrepr.make("Ontology", *args, **kwargs)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["handle"] = None
        return state

    def __setstate__(self, state):
        self.__dict__ = state

    # --- Serialization utils ------------------------------------------------

    def dump(self, file: BinaryIO, format: str = "obo"):
        """Serialize the ontology to a given file-handle.

        Arguments:
            file (~typing.BinaryIO): A binary file handle open in reading mode
                to write the serialized ontology into.
            format (str): The serialization format to use. Currently supported
                formats are: **obo**, **json**.

        Example:
            >>> ms = pronto.Ontology.from_obo_library("ms.obo")
            >>> with open("ms.json", "wb") as f:
            ...     ms.dump(f, format="json")

        """
        from .serializers import BaseSerializer

        for cls in BaseSerializer.__subclasses__():
            if cls.format == format:
                cls(self).dump(file)  # type: ignore
                break
        else:
            raise ValueError(f"could not find a serializer to handle {format!r}")

    def dumps(self, format: str = "obo") -> str:
        """Get a textual representation of the serialization ontology.

        Example:
            >>> go = pronto.Ontology("go.obo")
            >>> print(go.dumps())
            format-version: 1.2
            data-version: releases/2019-07-01
            ...

        """
        s = io.BytesIO()
        self.dump(s, format=format)
        return s.getvalue().decode("utf-8")

    # --- Data accessors -----------------------------------------------------

    def synonym_types(self) -> SizedIterator[SynonymType]:
        """Iterate over the synonym types of the ontology graph."""
        sources = [i.synonym_types() for i in self.imports.values()]
        sources.append(self.metadata.synonymtypedefs)  # type: ignore
        length = sum(map(len, sources))
        return SizedIterator(itertools.chain.from_iterable(sources), length)

    def terms(self) -> _OntologyTerms:
        """Query the terms of an ontology.

        Example:
            >>> pato = pronto.Ontology.from_obo_library("pato.obo")
            >>> len(pato.terms())
            2661
            >>> "PATO:0000186" in pato.terms()
            True
            >>> for term in sorted(pato.terms()):
            ...     print(term)
            Term('PATO:0000000', name='obsolete pato')
            Term('PATO:0000001', name='quality')
            ...

        """
        return _OntologyTerms(self)

    def relationships(self) -> _OntologyRelationships:
        """Query the relationships of an ontology.

        Example:
            >>> pato = pronto.Ontology.from_obo_library("pato.obo")
            >>> len(pato.relationships())
            24
            >>> "reciprocal_of" in pato.relationships()
            True
            >>> for relationship in pato.relationships():
            ...     print(relationship)
            Relationship('correlates_with', ...)
            Relationship('decreased_in_magnitude_relative_to', ...)
            ...

        """
        return _OntologyRelationships(self)

    @typechecked()
    def create_term(self, id: str) -> Term:
        """Create a new term with the given identifier.

        Returns:
            `Term`: the newly created term view, which attributes can the be
            modified directly.

        Raises:
            ValueError: if the provided ``id`` already identifies an entity
                in the ontology graph, or if it is not a valid OBO identifier.

        """
        if id in self:
            raise ValueError(f"identifier already in use: {id} ({self[id]})")
        self._terms.entities[id] = termdata = TermData(id)
        self._terms.lineage[id] = Lineage()
        return Term(self, termdata)

    @typechecked()
    def create_relationship(self, id: str) -> Relationship:
        """Create a new relationship with the given identifier.

        Raises:
            ValueError: if the provided ``id`` already identifies an entity
                in the ontology graph.

        """
        if id in self:
            raise ValueError(f"identifier already in use: {id} ({self[id]})")
        self._relationships.entities[id] = reldata = RelationshipData(id)
        self._relationships.lineage[id] = Lineage()
        return Relationship(self, reldata)

    @typechecked()
    def get_term(self, id: str) -> Term:
        """Get a term in the ontology graph from the given identifier.

        Raises:
            KeyError: if the provided ``id`` cannot be found in the terms of
                the ontology graph.

        """
        try:
            return Term(self, self._terms[id])
        except KeyError:
            pass
        for dep in self.imports.values():
            try:
                return Term(self, dep.get_term(id)._data())
            except KeyError:
                pass
        raise KeyError(id)

    @typechecked()
    def get_relationship(self, id: str) -> Relationship:
        """Get a relationship in the ontology graph from the given identifier.

        Builtin ontologies (``is_a`` and ``has_subclass``) can be accessed
        with this method.

        Raises:
            KeyError: if the provided ``id`` cannot be found in the
                relationships of the ontology graph.

        """
        # TODO: remove block in v3.0.0
        if id in relationship._BUILTINS:
            warnings.warn(
                "using the `is_a` relationship not be supported in future versions, "
                "use `superclasses` and `subclasses` API of entities instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return Relationship(self, relationship._BUILTINS[id])

        try:
            return Relationship(self, self._relationships[id])
        except KeyError:
            pass

        for dep in self.imports.values():
            try:
                return Relationship(self, dep.get_relationship(id)._data())
            except KeyError:
                pass

        raise KeyError(id)

    @typechecked()
    def get_synonym_type(self, id: str) -> SynonymType:
        """Get a synonym type in the ontology graph from the given identifier.

        Raises:
            KeyError: if the provided ``id`` does not resolve to a synonym type
                declared in this `Ontology` or one of its imports.

        """
        ty = next((ty for ty in self.metadata.synonymtypedefs if ty.id == id), None)
        if ty is not None:
            return ty
        for dep in self.imports.values():
            try:
                return dep.get_synonym_type(id)
            except KeyError:
                pass
        raise KeyError(id)
