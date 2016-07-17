import warnings
import weakref
import multiprocessing
import atexit

import pronto.utils

__all__ = ["Parser", "OboParser", "OwlXMLParser"]

class Parser(object):
    """An abstract parser object.
    """

    _instances = {}

    def __init__(self, timeout=None):
        self.terms = dict()
        self.meta = dict()
        self.imports = list()
        self._instances[type(self).__name__] = self

    @pronto.utils.timeout(0)
    def parse(self, stream, pool):
        """
        Parse the ontology file.

        Parameters
            stream (io.StringIO): A stream of the ontology file.
        """

        self.terms, self.meta, self.imports = dict(), dict(), list()

        self.read(stream)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()

        return self.meta, self.terms, self.imports

    def hook(self, *args, **kwargs):
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

    def init_workers(self, ParserProcess, nsmap=None, *args, **kwargs):
        self._rawterms = multiprocessing.Queue()
        self._terms = multiprocessing.Queue()
        self._processes = list()

        for _ in range(multiprocessing.cpu_count() * 2):
            self._processes.append(ParserProcess(self._rawterms, self._terms, nsmap))

        for p in self._processes:
            p.start()

    def shut_workers(self):
        self._rawterms.close()
        self._terms.close()

        for p in self._processes:
            p.terminate()

        for p in self._processes:
            p.join()


    @classmethod
    def __del__(cls):

        try:
            for p in cls.processes:
                p.terminate()

            cls._rawterms.close()
            cls._terms.close()
            del cls._terms
            del cls._rawterms
            del cls.processes

        except AttributeError:
            pass



atexit.register(Parser.__del__)


from pronto.parser.obo import OboParser

try:
   from pronto.parser.owl import OwlXMLParser
except ImportError:
   warnings.warn("You don't seem to have lxml installed on your machine, "
                 ".owl parsing will be disabled", pronto.utils.ProntoWarning)
