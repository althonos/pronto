"""
pronto.parser.owl
=================

This module defines the Owl parsing method.
"""

import functools
import itertools
import os
import collections
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
from .utils         import owl_ns, XMLNameSpacer, owl_to_obo
from ..relationship import Relationship
from ..term         import Term
from ..utils        import explicit_namespace, format_accession






class OwlXMLParser(Parser):

    ns = owl_ns

    def __init__(self):

        super(OwlXMLParser, self).__init__()

        self.extensions = ('.owl', '.ont')
        self.meta = collections.defaultdict(list)
        self.imports = set()
        self.terms = {}
        self._rawterms = []


    def hook(self, *args, **kwargs):
        """Returns True if this parser should be used.

        The current behaviour relies on filenames and file extension
        (.obo), but this is subject to change.
        """
        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extensions)


    def parse(self, stream):

        self.__init__()

        tree = etree.parse(stream)

        self._parse_meta(tree)
        self._parse_terms(tree)
        self._classify()

        return dict(self.meta), self.terms, self.imports

    def _parse_meta(self, tree):

        ontology = tree.find('owl:Ontology', self.ns)

        rdf = XMLNameSpacer('rdf')

        # tag.iter() starts on the element itself so we drop that
        for elem in itertools.islice(ontology.iter(), 1, None):

            basename = elem.tag.split('}', 1)[-1]
            if basename == 'imports':
                self.imports.add(next(six.itervalues(elem.attrib)))
            elif elem.text:
                self.meta[basename].append(elem.text)
            elif elem.get(rdf.resource) is not None:
                self.meta[basename].append(elem.get(rdf.resource))

    def _parse_terms(self, tree):

        rdf = XMLNameSpacer('rdf')
        owl = XMLNameSpacer('owl')

        for rawterm in tree.iterfind(owl.Class):

            if rawterm.get(rdf.about) is None:   # This avoids parsing a class
                continue                         # created by restriction

            self._rawterms.append(collections.defaultdict(list))
            self._rawterms[-1]['id'].append(self._get_id_from_url(rawterm.get(rdf.about)))

            for elem in itertools.islice(rawterm.iter(), 1, None):

                basename = elem.tag.split('}', 1)[-1]
                if elem.text:
                    self._rawterms[-1][basename].append(elem.text)
                elif elem.get(rdf.resource) is not None:
                    self._rawterms[-1][basename].append(elem.get(rdf.resource))


    def _classify(self):

        for rawterm in self._rawterms:

            _id = self._extract_obo_id(rawterm)
            name = self._extract_obo_name(rawterm)
            desc = self._extract_obo_desc(rawterm)
            relations = self._extract_obo_relation(rawterm)
            others = self._relabel_owl_properties(rawterm)

            self.terms[_id] = Term(_id, name, desc, dict(relations), others)


    @staticmethod
    def _extract_obo_id(rawterm):
        try:
            _id = rawterm['id'][0]
            del rawterm['id']
            return _id
        except IndexError:
            print(rawterm)



    @staticmethod
    def _extract_obo_name(rawterm):
        try:
            name = rawterm['label'][0]
        except IndexError:
            name = ''
        finally:
            del rawterm['label']
            return name

    @staticmethod
    def _get_id_from_url(url):
        if '#' in url: _id = url.split('#')[-1]
        else: _id = url.split('/')[-1]
        return _id.replace('_', ':')

    @staticmethod
    def _extract_obo_desc(rawterm):
        desc = ''
        try: desc = rawterm['definition'][0]
        except IndexError:
            try: desc = rawterm['IAO_0000115'][0]
            except IndexError: pass
            finally: del rawterm['IAO_0000115']
        finally: del rawterm['definition']
        return desc

    @staticmethod
    def _extract_obo_relation(rawterm):
        relations = collections.defaultdict(list)

        for other in rawterm['subClassOf']:
            relations[Relationship('is_a')].append(
                OwlXMLParser._get_id_from_url(other)
            )
        del rawterm['subClassOf']

        return relations


    @staticmethod
    def _relabel_owl_properties(rawterm):
        new_term = {}
        for old_k, old_v in six.iteritems(rawterm):
            try:
                new_term[owl_to_obo[old_k]] = old_v
            except KeyError:
                new_term[old_k] = old_v
        return new_term

    def _relabel_owl_metadata(self):
        new_meta = {}
        for old_k, old_v in six.iteritems(self.meta):
            try:
                new_meta[owl_to_obo[old_k]] = old_v
            except KeyError:
                new_term[old_k] = old_v
        self.meta = new_meta


OwlXMLParser()
