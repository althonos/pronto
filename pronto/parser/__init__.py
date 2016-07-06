import pronto.utils

__all__ = ["Parser", "OboParser", "OwlXMLParser"]

class Parser(object):
    """A basic parser object.


    The following functions need to
    """

    instances = {}

    def __init__(self, timeout=None):
        self.terms = dict()
        self.meta = dict()
        self.imports = list()
        self.instances[type(self).__name__] = self

    @pronto.utils.timeout(500)
    def parse(self, stream, pool):
        """
        Parse the ontology file.

        :param stream: A stream of the ontology file.
        :type stream: io.StringIO
        """

        self.terms, self.meta, self.imports = dict(), dict(), list()

        self.read(stream)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()

        return self.meta, self.terms, self.imports

    def hook(self, path):
        """Defines when the parser is used

        For Obo and Owl, based on file extension (altough that may need to
        change depending on Owl format).
        """
        raise NotImplementedError

    def read(self, stream):
        """Reads and preprocesses the stream.
        """
        raise NotImplementedError

    def makeTree(self, pool):
        raise NotImplementedError

    def metanalyze(self):
        raise NotImplementedError

    def manage_imports(self):
        raise NotImplementedError




from pronto.parser.obo import OboParser
from pronto.parser.owl import OwlXMLParser
