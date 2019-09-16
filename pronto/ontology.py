import datetime
import typing
import urllib.parse
from typing import BinaryIO, Dict, Mapping, Optional, Union

import contexter
import fastobo
import requests

from . import relationship
from .term import Term, _TermData
from .synonym import SynonymType
from .relationship import Relationship, _RelationshipData
from .metadata import Metadata
from .utils.io import decompress, get_handle, get_location
from .utils.repr import make_repr


class Ontology(Mapping[str, Term]):
    """An ontology.
    """

    def __init__(
        self,
        handle: Union[BinaryIO, str, None] = None,
        import_depth: int = -1,
        timeout: int = 2,
        session: Optional[requests.Session] = None,
    ):
        with contexter.Contexter() as ctx:
            self._default_session = session is None
            self.session = session or (ctx << requests.Session())
            self.import_depth = import_depth
            self.timeout = timeout
            self.imports = set()

            self._terms: Dict[str, _TermData] = {}
            self._relationships: Dict[str, _RelationshipData] = {}

            # Creating an ontology from scratch is supported
            if handle is None:
                self.path = self.handle = None
                return

            # Get the path and the handle from arguments
            if isinstance(handle, str):
                self.path: str = handle
                self.handle = ctx << get_handle(handle, self.session, timeout)
                handle = ctx << decompress(self.handle)
            elif hasattr(handle, 'read'):
                self.path: str = get_location(handle)
                self.handle = handle
                handle = decompress(self.handle)
            else:
                raise TypeError()  # TODO

            # Load the OBO AST using fastobo
            try:
                doc = fastobo.load(handle)
            except SyntaxError as s:
                location = self.path, s.lineno, s.offset, s.text
                raise SyntaxError(s.args[0], location) from None

        # Extract data from the syntax tree
        self.metadata = Metadata._from_ast(doc.header)
        if import_depth:
            for url in self.metadata.imports:
                p = urllib.parse.urlparse(url)
                if p.scheme not in {"ftp", "http", "https"}:
                    url = f"http://purl.obolibrary.org/obo/{url}.obo"
                    self.imports.add(Ontology(url), import_depth-1, timeout, session)

        for frame in doc:
            if isinstance(frame, fastobo.term.TermFrame):
                Term._from_ast(frame, self)
            elif isinstance(frame, fastobo.typedef.TypedefFrame):
                Relationship._from_ast(frame, self)

    def __len__(self):
        return len(self._terms)

    def __iter__(self):
        for termdata in self._terms.values():
            yield termdata.id

    def __getitem__(self, id):
        return Term(self, self._terms[id])

    def __repr__(self):
        args = (self.path,) if self.path is not None else ()
        kwargs = {
            "session": (self.session, self._default_session and self.session),
            "import_depth": (self.import_depth, -1),
            "timeout": (self.timeout, 2),
        }
        return make_repr("Ontology", *args, **kwargs)

    # ------------------------------------------------------------------------

    def create_term(self, id: str) -> Term:
        """Create a new term with the given identifier.
        """
        if id in self._terms or id in self._relationships:
            raise ValueError(f"identifier already in use: {id}")
        self._terms[id] = termdata = _TermData(id)
        return Term(self, termdata)

    def create_relationship(self, id: str) -> Relationship:
        if id in self._terms or id in self._relationships:
            raise ValueError(f"identifier already in use: {id}")
        self._relationships[id] = reldata = _RelationshipData(id)
        return Relationship(self, reldata)

    def get_term(self, id: str) -> Term:
        return Term(self, self._terms[id])

    def get_relationship(self, id: str) -> Relationship:
        if id in relationship._BUILTINS:
            return Relationship(self, relationship._BUILTINS[id])
        return Relationship(self, self._relationships[id])
