from lxml import etree
from functools import partial

import pronto.utils
import pronto.ontology
import pronto.term


class OwlXML(pronto.ontology.Ontology):
    """An ontology parsed from an owl xml file.
    """

    def _parse(self, handle):

        self._read(handle)
        self._makeTree()
        self._metanalyze()
        self._manage_imports()

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

        nspaced = partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        accession = partial(pronto.utils.format_accession, nsmap=self._ns)

        tid = accession(term.get(nspaced('rdf:about')))
        term_dict = {'name':'', 'relations': {}, 'desc': ''}

        translator = [
            {'hook': lambda c: c.tag == nspaced('rdfs:label'), 
             'callback': lambda c: c.text,
             'dest': 'name',
             'action': 'store'
            },
            {
             'hook': lambda c: c.tag == nspaced('rdfs:subClassOf'),
             'callback': lambda c: accession(c.get(nspaced('rdf:resource'))),
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

    def _manage_imports(self):
        nspaced = partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        self.imports = []
        for imp in self._tree.iterfind('./owl:Ontology/owl:imports', self._ns):
            path = imp.attrib[nspaced('rdf:resource')]
            if path.endswith('.owl'):
                self.imports.append(path)

    def _import(self):
        """Imports the required ontologies.

        :Example:
        >>> from pronto import OwlXML
        >>> nmr = OwlXML('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl', False)
        >>> nmr_i = OwlXML('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl', True)
        >>> bfo = OwlXML('http://purl.obolibrary.org/obo/bfo.owl', False)
        
        >>> all(term in nmr for term in bfo)
        False
        >>> all(term in nmr_i for term in bfo)
        True

        """
        for i in self.imports:
            self.merge(OwlXML(i))

    def _metanalyze(self):
        self.meta = {}
