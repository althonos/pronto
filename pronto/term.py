# coding: utf-8
"""
pronto.term
===========

This module defines the classes Term and TermList.
"""

#import functools

#from pronto import utils
from pronto.relationship import Relationship


class Term(object):
    """ An ontology term.
    """

    def __init__(self, tid, name, desc='', relations=None, other=None):
        self.id = tid
        self.name = name
        self.desc = desc
        self.relations = relations or dict()
        self.other = other or dict()
        self._rchildren, self._rparents = dict(), dict()
        self._children, self._parents = None, None

    def __repr__(self):
        return "<{}: {}>".format(self.id, self.name)

    @property
    def parents(self):
        if self._parents is not None:
            return self._parents
        else:
            self._parents = TermList()
            for rship in Relationship.bottomup:
                if rship in self.relations.keys():
                    self._parents.extend(self.relations[rship])
            return self._parents

    @property
    def children(self):
        if self._children is not None:
            return self._children
        else:
            self._children = TermList()
            for rship in Relationship.topdown:
                if rship in self.relations.keys():
                    self._children.extend(self.relations[rship])
            return self._children

    @property
    def obo(self):

        obo =  '[Term]' + '\n'
        obo += 'id: {}'.format(self.id) + '\n'
        obo += 'name: {}'.format(self.name) + '\n'

        if self.desc:
            obo += 'def: {}'.format(self.desc) + '\n'

        # add more bits of information
        for k,v in self.other.items():
            if isinstance(v, list):
                for x in v:
                    obo += '{}: {}'.format(k,x) + '\n'
            else:
                obo += '{}: {}'.format(k,v) + '\n'

        # add relationships (only bottom up ones)

        for relation in Relationship.bottomup:
            try:
                for companion in self.relations[relation]:

                    if relation is not Relationship('is_a'):
                        obo += 'relationship: '
                    obo += '{}: '.format(relation.obo_name)

                    if isinstance(companion, Term):
                        obo += '{} ! {}'.format(companion.id, companion.name) + '\n'
                    else:
                        obo += '{}'.format(companion)
                        obo += '\n'

            except KeyError:
                continue

        return obo

    @property
    def __deref__(self):
        """A dereferenced relations dictionary only contains other Terms id
        to avoid circular references when creating a json.
        """
        return Term(
            self.id,
            self.name,
            self.other,
            self.desc,
            {k.obo_name:v.id for k,v in self.relations.items()}
         )

    def _empty_cache(self):
        self._children, self._parents = None, None
        self._rchildren, self._rparents = dict(), dict()

    def rchildren(self, level=-1, intermediate=True):
        """Create a recursive list of children.

        Note that the :param:`intermediate` can be used to include every
        child to the returned list, not only the most nested ones.

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

            rchildren = TermList(set(rchildren))
            self._rchildren[(level, intermediate)] = rchildren
            return rchildren

    def rparents(self, level=-1, intermediate=True):
        """Create a recursive list of parents.

        Note that the :param:`intermediate` can be used to include every
        parent to the returned list, not only the top ones.

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

            rparents = TermList(set(rparents))
            self._rparents[(level, intermediate)] = rparents
            return rparents

class TermList(list):
    """A list of Terms.

    TermList behaves exactly like a list, except it contains shortcuts to
    generate lists of terms' attributes.

    Example:

        >>> from pronto import Ontology, Relationship
        >>> nmr = Ontology('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl')
        >>> type(nmr['NMR:1000031'].children)
        <class 'pronto.term.TermList'>

        >>> nmr['NMR:1000031'].children.id
        ['NMR:1000122', 'NMR:1000156', 'NMR:1000157', 'NMR:1000489']
        >>> nmr['NMR:1400014'].relations[Relationship('is_a')]
        [<NMR:1400011: cardinal part of NMR instrument>]


    .. note::
        It is also possible to call Term methods on a TermList to
        create a set of terms::

            >>> nmr['NMR:1000031'].rchildren(3, False).rparents(3, False).id
            ['NMR:1000031']

    """

    def __init__(self, *elements):
        list.__init__(self, *elements)
        self._check_content()

    def _check_content(self):
        for term in self:
            if not isinstance(term, Term):
                raise TypeError('TermList can only contain Terms.')

    def __getattr__(self, attr, *args, **kwargs):
        if attr in ['children', 'parents']:
            return TermList( [ y for x in self for y in getattr(x, attr)] )
        elif attr in ['rparents', 'rchildren']:
            #: we create a new method to allow the user
            #: to use, for instance, ``x.rchildren(3).rparents(2)``
            #: (this actually behaves as if you mapped the method
            #: on all terms of the TermList)
            def mapped(level=-1, intermediate=True):
                t = TermList(set([ y for x in self
                        for y in getattr(x, attr)(level, intermediate) ]))
                return t
            return mapped
        elif attr in ['id', 'name', 'desc', 'other']:
            return [getattr(x, attr) for x in self]
        else:
            getattr(list, attr)

    def __contains__(self, term):
        """
        Todo: write doc & test
        """
        return term in self.id or any(t for t in self if t==term)


