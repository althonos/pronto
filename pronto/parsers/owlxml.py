import datetime
import itertools
import re
import typing
import warnings
from typing import Optional

import dateutil.parser

from .base import BaseParser
from ..definition import Definition
from ..metadata import Metadata
from ..term import Term
from ..synonym import Synonym, _SynonymData
from ..relationship import Relationship
from ..pv import ResourcePropertyValue, LiteralPropertyValue
from ..xref import Xref
from ..utils.impl import etree

if typing.TYPE_CHECKING:
    from ..ontology import Ontology


class Namespace(object):

    def __init__(self, base: str):
        self.base = base

    def __getitem__(self, item: str) -> str:
        return f"{{{self.base}}}{item}"

    def raw(self, item: str) -> str:
        return f"{self.base}{item}"


_NS = {
    'dc':       Namespace("http://purl.org/dc/elements/1.1/"),
    'doap':     Namespace("http://usefulinc.com/ns/doap#"),
    'foaf':     Namespace("http://xmlns.com/foaf/0.1/"),
    'meta':     Namespace("http://www.co-ode.org/ontologies/meta.owl#"),
    'obo':      Namespace("http://purl.obolibrary.org/obo/"),
    'oboInOwl': Namespace("http://www.geneontology.org/formats/oboInOwl#"),
    'owl':      Namespace("http://www.w3.org/2002/07/owl#"),
    'protege':  Namespace("http://protege.stanford.edu/plugins/owl/protege#"),
    'rdf':      Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    'rdfs':     Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    'skos':     Namespace("http://www.w3.org/2004/02/skos/core#"),
    'ubprop':   Namespace("http://purl.obolibrary.org/obo/ubprop#"),
    'uberon':   Namespace("http://purl.obolibrary.org/obo/uberon#"),
    'xsd':      Namespace("http://www.w3.org/2001/XMLSchema#"),
}

_SYNONYMS = {
    _NS['oboInOwl'].raw('hasExactSynonym'): 'EXACT',
    _NS['oboInOwl'].raw('hasBroadSynonym'): 'BROAD',
    _NS['oboInOwl'].raw('hasNarrowSynonym'): 'NARROW',
    _NS['oboInOwl'].raw('hasRelatedSynonym'): 'RELATED',
}


