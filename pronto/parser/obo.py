"""
pronto.parser.obo
=================

This module defines the Obo parsing method.
"""

import chardet
import collections
import six
import os

from .              import Parser
from .utils         import OboSection
from ..relationship import Relationship
from ..term         import Term


# class _OboMultiClassifier(multiprocessing.Process): # pragma: no cover

#     def __init__(self, queue, results, *args, **kwargs):

#         super(_OboClassifier, self).__init__()

#         self.queue = queue
#         self.results = results

#     def run(self):

#         while True:

#             term = self.queue.get()

#             if term is None:
#                 break

#             self.results.put(self._classify(term))

#         #return {tid: Term(tid, name, desc, relations, term)}

#     @staticmethod
#     def _classify(term):

#         relations = {}

#         if 'relationship' in term:
#             #Relationship.lock.acquire()
#             #try:
#             _OboClassifier._process_relationship(term)
#             #finally:
#             #    Relationship.lock.release()

#         #if 'is_a' in term:
#         try:
#             term[Relationship('is_a')] = [ term['is_a'].format() ]
#             del term['is_a']
#         except AttributeError:
#             term[Relationship('is_a')] = term['is_a']
#             del term['is_a']
#         except KeyError:
#             pass
#             #term[Relationship('is_a')] = term['is_a'] if isinstance(term['is_a'])
#             #del term['is_a']

#         for key in tuple(term.keys()):
#             if isinstance(key, Relationship):
#                 relations = _OboClassifier._extract_relationship(term, key, relations)

#         desc = _OboClassifier._extract_description(term)
#         tid, name = _OboClassifier._extract_name_and_id(term)

#         return (tid, name, desc, relations, term)

#     @staticmethod
#     def _process_relationship(term):

#         # If term is a str
#         try:

#             name, value = term['relationship'].split(' ', 1)

#             name = Relationship(name)

#             try:
#                 term[name].append(value)
#             except KeyError:
#                 term[name] = [value]

#         # If term is a list
#         except AttributeError:

#             for r in term['relationship']:
#                 name, value = r.split(' ', 1)

#                 name = Relationship(name)

#                 try:
#                     term[name].append(value)
#                 except KeyError:
#                     term[name] = [value]

#         del term['relationship']

#     @staticmethod
#     def _extract_relationship(term, rship, relations):

#         #if rship.obo_name in term.keys():
#         #if isinstance(term[rship], list):
#         try:
#             relations[rship.obo_name] = [ x.split(' !')[0] for x in term[rship] ]
#         except AttributeError:
#             relations[rship.obo_name] = [ term[rship].split(' !')[0]]



#         del term[rship]

#         return relations

#     @staticmethod
#     def _extract_description(term):
#         try:
#         #if 'def' in term.keys():
#             desc = term['def']
#             del term['def']
#             return desc
#         except KeyError:
#             return ''

#     @staticmethod
#     def _extract_name_and_id(term):
#         if 'id' not in term.keys():
#             return '', ''
#         if 'name' in term.keys():
#             tid, name = term['id'], term['name']
#             del term['name']
#             del term['id']
#             return tid, name
#         else:
#             tid = term['id'][0]
#             name = ''
#             del term['id']
#             return tid, name


# class OboMultiParser(Parser):
#     """A parser for the Obo format.
#     """

#     def __init__(self):
#         super(OboParser, self).__init__()
#         self.extensions = ('obo',)

#         self._tempterm = {}
#         self._typedef = []
#         self._meta = {}

#         self._number_of_terms = 0

#     def hook(self, *args, **kwargs):
#         """Returns True if the file is an Obo file (extension is .obo)"""

#         if 'path' in kwargs:
#             split_path = kwargs['path'].split(os.extsep)
#             return any( (ext in split_path for ext in self.extensions) )

#     def read(self, stream):
#         """Read the stream and extract information in a 'raw' format."""
#         #self._rawterms, = multiprocessing.JoinableQueue()
#         self._typedef, self._meta = [], {}

#         self.init_workers(_OboClassifier)
#         self._number_of_terms = 0

#         IN = 'meta'
#         for line in stream:

#             if b"[Term]" in line:
#                 self._number_of_terms += 1

#             try:
#                 line = line.strip().decode('utf-8')
#             except AttributeError:
#                 line = line.strip()

#             IN = self._check_section(line) or IN
#             if ': ' in line:
#                 self._parse_line_statement(line, IN)

#         self._rawterms.put(self._tempterm)

#         for typedef in self._typedef:
#             Relationship._from_obo_dict(typedef)


