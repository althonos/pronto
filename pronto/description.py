# coding: utf-8
"""Definition of the `Description` class.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import six


class Description(six.text_type):
    """A description with optional cross-references.
    """

    _RX_OBO_EXTRACTER = re.compile(r'[\"\'](.*)[\"\']( \[(.+)\])?')

    @classmethod
    def from_obo(cls, obo_header):
        match = cls._RX_OBO_EXTRACTER.search(obo_header)
        if match is not None:
            desc, _, xref = match.groups()
        else:
            raise ValueError("not a valid obo definition")
        if xref is not None:
            xref = [x.split(' ')[0] for x in xref.split(', ')]
        return cls(desc, xref)

    def __new__(cls, text, xref=None):
        return super(Description, cls).__new__(cls, text)

    def __init__(self, text, xref=None):
        self.xref = xref or []

    def __repr__(self):
        return "Description('{}', {})".format(self, self.xref)

    @property
    def obo(self):
        return 'def: "{}" [{}]'.format(
            self, ', '.join(self.xref)
        )
