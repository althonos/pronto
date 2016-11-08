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
#FEAT# DESERIALIZE AS DATES
#FEAT# import dateutil.parser

try:
    import lxml.etree as etree
except ImportError: # pragma: no-cover
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        import xml.etree.ElementTree as etree

from .              import Parser
from .utils         import owl_ns, owl_to_obo, OwlSection
from ..relationship import Relationship
from ..term         import Term
from ..utils        import explicit_namespace, format_accession


RDF_ABOUT = "{{{}}}{}".format(owl_ns['rdf'], 'about')
RDF_RESOURCE = "{{{}}}{}".format(owl_ns['rdf'], 'resource')
RDF_DATATYPE = "{{{}}}{}".format(owl_ns['rdf'], 'datatype')
OWL_CLASS = "{{{}}}{}".format(owl_ns['owl'], 'Class')
OWL_ONTOLOGY = "{{{}}}{}".format(owl_ns['owl'], 'Ontology')



class OwlXMLParser(Parser):

    ns = owl_ns

    def __init__(self):
        super(OwlXMLParser, self).__init__()
        self.extensions = ('.owl', '.ont')

    def hook(self, *args, **kwargs):
        """Returns True if this parser should be used.

        The current behaviour relies on filenames and file extension
        (.owl, .ont), but this is subject to change.
        """
        if 'force' in kwargs and kwargs['force']:
            return True
        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extensions)

    def parse(self, stream):
        raise NotImplementedError

    @staticmethod
    def _get_id_from_url(url):
        if '#' in url: _id = url.split('#')[-1]
        else: _id = url.split('/')[-1]
        return _id.replace('_', ':')


