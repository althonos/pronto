# coding: utf-8
"""
pronto.parser
=============

This module defines the Parser virtual class.
"""

__all__ = ["Parser", "OboParser", "OwlXMLParser"]


class Parser(object):
    """An abstract parser object.
    """

    _instances = {}

    def __init__(self):
        self._instances[type(self).__name__] = self

    @classmethod
    def hook(cls, force=False, path=None, lookup=None):
        raise NotImplementedError

    #@pronto.utils.timeout(0)
    def parse(self, stream):
        """
        Parse the ontology file.

        Parameters
            stream (io.StringIO): A stream of the ontology file.

        Returns:
            dict: contains the metadata
            dict: contains the terms
            list: contains the imports
        """
        raise NotImplementedError


from .obo import OboParser
from .owl import OwlXMLParser, OwlXMLTreeParser, OwlXMLTargetParser
