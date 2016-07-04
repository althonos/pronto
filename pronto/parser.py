"""
pronto.parser

This module contains all the parsers used to parse an ontology. The base class
Parser can be derived to provide additional parsers to ontology files.
"""

import functools
import lxml.etree as etree
import weakref

import pronto.term
from pronto.relationship import RSHIPS

__all__ = ["Parser", "OboParser", "OwlXMLParser"]

class Parser(object):
    """A basic parser object."""

    instances = {}

    def __init__(self):
        self.terms = {}
        self.meta = {}
        self.imports = []
        self.instances[type(self).__name__] = weakref.proxy(self)
    
    def parse(self, stream, pool):
        raise NotImplemented
        return self.meta, self.terms, self.imports

    def hook(self, path):
        raise NotImplemented 

class OboParser(Parser):
    """A parser for the Obo format.
    """

    def __init__(self):
        super(OboParser, self).__init__()
        self._rawterms = []
        self._typedef = []
        self._meta = {}

    def parse(self, stream, pool):
        self.read(stream)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()
        return self.meta, self.terms, self.imports

    def read(self, stream):

        IN = 'meta'

        i = 0
        for line in stream: #.readlines():
            i += 1

            # maybe decode line
            try:
                line = line.strip().decode('utf-8')
            except AttributeError:
                line = line.strip()

            if '[Term]' in line:
                IN = 'terms'
                self._rawterms.append({})
            elif '[Typedef]' in line:
                IN = 'typedef'
                self._typedef.append({})

            if ': ' in line:

                k, v = line.split(': ', 1)

                if IN=='meta':
                    to_update = self._meta
                elif IN=='terms':
                    to_update = self._rawterms[-1]
                elif IN=='typedef':
                    to_update = self._typedef[-1]

                if k not in to_update.keys():
                    to_update[k] = v
                else:
                    if not isinstance(to_update[k], list):
                        to_update[k] = [to_update[k]]
                    to_update[k].append(v)

    def makeTree(self, pool):
        for t in pool.map(self._classify, self._rawterms):
            self.terms.update(t)

    def _classify(self, term):

            relations = {}

            if 'relationship' in term:

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


            for rship in RSHIPS:

                if rship in term.keys():

                    if isinstance(term[rship], list):
                        relations[rship] = [ x.split(' !')[0] for x in term[rship] ]
                    else:
                        relations[rship] = [ term[rship].split(' !')[0]]

                    del term[rship]

            if 'def' in term.keys():
                desc = term['def']
                del term['def']
            else:
                desc = ''

            if 'name' in term.keys():
                tid, name = term['id'], term['name']
                del term['name']
                del term['id']
            else:
                tid = term['id'][0]
                name = ''
                del term['id']

            return {tid: pronto.term.Term(tid, name, desc, relations, term)}

    def metanalyze(self):

        for key,value in self._meta.items():

            if key != 'remark':
                if not isinstance(value, list):
                    value = [value]

                if not key in self.meta.keys():
                    self.meta[key] = []
                self.meta[key].extend(value)

            else:

                for remark in value:
                    if ': ' in remark:
                        key_remark, value_remark = remark.split(': ', 1)

                        if not key_remark in self.meta:
                            self.meta[key_remark] = []

                            self.meta[key_remark].append(value_remark)
                    else:

                        if 'remark' not in self.meta:
                            self.meta['remark'] = []
                        self.meta['remark'].append(remark)

    def manage_imports(self):
        if 'import' in self.meta.keys():
            self.imports = self.meta['import']
            
class OwlXMLParser(Parser):
    """A parser for the owl xml format.
    """

    def __init__(self):
        super(OwlXMLParser, self).__init__()
        self._tree = None
        self._ns = {}

    def parse(self, stream, pool):
        """
        Parse the ontology file.

        :param stream: A stream of the ontology file.
        :type stream: io.StringIO
        """
        self.read(stream)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()
        return self.meta, self.terms, self.imports


    def read(self, stream):
        """
        Parse the content of the stream
        """
        self._tree = etree.parse(stream)
        self._ns = self._tree.find('.').nsmap
        self._ns['base'] = self._ns[None]
        del self._ns[None]

    def makeTree(self, pool):
        terms_elements = self._tree.findall('./owl:Class', self._ns)
        for t in pool.map(self._classify, terms_elements):
            self.terms.update(t)

    def _classify(self, term):

        nspaced = functools.partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        accession = functools.partial(pronto.utils.format_accession, nsmap=self._ns)

        if not term.attrib:
           return {}

        tid = accession(term.get(nspaced('rdf:about')))

        term_dict = {'name':'', 'relations': {}, 'desc': ''}

        translator = [
            {'hook': lambda c: c.tag == nspaced('rdfs:label'),
             'callback': lambda c: c.text,
             'dest': 'name',
             'action': 'store'
            },
            {
             'hook': lambda c: c.tag == nspaced('rdfs:subClassOf') \
                               and nspaced('rdf:resource') in c.attrib.keys(),
             'callback': lambda c: accession(c.get(nspaced('rdf:resource')) or c.get(nspaced('rdf:about'))),
             'dest': 'relations',
             'action': 'list',
             'list_to': 'is_a'
            },
            {'hook': lambda c: c.tag == nspaced('rdfs:comment'),
             'callback': lambda c: pronto.utils.parse_comment(c.text),
             'action': 'update'
            }
        ]

        for child in term.iterchildren():

            for rule in translator:

                if rule['hook'](child):

                    if rule['action'] == 'store':
                        term_dict[rule['dest']] = rule['callback'](child)

                    elif rule['action'] == 'list':

                        if not term_dict[rule['dest']]:
                            term_dict[rule['dest']][rule['list_to']] = []

                        term_dict[rule['dest']][rule['list_to']].append(rule['callback'](child))


                    elif rule['action'] == 'update':
                        term_dict.update(rule['callback'](child))


                    break

        if ':' in tid: #remove administrative classes
            return {tid: pronto.term.Term(tid, **term_dict)}
        else:
            return {}

    def manage_imports(self):
        nspaced = functools.partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        for imp in self._tree.iterfind('./owl:Ontology/owl:imports', self._ns):
            path = imp.attrib[nspaced('rdf:resource')]
            if path.endswith('.owl'):
                self.imports.append(path)

    def metanalyze(self):
        pass


OboParser()
OwlXMLParser()