import json
from functools import reduce

from pronto import utils
from pronto.relationship import RSHIPS

class Term(object):
    """ An ontology term.
    """

    def __init__(self, cid, name, desc, relations = {} , other={}):
        self.id = cid
        self.name = name
        self.desc = desc
        self.relations = relations
        self.other = other

    def __repr__(self):
        return "<{}: {}>".format(self.id, self.name)

    @property
    @utils.memoize
    def parents(self):
        parents = TermList()
        for parental_rship in ('is_a', 'is_part', 'part_of'):
            if parental_rship in self.relations.keys():
                parents.extend(self.relations[parental_rship])
        return parents

    @property
    #@utils.memoize
    def children(self):
        children = TermList()
        for children_rship in ('has_part', 'can_be'):
            if children_rship in self.relations.keys():

                children.extend(self.relations[children_rship])


        return children

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
        for relation,companions in self.relations.items():
            if relation in RSHIPS:

                for companion in companions:

                    if relation != 'is_a':
                        obo += 'relationship: '
                    obo += '{}: '.format(relation)
                    
                    if isinstance(companion, Term):
                        obo += '{} ! {}'.format(companion.id, companion.name) + '\n'
                    else:
                        obo += '{}'.format(companion)
                        obo += '\n'

        return obo

    def isReferenced(self):
        """
        Check if relations to other Terms are referenced or named.

        By default, this returns True for terms that have no relations
        to other terms.
        """
        if self.relations:
            linked_terms = reduce(lambda a,b: a+b, self.relations.values())
            return not all( isinstance(x, str) for x in linked_terms )
        return True

    def rchildren(self, *ontology_list, level=-1, intermediate=True):
        
        rchildren = []

        if level==0:
            return []

        if self.isReferenced():

            if self.children:
                
                if intermediate or level==1:
                    rchildren.extend(self.children)

                for child in self.children:
                    rchildren.extend(child.rchildren(level=level-1, 
                                                     intermediate=intermediate))

        return list(set(rchildren))

    @property    
    def __json__(self):

        jsondict = {'id': self.id ,#if not isinstance(self.id, Term) else self.id.id,
         'name': self.name,
         'other': self.other,
         'desc': self.desc,
         'relations': {k:[x.id for x in v]   for k, v in self.relations.items() }
         }

        return jsondic



class TermList(object):
    """A list of Terms.

    TermList behaves exactly like a list, except it contains shortcuts to 
    generate lists of terms' attributes.

    :Example:

    >>> from pronto import OwlXML
    >>> nmr = OwlXML('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl')
    >>> type(nmr['NMR:1000031'].children)
    <class 'pronto.term.TermList'>

    Use a shortcut:
    >>> nmr['NMR:1000031'].children.id
    ['NMR:1000122', 'NMR:1000156', 'NMR:1000157', 'NMR:1000489']
    >>> nmr['NMR:1400014'].relations['is_a']
    [<NMR:1400011: cardinal part of NMR instrument>]

    """

    def __init__(self, *elements):
        if not elements:
            self.terms = []
        elif elements:
            if len(elements)==1 and isinstance(elements[0], list):
                self.terms = elements[0].copy()
            else:
                self.terms = []
                for term in element:
                    if isinstance(term, Term):
                        self.terms.append(term)
                    else:
                        raise TypeError('TermList can only contain Terms.')

    def __repr__(self):
        return self.terms.__repr__()

    def __iter__(self):
        return self.terms.__iter__()

    def __getattr__(self, attr):
        if attr in ['children', 'parents']:
            return TermList( [ y for x in self.terms for y in getattr(x, attr)] )
        elif attr in ['id', 'name', 'desc', 'other']:
            return [getattr(x, attr) for x in self.terms]
        else:
            return getattr(self.terms, attr)

    def __getitem__(self, item):
        return self.terms[item]



if __name__ == "__main__":
    import doctest
    doctest.testmod()