"""
pronto.parser

This module contains all the parsers used to parse an ontology. The base class
Parser can be derived to provide additional parsers to ontology files.
"""

import pronto.term

from pronto.parser import Parser
from pronto.relationship import RSHIPS


class OboParser(Parser):
    """A parser for the Obo format.
    """

    def __init__(self):
        super(OboParser, self).__init__()
        self.extension = '.obo'
        self._rawterms = list()
        self._typedef = list()
        self._meta = dict()

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Obo file (extension is .obo)"""
        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extension)

    def read(self, stream):
        """Read the stream and extract information in a 'raw' format."""
        self._rawterms, self._typedef, self._meta = list(), list(), dict()
        IN = 'meta'
        for line in stream:
            line = line.strip().decode('utf-8') \
                   if hasattr(line, 'decode') \
                   else line.strip()
            IN = self._check_section(line) or IN
            if ': ' in line:
                self._parse_line_statement(line, IN)

    def makeTree(self, pool):
        """Create the proper ontology Tree from raw terms"""
        for t in pool.map(_classify, self._rawterms):
            self.terms.update(t)

    def metanalyze(self):
        """Analyze metadatas extracted from the beginning of the file."""

        for key,value in self._meta.items():
            if key != 'remark':
                self._parse_statement(key, value)
            else:
                for remark in value:
                    self._parse_remark(remark)

    def manage_imports(self):
        """Get metadatas concerning imports."""
        if 'import' in self.meta.keys():
            self.imports = self.meta['import']
        self.imports = list(set(self.imports))


    def _parse_remark(self, remark):
        """Parse a remark and add results to self.meta."""
        if ': ' in remark:
            key_remark, value_remark = remark.split(': ', 1)
            if not key_remark in self.meta:
                self.meta[key_remark] = []
            self.meta[key_remark].append(value_remark)
        else:
            if 'remark' not in self.meta:
                self.meta['remark'] = []
            self.meta['remark'].append(remark)

    def _parse_statement(self, key, value):
        """Parse a ``key: value`` statement in the ontology file."""
        if not isinstance(value, list):
            value = [value]
        if not key in self.meta.keys():
            self.meta[key] = []
        self.meta[key].extend(value)


    def _get_dict_to_update(self, IN):
        """Returns the right dictionnary to use"""
        if IN=='meta':
            return self._meta
        elif IN=='term':
            return self._rawterms[-1]
        elif IN=='typedef':
            return self._typedef[-1]

    def _check_section(self, line):
        """Check if current section must be changed."""
        if '[Term]' in line:
            self._rawterms.append({})
            return 'term'
        elif '[Typedef]' in line:
            self._typedef.append({})
            return 'typedef'

    def _parse_line_statement(self, line, IN):
        k, v = line.split(': ', 1)
        to_update = self._get_dict_to_update(IN)
        if k not in to_update.keys():
            to_update[k] = v
        else:
            if not isinstance(to_update[k], list):
                to_update[k] = [to_update[k]]
            to_update[k].append(v)



def _classify(term):

    relations = {}

    if 'relationship' in term:
        _process_relationship(term)

    for rship in RSHIPS:
        relations = _extract_relationship(term, rship, relations)

    desc = _extract_description(term)

    tid, name = _extract_name_and_id(term)

    if not tid:
        return {}

    return {tid: pronto.term.Term(tid, name, desc, relations, term)}


def _process_relationship(term):

    if isinstance(term['relationship'], list):
        for r in term['relationship']:
            name, value = r.split(' ', 1)

            if name not in term.keys():
                term[name] = []
            term[name].append(value)

    else:
        name, value = term['relationship'].split(' ', 1)

        if name not in term.keys():
            term[name] = []
        term[name].append(value)

    del term['relationship']

def _extract_relationship(term, rship, relations):
    if rship in term.keys():
        if isinstance(term[rship], list):
            relations[rship] = [ x.split(' !')[0] for x in term[rship] ]
        else:
            relations[rship] = [ term[rship].split(' !')[0]]
        del term[rship]
    return relations

def _extract_description(term):
    if 'def' in term.keys():
        desc = term['def']
        del term['def']
        return desc
    else:
        return ''

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

