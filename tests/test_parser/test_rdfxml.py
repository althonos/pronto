import io
import os
import unittest
import warnings
import xml.etree.ElementTree as etree

import pronto



class TestRdfXMLParser(unittest.TestCase):

    @staticmethod
    def get_ontology(content):
        xml = f"""<?xml version="1.0"?>

        <!DOCTYPE rdf:RDF [
            <!ENTITY rdf "http://www.w3.org/1999/02/22-rdf-syntax-ns#" >
            <!ENTITY Hugo "http://ncicb.nci.nih.gov/xml/owl/EVS/Hugo.owl#">
        ]>

        <rdf:RDF xmlns="http://purl.obolibrary.org/obo/TEMP#"
             xml:base="http://purl.obolibrary.org/obo/TEMP"
             xmlns:obo="http://purl.obolibrary.org/obo/"
             xmlns:owl="http://www.w3.org/2002/07/owl#"
             xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:xml="http://www.w3.org/XML/1998/namespace"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
             xmlns:doap="http://usefulinc.com/ns/doap#"
             xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
             xmlns:oboInOwl="http://www.geneontology.org/formats/oboInOwl#"
             xmlns:Hugo="http://ncicb.nci.nih.gov/xml/owl/EVS/Hugo.owl#"
             xmlns:chebi="http://purl.obolibrary.org/obo/chebi/">
            {content}
        </rdf:RDF>
        """
        s = io.BytesIO(xml.encode('utf-8'))
        return pronto.Ontology(s, import_depth=0)

    def setUp(self):
        warnings.simplefilter("error")

    def tearDown(self):
        warnings.simplefilter(warnings.defaultaction)

    # ---

    def test_iao(self):
        warnings.simplefilter("ignore")
        path = os.path.join(__file__, "..", "..", "data", "iao.owl")
        iao = pronto.Ontology(os.path.realpath(path))
        self.assertEqual(len(iao.terms()), 245)

    def test_aeo(self):
        warnings.simplefilter("ignore")
        path = os.path.join(__file__, "..", "..", "data", "aeo.owl")
        aeo = pronto.Ontology(os.path.realpath(path))
        self.assertEqual(len(aeo.terms()), 250)
        self.assertEqual(len(aeo.relationships()), 11)
        self.assertEqual(aeo["AEO:0000099"].name, "keratin-based structure")
        self.assertEqual(len(aeo["AEO:0000099"].definition.xrefs), 1)

    def test_invalid_xml_file(self):
        self.assertRaises(ValueError, self.get_ontology, "")

    # ------------------------------------------------------------------------

    def test_metadata_auto_generated_by(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <oboInOwl:auto-generated-by>pronto</oboInOwl:auto-generated-by>
            </owl:Ontology>
            """
        )
        self.assertEqual(ont.metadata.auto_generated_by, "pronto")

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

    def test_metadata_format_version(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <oboInOwl:hasOBOFormatVersion>1.2</oboInOwl:hasOBOFormatVersion>
            </owl:Ontology>
            """
        )
        self.assertEqual(ont.metadata.format_version, "1.2")

    def test_metadata_imports(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <owl:imports rdf:resource="http://purl.obolibrary.org/obo/ms.obo"/>
            </owl:Ontology>
            """
        )
        self.assertIn("http://purl.obolibrary.org/obo/ms.obo", ont.metadata.imports)

    def test_metadata_saved_by(self):
        ont = self.get_ontology(
            """
            <owl:Ontology>
                <oboInOwl:savedBy>Martin Larralde</oboInOwl:savedBy>
            </owl:Ontology>
            """
        )
        self.assertEqual(ont.metadata.saved_by, "Martin Larralde")

    # ------------------------------------------------------------------------

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

    def test_term_definition_as_property(self):
        ont = self.get_ontology("""
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <obo:IAO_0000115 rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a term</obo:IAO_0000115>
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
            </owl:Class>
        """)
        self.assertIn("TST:001", ont)
        self.assertEqual(ont["TST:001"].definition, "a term")
        self.assertEqual(len(ont["TST:001"].definition.xrefs), 0)

    def test_term_definition_as_axiom(self):
        ont = self.get_ontology("""
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <obo:IAO_0000115 rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a term</obo:IAO_0000115>
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
            </owl:Class>
            <owl:Axiom>
                <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
                <owl:annotatedProperty rdf:resource="http://purl.obolibrary.org/obo/IAO_0000115"/>
                <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a term</owl:annotatedTarget>
                <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
            </owl:Axiom>
        """)
        self.assertIn("TST:001", ont)
        self.assertEqual(ont["TST:001"].definition, "a term")
        self.assertEqual(list(ont["TST:001"].definition.xrefs)[0], pronto.Xref("ISBN:1234"))

    def test_term_multiple_labels(self):
        txt = """
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <rdfs:label>A</rdfs:label>
                <rdfs:label>B</rdfs:label>
            </owl:Class>
        """

        # check multiple labels is a syntax error in error mode
        with warnings.catch_warnings():
            warnings.simplefilter("error", pronto.warnings.SyntaxWarning)
            with self.assertRaises(SyntaxError):
                ont = self.get_ontology(txt)

        # check multiple labels is fine in ignore mode
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology(txt)
            self.assertIn(ont['TST:001'].name, ["A", "B"])

    def test_term_subclass_of(self):
        ont = self.get_ontology("""
            <owl:Ontology/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001"/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_002">
                <rdfs:subClassOf rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
            </owl:Class>
        """)
        self.assertIn(ont["TST:001"], ont["TST:002"].superclasses().to_set())
        self.assertIn(ont["TST:002"], ont["TST:001"].subclasses().to_set())

    def test_term_subset(self):
        ont = self.get_ontology("""
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/tst.owl"/>
            <owl:AnnotationProperty rdf:about="http://purl.obolibrary.org/obo/tst#ss">
                <rdfs:comment rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a subset</rdfs:comment>
                <rdfs:subPropertyOf rdf:resource="http://www.geneontology.org/formats/oboInOwl#SubsetProperty"/>
            </owl:AnnotationProperty>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                <oboInOwl:inSubset rdf:resource="http://purl.obolibrary.org/obo/tst#ss"/>
            </owl:Class>
        """)
        self.assertIn("TST:001", ont)
        self.assertEqual(ont["TST:001"].subsets, {"ss"})

    def test_term_synonym_as_property(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasExactSynonym rdf:datatype="http://www.w3.org/2001/XMLSchema#string">stuff</oboInOwl:hasExactSynonym>
                    <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                </owl:Class>
            """)
        self.assertIn("TST:001", ont)
        self.assertEqual(len(ont["TST:001"].synonyms), 1)
        syn = next(iter(ont["TST:001"].synonyms))
        self.assertEqual(syn.description, "stuff")
        self.assertEqual(syn.scope, "EXACT")
        self.assertEqual(syn.xrefs, set())

    def test_term_synonym_as_axiom(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasExactSynonym rdf:datatype="http://www.w3.org/2001/XMLSchema#string">stuff</oboInOwl:hasExactSynonym>
                    <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                </owl:Class>
                <owl:Axiom>
                    <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
                    <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"/>
                    <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">stuff</owl:annotatedTarget>
                    <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
                </owl:Axiom>
            """)
            self.assertIn("TST:001", ont)
            self.assertEqual(len(ont["TST:001"].synonyms), 1)
            syn = next(iter(ont["TST:001"].synonyms))
            self.assertEqual(syn.description, "stuff")
            self.assertEqual(syn.scope, "EXACT")
            self.assertEqual(syn.xrefs, {pronto.Xref("ISBN:1234")})

    def test_term_relationship(self):
        ont = self.get_ontology("""
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/RO_0002202">
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#TransitiveProperty"/>
                <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">RO:0002202</oboInOwl:hasDbXref>
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string"></oboInOwl:id>
                <oboInOwl:shorthand rdf:datatype="http://www.w3.org/2001/XMLSchema#string">develops_from</oboInOwl:shorthand>
                <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">develops from</rdfs:label>
            </owl:ObjectProperty>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001"/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_002">
                <rdfs:subClassOf>
                    <owl:Restriction>
                        <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/RO_0002202"/>
                        <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
                    </owl:Restriction>
                </rdfs:subClassOf>
            </owl:Class>
        """)
        self.assertIn("develops_from", [r.id for r in ont.relationships()])
        develops_from = ont.get_relationship("develops_from")
        self.assertIn(ont["TST:001"], ont["TST:002"].relationships[develops_from])

    def test_term_xref_as_property_resource(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
                    <oboInOwl:id rdf:resource="http://purl.obolibrary.org/obo/ISBN_1234"/>
                </owl:Class>
            """)
        self.assertEqual(len(ont["TST:001"].xrefs), 1)
        self.assertEqual(list(ont["TST:001"].xrefs)[0].id, "ISBN:1234")

    def test_term_xref_as_property_text(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
                    <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                </owl:Class>
            """)
        self.assertEqual(len(ont["TST:001"].xrefs), 1)
        self.assertEqual(list(ont["TST:001"].xrefs)[0].id, "ISBN:1234")

    def test_term_xref_as_axiom_without_description(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
                    <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                </owl:Class>
                <owl:Axiom>
                    <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
                    <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasDbXref"/>
                    <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</owl:annotatedTarget>
                </owl:Axiom>
            """)
        self.assertEqual(len(ont["TST:001"].xrefs), 1)
        self.assertEqual(list(ont["TST:001"].xrefs)[0].id, "ISBN:1234")
        self.assertEqual(list(ont["TST:001"].xrefs)[0].description, None)

    def test_term_xref_as_axiom_with_description(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology("""
                <owl:Ontology/>
                <owl:Class rdf:about="http://purl.obolibrary.org/obo/TST_001">
                    <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</oboInOwl:hasDbXref>
                    <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                </owl:Class>
                <owl:Axiom>
                    <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/TST_001"/>
                    <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasDbXref"/>
                    <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">ISBN:1234</owl:annotatedTarget>
                    <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a great book</rdfs:label>
                </owl:Axiom>
            """)
        self.assertEqual(len(ont["TST:001"].xrefs), 1)
        self.assertEqual(list(ont["TST:001"].xrefs)[0].id, "ISBN:1234")
        self.assertEqual(list(ont["TST:001"].xrefs)[0].description, "a great book")

    # ------------------------------------------------------------------------

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
        self.assertIn("TST:001", ont.relationships())
        self.assertTrue(ont.get_relationship("TST:001").cyclic)

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
        self.assertIn("TST:001", ont.relationships())
        self.assertTrue(ont.get_relationship("TST:001").functional)

    def test_relationship_multiple_labels(self):
        txt = """
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <rdfs:label>A</rdfs:label>
                <rdfs:label>B</rdfs:label>
            </owl:ObjectProperty>
        """

        # check multiple labels is a syntax error in error mode
        with warnings.catch_warnings():
            warnings.simplefilter("error", pronto.warnings.SyntaxWarning)
            with self.assertRaises(SyntaxError):
                ont = self.get_ontology(txt)

        # check multiple labels is fine in ignore mode
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.SyntaxWarning)
            ont = self.get_ontology(txt)
            self.assertIn(ont.get_relationship('TST:001').name, ["A", "B"])

    def test_relationship_reflexive(self):
        ont = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#ReflexiveProperty"/>
            </owl:ObjectProperty>
            """
        )
        self.assertIn("TST:001", ont.relationships())
        self.assertTrue(ont.get_relationship("TST:001").reflexive)

    def test_relationship_subset(self):
        ont = self.get_ontology("""
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/tst.owl"/>
            <owl:AnnotationProperty rdf:about="http://purl.obolibrary.org/obo/tst#ss">
                <rdfs:comment rdf:datatype="http://www.w3.org/2001/XMLSchema#string">a subset</rdfs:comment>
                <rdfs:subPropertyOf rdf:resource="http://www.geneontology.org/formats/oboInOwl#SubsetProperty"/>
            </owl:AnnotationProperty>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/tst#friend_of">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">friend_of</oboInOwl:id>
                <oboInOwl:inSubset rdf:resource="http://purl.obolibrary.org/obo/tst#ss"/>
            </owl:ObjectProperty>
        """)
        self.assertIn("friend_of", ont.relationships())
        self.assertEqual(ont.get_relationship("friend_of").subsets, {"ss"})

    def test_relationship_symmetric(self):
        ont = self.get_ontology(
            """
            <owl:Ontology/>
            <owl:ObjectProperty rdf:about="http://purl.obolibrary.org/obo/TST_001">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">TST:001</oboInOwl:id>
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#SymmetricProperty"/>
            </owl:ObjectProperty>
            """
        )
        self.assertIn("TST:001", ont.relationships())
        self.assertTrue(ont.get_relationship("TST:001").symmetric)

    def test_existing_synonym_type_extraction(self):
        ont = self.get_ontology(
            """
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/chebi.owl"/>

            <owl:AnnotationProperty rdf:about="http://purl.obolibrary.org/obo/chebi#BRAND_NAME">
                <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">BRAND NAME</rdfs:label>
                <rdfs:subPropertyOf rdf:resource="http://www.geneontology.org/formats/oboInOwl#SynonymTypeProperty"/>
            </owl:AnnotationProperty>

            <owl:Class rdf:about="http://purl.obolibrary.org/obo/CHEBI_4508">
                <oboInOwl:hasRelatedSynonym rdf:datatype="http://www.w3.org/2001/XMLSchema#string">Cataflam</oboInOwl:hasRelatedSynonym>
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">CHEBI:4508</oboInOwl:id>
            </owl:Class>
            <owl:Axiom>
                <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/CHEBI_4508"/>
                <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym"/>
                <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">Cataflam</owl:annotatedTarget>
                <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">DrugBank</oboInOwl:hasDbXref>
                <oboInOwl:hasSynonymType rdf:resource="http://purl.obolibrary.org/obo/chebi#BRAND_NAME"/>
            </owl:Axiom>
            """
        )
        syntype, = ont.metadata.synonymtypedefs
        synonym, = ont["CHEBI:4508"].synonyms
        self.assertEqual(synonym.scope, "RELATED")
        self.assertEqual(synonym.type, syntype)

    def test_missing_synonym_type_extraction(self):
        ont = self.get_ontology(
            """
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/chebi.owl"/>

            <owl:AnnotationProperty rdf:about="http://purl.obolibrary.org/obo/chebi#BRAND_NAME">
                <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">BRAND NAME</rdfs:label>
                <rdfs:subPropertyOf rdf:resource="http://www.geneontology.org/formats/oboInOwl#SynonymTypeProperty"/>
            </owl:AnnotationProperty>

            <owl:Class rdf:about="http://purl.obolibrary.org/obo/CHEBI_4508">
                <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">CHEBI:4508</oboInOwl:id>
            </owl:Class>
            <owl:Axiom>
                <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/CHEBI_4508"/>
                <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym"/>
                <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">Cataflam</owl:annotatedTarget>
                <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">DrugBank</oboInOwl:hasDbXref>
                <oboInOwl:hasSynonymType rdf:resource="http://purl.obolibrary.org/obo/chebi#BRAND_NAME"/>
            </owl:Axiom>
            """
        )
        syntype, = ont.metadata.synonymtypedefs
        synonym, = ont["CHEBI:4508"].synonyms
        self.assertEqual(synonym.scope, "RELATED")
        self.assertEqual(synonym.type, syntype)

    def test_rdf_datatype(self):
        ont = self.get_ontology(
            """
            <owl:Ontology/>

            <owl:Class rdf:about="http://ncicb.nci.nih.gov/xml/owl/EVS/Hugo.owl#HGNC_9990">
                <Hugo:COSMIC_ID rdf:datatype="&rdf;XMLLiteral">RGS2</Hugo:COSMIC_ID>
            </owl:Class>
            """
        )
        with self.assertRaises(ValueError):
            self.get_ontology(
                """
                <owl:Ontology/>
                <owl:Class rdf:about="http://ncicb.nci.nih.gov/xml/owl/EVS/Hugo.owl#HGNC_9990">
                    <Hugo:COSMIC_ID rdf:datatype="http://example.com/something">RGS2</Hugo:COSMIC_ID>
                </owl:Class>
                """
            )

    def test_implicit_annotations(self):
        ont = self.get_ontology(
            """
            <owl:Ontology rdf:about="http://purl.obolibrary.org/obo/chebi.owl"/>
            <owl:Class rdf:about="http://purl.obolibrary.org/obo/CHEBI_65">
                <chebi:charge rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">0</chebi:charge>
                <chebi:formula rdf:datatype="http://www.w3.org/2001/XMLSchema#string">C15H12O6</chebi:formula>
                <chebi:inchi>InChI=1S/C15H12O6/c16-7-1-2-9(11(18)3-7)10-6-21-13-5-8(17)4-12(19)14(13)15(10)20/h1-5,10,16-19H,6H2</chebi:inchi>
                <chebi:inchikey>WNHXBLZBOWXNQO-UHFFFAOYSA-N</chebi:inchikey>
                <chebi:mass rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">288.255</chebi:mass>
                <chebi:monoisotopicmass rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">288.06339</chebi:monoisotopicmass>
            </owl:Class>
            """
        )
        term = ont["CHEBI:65"]
        annotations = sorted(term.annotations, key=lambda pv: pv.property)
        self.assertEqual(len(annotations), 6)
        self.assertEqual(annotations[0].datatype, "xsd:integer")
        self.assertEqual(annotations[1].datatype, "xsd:string")
        self.assertEqual(annotations[2].datatype, "xsd:string")
        self.assertEqual(annotations[4].datatype, "xsd:decimal")
