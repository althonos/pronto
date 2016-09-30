"""
pronto.parser.owl
=================

This module defines the Owl parsing method.
"""

import functools
import os
import multiprocessing
import six

try:
    import lxml.etree as etree
    from lxml.etree import XMLSyntaxError as ParseError
except ImportError: # pragma: no cover
    try:
        import xml.etree.cElementTree as etree
        from xml.etree.cElementTree import ParseError
    except ImportError:
        import xml.etree.ElementTree as etree
        from xml.etree.ElementTree import ParseError

from .              import Parser
from ..relationship import Relationship
from ..term         import Term
from ..utils        import explicit_namespace, format_accession


class _OwlXMLClassifier(multiprocessing.Process): # pragma: no cover

    def __init__(self, queue, results):

        super(_OwlXMLClassifier, self).__init__()

        self.queue = queue
        self.results = results
        nsmap = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'}

        self.nspaced = functools.partial(explicit_namespace, nsmap=nsmap)
        self.accession = functools.partial(format_accession, nsmap=nsmap)

        self.translator = [
            {'hook':     lambda c: c.tag == self.nspaced('rdfs:label'),
             'callback': lambda c: c.text,
             'dest':     'name',
             'action':   'store',
            },
            {
             'hook':     lambda c: (c.tag == self.nspaced('rdfs:subClassOf')) \
                               and (self.nspaced('rdf:resource') in c.attrib),
             'callback': lambda c: self.accession(c.get(self.nspaced('rdf:resource')) \
                               or c.get(self.nspaced('rdf:about'))),
             'dest':     'relations',
             'action':   'list',
             'list_to':  'is_a',
            },
            {'hook':     lambda c: c.tag == self.nspaced('rdfs:comment'),
             'callback': lambda c: self.parse_comment(c.text),
             'action':   'update'
            }
        ]

    def run(self):

        while True:


            term = self.queue.get()

            if term is None:
                break

            try:
                classified_term = self._classify(etree.fromstring(term))
            except ParseError:
                self.results.put((None, None))
                break

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

        for child in term.iter():#term.iterchildren():

            for rule in self.translator:

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

        return (tid, term_dict)

    @staticmethod
    def parse_comment(comment):
        """Parse an rdfs:comment to extract information.

        Owl contains comment which can contain additional metadata (specially
        when the Owl file was converted from Obo to Owl). This function parses
        the comment to try to extract those metadata.

        Parameters:
            comment (str): if containing different sections (such as 'def:',
                'functional form' or 'altdef:'), the value of those sections will
                be returned in a dictionnary. If there are not sections, the
                comment is interpreted as a description

        Todo:
            * Add more parsing special cases

        """
        if comment is None:
            return {}

        commentlines = comment.split('\n')
        parsed = {}

        for (index, line) in enumerate(commentlines):

            line = line.strip()

            if line.startswith('Functional form:'):
                #if not 'other' in parsed.keys():
                #    parsed['other'] = dict()

                try:
                    parsed['other']['functional form'] = "\n".join(commentlines[index:])
                except KeyError:
                    parsed['other'] = {'functional form': "\n".join(commentlines[index:])}

                break

            if line.startswith('def:'):
                parsed['desc'] = line.split('def:')[-1].strip()

            elif ': ' in line:
                ref, value = [x.strip() for x in line.split(': ', 1)]

                try:
                    parsed['other'][ref].append(value)
                except KeyError:
                    try:
                        parsed['other'][ref] = [value]
                    except KeyError:
                        parsed['other'] = {ref: [value] }

            else:
                if not 'desc' in parsed:
                    parsed['desc'] = "\n".join(commentlines[index:])
                    break

        if not 'desc' in parsed and 'other' in parsed:
            #if 'tempdef' in parsed['other'].keys():
            try:
                parsed['desc'] = next(iter(parsed['other']['tempdef']), "")
                del parsed['other']['tempdef']
            except KeyError:
                pass

            #if 'altdef' in parsed['other'].keys():
            try:
                parsed['desc'] = next(iter(parsed['other']['altdef']), "")
                del parsed['other']['altdef']
            except KeyError:
                pass


        return parsed


