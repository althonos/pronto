# coding: utf-8
"""Definition of the Obo parser.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import string
import six

from .base import BaseParser
from .utils import OboSection
from ..description  import Description
from ..relationship import Relationship
from ..synonym import SynonymType, Synonym
from ..term import Term

_obo_synonyms_map = {'exact_synonym': 'EXACT', 'broad_synonym': 'BROAD',
                    'narrow_synonym': 'NARROW', 'synonym': 'RELATED'}

class OboParser(BaseParser):

    extensions = (".obo", ".obo.gz")

    @classmethod
    def hook(cls, force=False, path=None, lookup=None):
        """Test whether this parser should be used.

        The current behaviour relies on filenames, file extension
        and looking ahead a small buffer in the file object.

        """
        if force:
            return True
        elif path is not None and path.endswith(cls.extensions):
            return True
        elif lookup is not None and lookup.startswith(b'format-version:'):
            return True
        return False

    @classmethod
    def parse(cls, stream):  # noqa: D102

        _section    = OboSection.meta
        meta        = collections.defaultdict(list)
        typedefs    = []
        _rawterms   = []
        _rawtypedef = []

        _term_parser = cls._parse_term(_rawterms)
        next(_term_parser)

        for streamline in stream:

            # manage encoding && cleaning of line
            streamline = cls._strip_comment(streamline.decode('utf-8'))
            if streamline[:1] in string.whitespace:
                continue
            elif streamline[:1] == "[":
                _section = cls._check_section(streamline, _section)

            if _section is OboSection.meta:
                cls._parse_metadata(streamline, meta)
            elif _section is OboSection.typedef:
                cls._parse_typedef(streamline, _rawtypedef)
            elif _section is OboSection.term:
                _term_parser.send(streamline)
                #_rawterms = cls._parse_term(streamline, _rawterms)

        terms, typedefs = cls._classify(_rawtypedef, _rawterms)
        imports = set(meta['import']) if 'import' in meta else set()

        return dict(meta), terms, imports, typedefs

    @staticmethod
    def _strip_comment(line):
        in_quote = False
        for i, char in enumerate(line):
            if char == '"':
                in_quote = not in_quote
            elif not in_quote and char == '!':
                return line[:i]
        return line

    @staticmethod
    def _check_section(line, section):
        """Update the section being parsed.

        The parser starts in the `OboSection.meta` section but once
        it reaches the first ``[Typedef]``, it will enter the
        `OboSection.typedef` section, and/or when it reaches the first
        ``[Term]``, it will enter the `OboSection.term` section.

        """
        if "[Term]" in line:
            section = OboSection.term
        elif "[Typedef]" in line:
            section = OboSection.typedef
        return section

    @classmethod
    def _parse_metadata(cls, line, meta, parse_remarks=True):
        """Parse a metadata line.

        The metadata is organized as a ``key: value`` statement which
        is split into the proper key and the proper value.

        Arguments:
            line (str): the line containing the metadata
            parse_remarks(bool, optional): set to `False` to avoid
                parsing the remarks.

        Note:
            If the line follows the following schema:
            ``remark: key: value``, the function will attempt to extract
            the proper key/value instead of leaving everything inside
            the remark key.

            This may cause issues when the line is identified as such
            even though the remark is simply a sentence containing a
            colon,  such as ``remark: 090506 "Attribute"`` in Term
            deleted and new entries: Scan Type [...]"
            (found in imagingMS.obo). To prevent the splitting from
            happening, the text on the left of the colon must be less
            that *20 chars long*.

        """
        key, value = line.split(':', 1)
        key, value = key.strip(), value.strip()
        if parse_remarks and "remark" in key:                        # Checking that the ':' is not
            if 0<value.find(': ')<20:                                # not too far avoid parsing a sentence
                try:                                                 # containing a ':' as a key: value
                    cls._parse_metadata(value, meta, parse_remarks)  # obo statement nested in a remark
                except ValueError:                                   # (20 is arbitrary, it may require
                    pass                                             # tweaking)
        else:
            meta[key].append(value)
            try:
                syn_type_def = []
                for m in meta['synonymtypedef']:
                    if not isinstance(m, SynonymType):
                        x = SynonymType.from_obo(m)
                        syn_type_def.append(x)
                    else:
                        syn_type_def.append(m)
            except KeyError:
                pass
            else:
                meta['synonymtypedef'] = syn_type_def

    @staticmethod
    def _parse_typedef(line, _rawtypedef):
        """Parse a typedef line.

        The typedef is organized as a succesion of ``key:value`` pairs
        that are extracted into the same dictionnary until a new
        header is encountered

        Arguments:
            line (str): the line containing a typedef statement
        """
        if "[Typedef]" in line:
            _rawtypedef.append(collections.defaultdict(list))
        else:
            key, value = line.split(':', 1)
            _rawtypedef[-1][key.strip()].append(value.strip())
        #return _rawtypedef

    @staticmethod
    def _parse_term(_rawterms):
        """Parse a term line.

        The term is organized as a succesion of ``key:value`` pairs
        that are extracted into the same dictionnary until a new
        header is encountered

        Arguments:
            line (str): the line containing a term statement
        """
        line = yield
        _rawterms.append(collections.defaultdict(list))
        while True:
            line = yield
            if "[Term]" in line:
                _rawterms.append(collections.defaultdict(list))
            else:
                key, value = line.split(':', 1)
                _rawterms[-1][key.strip()].append(value.strip())
            #_rawterms

    @staticmethod
    def _classify(_rawtypedef, _rawterms):
        """Create proper objects out of extracted dictionnaries.

        New Relationship objects are instantiated with the help of
        the `Relationship._from_obo_dict` alternate constructor.

        New `Term` objects are instantiated by manually extracting id,
        name, desc and relationships out of the ``_rawterm``
        dictionnary, and then calling the default constructor.
        """
        terms = collections.OrderedDict()
        _cached_synonyms = {}

        typedefs = [
            Relationship._from_obo_dict( # instantiate a new Relationship
                {k:v for k,lv in six.iteritems(_typedef) for v in lv}
            )
            for _typedef in _rawtypedef
        ]

        for _term in _rawterms:
            synonyms = set()

            _id   = _term['id'][0]
            _name = _term.pop('name', ('',))[0]
            _desc = _term.pop('def', ('',))[0]

            _relations = collections.defaultdict(list)
            try:
                for other in _term.get('is_a', ()):
                    _relations[Relationship('is_a')].append(other.split('!')[0].strip())
            except IndexError:
                pass
            try:
                for relname, other in ( x.split(' ', 1) for x in _term.pop('relationship', ())):
                    _relations[Relationship(relname)].append(other.split('!')[0].strip())
            except IndexError:
                pass

            for key, scope in six.iteritems(_obo_synonyms_map):
                for obo_header in _term.pop(key, ()):
                    try:
                        s = _cached_synonyms[obo_header]
                    except KeyError:
                         s = Synonym.from_obo(obo_header, scope)
                         _cached_synonyms[obo_header] = s
                    finally:
                        synonyms.add(s)

            desc = Description.from_obo(_desc) if _desc else Description("")

            terms[_id] = Term(_id, _name, desc, dict(_relations), synonyms, dict(_term))
        return terms, typedefs


OboParser()
