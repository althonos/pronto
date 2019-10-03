import datetime
import itertools
import re
import typing
import warnings
from typing import Dict, Optional

import dateutil.parser

from .base import BaseParser
from ..definition import Definition
from ..metadata import Metadata
from ..term import Term
from ..synonym import Synonym, SynonymData
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
    "dc": Namespace("http://purl.org/dc/elements/1.1/"),
    "doap": Namespace("http://usefulinc.com/ns/doap#"),
    "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
    "meta": Namespace("http://www.co-ode.org/ontologies/meta.owl#"),
    "obo": Namespace("http://purl.obolibrary.org/obo/"),
    "oboInOwl": Namespace("http://www.geneontology.org/formats/oboInOwl#"),
    "owl": Namespace("http://www.w3.org/2002/07/owl#"),
    "protege": Namespace("http://protege.stanford.edu/plugins/owl/protege#"),
    "rdf": Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdfs": Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
    "ubprop": Namespace("http://purl.obolibrary.org/obo/ubprop#"),
    "uberon": Namespace("http://purl.obolibrary.org/obo/uberon#"),
    "xsd": Namespace("http://www.w3.org/2001/XMLSchema#"),
}

_SYNONYMS = {
    _NS["oboInOwl"].raw("hasExactSynonym"): "EXACT",
    _NS["oboInOwl"].raw("hasBroadSynonym"): "BROAD",
    _NS["oboInOwl"].raw("hasNarrowSynonym"): "NARROW",
    _NS["oboInOwl"].raw("hasRelatedSynonym"): "RELATED",
}


