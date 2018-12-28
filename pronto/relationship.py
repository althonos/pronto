# coding: utf-8
"""Definition of the `Relationship` class.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import collections
import six

from .utils import unique_everseen, output_str


class Relationship(object):
    """A Relationship object.

    The Relationship class actually behaves as a factory, creating new
    relationships via the default Python syntax only if no relationship
    of the same name are present in the class py:attribute::`_instances`
    (a dictionnary containing memoized relationships).

    Relationships are each singletons, so you can use the ``is`` operator
    to check for equality between relationships.

    Note:
       Relationships are pickable and always refer to the same adress even
       after being pickled and unpickled, but that requires to use at least
       pickle protocol 2 (which is not default on Python 2, so take care !)::

          >>> import pronto
          >>> import io, pickle
          >>>
          >>> src = io.BytesIO()
          >>> p = pickle.Pickler(src, pickle.HIGHEST_PROTOCOL)
          >>>
          >>> isa = pronto.Relationship('is_a')
          >>> isa_id = id(isa)
          >>>
          >>> p.dump(isa)
          >>> dst = io.BytesIO(src.getvalue())
          >>>
          >>> u = pickle.Unpickler(dst)
          >>> new_isa = u.load()
          >>>
          >>> id(new_isa) == isa_id
          True
          >>> # what's that black magic ?!

    """

    _instances = collections.OrderedDict()

    def __init__(self, obo_name, symmetry=None, transitivity=None,
                 reflexivity=None, complementary=None, prefix=None,
                 direction=None, comment=None, aliases=None):
        """Instantiate a new relationship.

        Arguments:
            obo_name (str): the name of the relationship as it appears
                in obo files (such as is_a, has_part, etc.)
            symetry (bool or None): the symetry of the relationship
            transitivity (bool or None): the transitivity of the relationship.
            reflexivity (bool or None): the reflexivity of the relationship.
            complementary (string or None): if any, the obo_name of the
                complementary relationship.
            direction (string, optional): if any, the direction of the
                relationship (can be 'topdown', 'bottomup', 'horizontal').
                A relationship with a direction set as 'topdown' will be
                counted as _childhooding_ when acessing `Term.children`.
            comment (string, optional): comments about the relationship.
            aliases (list, optional): a list of names that are synonyms to
                the obo name of this relationship.

        Note:
            For symetry, transitivity, reflexivity, the allowed values are
            the following:

            * `True` for reflexive, transitive, symmetric
            * `False` for areflexive, atransitive, asymmetric
            * `None` for non-reflexive, non-transitive, non-symmetric

        """
        if obo_name not in self._instances:

            if not isinstance(obo_name, six.text_type):
                obo_name = obo_name.decode('utf-8')
            if complementary is not None and not isinstance(complementary, six.text_type):
                complementary = complementary.decode('utf-8')
            if prefix is not None and not isinstance(prefix, six.text_type):
                prefix = prefix.decode('utf-8')
            if direction is not None and not isinstance(direction, six.text_type):
                direction = direction.decode('utf-8')
            if comment is not None and not isinstance(comment, six.text_type):
                comment = comment.decode('utf-8')

            self.obo_name = obo_name
            self.symmetry = symmetry
            self.transitivity = transitivity
            self.reflexivity = reflexivity
            self.complementary = complementary or ''
            self.prefix = prefix or ''
            self.direction = direction or ''
            self.comment = comment or ''
            if aliases is not None:
                self.aliases = [alias.decode('utf-8') if not isinstance(alias, six.text_type) else alias
                                    for alias in aliases]
            else:
                self.aliases = []

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
            Relationship('part_of')
            >>> print(Relationship('has_units').complement())
            None

        """
        if self.complementary:

            #if self.complementary in self._instances.keys():
            try:
                return self._instances[self.complementary]
            except KeyError:
                raise ValueError('{} has a complementary but it was not defined !')

        else:
            return None

    @output_str
    def __repr__(self):
        """Return a string reprensentation of the relationship.
        """
        return "Relationship('{}')".format(self.obo_name)

    def __new__(cls, obo_name, *args, **kwargs):
        """Create a relationship or returning an already existing one.

        This allows to do the following:

            >>> Relationship('has_part').direction
            u'topdown'

        The Python syntax is overloaded, and what looks like a object
        initialization in fact retrieves an existing object with all its
        properties already set. The Relationship class behaves like a
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

    @classmethod
    def topdown(cls):
        """Get all topdown `Relationship` instances.

        Returns:
            :obj:`generator`

        Example:

            >>> from pronto import Relationship
            >>> for r in Relationship.topdown():
            ...    print(r)
            Relationship('can_be')
            Relationship('has_part')

        """
        return tuple(unique_everseen(r for r in cls._instances.values() if r.direction=='topdown'))

    @classmethod
    def bottomup(cls):
        """Get all bottomup `Relationship` instances.

        Example:

            >>> from pronto import Relationship
            >>> for r in Relationship.bottomup():
            ...    print(r)
            Relationship('is_a')
            Relationship('part_of')
            Relationship('develops_from')

        """
        return tuple(unique_everseen(r for r in cls._instances.values() if r.direction=='bottomup'))

    def __getnewargs__(self):
        return (self.obo_name,)

    @classmethod
    def _from_obo_dict(cls, d):

        if d['id'] in cls._instances:
            return cls._instances[d['id']]

        try:
            complementary = d['inverse_of']
        except KeyError:
            complementary = ""

        try:
            transitivity = d['is_transitive'].lower() == "true"
        except KeyError:
            transitivity = None

        try:
            symmetry = d['is_symmetric'].lower() == "true"
        except KeyError:
            symmetry = None

        try:
            reflexivity = d['is_reflexive'].lower() == "true"
        except KeyError:
            reflexivity = None

        try:
            symmetry = d['is_antisymetric'].lower() == "false"
        except KeyError:
            pass

        return Relationship(d['id'], symmetry=symmetry, transitivity=transitivity,
                            reflexivity=reflexivity, complementary=complementary)

    @property
    @output_str
    def obo(self):
        """str: the `Relationship` serialized in an ``[Typedef]`` stanza.

        Note:
            The following guide was used:
            ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml
        """

        lines = [
            "[Typedef]",
            "id: {}".format(self.obo_name),
            "name: {}".format(self.obo_name)
        ]
        if self.complementary is not None:
            lines.append("inverse_of: {}".format(self.complementary))
        if self.symmetry is not None:
            lines.append("is_symmetric: {}".format(self.symmetry).lower())
        if self.transitivity is not None:
            lines.append("is_transitive: {}".format(self.transitivity).lower())
        if self.reflexivity is not None:
            lines.append("is_reflexive: {}".format(self.reflexivity).lower())
        if self.comment:
            lines.append("comment: {}".format(self.comment))
        return "\n".join(lines)




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

Relationship('has_domain', symmetry=False, transitivity=False)

Relationship('develops_from', symmetry=False, transitivity=True,
                              reflexivity=True, complementary='can_be',
                              direction='bottomup')
