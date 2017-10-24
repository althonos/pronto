# coding: utf-8
"""Definition of the Owl parser.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import itertools
import collections
import six
#FEAT# DESERIALIZE AS DATES
#FEAT# import dateutil.parser

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree

from .base import BaseParser
from .utils import owl_ns, owl_to_obo, OwlSection, owl_synonyms
from ..description import Description
from ..relationship import Relationship
from ..synonym import Synonym
from ..term import Term
from ..utils import nowarnings


RDF_ABOUT = "{{{}}}{}".format(owl_ns['rdf'], 'about')
RDF_RESOURCE = "{{{}}}{}".format(owl_ns['rdf'], 'resource')
RDF_DATATYPE = "{{{}}}{}".format(owl_ns['rdf'], 'datatype')
OWL_AXIOM = "{{{}}}{}".format(owl_ns['owl'], 'Axiom')
OWL_CLASS = "{{{}}}{}".format(owl_ns['owl'], 'Class')
OWL_ONTOLOGY = "{{{}}}{}".format(owl_ns['owl'], 'Ontology')



class OwlXMLParser(BaseParser):
    """An OwlXML Parser.

    Provides functions common to all OwlXMLParsers, such as a
    function to extract ontology terms id from a url, or the common
    `~OwlXMLParser.hook` method.
    """

    ns = owl_ns
    extensions = ('.owl', '.ont', '.owl.gz', '.ont.gz')

    @classmethod
    def hook(cls, force=False, path=None, lookup=None):  # noqa: D102
        if force:
            return True
        if path is not None and path.endswith(cls.extensions):
            return True
        if lookup is not None and lookup.startswith(b'<?xml'):
            return True
        return False

    @staticmethod
    def _get_basename(tag):
        return tag.split('}', 1)[-1]

    @staticmethod
    def _get_id_from_url(url):
        _id = url.split('#' if '#' in url else '/')[-1]
        return _id.replace('_', ':')

    @classmethod
    @nowarnings
    def parse(cls, stream):

        tree = etree.parse(stream)

        meta, imports = cls._parse_meta(tree)
        terms = collections.OrderedDict()

        for rawterm in cls._generate_rawterms(tree):
            term = cls._classify(rawterm)
            terms[term.id] = term
            # TODO: extract axioms through targeted XPaths

        meta = cls._relabel_to_obo(meta)
        return meta, terms, imports

    @staticmethod
    def _parse_meta(tree):

        imports = set()
        meta = collections.defaultdict(list)

        # tag.iter() starts on the element itself so we drop that
        for elem in itertools.islice(tree.find(OWL_ONTOLOGY).iter(), 1, None):
            # Check the tag is not a comment (lxml only)
            try:
                basename = elem.tag.split('}', 1)[-1]
                if basename == 'imports':
                    imports.add(next(six.itervalues(elem.attrib)))
                elif elem.text:
                    meta[basename].append(elem.text)
                elif elem.get(RDF_RESOURCE) is not None:
                    meta[basename].append(elem.get(RDF_RESOURCE))
            except AttributeError:
                pass

        meta['import'] = list(imports)
        return meta, imports

    @classmethod
    def _generate_rawterms(cls, tree):

        for elem in tree.iterfind(OWL_CLASS):

            if RDF_ABOUT not in elem.keys():   # This avoids parsing a class
                continue                       # created by restriction

            #_rawterms.append(collections.defaultdict(list))
            rawterm = collections.defaultdict(list)
            rawterm['id'].append(cls._get_id_from_url(elem.get(RDF_ABOUT)))

            for child in itertools.islice(elem.iter(), 1, None):
                try:
                    basename = child.tag.split('}', 1)[-1]
                    if child.text is not None:
                        child.text = child.text.strip()
                    if child.text:
                        rawterm[basename].append(child.text)
                    elif child.get(RDF_RESOURCE) is not None:
                        rawterm[basename].append(child.get(RDF_RESOURCE))
                except AttributeError:
                    pass

            yield dict(rawterm)


    @classmethod
    def _classify(cls, rawterm):
        return Term(
            rawterm.pop('id')[0],
            rawterm.pop('label', [''])[0],
            rawterm.pop('definition', None) or rawterm.pop('IAO_0000115', ''),
            cls._extract_obo_relation(rawterm),
            cls._extract_obo_synonyms(rawterm),
            cls._relabel_to_obo(rawterm),
        )

    @staticmethod
    def _extract_obo_synonyms(rawterm):
        synonyms = set()
        # keys in rawterm that define a synonym
        keys = set(owl_synonyms).intersection(rawterm.keys())
        for k in keys:
            for s in rawterm[k]:
                synonyms.add(Synonym(s, owl_synonyms[k]))
        return synonyms

    @classmethod
    def _extract_obo_relation(cls, rawterm):
        relations = {}
        if 'subClassOf' in rawterm:
            relations[Relationship('is_a')] = l = []
            l.extend(map(cls._get_id_from_url, rawterm.pop('subClassOf')))
        return relations

    @staticmethod
    def _relabel_to_obo(d):
        return {
            owl_to_obo.get(old_k, old_k): old_v
                for old_k, old_v in six.iteritems(d)
        }
