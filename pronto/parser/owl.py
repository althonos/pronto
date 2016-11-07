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
    from lxml.etree import XMLSyntaxError as ParseError
except ImportError: # pragma: no cover
    try:
        import xml.etree.cElementTree as etree
        from xml.etree.cElementTree import ParseError
    except ImportError:
        import xml.etree.ElementTree as etree
        from xml.etree.ElementTree import ParseError

from .              import Parser
from .utils         import owl_ns, XMLNameSpacer, owl_to_obo, OwlSection
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

        owl = XMLNameSpacer('owl')
        rdf = XMLNameSpacer('rdf')

        # tag.iter() starts on the element itself so we drop that
        for elem in itertools.islice(tree.find(owl.Ontology).iter(), 1, None):

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



class _OwlXMLTarget(object):


    owl = XMLNameSpacer('owl')

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

        elif tag == OWL_CLASS and RDF_ABOUT in attrib:
            self.current_section = OwlSection.classes
            self.classes.append(collections.defaultdict(dict))
            self.classes[-1]['id'] = {'data': [self._get_id_from_url(attrib[RDF_ABOUT])]}

        elif self.current_section == OwlSection.ontology:
            basename = self._get_basename(tag)
            try: self.ontology_tag[basename]['data'] = [attrib[RDF_RESOURCE]]
            except KeyError: pass
            try: self.ontology_tag[basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError: self.ontology_tag[basename]['datatype'] = ''

        elif self.current_section == OwlSection.classes:
            basename = self._get_basename(tag)
            try: self.classes[-1][basename]['data'].append(attrib[RDF_RESOURCE])
            except KeyError: pass
            #print(self.classes[-1])
            #if RDF_DATATYPE in attrib:
            try: self.classes[-1][basename]['datatype'] = attrib[RDF_DATATYPE]
            except KeyError: pass
            #print(self.classes[-1][basename])

    def end(self, tag):
        #print("end %s" % tag)
        if tag == OWL_ONTOLOGY:
            self.current_section = {'name': ''}

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

            #     try: self.classes[-1][basename]['data'].append(data)
            #     except KeyError: self.classes[-1][basename]['data'] = [data]

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

class OwlXMLTargetedParser(OwlXMLParser):

    def parse(self, stream):


        parser = etree.XMLParser(target = _OwlXMLTarget())

        self.meta, self._rawterms = etree.XML(stream.read(), parser)

        self._relabel_owl_metadata()
        self._classify()

        self.imports = set(self.meta['imports'])
        del self.meta['imports']

        return self.meta, self.terms, self.imports

    def _relabel_owl_metadata(self):

        new_meta = {}

        for k,v in self.meta.items():

            try:
                if v['datatype'] == "{}string".format(owl_ns['xsd']):

                    try:
                        new_meta[owl_to_obo[k]] = ''.join(self.meta[k]['data'])
                    except KeyError:
                        new_meta[k] = ''.join(self.meta[k]['data'])

                else:
                    try:
                        new_meta[owl_to_obo[k]] = self.meta[k]['data']
                    except KeyError:
                        new_meta[k] = self.meta[k]['data']

                #FEAT# DESERIALIZE AS DATES
                #FEAT# elif v['datatype'] == "{xsd}dateTime".format_map(owl_ns):
                #FEAT#     self.ontology_tag[k]['data'] = dateutil.parser.parse(self.ontology_tag[k]['data'][0])

            except TypeError:
                pass

        del self.meta
        self.meta = new_meta

    def _classify(self):


        while True:

            try:
                rawterm = self._rawterms.pop()
            except IndexError:
                break

            new_term = {}

            for k,v in rawterm.items():

                if not v:
                    continue

                try:

                    if 'datatype' in v and v['datatype'] == "{}string".format(owl_ns['xsd']):

                        try:
                            new_term[owl_to_obo[k]] = ''.join(rawterm[k]['data'])
                        except KeyError:
                            new_term[k] = ''.join(rawterm[k]['data'])

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

            self.terms[_id] = Term(_id, name, desc, new_term)

OwlXMLTargetedParser()
