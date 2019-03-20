# coding: utf-8
"""Definition of the `Term` and `TermList` classes.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import copy

import six

from .description import Description
from .relationship import Relationship
from .utils import output_str, unique_everseen

class Term(object):
    """A term in an ontology.

    Example:
        >>> ms = Ontology('tests/resources/psi-ms.obo')
        >>> type(ms['MS:1000015'])
        <class 'pronto.term.Term'>

    """

    __slots__ = ['id', 'name', 'desc', 'relations', 'other', 'synonyms',
                 '_children', '_parents', '_rchildren', '_rparents',
                 '__weakref__']

    def __init__(self, id, name='', desc='', relations=None, synonyms=None, other=None):
        """Create a new Term.

        Arguments:
            id (str): the Term id (e.g. "MS:1000031")
            name (str): the name of the Term in human language
            desc (str): a description of the Term
            relations (dict, optional): a dictionary containing the other
                terms the Term is in a relationship with.
            other (dict, optional): other information about the term
            synonyms (set, optional): a list containing :obj:`pronto.synonym.Synonym`
                objects relating to the term.

        Example:
            >>> new_term = Term('TR:001', 'new term', 'a new term')
            >>> linked_term = Term('TR:002', 'other new', 'another term',
            ...                    { Relationship('is_a'): 'TR:001'})

        """
        if not isinstance(id, six.text_type):
            id = id.decode('utf-8')
        if isinstance(desc, six.binary_type):
            desc = desc.decode('utf-8')
        if not isinstance(desc, Description):
            desc = Description(desc)
        if not isinstance(name, six.text_type):
            name = name.decode('utf-8')

        self.id = id
        self.name = name
        self.desc = desc
        self.relations = relations or {}
        self.other = other or {}
        self.synonyms = synonyms or set()

        self._rchildren  = {}
        self._rparents = {}
        self._children = None
        self._parents = None

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id \
           and self.name == other.name \
           and self.desc == other.desc \
           and self.relations == other.relations \
           and self.other == other.other \
           and self.synonyms == other.synonyms

    def __hash__(self):
        return hash((
            hash(self.id),
            hash(self.name),
            hash(self.desc),
            hash(frozenset(self.relations)),
            hash(frozenset(self.other)),
            hash(frozenset(self.synonyms))
        ))

    def __copy__(self):
        return Term(
            self.id,
            self.name,
            self.desc,
            self.relations,
            self.synonyms,
            self.other,
        )

    def __deepcopy__(self, memo):
        return Term(
            self.id,
            self.name,
            self.desc,
            copy.copy(self.relations),
            copy.copy(self.synonyms),
            copy.copy(self.other),
        )

    @output_str
    def __repr__(self):
        return "<{}: {}>".format(self.id, self.name)

    @property
    def parents(self):
        """~TermList: The direct parents of the `Term`.
        """
        if self._parents is None:
            bottomups = tuple(Relationship.bottomup())

            self._parents = TermList()
            self._parents.extend(
                [ other
                    for rship,others in six.iteritems(self.relations)
                        for other in others
                            if rship in bottomups
                ]

            )

        return self._parents

    @property
    def children(self):
        """~TermList: The direct children of the `Term`.
        """
        if self._children is None:
            topdowns = tuple(Relationship.topdown())
            self._children = TermList()
            self._children.extend(
                [ other
                    for rship,others in six.iteritems(self.relations)
                        for other in others
                            if rship in topdowns
                ]
            )
        return self._children

    @property
    @output_str
    def obo(self):
        """str: the `Term` serialized in an Obo ``[Term]`` stanza.

        Note:
            The following guide was used:
            ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml
        """
        def add_tags(stanza_list, tags):
            for tag in tags:
                if tag in self.other:
                    if isinstance(self.other[tag], list):
                        for attribute in self.other[tag]:
                            stanza_list.append("{}: {}".format(tag, attribute))
                    else:
                        stanza_list.append("{}: {}".format(tag, self.other[tag]))

        # metatags = ["id", "is_anonymous", "name", "namespace","alt_id", "def","comment",
        #             "subset","synonym","xref","builtin","property_value","is_a",
        #             "intersection_of","union_of","equivalent_to","disjoint_from",
        #             "relationship","created_by","creation_date","is_obsolete",
        #             "replaced_by", "consider"]

        stanza_list = ["[Term]"]

        # id
        stanza_list.append("id: {}".format(self.id))


        # name
        if self.name is not None:
            stanza_list.append("name: {}".format(self.name))
        else:
            stanza_list.append("name: ")

        add_tags(stanza_list, ['is_anonymous', 'alt_id'])

        # def
        if self.desc:
            stanza_list.append(self.desc.obo)

        # comment, subset
        add_tags(stanza_list, ['comment', 'subset'])

        # synonyms
        for synonym in sorted(self.synonyms, key=str):
            stanza_list.append(synonym.obo)

        add_tags(stanza_list, ['xref'])

        # is_a
        if Relationship('is_a') in self.relations:
            for companion in self.relations[Relationship('is_a')]:
                stanza_list.append("is_a: {} ! {}".format(companion.id, companion.name))

        add_tags(stanza_list, ['intersection_of', 'union_of', 'disjoint_from'])

        for relation in self.relations:
            if relation.direction=="bottomup" and relation is not Relationship('is_a'):
                stanza_list.extend(
                    "relationship: {} {} ! {}".format(
                        relation.obo_name, companion.id, companion.name
                    ) for companion in self.relations[relation]
                )

        add_tags(stanza_list, ['is_obsolete', 'replaced_by', 'consider',
                               'builtin', 'created_by', 'creation_date'])

        return "\n".join(stanza_list)

    @property
    def __deref__(self):
        """dict: the `Term` as a `dict` without circular references.
        """
        return {
            'id': self.id,
            'name': self.name,
            'other': self.other,
            'desc': self.desc,
            'relations': {k.obo_name:v.id for k,v in six.iteritems(self.relations)}
         }

    def __getstate__(self):
        return (
            self.id,
            self.name,
            tuple((k,v) for k,v in six.iteritems(self.other)),
            self.desc,
            tuple((k.obo_name,v.id) for k,v in six.iteritems(self.relations)),
            frozenset(self.synonyms),
        )

    def __setstate__(self, state):
        self.id = state[0]
        self.name = state[1]
        self.other = {k:v for (k,v) in state[2]}
        self.desc = state[3]
        self.relations = {Relationship(k):v for k,v in state[4]}
        self.synonyms = set(state[5])
        self._empty_cache()

    def _empty_cache(self):
        """Empty the cache of the Term's memoized functions.
        """
        self._children, self._parents = None, None
        self._rchildren, self._rparents = {}, {}

    def rchildren(self, level=-1, intermediate=True):
        """Create a recursive list of children.

        Parameters:
            level (int): The depth level to continue fetching children from
                (default is -1, to get children to the utter depths)
            intermediate (bool): Also include the intermediate children
                (default is True)

        Returns:
            :obj:`pronto.TermList`:
            The recursive children of the Term following the parameters

        """
        try:
            return self._rchildren[(level, intermediate)]

        except KeyError:

            rchildren = []

            if self.children and level:

                if intermediate or level==1:
                    rchildren.extend(self.children)

                for child in self.children:
                    rchildren.extend(child.rchildren(level=level-1,
                                                     intermediate=intermediate))

            rchildren = TermList(unique_everseen(rchildren))
            self._rchildren[(level, intermediate)] = rchildren
            return rchildren

    def rparents(self, level=-1, intermediate=True):
        """Create a recursive list of children.

        Note that the :param:`intermediate` can be used to include every
        parents to the returned list, not only the most nested ones.

        Parameters:
            level (int): The depth level to continue fetching parents from
                (default is -1, to get parents to the utter depths)
            intermediate (bool): Also include the intermediate parents
                (default is True)

        Returns:
            :obj:`pronto.TermList`:
            The recursive children of the Term following the parameters

        """
        try:
            return self._rparents[(level, intermediate)]

        except KeyError:

            rparents = []

            if self.parents and level:

                if intermediate or level==1:
                    rparents.extend(self.parents)

                for parent in self.parents:
                    rparents.extend(parent.rparents(level=level-1,
                                                     intermediate=intermediate))

            rparents = TermList(unique_everseen(rparents))
            self._rparents[(level, intermediate)] = rparents
            return rparents


class TermList(list):
    """A list of `Term` instances.

    TermList behaves exactly like a list, except it contains shortcuts to
    generate lists of terms' attributes.

    Example:
        >>> nmr = Ontology('tests/resources/nmrCV.owl')
        >>> type(nmr['NMR:1000031'].children)
        <class 'pronto.term.TermList'>

        >>> nmr['NMR:1000031'].children.id
        [u'NMR:1000122', u'NMR:1000156', u'NMR:1000157', u'NMR:1000489']
        >>> nmr['NMR:1400014'].relations[Relationship('is_a')]
        [<NMR:1400011: cardinal part of NMR instrument>]


    .. tip::
        It is also possible to call Term methods on a TermList to
        create another TermList::

            >>> nmr['NMR:1000031'].rchildren(3, False).rparents(3, False).id
            [u'NMR:1000031']

    """

    def __init__(self, elements=None):
        """Create a new `TermList`.

        Arguments:
            elements (collections.Iterable, optional): an Iterable
                that yields `Term` objects.

        Raises:
            TypeError: when the given ``elements`` are not instances
                of `Term`.

        """
        super(TermList, self).__init__()
        self._contents = set()
        try:
            for t in elements or []:
                super(TermList, self).append(t)
                self._contents.add(t.id)
        except AttributeError:
            raise TypeError('TermList can only contain Terms.')

    def append(self, element):
        if element not in self:
            super(TermList, self).append(element)
            try:
                self._contents.add(element.id)
            except AttributeError:
                self._contents.add(element)

    def extend(self, sequence):
        for element in sequence:
            self.append(element)

    def rparents(self, level=-1, intermediate=True):
        return TermList(unique_everseen(
            y for x in self for y in x.rparents(level, intermediate)
        ))

    def rchildren(self, level=-1, intermediate=True):
        return TermList(unique_everseen(
            y for x in self for y in x.rchildren(level, intermediate)
        ))

    @property
    def children(self):
        """~TermList: the children of all the terms in the list.
        """
        return TermList(unique_everseen(
            y for x in self for y in x.children
        ))

    @property
    def parents(self):
        """~TermList: the parents of all the terms in the list.
        """
        return TermList(unique_everseen(
            y for x in self for y in x.parents
        ))

    @property
    def id(self):
        """list: a list of id corresponding to each term of the list.
        """
        return [x.id for x in self]

    @property
    def name(self):
        """list: the name of all the terms in the list.
        """
        return [x.name for x in self]

    @property
    def desc(self):
        """list: the description of all the terms in the list.
        """
        return [x.desc for x in self]

    @property
    def other(self):
        """list: the "other" property of all the terms in the list.
        """
        return [x.other for x in self]

    @property
    def obo(self):
        """list: all the terms in the term list serialized in obo.
        """
        return [x.obo for x in self]

    def __getstate__(self):
        return tuple(x for x in self)

    def __setstate__(self, state):
        pass

    def __contains__(self, term):
        """Check if the TermList contains a term.

        The method allows to check for the presence of a Term in a
        TermList based on a Term object or on a term accession number.

        Example:

            >>> from pronto import *
            >>> nmr = Ontology('tests/resources/nmrCV.owl')
            >>> 'NMR:1000122' in nmr['NMR:1000031'].children
            True
            >>> nmr['NMR:1000122'] in nmr['NMR:1000031'].children
            True

        """
        try:
            _id = term.id
        except AttributeError:
            _id = term
        return _id in self._contents
        #return any((t.id==_id if isinstance(t, Term) else t==_id for t in self))
