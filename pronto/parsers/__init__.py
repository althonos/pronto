import abc
import os
import typing
import urllib.parse

import fastobo

from ..metadata import Metadata
from ..term import Term
from ..relationship import Relationship


class BaseParser(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def parse_into(cls, handle: typing.BinaryIO, ont: 'Ontology'):
        return NotImplemented

    @classmethod
    @abc.abstractmethod
    def can_parse(cls, path: str, buffer: bytes):
        return NotImplemented


class OboParser(BaseParser):

    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b'format-version:')

    @classmethod
    def parse_into(cls, handle, ont):
        # Load the OBO document through an iterator using fastobo
        doc = fastobo.iter(handle)

        # Extract metadata from the syntax tree
        ont.metadata = Metadata._from_ast(doc.header())

        # Import dependencies obtained from the header
        if ont.import_depth != 0:
            for ref in ont.metadata.imports:
                s = urllib.parse.urlparse(ref).scheme
                if s in {"ftp", "http", "https"} or os.path.exists(ref):
                    url = ref
                elif os.path.exists(f"{ref}.obo"):
                    url = f"{ref}.obo"
                elif os.path.exists(f"{url}.json"):
                    url = f"{ref}.json"
                else:
                    url = f"http://purl.obolibrary.org/obo/{ref}.obo"
                ont.imports[ref] = type(ont)(
                    url,
                    ont.import_depth-1,
                    ont.timeout,
                    ont.session
                )

        # Extract frames from the current document.
        try:
            for frame in doc:
                if isinstance(frame, fastobo.term.TermFrame):
                    Term._from_ast(frame, ont)
                elif isinstance(frame, fastobo.typedef.TypedefFrame):
                    Relationship._from_ast(frame, ont)
        except SyntaxError as s:
            location = ont.path, s.lineno, s.offset, s.text
            raise SyntaxError(s.args[0], location) from None


class OboJsonParser(BaseParser):

    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith(b'{')

    @classmethod
    def parse_into(cls, handle, ont):
        # Load the OBO document through an iterator using fastobo
        doc = fastobo.load_graph(handle)

        # Extract metadata from the syntax tree
        ont.metadata = Metadata._from_ast(doc.header)

        # Import dependencies obtained from the header
        if ont.import_depth != 0:
            for ref in ont.metadata.imports:
                s = urllib.parse.urlparse(ref).scheme
                if s in {"ftp", "http", "https"} or os.path.exists(ref):
                    url = ref
                elif os.path.exists(f"{ref}.obo"):
                    url = f"{ref}.obo"
                elif os.path.exists(f"{url}.json"):
                    url = f"{ref}.json"
                else:
                    url = f"http://purl.obolibrary.org/obo/{ref}.obo"
                ont.imports[ref] = type(ont)(
                    url,
                    ont.import_depth-1,
                    ont.timeout,
                    ont.session
                )

        # Extract frames from the current document.
        try:
            for frame in doc:
                if isinstance(frame, fastobo.term.TermFrame):
                    Term._from_ast(frame, ont)
                elif isinstance(frame, fastobo.typedef.TypedefFrame):
                    Relationship._from_ast(frame, ont)
        except SyntaxError as s:
            location = ont.path, s.lineno, s.offset, s.text
            raise SyntaxError(s.args[0], location) from None