class OwlXMLParser(BaseParser):

    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith((b'<?xml', b'<rdf:RDF', b'<owl:'))

    def parse_from(self, handle):

        # Load the XML document into an XML Element tree
        tree: etree.ElementTree = etree.parse(handle)

        # Load metadata from the `owl:Ontology` element and process imports
        owl_ontology = tree.find(_NS['owl']['Ontology'])
        if owl_ontology is None:
            raise ValueError("could not find `owl:Ontology` element")
        self._extract_meta(owl_ontology)
        self.process_imports()

        # TODO
        # for class_ in tree.iterfind(_NS['owl']['ObjectProperty']):
        #     self._extract_relationship(class_)
        for class_ in tree.iterfind(_NS['owl']['Class']):
            self._extract_term(class_)
        for axiom in tree.iterfind(_NS['owl']['Axiom']):
            self._process_axiom(axiom)

    def _compact_id(self, iri: str) -> str:
        match = re.match('^http://purl.obolibrary.org/obo/([^_]+)_(.*)$', iri)
        if match is not None:
            return ':'.join(match.groups())
        return iri

    def _extract_resource_pv(self, elem: etree.Element) -> ResourcePropertyValue:
        property = re.sub('{|}', '', elem.tag)
        resource = elem.attrib[_NS['rdf']['resource']]
        return ResourcePropertyValue(property, resource)

    def _extract_literal_pv(self, elem: etree.Element) -> LiteralPropertyValue:
        property = re.sub('{|}', '', elem.tag)
        datatype = elem.get(_NS['rdf']['datatype'])
        if datatype is None:
            warnings.warn(f'{elem} contains text but no `xsd:datatype`', stacklevel=2)
            datatype = _NS['xsd'].raw('string')
        return LiteralPropertyValue(property, typing.cast(str, elem.text), datatype)

    def _extract_meta(self, elem: etree.Element):
        """Extract the metadata from an `owl:Ontology` element.
        """

        meta = self.ont.metadata = Metadata()
        if __debug__:
            if elem.tag != _NS['owl']['Ontology']:
                raise ValueError("expected `owl:Ontology` element")

        # extract OBO format version
        iri = elem.get(_NS['rdf']['about'])
        if iri is not None:
            match = re.match('^http://purl.obolibrary.org/obo/(.*).(obo|owl)$', iri)
            meta.ontology = match.group(1) if match is not None else iri

        # extract metadta from child elements
        for child in elem:
            if child.tag == _NS['rdfs']['comment'] and child.text is not None:
                meta.remarks.add(child.text)
            elif child.tag == _NS['oboInOwl']['hasOBOFormatVersion']:
                meta.format_version = child.text
            elif child.tag == _NS['oboInOwl']['saved-by']:
                meta.saved_by = child.text
            elif child.tag == _NS['oboInOwl']['auto-generated-by']:
                meta.auto_generated_by = child.text
            elif child.tag == _NS['oboInOwl']['default-namespace']:
                meta.default_namespace = child.text
            elif child.tag == _NS['oboInOwl']['date']:
                meta.date = datetime.datetime.strptime(child.text, '%d:%m:%Y %H:%M')
            elif child.tag == _NS['oboInOwl']['NamespaceIdRule']:
                meta.namespace_id_rule = child.text
            elif child.tag == _NS['owl']['imports']:
                meta.imports.add(child.get(_NS['rdf']['resource']))
            elif child.tag == _NS['owl']['versionIRI']:
                iri = child.get(_NS['rdf']['resource'])
                if iri is not None and meta.ontology is not None:
                    rx = "^http://purl.obolibrary.org/obo/{0}/(.*)/{0}.(obo|owl)$"
                    match = re.match(rx.format(meta.ontology), iri)
                else:
                    match = None
                meta.data_version = iri if match is None else match.group(1)
            elif _NS['rdf']['resource'] in child.attrib:
                meta.annotations.add(self._extract_resource_pv(child))
            elif child.text is not None:
                meta.annotations.add(self._extract_literal_pv(child))
            else:
                warnings.warn(f'unknown element in `owl:Ontology`: {child}')

    def _extract_term(self, elem: etree.Element):
        if __debug__:
            if elem.tag != _NS['owl']['Class']:
                raise ValueError("expected `owl:Class` element")

        # only create the term if it is not a restriction
        iri = elem.get(_NS['rdf']['about'])
        if iri is None: # ignore
            return None

        # attempt to extract the compact id of the term
        e = elem.find(_NS['oboInOwl']['id'])
        id_ = e.text if e is not None and e.text else self._compact_id(iri)
        term = self.ont.get_term(id_) if id_ in self.ont else self.ont.create_term(id_)
        termdata = term._data()

        # extract attributes
        for child in elem:
            if child.tag == _NS['rdfs']['subClassOf']:
                if _NS['rdf']['resource'] in child.attrib:
                    iri = self._compact_id(child.attrib[_NS['rdf']['resource']])
                    termdata.relationships.setdefault("is_a", set()).add(iri)
                else:
                    pass # TODO: subclassing relationship for relationship
            elif child.tag == _NS['oboInOwl']['inSubset']:
                iri = self._compact_id(child.attrib[_NS['rdf']['resource']])
                termdata.subsets.add(iri)
            elif child.tag == _NS['rdfs']['comment']:
                term.comment = child.text
            elif child.tag in (_NS['oboInOwl']['created_by'], _NS['dc']['creator']):
                term.created_by = child.text
            elif child.tag in (_NS['oboInOwl']['creation_date'], _NS['dc']['date']):
                term.creation_date = dateutil.parser.parse(child.text)
            elif child.tag == _NS['oboInOwl']['hasOBONamespace']:
                if child.text != self.ont.metadata.default_namespace:
                    term.namespace = child.text
            elif child.tag == _NS["rdfs"]["label"]:
                term.name = child.text
            elif child.tag == _NS['obo']['IAO_0000115'] and child.text is not None:
                term.definition = Definition(child.text)
            elif child.tag == _NS['oboInOwl']['hasExactSynonym']:
                termdata.synonyms.add(_SynonymData(child.text, scope="EXACT"))
            elif child.tag == _NS['oboInOwl']['hasRelatedSynonym']:
                termdata.synonyms.add(_SynonymData(child.text, scope="RELATED"))
            elif child.tag == _NS['oboInOwl']['hasBroadSynonym']:
                termdata.synonyms.add(_SynonymData(child.text, scope="BROAD"))
            elif child.tag == _NS['oboInOwl']['hasNarrowSynonym']:
                termdata.synonyms.add(_SynonymData(child.text, scope="NARROW"))
            elif child.tag == _NS['owl']['equivalentClass'] and child.text is not None:
                termdata.equivalent_to.add(self._compact_id(child.text))
            elif child.tag == _NS['owl']['deprecated']:
                term.obsolete = child.text == "true"
            elif child.tag == _NS['oboInOwl']['hasDbXref'] and child.text is not None:
                termdata.xrefs.add(Xref(child.text))
            elif child.tag == _NS['oboInOwl']['hasAlternativeId']:
                termdata.alternate_ids.add(child.text)
            elif child.tag == _NS['owl']['disjointWith']:
                if _NS['rdf']['resource'] in child.attrib:
                    iri = child.attrib[_NS['rdf']['resource']]
                    termdata.disjoint_from.add(self._compact_id(iri))
                else:
                    warnings.warn('`owl:disjointWith` element without `rdf:resource`')
            elif child.tag == _NS['obo']['IAO_0100001']:
                if _NS['rdf']['resource'] in child.attrib :
                    iri = child.attrib[_NS['rdf']['resource']]
                    termdata.replaced_by.add(self._compact_id(iri))
                elif _NS['rdf']['datatype'] in child.attrib:
                    termdata.replaced_by.add(self._compact_id(child.text))
                else:
                    warnings.warn("could not extract ID from IAO:0100001 annotation")
            elif child.tag != _NS['oboInOwl']['id']:
                if _NS['rdf']['resource'] in child.attrib:
                    termdata.annotations.add(self._extract_resource_pv(child))
                elif _NS['rdf']['datatype'] and child.text is not None:
                    termdata.annotations.add(self._extract_literal_pv(child))
                else:
                    warnings.warn(f'unknown element in `owl:Class`: {child}')

    def _process_axiom(self, elem: etree.Element):
        _resource = _NS['rdf']['resource']

        elem_source = elem.find(_NS['owl']['annotatedSource'])
        elem_property = elem.find(_NS['owl']['annotatedProperty'])
        elem_target = elem.find(_NS['owl']['annotatedTarget'])

        if elem_property is None or _resource not in elem_property.attrib:
            return
        if elem_source is None or _resource not in elem_source.attrib:
            return
        if elem_target is None:
            return

        property = elem_property.attrib[_resource]
        if property == _NS['obo'].raw("IAO_0000115") and elem_target.text is not None:
            entity = self.ont[self._compact_id(elem_source.attrib[_resource])]
            entity.definition = d = Definition(elem_target.text)
            for child in elem.iterfind(_NS['oboInOwl']['hasDbXref']):
                if child.text is not None:
                    d.xrefs.add(Xref(child.text))
                else:
                    warnings.warn("`oboInOwl:hasDbXref` element has no text")

        elif property == _NS['oboInOwl'].raw('hasDbXref') and elem_target.text is not None:
            entity = self.ont[self._compact_id(elem_source.attrib[_resource])]
            label = elem.find(_NS['rdfs']['label'])
            if label is not None and label.text is not None:
                entity._data().xrefs.add(Xref(elem_target.text, label.text))
            else:
                entity._data().xrefs.add(Xref(elem_target.text))

        elif property in _SYNONYMS:
            entity = self.ont[self._compact_id(elem_source.attrib[_resource])]
            try:
                s = next(s for s in entity.synonyms if s.description == elem_target.text)
                synonym = s._data()
                if synonym.scope != _SYNONYMS[property]:
                    msg = "synonym {} contains different scopes in axiom and class: {} != {}"
                    raise ValueError(msg.format(elem_target.text, synonym.scope, _SYNONYMS[property]))
            except StopIteration:
                synonym = _SynonymData(elem_target.text, scope=_SYNONYMS[property])
                entity._data().synonyms.add(synonym)
            for child in elem.iterfind(_NS['oboInOwl']['hasDbXref']):
                if child.text is not None:
                    synonym.xrefs.add(Xref(child.text))
                else:
                    warnings.warn("`oboInOwl:hasDbXref` element has no text")

        else:
            warnings.warn(f"unknown axiom property: {property}")
