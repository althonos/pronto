"""
pronto.parser.obo
=================

This module defines the Obo parsing method.
"""

import collections
import six

from .              import Parser
from .utils         import OboSection
from ..relationship import Relationship
from ..term         import Term


class OboParser(Parser):

    def __init__(self):
        """Initializes the parser.
        """
        #if type(self).__name__ not in self._instances:
        #    self._instances[type(self).__name__] = self
        super(OboParser, self).__init__()

        self.terms       = {}
        self.meta        = collections.defaultdict(list)
        self._rawterms   = []
        self._rawtypedef = []
        self._section    = OboSection.meta

        self.extensions = (".obo", ".obo.gz")

    def hook(self, **kwargs):
        """Returns True if this parser should be used.

        The current behaviour relies on filenames and file extension
        (.obo), but this is subject to change.
        """
        if 'force' in kwargs and kwargs['force']:
            return True
        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extensions)


    def parse(self, stream):
        """Parse the stream provided.

        Parameters:
            stream (file handle): a binary stream of the file to parse

        Returns:
            dict: a dictionary containing the metadata headers
            dict: a dictionnary containing the terms
            set:  a set containing the imports

        """

        self.__init__() # resets values to empty lists

        for streamline in stream:

            # manage encoding && cleaning of line
            streamline = streamline.strip().decode('utf-8')
            if not streamline: continue

            self._check_section(streamline)
            if self._section is OboSection.meta:
                self._parse_metadata(streamline)
            elif self._section is OboSection.typedef:
                self._parse_typedef(streamline)
            elif self._section is OboSection.term:
                self._parse_term(streamline)

        self._classify()

        return dict(self.meta), self.terms, set(self.meta['import'])

    def _check_section(self, line):
        """Updates the section currently parsed

        The parser starts in the OboSection.meta section but once
        it reaches the first [Typedef], it will enter the OboSection.typedef
        section, and/or when it reaches the first [Term], it will enter
        the OboSection.term section.
        """
        if line=="[Term]":
            self._section = OboSection.term
        if line=="[Typedef]":
            self._section = OboSection.typedef

    def _parse_metadata(self, line, parse_remarks=True):
        """Parse a metadata line

        The metadata is organized as a "key: value" statement which
        is split into the proper key and the proper value.

        Parameters:
            line (str): the line containing the metadata
            parse_remarks(bool): if the remarks should be parsed as well
                (read the note) [default: True]

        Note:
            If the line follows the following schema: "remark: key: value",
            the function will attempt to extract the proper key/value
            instead of leaving everything inside the remark key.

            This may cause issues when the line is identified as such even
            though the remark is simply a sentence containing a colon, such as
            "remark: 090506 "Attribute" in Term deleted and new entries: Scan Type [...]"
            (found in imagingMS.obo). To prevent the splitting from happening,
            the text on the left of the colon must be less that *20 chars long*.
        """

        key, value = (x.strip() for x in line.split(':', 1))

        if parse_remarks and key=="remark":
            if 0<value.find(': ')<20:                       # Checking that the ':' is not
                try:                                        # not too far avoid parsing a sentence
                    self._parse_metadata(value.strip())     # containing a ':' as a key: value
                    return                                  # obo statement nested in a remark
                except ValueError: pass                     # (20 is arbitrary, it may require tweaking)
        self.meta[key].append(value)

    def _parse_typedef(self, line):
        """Parse a typedef line

        The typedef is organized as a succesion of key:value pairs
        that are extracted into the same dictionnary until a new
        "[Typedef]" header is encountered

        Parameters:
            line (str): the line containing a typedef statement
        """
        if line.strip()=="[Typedef]":
            self._rawtypedef.append(collections.defaultdict(list))
        else:
            key, value = (x.strip() for x in line.split(':', 1))
            self._rawtypedef[-1][key].append(value)

    def _parse_term(self, line):
        """Parse a term line

        The term is organized as a succesion of key:value pairs
        that are extracted into the same dictionnary until a new
        "[Term]" header is encountered

        Parameters:
            line (str): the line containing a term statement
        """
        if line.strip()=="[Term]":
            self._rawterms.append(collections.defaultdict(list))
        else:
            key, value = (x.strip() for x in line.split(':', 1))
            self._rawterms[-1][key].append(value)

    def _classify(self):
        """Create proper objects out of the extracted dictionnaries

        New Relationship objects are instantiated with the help of
        the :obj:`Relationship._from_obo_dict` alternate constructor.

        New Term objects are instantiated by manually extracting id,
        name, desc and relationships out of the raw _term dictionnary,
        and then calling the default constructor.
        """

        for _typedef in self._rawtypedef:
            Relationship._from_obo_dict( # instantiate a new Relationship
                {k:v for k,lv in six.iteritems(_typedef) for v in lv}
            )

        for _term in self._rawterms:
            _id   = _term['id'][0]

            try: _name = _term['name'][0]
            except IndexError: _name = ''
            finally: del _term['name']

            try: _desc = _term['def'][0]
            except IndexError: _desc = ''
            finally: del _term['def']

            _relations = collections.defaultdict(list)
            try:
                for other in _term['is_a']:
                    _relations[Relationship('is_a')].append(other.split('!')[0].strip())
            except IndexError: pass
            finally: del _term['is_a']

            try:
                for relname, other in ( x.split(' ', 1) for x in _term['relationship'] ):
                    _relations[Relationship(relname)].append(other.split('!')[0].strip())
            except IndexError: pass
            finally: del _term['relationship']

            self.terms[_id] = Term(_id, _name, _desc, dict(_relations), dict(_term))

OboParser()
