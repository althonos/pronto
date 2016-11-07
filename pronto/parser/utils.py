# coding: utf-8

class OboSection(object):
    meta    = 1
    typedef = 2
    term    = 3


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
}










class XMLNameSpacer(object):

    def __init__(self, name, nsmap=owl_ns):
        self.name = name
        self.absolute_name = nsmap[name]

    def __getattr__(self, attr):
        return "{{{}}}{}".format(self.absolute_name, attr)