class OwlXMLTreeParser(OwlXMLParser):

    def parse(self, stream):

        tree = etree.parse(stream)

        meta, imports = self._parse_meta(tree)
        _rawterms = self._parse_terms(tree)
        del tree

        terms = self._classify(_rawterms)
        del _rawterms
        meta = self._relabel_owl_metadata(meta)

        return meta, terms, imports

    @staticmethod
    def _parse_meta(tree):

        imports = set()
        meta = collections.defaultdict(list)

        # tag.iter() starts on the element itself so we drop that
        for elem in itertools.islice(tree.find(OWL_ONTOLOGY).iter(), 1, None):

            basename = elem.tag.split('}', 1)[-1]
            if basename == 'imports':
                imports.add(next(six.itervalues(elem.attrib)))
            elif elem.text:
                meta[basename].append(elem.text)
            elif elem.get(RDF_RESOURCE) is not None:
                meta[basename].append(elem.get(RDF_RESOURCE))

        return meta, imports

    def _parse_terms(self, tree):

        _rawterms = []

        for rawterm in tree.iterfind(OWL_CLASS):

            if rawterm.get(RDF_ABOUT) is None:   # This avoids parsing a class
                continue                         # created by restriction

            _rawterms.append(collections.defaultdict(list))
            _rawterms[-1]['id'].append(self._get_id_from_url(rawterm.get(RDF_ABOUT)))

            for elem in itertools.islice(rawterm.iter(), 1, None):

                basename = elem.tag.split('}', 1)[-1]
                if elem.text:
                    _rawterms[-1][basename].append(elem.text)
                elif elem.get(RDF_RESOURCE) is not None:
                    _rawterms[-1][basename].append(elem.get(RDF_RESOURCE))

        return _rawterms

    def _classify(self, _rawterms):
        terms = {}
        for rawterm in _rawterms:
            _id = self._extract_obo_id(rawterm)
            name = self._extract_obo_name(rawterm)
            desc = self._extract_obo_desc(rawterm)
            relations = self._extract_obo_relation(rawterm)
            others = self._relabel_owl_properties(rawterm)
            terms[_id] = Term(_id, name, desc, dict(relations), others)
        return terms

    @staticmethod
    def _extract_obo_id(rawterm):
        # try:
        _id = rawterm['id'][0]
        del rawterm['id']
        return _id
        # except IndexError:
        #     print(rawterm)

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
        try: desc = rawterm['definition'][0]
        except IndexError:
            try: desc = rawterm['IAO_0000115'][0]
            except IndexError: pass
            finally: del rawterm['IAO_0000115']
        finally: del rawterm['definition']
        return desc

    def _extract_obo_relation(self, rawterm):
        relations = collections.defaultdict(list)

        for other in rawterm['subClassOf']:
            relations[Relationship('is_a')].append(
                self._get_id_from_url(other)
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

#OwlXMLTreeParser()


class _OwlXMLTarget(object):

    def __init__(self, meta=None, rawterms=None):
        self.ontology_tag = meta or collections.defaultdict(dict)
        self.classes = rawterms or []

        self.current_section = None
        self.current_tag = {'name':''}

    def start(self, tag, attrib):
        #print("start %s %r" % (tag, dict(attrib)))

        self.current_tag['name'] = tag

        if tag == OWL_ONTOLOGY and RDF_ABOUT in attrib:
            self.current_section = OwlSection.ontology
            self.ontology_tag['href'] = attrib[RDF_ABOUT]

        elif tag == OWL_CLASS:
            if RDF_ABOUT in attrib:
                self.in_fake_class = False
                self.current_section = OwlSection.classes
                self.classes.append(collections.defaultdict(dict))
                self.classes[-1]['id'] = {'data': [self._get_id_from_url(attrib[RDF_ABOUT])]}
            else:
                self.in_fake_class = True

        elif self.current_section == OwlSection.ontology:
            basename = self._get_basename(tag)
            try: self.ontology_tag[basename]['data'] = [attrib[RDF_RESOURCE]]
            except KeyError: pass
            try: self.ontology_tag[basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError: self.ontology_tag[basename]['datatype'] = ''

        elif self.current_section == OwlSection.classes:
            basename = self._get_basename(tag)
            try: self.classes[-1][basename] = {'data': [ attrib[RDF_RESOURCE] ]}
            except KeyError: pass
            #print(self.classes[-1])
            #if RDF_DATATYPE in attrib:
            try: self.classes[-1][basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError: pass
            #print(self.classes[-1][basename])

    def end(self, tag):
        #print("end %s" % tag)
        if tag == OWL_ONTOLOGY:
            self.current_section = None

        if tag == OWL_CLASS:
            if self.in_fake_class:
                self.current_section = OwlSection.classes
            else:
                self.current_section = None
            self.in_fake_class = False

    def data(self, data):
        #print("data %r" % data)
        data = data.strip()

        if data:

            if self.current_section == OwlSection.ontology:
                basename = self._get_basename(self.current_tag['name'])
                try: self.ontology_tag[basename]['data'].append(data)
                except KeyError: self.ontology_tag[basename]['data'] = [data]

            elif self.current_section == OwlSection.classes:
                basename = self._get_basename(self.current_tag['name'])
                if basename in self.classes[-1]:
                    if 'data' in self.classes[-1][basename]:
                        self.classes[-1][basename]['data'].append(data)
                    else:
                        self.classes[-1][basename]['data'] = [data]

            del data

    def comment(self, text):
        pass
        #print("comment %s" % text)

    def close(self):
        return self.ontology_tag, self.classes

    @staticmethod
    def _get_basename(tag):
        return tag.split('}', 1)[-1]

    @staticmethod
    def _get_id_from_url(url):
        if '#' in url: _id = url.split('#')[-1]
        else: _id = url.split('/')[-1]
        return _id.replace('_', ':')

class OwlXMLTargetParser(OwlXMLParser):

    def parse(self, stream):

        parser = etree.XMLParser(target=_OwlXMLTarget())

        while True:
            chunk = stream.read(1024)
            if not chunk: break
            parser.feed(chunk)

        meta, _rawterms = parser.close()
        del parser

        meta = self._relabel_owl_metadata(meta)
        terms = self._classify(_rawterms)
        del _rawterms

        try:
            imports = set(meta['imports'])
            del meta['imports']
        except KeyError:
            imports = set()

        return meta, terms, imports

    @staticmethod
    def _relabel_owl_metadata(meta):

        new_meta = {}

        for k,v in meta.items():

            try:
                if v['datatype'] == "{}string".format(owl_ns['xsd']):

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

    def _classify(self, rawterms):

        terms = {}

        #while True:
        for rawterm in rawterms:

            new_term = {}

            for k,v in rawterm.items():

                if not v:
                    continue

                try:

                    if 'datatype' in v and v['datatype'] == "{}string".format(owl_ns['xsd']) and k != "id":

                        try:
                            new_term[owl_to_obo[k]] = ''.join(rawterm[k]['data'])
                        except KeyError:
                            new_term[k] = ''.join(rawterm[k]['data'])

                    elif k == "subClassOf":
                        new_term[Relationship('is_a')] = [self._get_id_from_url(t) for t in rawterm['subClassOf']['data']]

                    else:
                        try:
                            new_term[owl_to_obo[k]] = rawterm[k]['data'][0]
                        except KeyError:
                            new_term[k] = rawterm[k]['data'][0]

                except TypeError:
                    pass

            del rawterm

            _id = new_term['id']
            del new_term['id']

            try:
                name = new_term['label']
                del new_term['label']
            except KeyError:
                name = ''


            try:
                desc = new_term['IAO_0000115']
                del new_term['IAO_0000115']
            except KeyError:
                desc = ''

            relations = {}
            try:
                relations[Relationship('is_a')] = new_term[Relationship('is_a')]
                del new_term[Relationship('is_a')]
            except KeyError:
                pass

            terms[_id] = Term(_id, name, desc, relations, new_term)
            del new_term

        return terms

OwlXMLTargetParser()
