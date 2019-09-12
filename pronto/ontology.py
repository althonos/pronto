import datetime
import typing
from typing import BinaryIO, Dict, Mapping, Optional, Union

import contexter
import fastobo
import requests

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
        self._default_session = session is None
        self.session = session or requests.Session()
        self.import_depth = import_depth
        self.timeout = timeout

        self._terms: Dict[str, _TermData] = {}
        self._relationships: Dict[str, _RelationshipData] = {}

        # Creating an ontology from scratch is supported
        if handle is None:
            self.path = self.handle = None
            return

        # Get the path and the handle from arguments
        with contexter.Contexter() as ctx:
            # Get the decompressed, binary stream
            if isinstance(handle, str):
                self.path: str = handle
                self.handle = ctx << get_handle(handle, self.session, timeout)
            elif hasattr(handle, 'read'):
                self.path: str = get_location(handle)
                self.handle = handle
            else:
                raise TypeError()  # TODO

            # Load the OBO AST using fastobo
            handle = decompress(self.handle)
            try:
                doc = fastobo.load(handle)
            except SyntaxError as s:
                location = self.path, s.lineno, s.offset, s.text
                raise SyntaxError(s.args[0], location) from None

        # Extract data from the syntax tree
        self.metadata = Metadata._from_ast(doc.header)
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
        self._terms[id] = termdata = _TermData(id)
        return Term(self, termdata)
