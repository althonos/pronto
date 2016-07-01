
import json
import os
import urllib.request as rq 
import collections

from multiprocessing.dummy import Pool

from pronto import utils
from pronto.term import Term, TermList
from pronto.relationship import RSHIPS, RSHIP_INVERSE


class Ontology(object):
    """The base class for an ontology.

    Ontologies inheriting from this class will be able to use the same API as
    providing they generated the expected structure in the :func:`_parse` 
    method.
    """
    
    def __init__(self, location=None):

        self.terms = {}
        self.meta = {}

        if location is not None:
            self.pool = Pool(16)

            if location.startswith('http') or location.startswith('ftp'):
                handle = rq.urlopen(location)
            else:
                if not os.path.exists(location):
                    raise FileNotFoundError('Ontology file {} could not be found'.format(location))
                else:
                    handle = open(location, 'r')

            self._parse(handle)

            self.pool.close()

            self._adopt()

            
            self._reference()
                
            
            self.pool.join()
            del self.pool

    @property
    def json(self):
        """Returns the ontology serialized in json format.
        """        
        return json.dumps(self.terms, indent=4, sort_keys=True,
                          default=lambda o: o.__json__)

    @property
    def obo(self):
        """Returns the ontology serialized in obo format.
        """
        obo = ""

        for accession in sorted(self.terms.keys()):
            obo += '\n'
            obo += self.terms[accession].obo

        return obo

    def _reference(self):
        """Make relationships point to classes of ontology instead of ontology id"""
        for termkey,termval in self.terms.items():
            for relkey, relval in termval.relations.items():

                relvalref = [self.terms[x] if x in self.terms.keys() 
                             else Term(x, '','') if not isinstance(x, Term)
                             else x for x in relval]
                self.terms[termkey].relations[relkey] = relvalref

    def __getitem__(self, item):
        return self.terms[item]

    def __contains__(self, item):
        if isinstance(item, Term):
            return item in self.terms.values()
        elif isinstance(item, str):
            return item in self.terms.keys()
        else:
            raise TypeError("'in <ontology>' requires string or Term as left operand, not {}".format(type(item)))

    def __iter__(self):
        self._terms_accessions = sorted(self.terms.keys())
        self._index = -1
        return self

    def __next__(self):
        try:
            self._index += 1
            return self.terms[self._terms_accessions[self._index]]
        except IndexError:
            del self._index
            del self._terms_accessions
            raise StopIteration
    

    def _adopt(self):
        """Make terms aware of their childs via 'can_be' and 'has_part' relationships"""

        relationships = []

        for term in self:

            if 'is_a' in term.relations.keys():
                for parent in term.relations['is_a']:
                    relationships.append( (parent, 'can_be', term.id ) )

            if 'part_of' in term.relations.keys():
                for parent in term.relations['part_of']:
                    relationships.append( (parent, 'has_part', term.id ) )

            if 'is_part' in term.relations.keys():
                for parent in term.relations['is_part']:
                    relationships.append( (parent, 'part_of', term.id ) )
            
        for parent, rel, child in relationships:
            
            if parent in self:
                if not rel in self[parent].relations.keys():
                
                    self[parent].relations[rel] = TermList()
                
                self[parent].relations[rel].append(child)

    def merge(self, other):
        """Merges another ontology into the current one.

        :Example:

        >>> from pronto import OwlXML, Obo
        >>> nmr = OwlXML('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl')
        >>> ms = Obo('http://purl.obolibrary.org/obo/ms.obo')
        >>> 'NMR:1000271' in nmr
        True
        >>> 'NMR:1000271' in ms
        False
        >>> ms.merge(nmr)
        >>> 'NMR:1000271' in ms
        True

        """
        if isinstance(other, Ontology):
            self.terms.update(other.terms)
            self._reference()
        else:
            raise TypeError("'merge' requires an Ontology as argument, not {}".format(type(other)))
        



if __name__ == "__main__":
    import doctest
    doctest.testmod()



