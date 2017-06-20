"""
pronto.parser.owl
=================

This module defines the Owl parsing method.
"""
from __future__ import unicode_literals

import itertools
import collections
import six
#FEAT# DESERIALIZE AS DATES
#FEAT# import dateutil.parser

try:
    import lxml.etree as etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

from .              import Parser
from .utils         import owl_ns, owl_to_obo, OwlSection
from ..relationship import Relationship
from ..synonym      import Synonym
from ..term         import Term
from ..utils        import nowarnings


RDF_ABOUT = "{{{}}}{}".format(owl_ns['rdf'], 'about')
RDF_RESOURCE = "{{{}}}{}".format(owl_ns['rdf'], 'resource')
RDF_DATATYPE = "{{{}}}{}".format(owl_ns['rdf'], 'datatype')
OWL_CLASS = "{{{}}}{}".format(owl_ns['owl'], 'Class')
OWL_ONTOLOGY = "{{{}}}{}".format(owl_ns['owl'], 'Ontology')

_owl_synonyms_map = {"hasExactSynonym": "EXACT", "hasNarrowSynonym": "NARROW",
                     "hasBroadSynonym": "BROAD", "hasRelatedSynonym": "RELATED",
                     "hasSynonym": "RELATED"}

class OwlXMLParser(Parser):
    """Abstract OwlXMLParser.

    Provides functions common to all OwlXMLParsers, such as a function to
    extract ontology terms id from a url, or the common :obj:`hook` method.
    """

    ns = owl_ns
    extensions = ('.owl', '.ont', '.owl.gz', '.ont.gz')

    @classmethod
    def hook(cls, force=False, path=None, lookup=None):
        """Returns True if this parser should be used.

        The current behaviour relies on filenames and file extension
        (.owl, .ont), but this is subject to change.
        """
        if force:
            return True
        if path is not None and path.endswith(cls.extensions):
            return True
        if lookup is not None and lookup.startswith(b'<?xml'):
            return True
        return False


    @classmethod
    def parse(self, stream):
        """Parse the stream.

        This method is a classmethod, so it can be used to simply extract
        metadata, terms and imports of a file-like object without creating
        an ontology.

        Example:
            >>> fromp

        Parameters:
            stream (file handle): a binary stream of the file to parse

        Returns:
            dict: a dictionary containing the metadata headers
            dict: a dictionnary containing the terms
            set:  a set containing the imports
        """
        raise NotImplementedError

    @staticmethod
    def _get_id_from_url(url):
        if '#' in url:
            _id = url.split('#')[-1]
        else:
            _id = url.split('/')[-1]
        return _id.replace('_', ':')


