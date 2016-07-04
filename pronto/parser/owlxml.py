

import multiprocessing.pool
import lxml.etree as etree
import functools

import pronto.utils

class OwlXMLParser(object):
    """An ontology parsed from an owl xml file.
    """

    def parse(self, handle, pool):

        self.read(handle)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()

        return self.meta, self.terms, self.imports


    def read(self, handle):
        self._tree = etree.parse(handle)

        self._ns = self._tree.find('.').nsmap
        self._ns['base'] = self._ns[None]
        del self._ns[None]

    def makeTree(self, pool):

        self.terms = {}

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
        self.imports = []
        for imp in self._tree.iterfind('./owl:Ontology/owl:imports', self._ns):
            path = imp.attrib[nspaced('rdf:resource')]
            if path.endswith('.owl'):
                self.imports.append(path)

    def metanalyze(self):
        self.meta = {}
