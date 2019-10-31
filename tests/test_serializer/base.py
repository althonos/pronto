import io
import textwrap

import pronto


class TestSerializer(object):

    format = NotImplemented

    def assertRoundtrip(self, text):
        text = textwrap.dedent(text).lstrip()
        ont = pronto.Ontology(io.BytesIO(text.encode('utf-8')))
        doc = ont.dumps(self.format)
        self.assertMultiLineEqual(text, doc)
