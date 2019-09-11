from __future__ import annotations

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






class Ontology(Mapping[str, Term]):
    """An ontology.
    """

    def __init__(
        self,
        handle: Union[BinaryIO, str],
        imports: bool=True,
        import_depth: int=-1,
        timeout: float=2,
        session: Optional[requests.Session]=None,
    ):
        self._terms: Dict[str, _TermData] = {}
        self._relationships: Dict[str, _RelationshipData] = {}
        # self._xrefs: Dict[str, _XrefData] = {}

        self._parsed_by = None
        self._session = session or requests.Session()

        # Creating an ontology from scratch is supported
        if handle is None:
            self.path = None
            return

        # with contexter.Contexter() as ctx:
        # Get the decompressed, binary stream
        if isinstance(handle, str):
            self.path: str = handle
            handle = get_handle(handle, self._session)
        elif hasattr(handle, 'read'):
            self.path: str = get_location(handle)
        else:
            raise TypeError()  # TODO

        # Load the OBO AST using fastobo
        handle = decompress(handle)
        doc = fastobo.load(handle)

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
            yield Term(self, termdata)

    def __getitem__(self, id):
        return Term(self, self._terms[id])

    # ------------------------------------------------------------------------

    def create_term(self, id: str) -> Term:
        """Create a new term with the given identifier.
        """
        self._terms[id] = termdata = _TermData(id)
        return Term(self, termdata)
