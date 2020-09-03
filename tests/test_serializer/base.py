import io
import tempfile
import textwrap

import pronto


class TestSerializer(object):

    format = NotImplemented

    def assertRoundtrip(self, text):
        text = textwrap.dedent(text).lstrip()
        ont = pronto.Ontology(io.BytesIO(text.encode('utf-8')))
        doc = ont.dumps(self.format)
        self.assertMultiLineEqual(text, doc)

    def test_superclass_add(self):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        t2 = ont.create_term("TST:002")
        t2.superclasses().add(t1)
        self.assertIn(t1, t2.superclasses().to_set())
        self.assertIn(t2, t1.subclasses().to_set())

        with tempfile.NamedTemporaryFile() as f:
            doc = ont.dump(f)
            new = pronto.Ontology(f.name)

        self.assertIn(new["TST:001"], new["TST:002"].superclasses().to_set())
        self.assertIn(new["TST:002"], new["TST:001"].subclasses().to_set())

    def test_subclass_add(self):
        ont = pronto.Ontology()
        t1 = ont.create_term("TST:001")
        t2 = ont.create_term("TST:002")
        t1.subclasses().add(t2)
        self.assertIn(t1, t2.superclasses().to_set())
        self.assertIn(t2, t1.subclasses().to_set())

        with tempfile.NamedTemporaryFile() as f:
            doc = ont.dump(f)
            new = pronto.Ontology(f.name)

        self.assertIn(new["TST:001"], new["TST:002"].superclasses().to_set())
        self.assertIn(new["TST:002"], new["TST:001"].subclasses().to_set())
