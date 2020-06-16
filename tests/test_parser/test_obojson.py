import unittest
import warnings
from pathlib import Path

import pronto


class TestOboJsonExamples(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("error")

    def tearDown(self):
        warnings.simplefilter(warnings.defaultaction)

    @staticmethod
    def get_path(name):
        folder = Path(__file__).parent.parent / "data" / "obographs"
        return str(folder / f"{name}.json")

    def test_abox(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", pronto.warnings.NotImplementedWarning)
            ont = pronto.Ontology(self.get_path("abox"))
        self.assertEqual(len(ont.terms()), 3) # Person (implicit), Male and Female

    @unittest.expectedFailure
    def test_basic(self):
        ont = pronto.Ontology(self.get_path("basic"))
        self.assertIn("test manus ontology", ont.metadata.remarks)
        self.assertIn("UBERON:0002101", ont)
        self.assertIn("UBERON:0002470", ont)
        self.assertIn("UBERON:0002102", ont)
        self.assertIn("UBERON:0002398", ont)
        self.assertIn(ont["UBERON:0002398"], ont["UBERON:0002470"].subclasses().to_set())
        self.assertIn(ont["UBERON:0002102"], ont["UBERON:0002101"].subclasses().to_set())
        self.assertIn(ont["UBERON:0002102"], ont["UBERON:0002398"].relationships[ont["part_of"]])

    def test_equiv_node_set(self):
        ont = pronto.Ontology(self.get_path("equivNodeSetTest"))
        self.assertIn("DOID:0001816", ont)
        self.assertIn("NCIT:C3088", ont)
        self.assertIn("Orphanet:263413", ont)
        self.assertIn(ont["DOID:0001816"], ont["NCIT:C3088"].equivalent_to)
        self.assertIn(ont["NCIT:C3088"], ont["DOID:0001816"].equivalent_to)
        self.assertIn(ont["DOID:0001816"], ont["Orphanet:263413"].equivalent_to)
        self.assertIn(ont["Orphanet:263413"], ont["DOID:0001816"].equivalent_to)

    def test_obsoletion_example(self):
        ont = pronto.Ontology(self.get_path("obsoletion_example"))
        self.assertIn("X:1", ont)
        self.assertIn("X:2", ont)
        self.assertIn("Y:1", ont)
        self.assertIn("Y:2", ont)
        self.assertTrue(ont["X:2"].obsolete)
        self.assertIn(ont["X:1"], ont["X:2"].replaced_by)
        self.assertTrue(ont["Y:2"].obsolete)
        self.assertTrue(ont["Y:1"], ont["Y:2"].replaced_by)

    def test_nucleus(self):
        ont = pronto.Ontology(self.get_path("equivNodeSetTest"))
