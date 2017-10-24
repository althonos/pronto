# coding: utf-8
"""miscellaneous parsing utilities.

This module defines mapping to convert metadata from obo to owl and
owl to obo, as well as enums to state the section of the ontology
the parser is currently looking at.
"""
from __future__ import unicode_literals

import six

try:                        # Use enums if possible to improve
    from enum import Enum   # output but don't have to dl enum32
except ImportError:         # backport as it's not that important
    Enum = object           # enough to truly depend on it


class OboSection(Enum):  # noqa: D101
    meta    = 1
    typedef = 2
    term    = 3

class OwlSection(Enum):  # noqa: D101
    ontology = 1
    classes  = 2
    axiom    = 3


owl_ns = {
    'dc':       "http://purl.org/dc/elements/1.1/",
    'doap':     "http://usefulinc.com/ns/doap#",
    'foaf':     "http://xmlns.com/foaf/0.1/",
    'meta':     "http://www.co-ode.org/ontologies/meta.owl#",
    'obo':      "http://purl.obolibrary.org/obo/",
    'oboInOwl': "http://www.geneontology.org/formats/oboInOwl#",
    'owl':      "http://www.w3.org/2002/07/owl#",
    'protege':  "http://protege.stanford.edu/plugins/owl/protege#",
    'rdf':      "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    'rdfs':     "http://www.w3.org/2000/01/rdf-schema#",
    'skos':     "http://www.w3.org/2004/02/skos/core#",
    'ubprop':   "http://purl.obolibrary.org/obo/ubprop#",
    'uberon':   "http://purl.obolibrary.org/obo/uberon#",
    'xsd':      "http://www.w3.org/2001/XMLSchema#",
}

owl_to_obo = {
    'hasDbXref': 'xref',
    'equivalentClass': 'equivalent_to',
    'inSubset': 'subset',
    'hasOBONamespace': 'namespace',
    'hasOBOFormatVersion': 'format-version',
    'imports': 'import',

    #FEAT# Translate Information Ontology
    #FEAT# 'IAO_0000115': 'definition',

    #FEAT# Extract Owl defined Relationship
    #FEAT# 'is_metadata_tag': 'is_metadata_tag',
}

obo_to_owl = {
    v:k for k,v in six.iteritems(owl_to_obo)
}

owl_synonyms = {
    "hasExactSynonym": "EXACT",
    "hasNarrowSynonym": "NARROW",
    "hasBroadSynonym": "BROAD",
    "hasRelatedSynonym": "RELATED",
    "hasSynonym": "RELATED"
}
