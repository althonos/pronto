
import functools
import os
import multiprocessing
import lxml.etree as etree

from pronto.parser import Parser
from pronto.relationship import Relationship
import pronto.utils


class _OwlXMLClassifier(multiprocessing.Process):

    def __init__(self, queue, results):

        super(_OwlXMLClassifier, self).__init__()

        self.queue = queue
        self.results = results
        nsmap = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'}
        #self.nsmap = nsmap

        self.nspaced = functools.partial(pronto.utils.explicit_namespace, nsmap=nsmap)
        self.accession = functools.partial(pronto.utils.format_accession, nsmap=nsmap)


    def run(self):

        while True:

            term = self.queue.get()

            if term is None:
                #self.queue.task_done()
                break

            classified_term = self._classify(etree.fromstring(term))

            if classified_term:
                self.results.put(classified_term)

    def _classify(self, term):
        """
        Map raw information extracted from each owl Class.

        The raw data (in an etree.Element object) is extracted to a proper
        dictionnary containing a Term referenced by its id, which is then
        used to update :attribute:terms

        Todo:
            * Split into smaller methods to lower code complexity.
        """

        if not term.attrib:
           return {}

        tid = self.accession(term.get(self.nspaced('rdf:about')))

        term_dict = {'name':'', 'relations': {}, 'desc': ''}

        translator = [
            {'hook': lambda c: c.tag == self.nspaced('rdfs:label'),
             'callback': lambda c: c.text,
             'dest': 'name',
             'action': 'store'
            },
            {
             'hook': lambda c: c.tag == self.nspaced('rdfs:subClassOf') \
                               and self.nspaced('rdf:resource') in c.attrib.keys(),
             'callback': lambda c: self.accession(c.get(self.nspaced('rdf:resource')) or c.get(self.nspaced('rdf:about'))),
             'dest': 'relations',
             'action': 'list',
             'list_to': 'is_a',
            },
            {'hook': lambda c: c.tag == self.nspaced('rdfs:comment'),
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

                        try:
                            term_dict[rule['dest']][rule['list_to']].append(rule['callback'](child))
                        except KeyError:
                            term_dict[rule['dest']][rule['list_to']] = [rule['callback'](child)]


                    elif rule['action'] == 'update':
                        term_dict.update(rule['callback'](child))


                    break

        #if ':' in tid: #remove administrative classes
        return (tid, term_dict)#{tid: pronto.term.Term(tid, **term_dict)}
        #else:
        #    return {}





class OwlXMLParser(Parser):
    """A parser for the owl xml format.
    """

    def __init__(self):
        super(OwlXMLParser, self).__init__()
        self._tree = None
        self._ns = dict()
        self.extensions = ('.owl', '.xml', '.ont')

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Owl file (extension is .owl)"""
        if 'path' in kwargs:
            return os.path.splitext(kwargs['path'])[1] in self.extensions

    def read(self, stream):
        """
        Parse the content of the stream
        """

        self.init_workers(_OwlXMLClassifier)

        events = ("start", "end", "start-ns")

        owl_imports, owl_class, rdf_resource = "", "", ""



        for event, element in etree.iterparse(stream, huge_tree=True, events=events):

            if element is None:
                break

            if event == "start-ns":
                self._ns.update({element[0]:element[1]})

                if element[0]== 'owl':
                    owl_imports = "".join(["{", element[1], "}", "imports"])
                    owl_class = "".join(["{", element[1], "}", "Class"])
                elif element[0] == 'rdf':
                    rdf_resource = "".join(["{", element[1], "}", "resource"])

            elif element.tag==owl_imports and event=='end':
                self.imports.append(element.attrib[rdf_resource])
                element.clear()

            elif element.tag==owl_class and event=='end':
                self._rawterms.put(etree.tostring(element))
                element.clear()



    def makeTree(self):
        """
        Maps :function:_classify to each term of the file via a ThreadPool.

        Once all the raw terms are all classified, the :attrib:terms dictionnary
        gets updated.

        Arguments:
            pool (Pool): a pool of workers that is used to map the _classify
                function on the terms.
        """
        #terms_elements = self._tree.iterfind('./owl:Class', self._ns)
        #for t in pool.map(self._classify, self._elements):
        #    self.terms.update(t)

        accession = functools.partial(pronto.utils.format_accession, nsmap=self._ns)

        while self._terms.qsize() > 0 or self._rawterms.qsize() > 0:


            tid, d = self._terms.get()

            tid = pronto.utils.format_accession(tid, self._ns)

            d['relations'] = { Relationship(k):[accession(x) for x in v] for k,v in d['relations'].items() }

            self.terms[tid] = pronto.term.Term(tid, **d)

        self.shut_workers()

    def manage_imports(self):
        pass
        #nspaced = functools.partial(pronto.utils.explicit_namespace, nsmap=self._ns)
        #for imp in self._tree.iterfind('./owl:Ontology/owl:imports', self._ns):
        #    path = imp.attrib[nspaced('rdf:resource')]
        #    if path.endswith('.owl'):
        #        self.imports.append(path)

    def metanalyze(self):
        """
        Extract metadata from the headers of the owl file.

        Todo:
            * Implement that method !
        """
        pass


OwlXMLParser()
