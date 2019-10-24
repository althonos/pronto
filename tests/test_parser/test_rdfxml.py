import io
import unittest
import warnings
import xml.etree.ElementTree as etree

import pronto



class TestRdfXMLParser(unittest.TestCase):

    @staticmethod
    def get_ontology(content):
        xml = f"""
        <rdf:RDF xmlns="http://purl.obolibrary.org/obo/TEMP#"
             xml:base="http://purl.obolibrary.org/obo/TEMP"
             xmlns:owl="http://www.w3.org/2002/07/owl#"
             xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:xml="http://www.w3.org/XML/1998/namespace"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
             xmlns:doap="http://usefulinc.com/ns/doap#"
             xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
             xmlns:oboInOwl="http://www.geneontology.org/formats/oboInOwl#">
            {content}
        </rdf:RDF>
        """
        s = io.BytesIO(xml.encode('utf-8'))
        return pronto.Ontology(s, import_depth=0)

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("error")

    @classmethod
    def tearDownClass(cls):
        warnings.simplefilter(warnings.defaultaction)

    def test_metadata_imports(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <owl:imports rdf:resource="http://purl.obolibrary.org/obo/ms.obo"/>
            </owl:Ontology>
            """
        )
        self.assertIn("http://purl.obolibrary.org/obo/ms.obo", ont.metadata.imports)

    def test_metadata_default_namespace(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <oboInOwl:hasDefaultNamespace rdf:datatype="http://www.w3.org/2001/XMLSchema#string">thing</oboInOwl:hasDefaultNamespace>
            </owl:Ontology>
            """
        )
        self.assertEqual(ont.metadata.default_namespace, "thing")

    def test_metadata_data_version(self):
        # owl:versionrIRI
        ont = self.get_ontology(
            """
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/ms.owl">
                <owl:versionIRI rdf:resource="http://purl.obolibrary.org/obo/ms/4.1.30/ms.owl"/>
            </owl:Ontology>
            """
        )
        self.assertEqual(ont.metadata.ontology, "ms")
        self.assertEqual(ont.metadata.data_version, "4.1.30")
        # doap:Version
        ont2 = self.get_ontology(
            "<owl:Ontology><doap:Version>0.1.0</doap:Version></owl:Ontology>"
        )
        self.assertEqual(ont2.metadata.data_version, "0.1.0")

    def test_term_consider(self):
        # Extract from `oboInOwl:consider` text
        ont = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:consider rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:002</oboInOwl:consider>
            </owl:Class>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_002"/>
            """
        )
        self.assertIn("TST:001", ont)
        self.assertIn("TST:002", ont)
        self.assertIn(ont["TST:002"], ont["TST:001"].consider)
        # Extract from `oboInOwl:consider` RDF resource
        ont2 = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:consider rdf:resource="http://purl.obolibrary.org/obo/TST_002"/>
            </owl:Class>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_002"/>
            """
        )
        self.assertIn("TST:001", ont2)
        self.assertIn("TST:002", ont2)
        self.assertIn(ont2["TST:002"], ont2["TST:001"].consider)

    def test_relationship_cyclic(self):
        ont = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                <oboInOwl:is_cyclic rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</oboInOwl:is_cyclic>
            </owl:ObjectProperty>
            """
        )
        self.assertIn("TST:001", ont)
        self.assertTrue(ont["TST:001"].cyclic)

    def test_relationship_functional(self):
        ont = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>
            </owl:ObjectProperty>
            """
        )
        self.assertIn("TST:001", ont)
        self.assertTrue(ont["TST:001"].functional)
