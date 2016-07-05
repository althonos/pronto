
import functools
import os
import lxml.etree as etree

from pronto.parser import Parser
import pronto.utils


class OwlXMLParser(Parser):
    """A parser for the owl xml format.
    """

    def __init__(self):
        super(OwlXMLParser, self).__init__()
        self._tree = None
        self._ns = {}
        self.extensions = ('.owl', '.xml', '.ont')

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Owl file (extension is .owl)"""
        if 'path' in kwargs:
            return os.path.splitext(kwargs['path'])[1] in self.extensions

    def read(self, stream):
        """
        Parse the content of the stream
        """
        self._tree = etree.parse(stream)
        self._ns = self._tree.find('.').nsmap
        if None in self._ns.keys():
            self._ns['base'] = self._ns[None]
            del self._ns[None]

    def makeTree(self, pool):
        """
        Maps :function:_classify to each term of the file via a ThreadPool.

        Once all the raw terms are all classified, the :attrib:terms dictionnary
        gets updated.

        Arguments:
            pool (Pool): a pool of workers that is used to map the _classify
                function on the terms.
        """
        terms_elements = self._tree.findall('./owl:Class', self._ns)
        for t in pool.map(self._classify, terms_elements):
            self.terms.update(t)

    def _classify(self, term):
        """
        Map raw information extracted from each owl Class.

        The raw data (in an etree.Element object) is extracted to a proper
        dictionnary containing a Term referenced by its id, which is then
        used to update :attribute:terms

        Todo:
            * Split into smaller methods to lower code complexity.
        """

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

        #if ':' in tid: #remove administrative classes
        return {tid: pronto.term.Term(tid, **term_dict)}
        #else:
        #    return {}

    def manage_imports(self):
        nspaced = functools.partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        for imp in self._tree.iterfind('./owl:Ontology/owl:imports', self._ns):
            path = imp.attrib[nspaced('rdf:resource')]
            if path.endswith('.owl'):
                self.imports.append(path)

    def metanalyze(self):
        """
        Extract metadata from the headers of the owl file.

        Todo:
            * Implement that method !
        """
        pass


OwlXMLParser()
