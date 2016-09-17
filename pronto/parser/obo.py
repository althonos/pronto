"""
pronto.parser.obo
=================

This module defines the Obo parsing method.
"""

import multiprocessing
import six

from .              import Parser
from ..relationship import Relationship
from ..term         import Term


class _OboClassifier(multiprocessing.Process): # pragma: no cover

    def __init__(self, queue, results, *args, **kwargs):

        super(_OboClassifier, self).__init__()

        self.queue = queue
        self.results = results

    def run(self):

        while True:

            term = self.queue.get()

            if term is None:
                break

            self.results.put(self._classify(term))

        #return {tid: Term(tid, name, desc, relations, term)}

    @staticmethod
    def _classify(term):

        relations = {}

        if 'relationship' in term:
            #Relationship.lock.acquire()
            #try:
            _OboClassifier._process_relationship(term)
            #finally:
            #    Relationship.lock.release()

        #if 'is_a' in term:
        try:
            term[Relationship('is_a')] = [ term['is_a'].format() ]
            del term['is_a']
        except AttributeError:
            term[Relationship('is_a')] = term['is_a']
            del term['is_a']
        except KeyError:
            pass
            #term[Relationship('is_a')] = term['is_a'] if isinstance(term['is_a'])
            #del term['is_a']

        for key in tuple(term.keys()):
            if isinstance(key, Relationship):
                relations = _OboClassifier._extract_relationship(term, key, relations)

        desc = _OboClassifier._extract_description(term)
        tid, name = _OboClassifier._extract_name_and_id(term)

        return (tid, name, desc, relations, term)

    @staticmethod
    def _process_relationship(term):

        # If term is a str
        try:

            name, value = term['relationship'].split(' ', 1)

            name = Relationship(name)

            try:
                term[name].append(value)
            except KeyError:
                term[name] = [value]

        # If term is a list
        except AttributeError:

            for r in term['relationship']:
                name, value = r.split(' ', 1)

                name = Relationship(name)

                try:
                    term[name].append(value)
                except KeyError:
                    term[name] = [value]

        del term['relationship']

    @staticmethod
    def _extract_relationship(term, rship, relations):

        #if rship.obo_name in term.keys():
        #if isinstance(term[rship], list):
        try:
            relations[rship.obo_name] = [ x.split(' !')[0] for x in term[rship] ]
        except AttributeError:
            relations[rship.obo_name] = [ term[rship].split(' !')[0]]



        del term[rship]

        return relations

    @staticmethod
    def _extract_description(term):
        try:
        #if 'def' in term.keys():
            desc = term['def']
            del term['def']
            return desc
        except KeyError:
            return ''

    @staticmethod
    def _extract_name_and_id(term):
        if 'id' not in term.keys():
            return '', ''
        if 'name' in term.keys():
            tid, name = term['id'], term['name']
            del term['name']
            del term['id']
            return tid, name
        else:
            tid = term['id'][0]
            name = ''
            del term['id']
            return tid, name


class OboParser(Parser):
    """A parser for the Obo format.
    """

    def __init__(self):
        super(OboParser, self).__init__()
        self.extension = '.obo'

        self._tempterm = {}
        self._typedef = []
        self._meta = {}

        self._number_of_terms = 0

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Obo file (extension is .obo)"""

        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extension)

    def read(self, stream):
        """Read the stream and extract information in a 'raw' format."""
        #self._rawterms, = multiprocessing.JoinableQueue()
        self._typedef, self._meta = [], {}

        self.init_workers(_OboClassifier)
        self._number_of_terms = 0

        IN = 'meta'
        for line in stream:

            if b"[Term]" in line:
                self._number_of_terms += 1

            try:
                line = line.strip().decode('utf-8')
            except AttributeError:
                line = line.strip()

            IN = self._check_section(line) or IN
            if ': ' in line:
                self._parse_line_statement(line, IN)

        self._rawterms.put(self._tempterm)

    def makeTree(self):
        """Create the proper ontology Tree from raw terms"""

        while len(self.terms) < self._number_of_terms: #not self._terms.empty() or not self._rawterms.empty(): #self._terms.qsize() > 0 or self._rawterms.qsize() > 0:
            d = self._terms.get()

            if d[0] not in self.terms:
                self.terms[d[0]] = Term(
                    d[0], d[1], d[2], {Relationship(k):v for k,v in six.iteritems(d[3])}, d[4]
                )

            del d
            #print("{} / {} terms extracted".format(len(self.terms), self._number_of_terms))

        self.shut_workers()

    def metanalyze(self):
        """Analyze metadatas extracted from the beginning of the file."""

        for key,value in six.iteritems(self._meta):
            if key != 'remark':
                self._parse_statement(key, value)
            else:
                for remark in value:
                    self._parse_remark(remark)

    def manage_imports(self):
        """Get metadatas concerning imports."""
        try:
        #if 'import' in self.meta: #.keys():
            self.imports = set(self.meta['import'])

        except KeyError:
            pass #self.imports = set()

    def _parse_remark(self, remark):
        """Parse a remark and add results to self.meta."""
        try:
            key_remark, value_remark = remark.split(': ', 1)
            try:
                self.meta[key_remark].append(value_remark)
            except KeyError:
                self.meta[key_remark] = [value_remark]

        except ValueError:
            try:
                self.meta['remark'].append(remark)
            except KeyError:
                self.meta['remark'] = [remark]

    def _parse_statement(self, key, value):
        """Parse a ``key: value`` statement in the ontology file."""

        try:
            self.meta[key].extend(value)
        except TypeError:
            self.meta[key].append(value)
        except KeyError:
            try:
                self.meta[key] = [ value.format() ]
            except AttributeError:
                self.meta[key] = value

    def _get_dict_to_update(self, IN):
        """Returns the right dictionnary to use"""
        if IN=='meta':
            return self._meta
        elif IN=='term':
            return self._tempterm
        elif IN=='typedef':
            return self._typedef[-1]

    def _check_section(self, line):
        """Check if current section must be changed."""
        if '[Term]' in line:
            if self._tempterm:
                self._rawterms.put(self._tempterm)
            self._tempterm = {}
            return 'term'

        elif '[Typedef]' in line:
            self._typedef.append({})
            return 'typedef'

    def _parse_line_statement(self, line, IN):
        k, v = line.split(': ', 1)
        to_update = self._get_dict_to_update(IN)

        try:
            to_update[k].append(v)
        except AttributeError:
            to_update[k] = [to_update[k], v]
        except KeyError:
            to_update[k] = v


OboParser()
