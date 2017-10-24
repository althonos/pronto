# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseParser(object):
    """An abstract parser object.
    """

    @classmethod
    @abc.abstractmethod
    def hook(cls, force=False, path=None, lookup=None):
        """Test whether this parser should be used.

        The current behaviour relies on filenames, file extension
        and looking ahead a small buffer in the file object.
        """

    @classmethod
    @abc.abstractmethod
    def parse(self, stream):
        """
        Parse the ontology file.

        Parameters
            stream (io.StringIO): A stream of ontologic data.

        Returns:
            (dict, dict, list): a tuple of metadata, dict, and imports.

        """