class OwlXMLTreeParser(OwlXMLParser):

    @classmethod
    @nowarnings
    def parse(cls, stream):

        parser = etree.XMLParser()

        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            parser.feed(chunk)

        tree = parser.close()
        del parser

        meta, imports = cls._parse_meta(tree)
        _rawterms = cls._parse_terms(tree)
        del tree

        terms = cls._classify(_rawterms)
        del _rawterms
        meta = cls._relabel_owl_metadata(meta)

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
    def _parse_terms(cls, tree):

        _rawterms = []

        for rawterm in tree.iterfind(OWL_CLASS):

            if rawterm.get(RDF_ABOUT) is None:   # This avoids parsing a class
                continue                         # created by restriction

            _rawterms.append(collections.defaultdict(list))
            _rawterms[-1]['id'].append(cls._get_id_from_url(rawterm.get(RDF_ABOUT)))

            for elem in itertools.islice(rawterm.iter(), 1, None):
                try:
                    basename = elem.tag.split('}', 1)[-1]
                    if elem.text is not None:
                        elem.text = elem.text.strip()
                    if elem.text:
                        _rawterms[-1][basename].append(elem.text)
                    elif elem.get(RDF_RESOURCE) is not None:
                        _rawterms[-1][basename].append(elem.get(RDF_RESOURCE))
                except AttributeError:
                    pass

        return _rawterms

    @classmethod
    def _classify(cls, _rawterms):
        terms = collections.OrderedDict()
        for rawterm in _rawterms:
            _id = cls._extract_obo_id(rawterm)
            name = cls._extract_obo_name(rawterm)
            desc = cls._extract_obo_desc(rawterm)
            relations = cls._extract_obo_relation(rawterm)
            synonyms = cls._extract_obo_synonyms(rawterm)
            others = cls._relabel_owl_properties(rawterm)
            terms[_id] = Term(_id, name, desc, dict(relations), synonyms, others)
        return terms

    @staticmethod
    def _extract_obo_synonyms(rawterm):
        synonyms = set()
        for k,v in six.iteritems(_owl_synonyms_map):
            try:
                for s in rawterm[k]:
                    synonyms.add(Synonym(s, v))
                del rawterm[k]
            except KeyError:
                pass
        return synonyms

    @staticmethod
    def _extract_obo_id(rawterm):
        _id = rawterm['id'][0]
        del rawterm['id']
        return _id

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
    def _extract_obo_desc(rawterm):
        desc = ''
        try:
            desc = rawterm['definition'][0]
        except IndexError:
            try:
                desc = rawterm['IAO_0000115'][0]
            except IndexError:
                pass
            finally:
                del rawterm['IAO_0000115']
        finally:
            del rawterm['definition']
        return desc

    @classmethod
    def _extract_obo_relation(cls, rawterm):
        relations = collections.defaultdict(list)

        for other in rawterm['subClassOf']:
            relations[Relationship('is_a')].append(
                cls._get_id_from_url(other)
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

    @staticmethod
    def _relabel_owl_metadata(meta):
        new_meta = {}
        for old_k, old_v in six.iteritems(meta):
            try:
                new_meta[owl_to_obo[old_k]] = old_v
            except KeyError:
                new_meta[old_k] = old_v
        del meta
        return new_meta

OwlXMLTreeParser()


class _OwlXMLTarget(object):

    def __init__(self, meta=None, rawterms=None):
        self.ontology_tag = meta or collections.defaultdict(dict)
        self.classes = rawterms or []

        self.current_section = None
        self.current_tag = {'name':''}
        self.current_depth = 0

    def start(self, tag, attrib):
        self.current_depth += 1
        self.current_tag['name'] = tag

        if tag == OWL_ONTOLOGY and RDF_ABOUT in attrib:
            self.current_section = OwlSection.ontology
            self.ontology_tag['href'] = attrib[RDF_ABOUT]

        elif tag == OWL_CLASS:
            if RDF_ABOUT in attrib:
                self.current_section = OwlSection.classes
                self.classes.append(collections.defaultdict(dict))
                self.classes[-1]['id'] = {
                    'data': [OwlXMLParser._get_id_from_url(attrib[RDF_ABOUT])],
                }

        elif self.current_section == OwlSection.ontology:
            basename = self._get_basename(tag)
            try:
                self.ontology_tag[basename]['data'] = [attrib[RDF_RESOURCE]]
            except KeyError:
                pass
            try:
                self.ontology_tag[basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError:
                self.ontology_tag[basename]['datatype'] = ''

        elif self.current_section == OwlSection.classes:
            basename = self._get_basename(tag)
            try:
                self.classes[-1][basename] = {
                    'data': [attrib[RDF_RESOURCE]],
                }
            except KeyError:
                pass
            try:
                self.classes[-1][basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError:
                pass

    def end(self, tag):
        self.current_depth -= 1

        if tag == OWL_ONTOLOGY:
            self.current_section = None

        if tag == OWL_CLASS:
            if self.current_depth > 1:
                self.current_section = OwlSection.classes
            else:
                self.current_section = None

    def data(self, data):
        data = data.strip()

        if data:

            if self.current_section == OwlSection.ontology:
                basename = self._get_basename(self.current_tag['name'])
                try:
                    self.ontology_tag[basename]['data'].append(data)#' {}'.format(data).strip())
                except KeyError:
                    self.ontology_tag[basename]['data'] = [data]

            elif self.current_section == OwlSection.classes:
                basename = self._get_basename(self.current_tag['name'])
                if basename in self.classes[-1]:
                    if 'data' in self.classes[-1][basename]:
                        self.classes[-1][basename]['data'].append(data)#' {}'.format(data).strip())
                    else:
                        self.classes[-1][basename]['data'] = [data]

            del data

    # def comment(self, text):
    #     pass

    def close(self):
        return self.ontology_tag, self.classes

    @staticmethod
    def _get_basename(tag):
        return tag.split('}', 1)[-1]

class OwlXMLTargetParser(OwlXMLParser):

    @classmethod
    @nowarnings
    def parse(cls, stream):

        parser = etree.XMLParser(target=_OwlXMLTarget())

        while True:
            chunk = stream.read(1024)
            if not chunk:
                break
            parser.feed(chunk)

        meta, _rawterms = parser.close()
        del parser

        meta = cls._relabel_owl_metadata(meta)
        terms = cls._classify(_rawterms)
        del _rawterms

        try:
            imports = set(meta['import'])
        except KeyError:
            imports = set()

        return meta, terms, imports

    @staticmethod
    def _relabel_owl_metadata(meta):

        new_meta = {}

        for k,v in meta.items():

            try:
                if v['datatype'] == "{}string".format(owl_ns['xsd']) and k not in {'hasDbXref', 'subClassOf'}:

                    try:
                        new_meta[owl_to_obo[k]] = ''.join(meta[k]['data'])
                    except KeyError:
                        new_meta[k] = ''.join(meta[k]['data'])

                else:
                    try:
                        new_meta[owl_to_obo[k]] = meta[k]['data']
                    except KeyError:
                        new_meta[k] = meta[k]['data']

                #FEAT# DESERIALIZE AS DATES
                #FEAT# elif v['datatype'] == "{xsd}dateTime".format_map(owl_ns):
                #FEAT#     self.ontology_tag[k]['data'] = dateutil.parser.parse(self.ontology_tag[k]['data'][0])

            except TypeError:
                pass

        return new_meta

    @classmethod
    def _classify(cls, rawterms):

        terms = collections.OrderedDict()

        #while True:
        for rawterm in rawterms:

            new_term = {}
            synonyms = set()

            for k,v in rawterm.items():

                if not v:
                    continue

                try:

                    # if 'datatype' in v and v['datatype'] == "{}string".format(owl_ns['xsd']) and k != "id":

                    #     try:
                    #         new_term[owl_to_obo[k]] = ''.join(rawterm[k]['data'])
                    #     except KeyError:
                    #         new_term[k] = ''.join(rawterm[k]['data'])

                    if k == "subClassOf":
                        new_term[Relationship('is_a')] = [cls._get_id_from_url(t) for t in rawterm[k]['data']]

                    elif k in _owl_synonyms_map:
                        for s in v['data']:
                            synonyms.add(Synonym(s, _owl_synonyms_map[k]))
                    else:
                        try:
                            new_term[owl_to_obo[k]] = rawterm[k]['data']
                        except KeyError:
                            new_term[k] = rawterm[k]['data']

                except TypeError:
                    pass

            del rawterm

            _id = new_term['id'][0]
            del new_term['id']

            try:
                name = new_term['label'][0]
                del new_term['label']
            except KeyError:
                name = ''


            try:
                desc = ''.join(new_term['IAO_0000115'])
                del new_term['IAO_0000115']
            except KeyError:
                desc = ''

            relations = {}
            try:
                relations[Relationship('is_a')] = new_term[Relationship('is_a')]
                del new_term[Relationship('is_a')]
            except KeyError:
                pass

            terms[_id] = Term(_id, name, desc, relations, synonyms, new_term)
            del new_term
            del synonyms

        return terms

OwlXMLTargetParser()
