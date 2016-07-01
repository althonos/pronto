from lxml import etree
from functools import partial

from pronto.ontology import Ontology
from pronto.term import Term
from pronto.utils import explicit_namespace, parse_comment, format_accession

class OwlXML(Ontology):
    """An ontology parsed from an owl xml file.
    """

    def _parse(self, handle):

        self._read(handle)
        self._makeTree()
        self._metanalyze()

        del self._tree
        del self._ns

    def _read(self, handle):
        self._tree = etree.parse(handle)
        
        self._ns = self._tree.find('.').nsmap
        self._ns['base'] = self._ns[None]
        del self._ns[None]

    def _makeTree(self):

        terms_elements = self._tree.findall('./owl:Class', self._ns)
        
        for t in self.pool.map(self._classify, terms_elements):
            self.terms.update(t)

                
    def _classify(self, term):

        nspaced = partial(explicit_namespace, nsmap=self._ns)

        tid = format_accession(term.get(nspaced('rdf:about')), self._ns)
        term_dict = {'name':'', 'relations': {}, 'desc': ''}

        translator = [
            {'hook': lambda c: c.tag == nspaced('rdfs:label'), 
             'callback': lambda c: c.text,
             'dest': 'name',
             'action': 'store'
            },
            {
             'hook': lambda c: c.tag == nspaced('rdfs:subClassOf'),
             'callback': lambda c: format_accession(c.get(nspaced('rdf:resource')), self._ns),
             'dest': 'relations',
             'action': 'list',
             'list_to': 'is_a'
            },
            {'hook': lambda c: c.tag == nspaced('rdfs:comment'), 
             'callback': lambda c: parse_comment(c.text),
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
            return {tid: Term(tid, **term_dict)}
        else:
            return {}

    def _metanalyze(self):
        self.meta = {}
