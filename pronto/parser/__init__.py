"""
pronto.parser
=============

This module defines the Parser virtual class.
"""

import warnings
import weakref
import multiprocessing
import time
#import atexit

from ..utils import ProntoWarning


__all__ = ["Parser", "OboParser", "OwlXMLParser"]


class Parser(object):
    """An abstract parser object.
    """

    _instances = {}

    def __init__(self, timeout=None):
        self.terms = {}
        self.meta = {}
        self.imports = []
        self._instances[type(self).__name__] = self
        self._rawterms, self._terms, self._processes= None, None, None

    #@pronto.utils.timeout(0)
    def parse(self, stream):
        """
        Parse the ontology file.

        Parameters
            stream (io.StringIO): A stream of the ontology file.
        """

        self.terms, self.meta, self.imports = {}, {}, set()

        self.read(stream)
        self.makeTree()
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

    def makeTree(self):
        raise NotImplementedError

    def metanalyze(self):
        raise NotImplementedError

    def manage_imports(self):
        raise NotImplementedError

    def init_workers(self, ParserProcess, *args, **kwargs):

        self._rawterms = multiprocessing.Queue()
        self._terms = multiprocessing.Queue()
        self._processes = []

        for _ in range(multiprocessing.cpu_count() * 2):
            self._processes.append(ParserProcess(self._rawterms, self._terms))

        for p in self._processes:
            p.start()

    def shut_workers(self):

        #self._terms._empty_queue()
        #self._rawterms._empty_queue()

        self._rawterms.close()
        self._terms.close()

        #while self._processes:
        for p in multiprocessing.active_children():
            #p = self._processes.pop()
            p.terminate()

        #for p in self._processes:
        #    p.join()

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


#atexit.register(Parser.__del__)


from pronto.parser.obo import OboParser
try:
   from pronto.parser.owl import OwlXMLParser
except ImportError:
   warnings.warn("You don't seem to have lxml installed on your machine, "
                 ".owl parsing will be disabled", ProntoWarning)
