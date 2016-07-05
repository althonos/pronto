import weakref

RSHIPS = ('has_regexp', 'has_order', 'has_units', 'has_domain', 'is_a', 'part_of', 'is_part')
RSHIP_INVERSE = {'is_a': 'can_be', 'is_part':'has_part', 'part_of': 'has_part'}




class Relationship(object):

    instances = {}



    def __init__(self, obo_name, symmetry=None, transitivity=None,
                 reflexivity=None, complementary=None, prefix=None,
                 direction=None, comment=None, aliases=None):
        """Instantiate a new relationship.

        :param symetry: default None, the symetry of the relationship
        :type symetry: bool or None

        :param transitivity: default None, the transitivity of the
                             relationship
        :type transitivity: bool or None

        :param reflexivity: default None, the reflexivity of the relationship
        :type reflexivity: bool or None

        :param complementary: the obo_name of the complementary relationship
                              (if any).
        :type complementary: string or None

        :param direction: default None, the direction of the relationship
                          (can be 'topdown', 'bottomup', 'horizontal').
                          A relationship's direction must be set at 'topdown'
                          to work with the 'children' method of a Term.

        """


        self.obo_name = obo_name

        self.symmetry = symmetry
        self.transitivity = reflexivity
        self.reflexivity = reflexivity

        self.complementary = complementary or ''

        self.prefix = prefix or ''

        self.direction = direction or ''

        self.comment = comment or ''

        self.aliases = aliases or []
        self.instances[obo_name] = weakref.proxy(self)
        for alias in self.aliases:
            self.instances[alias] = weakref.proxy(self)



    def complement(self):
        """Return the complementary relationship of self.

        :raise ValueError: if the relationship has a complementary
                           which was not defined.
        """

        if self.complementary:

            if self.complementary in self.instances.keys():
                return self.instances[self.complementary]
            else:
                raise ValueError('{} has a complementary but it was not defined !')

        else:
            return None




IS_A      = Relationship('is_a', symmetry=False, transitivity=True,
                    reflexivity=True, complementary='can_be',
                    direction='bottomup')

CAN_BE    = Relationship('can_be', symmetry=False, transitivity=True,
                    reflexivity=True, complementary='is_a',
                    direction='topdown')

HAS_PART  = Relationship('has_part', symmetry=False, transitivity=True,
                        reflexivity=True, complementary='part_of',
                        direction='topdown')

PART_OF   = Relationship('part_of', symmetry=False, transitivity=True,
                        reflexivity=True, complementary='has_part',
                        direction='bottomup', aliases=['is_part'])

HAS_UNITS = Relationship('has_units', symmetry=False, transitivity=False,
                         reflexivity=None)


