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

from six.moves import map

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

    @classmethod
    @nowarnings
    def parse(cls, stream):  # noqa: D102

        tree = etree.parse(stream)

        meta = cls._extract_resources(tree.find(OWL_ONTOLOGY))
        terms = collections.OrderedDict()

        for rawterm in cls._iter_rawterms(tree):
            term = Term(
                rawterm.pop('id'),
                rawterm.pop('label', [''])[0],
                rawterm.pop('definition', '') or rawterm.pop('IAO_0000115', ''),
                cls._extract_obo_relation(rawterm),
                cls._extract_obo_synonyms(rawterm),
                cls._relabel_to_obo(rawterm),
            )
            terms[term.id] = term
            # TODO: extract axioms through targeted XPaths

        terms = cls._annotate(terms, tree)
        meta = cls._relabel_to_obo(meta)
        meta.setdefault('imports', [])

        return meta, terms, set(meta['imports']), []

    @classmethod
    def _annotate(cls, terms, tree):

        for axiom in map(cls._extract_resources, tree.iterfind(OWL_AXIOM)):

            if not 'annotatedSource' in axiom:
                continue

            prop = cls._get_id_from_url(axiom['annotatedProperty'][0])
            src = cls._get_id_from_url(axiom['annotatedSource'][0])
            target = axiom.get('annotatedTarget')

            # annotated description with xrefs
            if prop == 'IAO:0000115':
                if src in terms:
                    terms[src].desc = Description(
                        ''.join(target or []), axiom.get('hasDbXref', [])
                    )

        return terms



    @staticmethod
    def _get_basename(tag):
        """Remove the namespace part of the tag.
        """
        return tag.split('}', 1)[-1]

    @staticmethod
    def _get_id_from_url(url):
        """Extract the ID of a term from an XML URL.
        """
        _id = url.split('#' if '#' in url else '/')[-1]
        return _id.replace('_', ':')

    @staticmethod
    def _extract_resources(elem):
        """Extract the children of an element as a key/value mapping.
        """
        resources = collections.defaultdict(list)
        for child in itertools.islice(elem.iter(), 1, None):
            try:
                basename = child.tag.split('}', 1)[-1]
                if child.text is not None:
                    child.text = child.text.strip()
                if child.text:
                    resources[basename].append(child.text)
                elif child.get(RDF_RESOURCE) is not None:
                    resources[basename].append(child.get(RDF_RESOURCE))
            except AttributeError:
                pass
        return dict(resources)

    @classmethod
    def _iter_rawterms(cls, tree):
        """Iterate through the raw terms (Classes) in the ontology.
        """
        for elem in tree.iterfind(OWL_CLASS):
            if RDF_ABOUT not in elem.keys():   # This avoids parsing a class
                continue                       # created by restriction
            rawterm = cls._extract_resources(elem)
            rawterm['id'] = cls._get_id_from_url(elem.get(RDF_ABOUT))
            yield rawterm

    @staticmethod
    def _extract_obo_synonyms(rawterm):
        """Extract the synonyms defined in the rawterm.
        """
        synonyms = set()
        # keys in rawterm that define a synonym
        keys = set(owl_synonyms).intersection(rawterm.keys())
        for k in keys:
            for s in rawterm[k]:
                synonyms.add(Synonym(s, owl_synonyms[k]))
        return synonyms

    @classmethod
    def _extract_obo_relation(cls, rawterm):
        """Extract the relationships defined in the rawterm.
        """
        relations = {}
        if 'subClassOf' in rawterm:
            relations[Relationship('is_a')] = l = []
            l.extend(map(cls._get_id_from_url, rawterm.pop('subClassOf')))
        return relations

    @staticmethod
    def _relabel_to_obo(d):
        """Change the keys of ``d`` to use Obo labels.
        """
        return {
            owl_to_obo.get(old_k, old_k): old_v
                for old_k, old_v in six.iteritems(d)
        }
