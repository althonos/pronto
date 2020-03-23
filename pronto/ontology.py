import contextlib
import itertools
import io
import typing
from typing import BinaryIO, Dict, Mapping, Optional, Set, Union

from . import relationship
from .term import Term, TermData
from .relationship import Relationship, RelationshipData
from .logic.lineage import Lineage
from .metadata import Metadata
from .utils.io import decompress, get_handle, get_location
from .utils.iter import SizedIterator
from .utils.meta import roundrepr, typechecked


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
    _inheritance: Dict[str, Lineage]
    _terms: Dict[str, TermData]
    _relationships: Dict[str, RelationshipData]

    # --- Constructors -------------------------------------------------------

    @classmethod
    def from_obo_library(
        cls, slug: str, import_depth: int = -1, timeout: int = 5
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

        Example:
            >>> ms = pronto.Ontology.from_obo_library("apo.obo")
            >>> ms.metadata.ontology
            'apo'
            >>> ms.path
            'http://purl.obolibrary.org/obo/apo.obo'

        """
        return cls(f"http://purl.obolibrary.org/obo/{slug}", import_depth, timeout)

    def __init__(
        self,
        handle: Union[BinaryIO, str, None] = None,
        import_depth: int = -1,
        timeout: int = 5,
    ):
        """Create a new `Ontology` instance.

        Arguments:
            handle (str, ~typing.BinaryIO, or None): Either the path to a file
                or a binary file handle that contains a serialized version of
                the ontology. If `None` is given, an empty `Ontology` is
                returned and can be populated manually.
            import_depth (int): The maximum depth of imports to resolve in the
                ontology tree. *Note that the library may not behave correctly
                when not importing the complete dependency tree, so you should
                probably use the default value and import everything*.
            timeout (int): The timeout in seconds to use when performing
                network I/O, for instance when connecting to the OBO library
                to download imports.
            cache (bool): Enable caching of subclassing relationships to make
                `Term.subclasses` much faster, at the cost of a slightly
                longer parsing step (about 5% of the total time).

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

            self._inheritance = dict()
            self._terms: Dict[str, TermData] = {}
            self._relationships: Dict[str, RelationshipData] = {}

            # Creating an ontology from scratch is supported
            if handle is None:
                self.metadata = Metadata()
                self.path = self.handle = None
                return

            # Get the path and the handle from arguments
            if isinstance(handle, str):
                self.path = handle
                self.handle = ctx.enter_context(get_handle(handle, timeout))
                _handle = ctx.enter_context(decompress(self.handle))
            elif hasattr(handle, "read"):
                self.path = get_location(handle)
                self.handle = handle
                _handle = decompress(self.handle)
            else:
                raise TypeError(f"could not parse ontology from {handle!r}")

            # Parse the ontology using the appropriate parser
            buffer = _handle.peek(io.DEFAULT_BUFFER_SIZE)
            for cls in BaseParser.__subclasses__():
                if cls.can_parse(typing.cast(str, self.path), buffer):
                    cls(self).parse_from(_handle)
                    break
            else:
                raise ValueError(f"could not find a parser to parse {handle!r}")

            # Populate the subclassing cache
            self._build_inheritance_cache()

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
            >>> len(ms.relationships())
            28

        """
        return (
            len(self._terms)
            + len(self._relationships)
            + sum(map(len, self.imports.values()))
        )

    def __iter__(self) -> SizedIterator[str]:
        """Yield the identifiers of all the entities part of the ontology.
        """
        terms, relationships = self.terms(), self.relationships()
        return SizedIterator(
            (entity.id for entity in itertools.chain(terms, relationships)),
            length=len(terms) + len(relationships),
        )

    def __contains__(self, item: object) -> bool:
        if isinstance(item, str):
            return (
                any(item in i for i in self.imports.values())
                or item in self._terms
                or item in self._relationships
                or item in relationship._BUILTINS
            )
        return False

    def __getitem__(self, id: str) -> Union[Term, Relationship]:
        """Get any entity in the ontology graph with the given identifier.
        """
        try:
            return self.get_relationship(id)
        except KeyError:
            pass
        try:
            return self.get_term(id)
        except KeyError:
            pass
        raise KeyError(id)

    def __repr__(self):
        """Return a textual representation of `self` that should roundtrip.
        """
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

    # --- Private helpers ----------------------------------------------------

    def _build_inheritance_cache(self) -> None:
        self._inheritance.clear()
        for t1 in self.terms():
            for t2 in t1._data().relationships.get("is_a", []):
                self._inheritance.setdefault(t2, Lineage()).sub.add(t1.id)
                self._inheritance.setdefault(t1.id, Lineage()).sup.add(t2)

    # --- Serialization utils ------------------------------------------------

    def dump(self, file: BinaryIO, format: str = "obo"):
        f"""Serialize the ontology to a given file-handle.

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
                cls(self).dump(file)
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

    def terms(self) -> SizedIterator[Term]:
        """Iterate over the terms of the ontology graph.
        """
        return SizedIterator(
            itertools.chain(
                (
                    Term(self, t._data())
                    for ref in self.imports.values()
                    for t in ref.terms()
                ),
                (Term(self, t) for t in self._terms.values()),
            ),
            length=(
                sum(len(r.terms()) for r in self.imports.values()) + len(self._terms)
            ),
        )

    def relationships(self) -> SizedIterator[Relationship]:
        """Iterate over the relationships of the ontology graph.

        Builtin relationships (``is_a``) are not part of the yielded entities,
        yet they can still be accessed with the `Ontology.get_relationship`
        method.
        """
        return SizedIterator(
            itertools.chain(
                (
                    Relationship(self, r._data())
                    for ref in self.imports.values()
                    for r in ref.relationships()
                ),
                (self.get_relationship(r) for r in self._relationships),
            ),
            length=(
                sum(len(r.relationships()) for r in self.imports.values())
                + len(self._relationships)
            ),
        )

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
        self._terms[id] = termdata = TermData(id)
        self._inheritance[id] = Lineage()
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
        self._relationships[id] = reldata = RelationshipData(id)
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
        try:
            return Relationship(self, self._relationships[id])
        except KeyError:
            pass
        try:
            return Relationship(self, relationship._BUILTINS[id])
        except KeyError:
            pass
        for dep in self.imports.values():
            try:
                return Relationship(self, dep.get_relationship(id)._data())
            except KeyError:
                pass
        raise KeyError(id)