#     def makeTree(self):
#         """Create the proper ontology Tree from raw terms"""

#         while len(self.terms) < self._number_of_terms: #not self._terms.empty() or not self._rawterms.empty(): #self._terms.qsize() > 0 or self._rawterms.qsize() > 0:
#             d = self._terms.get()

#             if d[0] not in self.terms:
#                 self.terms[d[0]] = Term(
#                     d[0], d[1], d[2], {Relationship(k):v for k,v in six.iteritems(d[3])}, d[4]
#                 )

#             del d

#         self.shut_workers()

#     def metanalyze(self):
#         """Analyze metadatas extracted from the beginning of the file."""

#         for key,value in six.iteritems(self._meta):
#             if key != 'remark':
#                 self._parse_statement(key, value)
#             else:
#                 for remark in value:
#                     self._parse_remark(remark)

#     def manage_imports(self):
#         """Get metadatas concerning imports."""
#         try:
#             self.imports = set(self.meta['import'])
#         except KeyError:
#             pass

#     def _parse_remark(self, remark):
#         """Parse a remark and add results to self.meta."""
#         try:
#             key_remark, value_remark = remark.split(': ', 1)
#             try:
#                 self.meta[key_remark].append(value_remark)
#             except KeyError:
#                 self.meta[key_remark] = [value_remark]

#         except ValueError:
#             try:
#                 self.meta['remark'].append(remark)
#             except KeyError:
#                 self.meta['remark'] = [remark]

#     def _parse_statement(self, key, value):
#         """Parse a ``key: value`` statement in the ontology file."""

#         try:
#             self.meta[key].extend(value)
#         except TypeError:
#             self.meta[key].append(value)
#         except KeyError:
#             try:
#                 self.meta[key] = [ value.format() ]
#             except AttributeError:
#                 self.meta[key] = value

#     def _get_dict_to_update(self, IN):
#         """Returns the right dictionnary to use"""
#         if IN=='meta':
#             return self._meta
#         elif IN=='term':
#             return self._tempterm
#         elif IN=='typedef':
#             return self._typedef[-1]

#     def _check_section(self, line):
#         """Check if current section must be changed."""
#         if '[Term]' in line:
#             if self._tempterm:
#                 self._rawterms.put(self._tempterm)
#             self._tempterm = {}
#             return 'term'

#         elif '[Typedef]' in line:

#             self._typedef.append({})
#             return 'typedef'

#     def _parse_line_statement(self, line, IN):
#         k, v = line.split(': ', 1)
#         to_update = self._get_dict_to_update(IN)

#         try:
#             to_update[k].append(v)
#         except AttributeError:
#             to_update[k] = [to_update[k], v]
#         except KeyError:
#             to_update[k] = v


# OboMultiParser()



class OboParser(Parser):

    def __init__(self):
        """Initializes the parser
        """
        if type(self).__name__ not in self._instances:
            self._instances[type(self).__name__] = self

        self.terms       = {}
        self.meta        = collections.defaultdict(list)
        self._rawterms   = []
        self._rawtypedef = []
        self._section    = OboSection.meta

        self.extensions = ".obo"


    def hook(self, *args, **kwargs):
        """Returns True if this parser should be used.

        The current behaviour relies on filenames and file extension
        (.obo), but this is subject to change.
        """
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
            encoding = chardet.detect(streamline)['encoding']
            streamline = streamline.strip().decode(encoding)
            if not streamline: continue

            self._check_section(streamline)
            if self._section is OboSection.meta:
                self._parse_metadata(streamline)
            elif self._section is OboSection.typedef:
                self._parse_typedef(streamline)
            elif self._section is OboSection.term:
                self._parse_term(streamline)

        self._classify()

        return dict(self.meta), self.terms, set(self.meta['imports'])


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

            try:
                _name = _term['name'][0]
                del _term['name']
            except IndexError: _name = ''

            try:
                _desc = _term['def'][0]
                del _term['def']
            except IndexError: _desc = ''

            _relations = collections.defaultdict(list)
            try:
                for other in _term['is_a']:
                    _relations[Relationship('is_a')].append(other.split('!')[0].strip())
                del _term['is_a']
            except IndexError: pass

            try:
                for relname, other in ( x.split(' ', 1) for x in _term['relationship'] ):
                    _relations[Relationship(relname)].append(other.split('!')[0].strip())
                del _term['relationship']
            except IndexError: pass

            self.terms[_id] = Term(_id, _name, _desc, dict(_relations), dict(_term))


OboParser()
