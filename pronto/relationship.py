# coding: utf-8

#RSHIPS = ('has_regexp', 'has_order', 'has_units', 'has_domain', 'is_a', 'part_of', 'is_part')
#RSHIP_INVERSE = {'is_a': 'can_be', 'is_part':'has_part', 'part_of': 'has_part'}

import multiprocessing

import pronto.utils


class Relationship(object):
    """
    A Relationship object.

    The Relationship class actually behaves as a factory, creating new
    relationships via the default Python syntax only if no relationship
    of the same name are present in the class py:attribute:: _instances
    (a dictionnary containing memoized relationships).

    """

    _instances = {}
    _lock = multiprocessing.Lock()

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
        """
        if obo_name not in self._instances.keys():
            self.obo_name = obo_name
            self.symmetry = symmetry
            self.transitivity = reflexivity
            self.reflexivity = reflexivity
            self.complementary = complementary or ''
            self.prefix = prefix or ''
            self.direction = direction or ''
            self.comment = comment or ''
            self.aliases = aliases or []
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
        return "Relationship({})".format(self.obo_name)

    def __new__(cls, obo_name, *args, **kwargs):
        """Overloaded py:method::__new__ method that _memoizes_ the objects.

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
        if obo_name in cls._instances:
            return cls._instances[obo_name]
        else:
            return super(Relationship, cls).__new__(cls)

    @pronto.utils.classproperty
    def topdown(self):
        return (r for r in self._instances.values() if r.direction=='topdown')

    @pronto.utils.classproperty
    def bottomup(self):
        return (r for r in self._instances.values() if r.direction=='bottomup')

    @pronto.utils.classproperty
    def lock(self):
        return self._lock


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


