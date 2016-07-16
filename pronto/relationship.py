# coding: utf-8

import multiprocessing
import threading
import functools
import collections

import pronto.utils


class Relationship(object):
    """
    A Relationship object.

    The Relationship class actually behaves as a factory, creating new
    relationships via the default Python syntax only if no relationship
    of the same name are present in the class py:attribute:: _instances
    (a dictionnary containing memoized relationships).

    """

    _instances = collections.OrderedDict()
    _lock = multiprocessing.Lock()
    _tlock = threading.Lock()

    def __init__(self, obo_name, symmetry=None, transitivity=None,
                 reflexivity=None, complementary=None, prefix=None,
                 direction=None, comment=None, aliases=None):
        """Instantiate a new relationship.

        Parameters:
            obo_name (str): the name of the relationship as it appears
                in obo files (such as is_a, has_part, etc.)
            symetry (bool or None): the symetry of the relationship
            transitivity (bool or None): the transitivity of the relationship.
            reflexivity (bool or None): the reflexivity of the relationship.
            complementary (string or None): if any, the obo_name of the
                complementary relationship.
            direction (string or None): if any, the direction of the
                relationship (can be 'topdown', 'bottomup', 'horizontal').
                A relationship with a direction set as 'topdown' will be
                counted as _childhooding_ when using the Term.children
                property.
            comment (string or None): comments about the Relationship
            aliases (list or None): a list of names that are synonyms to
                this Relationship obo_name

        .. note::
            For :symetry, transitivity, reflexivity, the allowed values are
            the following:
                - True for reflexive, transitive, symmetric
                - False for areflexive, atransitive, asymmetric
                - None for non-reflexive, non-transitive, non-symmetric


        """
        if obo_name not in self._instances:
            self.obo_name = obo_name
            self.symmetry = symmetry
            self.transitivity = reflexivity
            self.reflexivity = reflexivity
            self.complementary = complementary or ''
            self.prefix = prefix or ''
            self.direction = direction or ''
            self.comment = comment or ''
            self.aliases = aliases or list()
            self._instances[obo_name] = self
            for alias in self.aliases:
                self._instances[alias] = self

    def complement(self):
        """Return the complementary relationship of self.

        Raises:
            ValueError: if the relationship has a complementary
                        which was not defined.

        Returns:
            complementary (Relationship): the complementary relationship.

        Example:

            >>> from pronto.relationship import Relationship
            >>> print(Relationship('has_part').complement())
            Relationship(part_of)
            >>> print(Relationship('has_units').complement())
            None

        """

        if self.complementary:

            if self.complementary in self._instances.keys():
                return self._instances[self.complementary]
            else:
                raise ValueError('{} has a complementary but it was not defined !')

        else:
            return None

    def __repr__(self):
        """Overloaded :obj:`object.__repr__`"""
        return "Relationship({})".format(self.obo_name)

    def __new__(cls, obo_name, *args, **kwargs):
        """Overloaded :obj:`object.__new__` method that __memoizes__ the objects.

        This allows to do the following (which is frecking cool):

            >>> Relationship('has_part').direction
            'topdown'

        The Python syntax is overloaded, and what looks like a object
        initialization in fact retrieves an existing object with all its
        properties already set ! The Relationship class behaves like a
        factory of its own objects !

        Todo:
            * Add a warning for unknown relationship (the goal being to
              instantiate every known ontology relationship and even
              allow instatiation of file-defined relationships).

        """
        if obo_name in cls._instances.keys():
            return cls._instances[obo_name]
        else:
            return super(Relationship, cls).__new__(cls)

    #@pronto.utils.classproperty
    @classmethod
    def topdown(cls):
        """Get all topdown Relationship instances

        Returns:
            :obj:`generator`

        Example:

            >>> from pronto import Relationship
            >>> for r in Relationship.topdown():
            ...    print(r)
            Relationship(can_be)
            Relationship(has_part)

        """
        return (r for r in cls._instances.values() if r.direction=='topdown')

    #@pronto.utils.classproperty
    @classmethod
    def bottomup(self):
        """Get all bottomup Relationship instances

        Example:

            >>> from pronto import Relationship
            >>> for r in Relationship.bottomup():
            ...    print(r)
            Relationship(is_a)
            Relationship(part_of)

        """
        return pronto.utils.unique_everseen(r for r in self._instances.values() if r.direction=='bottomup')

    @pronto.utils.classproperty
    def lock(self):
        """A multiprocessing.Lock provided at a class level

        This allows to use pronto's Relationship objects in a multiprocessed
        environment.

        Todo:
            * Use the lock within Relationship.__init__ method and Relationship.topdown
              and Relationship.bottomup
            * Write a classmethod Relationship.instances that wraps the process of acquiring
              the lock during iteration to avoid data races within iteration if other Relationship
              if created (! may end in a deadlock)

        """
        return self._lock

    @pronto.utils.classproperty
    def tlock(self):
        """A threading.Lock provided at a class level
        """
        return self._tlock



Relationship('is_a', symmetry=False, transitivity=True,
                    reflexivity=True, complementary='can_be',
                    direction='bottomup')

Relationship('can_be', symmetry=False, transitivity=True,
                    reflexivity=True, complementary='is_a',
                    direction='topdown')

Relationship('has_part', symmetry=False, transitivity=True,
                        reflexivity=True, complementary='part_of',
                        direction='topdown')

Relationship('part_of', symmetry=False, transitivity=True,
                        reflexivity=True, complementary='has_part',
                        direction='bottomup', aliases=['is_part'])

Relationship('has_units', symmetry=False, transitivity=False,
                          reflexivity=None)


Relationship('has_domain', symmetry=False, transitivity=False,
                           reflexivity=None)