class OwlXMLParser(Parser):
    """A parser for the owl xml format.
    """

    def __init__(self, daemon=False):
        super(OwlXMLParser, self).__init__()
        self._tree = None
        self._ns = {}
        self._meta = {}
        self.extensions = ('owl', 'xml', 'ont')

        self._number_of_terms = 0

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Owl file (extension is .owl)"""
        if 'path' in kwargs:
            split_path = kwargs['path'].split(os.extsep)
            return any( (ext in split_path for ext in self.extensions) )

            #ext = kwargs['path'].split("
					#os.path.splitext(kwargs['path'])[1] in self.extensions

    def read(self, stream):
        """
        Parse the content of the stream
        """

        self.init_workers(_OwlXMLClassifier)
        self._number_of_terms = 0

        events = ("end", "start-ns")

        owl_imports, owl_class, rdf_resource, obo_in_owl = "", "", "", ""
        l_obo_in_owl = 0

        context = etree.iterparse(stream, events=events)

        for event, element in context: #etree.iterparse(stream, #huge_tree=True,
                                       #                events=events):

            if element is None:
                break

            if event == "start-ns":
                self._ns.update({element[0]:element[1]})

                if element[0]=='owl':
                    owl_imports = "".join(["{", element[1], "}", "imports"])
                    owl_class = "".join(["{", element[1], "}", "Class"])
                elif element[0]=='rdf':
                    rdf_resource = "".join(["{", element[1], "}", "resource"])
                elif element[0]=="oboInOwl":
                    obo_in_owl = "".join(["{", element[1], "}"])
                    l_obo_in_owl = len(obo_in_owl)

                del event
                del element
                continue

            elif element.tag==owl_imports:
                self.imports.add(element.attrib[rdf_resource])

            elif element.tag==owl_class:
                if element.attrib:
                    self._rawterms.put(etree.tostring(element))
                    self._number_of_terms += 1

            elif obo_in_owl and element.tag.startswith(obo_in_owl):
                try:
                    self._meta[element.tag[l_obo_in_owl:]].append(element)
                except KeyError:
                    self._meta[element.tag[l_obo_in_owl:]] = [element]

                del element
                continue

            else:
                continue

            element.clear()

            try:
                for ancestor in element.xpath('ancestor-or-self::*'):
                    while ancestor.getprevious() is not None:
                        del ancestor.getparent()[0]
            except AttributeError:
                pass

            del element

        del context

    def makeTree(self):
        """
        Maps :function:_classify to each term of the file via a ThreadPool.

        Once all the raw terms are all classified, the :attrib:terms dictionnary
        gets updated.

        Arguments:
            pool (Pool): a pool of workers that is used to map the _classify
                function on the terms.
        """

        accession = functools.partial(format_accession, nsmap=self._ns)

        while len(self.terms) < self._number_of_terms:

            tid, d = self._terms.get()

            if tid is None and d is None:
                break

            tid = format_accession(tid, self._ns)

            d['relations'] = { Relationship(k):[accession(x) for x in v] for k,v in six.iteritems(d['relations']) }

            if not tid in self.terms:
                self.terms[tid] = Term(tid, **d)

        self.shut_workers()

    def manage_imports(self):
        pass

    def metanalyze(self):
        """
        Extract metadata from the headers of the owl file.
        """

        obomap = {    #"created_by":      "creator",
                   "hasOBONamespace": "namespace",
                   "hasOBOFormatVersion": "format-version",
                 }

        exclusion = {"hasOBONamespace", "id", "hasExactSynonym", "hasDbXref", "hasBroadSynonym"}

        self.meta = dict([
            (obomap[k],[x.text for x in v]) if k in obomap else (k,[x.text for x in v])
                for k,v in six.iteritems(self._meta)
                    if k not in exclusion

        ])

        try:
            self.meta["namespace"] = list(set([ x.text for x in self._meta["hasOBONamespace"]]))
        except KeyError:
            pass


OwlXMLParser()