class OwlXMLParser(BaseParser):

    # -- BaseParser interface ------------------------------------------------

    @classmethod
    def can_parse(cls, path, buffer):
        return buffer.lstrip().startswith((b"<?xml", b"<rdf:RDF", b"<owl:"))

    def parse_from(self, handle):
        # Load the XML document into an XML Element tree
        tree: etree.ElementTree = etree.parse(handle)

        # Keep a map of aliases (IRI -> local OBO id)
        aliases: Dict[str, str] = dict()

        # Load metadata from the `owl:Ontology` element and process imports
        owl_ontology = tree.find(_NS["owl"]["Ontology"])
        if owl_ontology is None:
            raise ValueError("could not find `owl:Ontology` element")
        self._extract_meta(owl_ontology)
        self.process_imports()

        # Parse typedef first to handle OBO shorthand renaming
        for prop in tree.iterfind(_NS["owl"]["ObjectProperty"]):
            self._extract_object_property(prop, aliases)
        for class_ in tree.iterfind(_NS["owl"]["Class"]):
            self._extract_term(class_, aliases)
        for axiom in tree.iterfind(_NS["owl"]["Axiom"]):
            self._process_axiom(axiom, aliases)

    # -- Helper methods ------------------------------------------------------

    def _compact_id(self, iri: str) -> str:
        """Compact an OBO identifier into a prefixed identifier.
        """
        match = re.match("^http://purl.obolibrary.org/obo/([^#_]+)_(.*)$", iri)
        if match is not None:
            return ":".join(match.groups())
        return iri

    def _extract_resource_pv(self, elem: etree.Element) -> ResourcePropertyValue:
        property = re.sub("{|}", "", elem.tag)
        resource = elem.attrib[_NS["rdf"]["resource"]]
        return ResourcePropertyValue(property, resource)

    def _extract_literal_pv(self, elem: etree.Element) -> LiteralPropertyValue:
        property = re.sub("{|}", "", elem.tag)
        datatype = elem.get(_NS["rdf"]["datatype"])
        if datatype is None:
            warnings.warn(f"{elem} contains text but no `xsd:datatype`", stacklevel=2)
            datatype = _NS["xsd"].raw("string")
        return LiteralPropertyValue(property, typing.cast(str, elem.text), datatype)

    def _extract_meta(self, elem: etree.Element):
        """Extract the metadata from an `owl:Ontology` element.
        """

        meta = self.ont.metadata = Metadata()
        if __debug__:
            if elem.tag != _NS["owl"]["Ontology"]:
                raise ValueError("expected `owl:Ontology` element")

        # extract OBO format version
        iri = elem.get(_NS["rdf"]["about"])
        if iri is not None:
            match = re.match("^http://purl.obolibrary.org/obo/(.*).(obo|owl)$", iri)
            meta.ontology = match.group(1) if match is not None else iri

        # extract metadta from child elements
        for child in elem:
            if child.tag == _NS["rdfs"]["comment"] and child.text is not None:
                meta.remarks.add(child.text)
            elif child.tag == _NS["oboInOwl"]["hasOBOFormatVersion"]:
                meta.format_version = child.text
            elif child.tag == _NS["oboInOwl"]["saved-by"]:
                meta.saved_by = child.text
            elif child.tag == _NS["oboInOwl"]["auto-generated-by"]:
                meta.auto_generated_by = child.text
            elif child.tag == _NS["oboInOwl"]["default-namespace"]:
                meta.default_namespace = child.text
            elif child.tag == _NS["oboInOwl"]["date"]:
                meta.date = datetime.datetime.strptime(child.text, "%d:%m:%Y %H:%M")
            elif child.tag == _NS["oboInOwl"]["NamespaceIdRule"]:
                meta.namespace_id_rule = child.text
            elif child.tag == _NS["owl"]["imports"]:
                meta.imports.add(child.get(_NS["rdf"]["resource"]))
            elif child.tag == _NS["owl"]["versionIRI"]:
                iri = child.get(_NS["rdf"]["resource"])
                if iri is not None and meta.ontology is not None:
                    rx = "^http://purl.obolibrary.org/obo/{0}/(.*)/{0}.(obo|owl)$"
                    match = re.match(rx.format(meta.ontology), iri)
                else:
                    match = None
                meta.data_version = iri if match is None else match.group(1)
            elif _NS["rdf"]["resource"] in child.attrib:
                meta.annotations.add(self._extract_resource_pv(child))
            elif child.text is not None:
                meta.annotations.add(self._extract_literal_pv(child))
            else:
                warnings.warn(f"unknown element in `owl:Ontology`: {child}")

    def _extract_term(self, elem: etree.Element, aliases: Dict[str, str]):
        """Extract the term from a `owl:Class` element.
        """
        if __debug__:
            if elem.tag != _NS["owl"]["Class"]:
                raise ValueError("expected `owl:Class` element")

        # only create the term if it is not a class by restriction
        iri = elem.get(_NS["rdf"]["about"])
        if iri is None:
            return None

        # attempt to extract the compact id of the term
        e = elem.find(_NS["oboInOwl"]["id"])
        id_ = e.text if e is not None and e.text else self._compact_id(iri)

        # get or create the term
        term = (self.ont.get_term if id_ in self.ont else self.ont.create_term)(id_)
        termdata = term._data()

        # extract attributes from annotation of the OWL class
        for child in elem:

            tag: str = child.tag
            text: Optional[str] = child.text
            attrib: Dict[str, str] = child.attrib

            if tag == _NS["rdfs"]["subClassOf"]:
                if _NS["rdf"]["resource"] in attrib:
                    iri = self._compact_id(attrib[_NS["rdf"]["resource"]])
                    termdata.relationships.setdefault("is_a", set()).add(iri)
                else:
                    pass  # TODO: relationships
            elif tag == _NS["oboInOwl"]["inSubset"]:
                iri = self._compact_id(attrib[_NS["rdf"]["resource"]])
                termdata.subsets.add(iri)
            elif tag == _NS["rdfs"]["comment"]:
                termdata.comment = text
            elif tag in (_NS["oboInOwl"]["created_by"], _NS["dc"]["creator"]):
                termdata.created_by = text
            elif tag in (_NS["oboInOwl"]["creation_date"], _NS["dc"]["date"]):
                termdata.creation_date = dateutil.parser.parse(text)
            elif tag == _NS["oboInOwl"]["hasOBONamespace"]:
                if text != self.ont.metadata.default_namespace:
                    termdata.namespace = text
            elif tag == _NS["rdfs"]["label"]:
                termdata.name = text
            elif tag == _NS["obo"]["IAO_0000115"] and text is not None:
                termdata.definition = Definition(text)
            elif tag == _NS["oboInOwl"]["hasExactSynonym"]:
                termdata.synonyms.add(SynonymData(text, scope="EXACT"))
            elif tag == _NS["oboInOwl"]["hasRelatedSynonym"]:
                termdata.synonyms.add(SynonymData(text, scope="RELATED"))
            elif tag == _NS["oboInOwl"]["hasBroadSynonym"]:
                termdata.synonyms.add(SynonymData(text, scope="BROAD"))
            elif tag == _NS["oboInOwl"]["hasNarrowSynonym"]:
                termdata.synonyms.add(SynonymData(text, scope="NARROW"))
            elif tag == _NS["owl"]["equivalentClass"] and text is not None:
                termdata.equivalent_to.add(self._compact_id(text))
            elif tag == _NS["owl"]["deprecated"]:
                termdata.obsolete = text == "true"
            elif tag == _NS["oboInOwl"]["hasDbXref"]:
                if text is not None:
                    termdata.xrefs.add(Xref(text))
                else:
                    termdata.xrefs.add(Xref(attrib[_NS["rdf"]["resource"]]))
            elif tag == _NS["oboInOwl"]["hasAlternativeId"]:
                termdata.alternate_ids.add(text)
            elif tag == _NS["owl"]["disjointWith"]:
                if _NS["rdf"]["resource"] in attrib:
                    iri = attrib[_NS["rdf"]["resource"]]
                    termdata.disjoint_from.add(self._compact_id(iri))
                else:
                    warnings.warn("`owl:disjointWith` element without `rdf:resource`")
            elif tag == _NS["obo"]["IAO_0100001"]:
                if _NS["rdf"]["resource"] in attrib:
                    iri = attrib[_NS["rdf"]["resource"]]
                    termdata.replaced_by.add(self._compact_id(iri))
                elif _NS["rdf"]["datatype"] in attrib:
                    termdata.replaced_by.add(self._compact_id(text))
                else:
                    warnings.warn("could not extract ID from IAO:0100001 annotation")
            elif tag != _NS["oboInOwl"]["id"]:
                if _NS["rdf"]["resource"] in attrib:
                    termdata.annotations.add(self._extract_resource_pv(child))
                elif _NS["rdf"]["datatype"] and text is not None:
                    termdata.annotations.add(self._extract_literal_pv(child))
                else:
                    warnings.warn(f"unknown element in `owl:Class`: {child}")

    def _extract_object_property(self, elem: etree.Element, aliases: Dict[str, str]):
        """Extract the object property from an `owl:ObjectProperty` element.
        """
        if __debug__:
            if elem.tag != _NS["owl"]["ObjectProperty"]:
                raise ValueError("expected `owl:ObjectProperty` element")

        # only create the term if it is not a restriction
        iri = elem.get(_NS["rdf"]["about"])
        if iri is None:  # ignore
            return None

        # attempt to extract the compact id of the term
        elem_id = elem.find(_NS["oboInOwl"]["id"])
        elem_sh = elem.find(_NS["oboInOwl"]["shorthand"])
        if elem_sh is not None and elem_sh.text is not None:
            id_ = aliases[iri] = elem_sh.text
        elif elem_id is not None and elem_id.text is not None:
            id_ = aliases[iri] = elem_id.text
        else:
            id_ = self._compact_id(iri)

        # Create the relationship
        rel = (
            self.ont.get_relationship
            if id_ in self.ont
            else self.ont.create_relationship
        )(id_)
        reldata = rel._data()

        # extract attributes from annotation of the OWL relationship
        for child in elem:
            if child.tag == _NS["rdfs"]["subObjectPropertyOf"]:
                if _NS["rdf"]["resource"] in child.attrib:
                    iri = self._compact_id(child.attrib[_NS["rdf"]["resource"]])
                    reldata.relationships.setdefault("is_a", set()).add(iri)
                else:
                    pass  # TODO: subclassing relationship for relationship
            elif child.tag == _NS["oboInOwl"]["inSubset"]:
                iri = self._compact_id(child.attrib[_NS["rdf"]["resource"]])
                reldata.subsets.add(iri)
            elif child.tag == _NS["rdf"]["type"]:
                resource = child.get(_NS["rdf"]["resource"])
                if resource == _NS["owl"].raw("TransitiveProperty"):
                    reldata.transitive = True
                elif resource == _NS["owl"].raw("ReflexiveProperty"):
                    reldata.reflexive = True
                elif resource == _NS["owl"].raw("SymmetricProperty"):
                    reldata.symmetric = True
                elif resource == _NS["owl"].raw("AsymmetricProperty"):
                    reldata.asymmetric = True
                elif resource == _NS["owl"].raw("FunctionalProperty"):
                    reldata.functional = True
                elif resource == _NS["owl"].raw("InverseFunctionalProperty"):
                    reldata.inverse_functional = True
            elif child.tag == _NS["rdfs"]["comment"]:
                reldata.comment = child.text
            elif child.tag in (_NS["oboInOwl"]["created_by"], _NS["dc"]["creator"]):
                reldata.created_by = child.text
            elif child.tag in (_NS["oboInOwl"]["creation_date"], _NS["dc"]["date"]):
                reldata.creation_date = dateutil.parser.parse(child.text)
            elif child.tag == _NS["oboInOwl"]["hasOBONamespace"]:
                if child.text != self.ont.metadata.default_namespace:
                    reldata.namespace = child.text
            elif child.tag == _NS["rdfs"]["label"]:
                reldata.name = child.text
            elif (
                child.tag == _NS["rdfs"]["domain"]
                and _NS["rdf"]["resource"] in child.attrib
            ):
                reldata.domain = self._compact_id(child.attrib[_NS["rdf"]["resource"]])
            elif (
                child.tag == _NS["rdfs"]["range"]
                and _NS["rdf"]["resource"] in child.attrib
            ):
                reldata.range = self._compact_id(child.attrib[_NS["rdf"]["resource"]])
            elif child.tag == _NS["obo"]["IAO_0000115"] and child.text is not None:
                reldata.definition = Definition(child.text)
            elif child.tag == _NS["oboInOwl"]["hasExactSynonym"]:
                reldata.synonyms.add(SynonymData(child.text, scope="EXACT"))
            elif child.tag == _NS["oboInOwl"]["hasRelatedSynonym"]:
                reldata.synonyms.add(SynonymData(child.text, scope="RELATED"))
            elif child.tag == _NS["oboInOwl"]["hasBroadSynonym"]:
                reldata.synonyms.add(SynonymData(child.text, scope="BROAD"))
            elif child.tag == _NS["oboInOwl"]["hasNarrowSynonym"]:
                reldata.synonyms.add(SynonymData(child.text, scope="NARROW"))
            elif child.tag == _NS["oboInOwl"]["is_cyclic"] and child.text is not None:
                reldata.cyclic = child.text == "true"
            elif child.tag == _NS["obo"]["IAO_0000427"] and child.text is not None:
                reldata.antisymmetric = child.text == "true"
            elif child.tag == _NS["owl"]["equivalentClass"] and child.text is not None:
                reldata.equivalent_to.add(self._compact_id(child.text))
            elif child.tag == _NS["owl"]["deprecated"]:
                reldata.obsolete = child.text == "true"
            elif child.tag == _NS["oboInOwl"]["hasDbXref"]:
                if child.text is not None:
                    reldata.xrefs.add(Xref(child.text))
                else:
                    reldata.xrefs.add(Xref(child.attrib[_NS["rdf"]["resource"]]))
            elif child.tag == _NS["oboInOwl"]["hasAlternativeId"]:
                reldata.alternate_ids.add(child.text)
            elif child.tag == _NS["obo"]["IAO_0100001"]:
                if _NS["rdf"]["resource"] in child.attrib:
                    iri = child.attrib[_NS["rdf"]["resource"]]
                    reldata.replaced_by.add(self._compact_id(iri))
                elif _NS["rdf"]["datatype"] in child.attrib:
                    reldata.replaced_by.add(self._compact_id(child.text))
                else:
                    warnings.warn("could not extract ID from IAO:0100001 annotation")
            elif child.tag not in (_NS["oboInOwl"]["id"], _NS["oboInOwl"]["shorthand"]):
                if _NS["rdf"]["resource"] in child.attrib:
                    reldata.annotations.add(self._extract_resource_pv(child))
                elif _NS["rdf"]["datatype"] and child.text is not None:
                    reldata.annotations.add(self._extract_literal_pv(child))
                else:
                    warnings.warn(f"unknown element in `owl:ObjectProperty`: {child}")

        return rel

    def _process_axiom(self, elem: etree.Element, aliases: Dict[str, str]):
        elem_source = elem.find(_NS["owl"]["annotatedSource"])
        elem_property = elem.find(_NS["owl"]["annotatedProperty"])
        elem_target = elem.find(_NS["owl"]["annotatedTarget"])

        for elem in (elem_source, elem_property, elem_target):
            if elem is None or _NS["rdf"]["resource"] not in elem.attrib:
                return

        property = elem_property.attrib[_NS["rdf"]["resource"]]
        if property == _NS["obo"].raw("IAO_0000115") and elem_target.text is not None:
            iri = elem_source.attrib[_NS["rdf"]["resource"]]
            resource = aliases.get(iri, iri)
            entity = self.ont[self._compact_id(resource)]

            entity.definition = d = Definition(elem_target.text)
            for child in elem.iterfind(_NS["oboInOwl"]["hasDbXref"]):
                if child.text is not None:
                    try:
                        d.xrefs.add(Xref(child.text))
                    except ValueError:
                        warnings.warn(f"could not parse Xref: {child.text!r}")
                elif _NS["rdf"]["resource"] in child.attrib:
                    d.xrefs.add(Xref(child.get(_NS["rdf"]["resource"])))
                else:
                    print(child, child.attrib)
                    warnings.warn("`oboInOwl:hasDbXref` element has no text")

        elif (
            property == _NS["oboInOwl"].raw("hasDbXref")
            and elem_target.text is not None
        ):
            iri = elem_source.attrib[_NS["rdf"]["resource"]]
            resource = aliases.get(iri, iri)
            entity = self.ont[self._compact_id(resource)]
            label = elem.find(_NS["rdfs"]["label"])

            if label is not None and label.text is not None:
                entity._data().xrefs.add(Xref(elem_target.text, label.text))
            else:
                entity._data().xrefs.add(Xref(elem_target.text))

        elif property in _SYNONYMS:
            iri = elem_source.attrib[_NS["rdf"]["resource"]]
            resource = aliases.get(iri, iri)
            entity = self.ont[self._compact_id(resource)]

            try:
                synonym = next(
                    s._data()
                    for s in entity.synonyms
                    if s.description == elem_target.text
                    and s.scope == _SYNONYMS[property]
                )
            except StopIteration:
                synonym = SynonymData(elem_target.text, scope=_SYNONYMS[property])
                entity._data().synonyms.add(synonym)
            for child in elem.iterfind(_NS["oboInOwl"]["hasDbXref"]):
                if child.text is not None:
                    synonym.xrefs.add(Xref(child.text))
                else:
                    warnings.warn("`oboInOwl:hasDbXref` element has no text")

        else:
            warnings.warn(f"unknown axiom property: {property!r}")
