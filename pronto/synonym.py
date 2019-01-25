# coding: utf-8
"""Definition of the `SynonymType` and `Synonym` classes.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import re
import six
import collections

from .utils import output_str


class SynonymType(object):
    """A synonym type in an ontology.

    Attributes:
        name(str): the name of the synonym type
        scope(str, optional): the scope all synonyms of
            that type will always have(either 'EXACT',
            'BROAD', 'NARROW', 'RELATED', or None).
        desc(Description): the description of the synonym type

    """

    __slots__ = ['name', 'desc', 'scope']
    _instances = collections.OrderedDict()
    _RX_OBO_EXTRACTER = re.compile(r'(?P<name>[^ ]*)[ ]*\"(?P<desc>.*)\"[ ]*(?P<scope>BROAD|NARROW|EXACT|RELATED)?')

    def __init__(self, name, desc, scope=None):
        """Create a new synonym type.

        Arguments:
            name (str): the name of the synonym type.
            desc (str): the description of the synonym type.
            scope (str, optional): the scope modifier.
        """
        self.name = name
        self.desc = desc
        if scope in {'BROAD', 'NARROW', 'EXACT', 'RELATED', None}:
            self.scope = scope
        elif scope in {six.b('BROAD'), six.b('NARROW'), six.b('EXACT'), six.b('RELATED')}:
            self.scope = scope.decode('utf-8')
        else:
            raise ValueError("scope must be 'NARROW', 'BROAD', 'EXACT', 'RELATED' or None")
        self._register()

    def _register(self):
        self._instances[self.name] = self

    @classmethod
    def from_obo(cls, obo_header):
        if isinstance(obo_header, six.binary_type):
            obo_header = obo_header.decode('utf-8')

        groupdict = cls._RX_OBO_EXTRACTER.search(obo_header).groupdict()
        result = {k:v.strip() if v else None for k,v in six.iteritems(groupdict)}
        return cls(**result)

    @property
    def obo(self):
        """str: the synonym type serialized in obo format.
        """
        return ' '.join(['synonymtypedef:', self.name,
                         '"{}"'.format(self.desc),
                         self.scope or '']).strip()

    @output_str
    def __repr__(self):
        return ''.join(['<SynonymType: ', self.name, ' ',
                        '"{}"'.format(self.desc),
                        ' {}>'.format(self.scope) \
                        if self.scope else '>']).strip()

    def __hash__(self):
        return hash((self.name, self.desc, self.scope))


class Synonym(object):
    """A synonym in an ontology.
    """

    _RX_OBO_EXTRACTER = re.compile(r'\"(?P<desc>.*)\" *(?P<scope>EXACT |BROAD |NARROW |RELATED )? *(?P<syn_type>[^ ]+)? *\[(?P<xref>.*)\]')

    def __init__(self, desc, scope=None, syn_type=None, xref=None):
        """Create a new synonym.

        Arguments:
            desc (str): a description of the synonym.
            scope (str, optional): the scope of the synonym (either
                EXACT, BROAD, NARROW or RELATED).
            syn_type (SynonymType, optional): the type of synonym if
                relying on a synonym type defined in the *Typedef*
                section of the ontology.
            xref (list, optional): a list of cross-references for the
                synonym.

        """
        if isinstance(desc, six.binary_type):
            self.desc = desc.decode('utf-8')
        elif isinstance(desc, six.text_type):
            self.desc = desc
        else:
            raise ValueError("desc must be bytes or str, not {}".format(type(desc).__name__))

        if isinstance(scope, six.binary_type):
            self.scope = scope.decode('utf-8')
        elif isinstance(scope, six.text_type):
            self.scope = scope
        elif scope is None:
            self.scope = "RELATED"

        if syn_type is not None:
            try:
                self.syn_type = SynonymType._instances[syn_type]
                self.scope = self.syn_type.scope or self.scope or 'RELATED'
            except KeyError as e:
                raise ValueError("Undefined synonym type: {}".format(syn_type))
        else:
            self.syn_type = None

        if self.scope not in {'EXACT', 'BROAD', 'NARROW', 'RELATED', None}:
            raise ValueError("scope must be 'NARROW', 'BROAD', 'EXACT', 'RELATED' or None")

        self.xref = xref or []

    @classmethod
    def from_obo(cls, obo_header, scope='RELATED'):

        if isinstance(obo_header, six.binary_type):
            obo_header = obo_header.decode('utf-8')

        groupdict = cls._RX_OBO_EXTRACTER.search(obo_header).groupdict()
        if groupdict.get('xref', ''):
            groupdict['xref'] = [x.strip() for x in groupdict['xref'].split(',')]
        groupdict['syn_type'] = groupdict['syn_type'] or None
        groupdict['scope'] = None if groupdict['scope'] is None else groupdict['scope'].rstrip()

        return cls(**groupdict)

    @property
    def obo(self):
        """str: the synonym serialized in obo format.
        """
        return 'synonym: "{}" {} [{}]'.format(
            self.desc,
            ' '.join([self.scope, self.syn_type.name])\
                if self.syn_type else self.scope,
            ', '.join(self.xref)
        )

    @output_str
    def __repr__(self):
        return '<Synonym: "{}" {} [{}]>'.format(
            self.desc,
            ' '.join([self.scope, self.syn_type.name])\
                if self.syn_type else self.scope,
            ', '.join(self.xref)
        )

    def __eq__(self, other):
        return self.desc==other.desc and self.scope==other.scope and self.syn_type==other.syn_type and self.xref==other.xref

    def __hash__(self):
        return hash((self.desc, self.scope, self.syn_type, tuple(self.xref)))
