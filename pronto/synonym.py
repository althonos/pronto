import re
import six
import collections


class SynonymType(object):
    """A custom synonym type (obo-style).

    Attributes:
        name(str): the name of the synonym type
        scope(str, optional): the scope all synonyms of
            that type will always have(either 'EXACT',
            'BROAD', 'NARROW', 'RELATED', or None).
        desc(str): the description of the synonym type
    """
    _instances = collections.OrderedDict()
    _RX_OBO_EXTRACTER = re.compile(six.u(r'([^ ]*) \"([^\"]*)\" ?(BROAD|NARROW|EXACT|RELATED|)'))

    def __init__(self, name, desc, scope=None):
        self.name = name
        self.desc = desc
        if scope is None:
            self.scope = scope
        elif scope in {six.u('BROAD'), six.u('NARROW'), six.u('EXACT'), six.u('RELATED')}:
            self.scope = scope
        elif scope in {six.b('BROAD'), six.b('NARROW'), six.b('EXACT'), six.b('RELATED')}:
            self.scope = scope.decode('utf-8')
        else:
            raise ValueError("scope must be 'NARROW', 'BROAD', 'EXACT', 'RELATED' or None")
        self._register()

    def _register(self):
        self._instances[self.name] = self

    @classmethod
    def from_obo_header(cls, obo_header):
        if isinstance(obo_header, six.binary_type):
            obo_header = obo_header.decode('utf-8')
        result = list(cls._RX_OBO_EXTRACTER.search(obo_header).groups())
        scope = result.pop(-1) or None
        return cls(result[0], result[1], scope)

    @property
    def obo(self):
        return six.u(' ').join(['synonymtypedef:', self.name,
                                '"{}"'.format(self.desc),
                                self.scope or '']).strip()

    def __repr__(self):
        return six.u('').join(['<SynonymType: ', self.name, ' ',
                                '"{}"'.format(self.desc),
                                 ' {}>'.format(self.scope) \
                                    if self.scope else '>']).strip()


class Synonym(object):
    """A synonym representation (obo-like).

    Attributes:
        desc (str): a description of the synonym
        syn_type (SynonymType, optional): the type of synonym if relying
            on a custom type defined in the ontology metadata
        scope (str, optional): the scope of the synonym (either EXACT,
            BROAD, NARROW or RELATED).
        xref (list, optional): the list of the cross-references of
            the synonym
    """
    _RX_OBO_EXTRACTER = re.compile(r'\"([^\"]*)\" ?(EXACT|BROAD|NARROW|RELATED|) ?([^ ]*)')
    _RX_LIST_EXTRACTER = re.compile(r'\[([^\]]*)\]')

    def __init__(self, desc, scope=None, syn_type=None, xref=None):

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

        if not self.scope in {'EXACT', 'BROAD', 'NARROW', 'RELATED', None}:
            raise ValueError("scope must be 'NARROW', 'BROAD', 'EXACT', 'RELATED' or None")

        self.xref = xref or []

    @classmethod
    def from_obo_header(cls, obo_header, scope='RELATED'):

        if isinstance(obo_header, six.binary_type):
            obo_header = obo_header.decode('utf-8')

        result = cls._RX_OBO_EXTRACTER.search(obo_header).groups()
        xref = [x.strip() for x in cls._RX_LIST_EXTRACTER.search(obo_header).group(1).split(',')]

        if result[-1].startswith('['):
            type_name = None
        else:
            type_name = result[-1]

        return cls(result[0].strip(), result[1] or scope, type_name, xref)

    @property
    def obo(self):
        return 'synonym: "{}" {} [{}]'.format(
            self.desc,
            ' '.join([self.scope, self.syn_type])\
                if self.syn_type else self.scope,

        )

    def __repr__(self):
        return '<Synonym: "{}" {} [{}]>'.format(
            self.desc,
            ' '.join([self.scope, self.syn_type.name])\
                if self.syn_type else self.scope,
                ', '.join(self.xref)
        )


