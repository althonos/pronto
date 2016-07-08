# coding: utf-8
"""
pronto.ontology
===============

This submodule contains the definition of the Ontology class.
"""


import json
import os
import warnings

import multiprocessing.dummy

try:
    import urllib.request as rq
    from urllib.error import URLError, HTTPError
except ImportError:
    import urllib2 as rq
    from urllib2 import URLError, HTTPError
    from pronto.utils import TimeoutError


import pronto.term
import pronto.parser
import pronto.utils


class Ontology(object):
    """The base class for an ontology.

    Ontologies inheriting from this class will be able to use the same API as
    providing they generated the expected structure in the :func:`_parse`
    method.

    Examples:
        Import an ontology from a remote location:

            >>> from pronto import Ontology
            >>> envo = Ontology("https://raw.githubusercontent.com/"
            ... "EnvironmentOntology/envo/master/src/envo/envo.obo")

        Merge two local ontologies and export the merge:

            >>> uo = Ontology("resources/uo.owl", False)
            >>> cl = Ontology("resources/cl.ont", False)

        Export an ontology with its dependencies embedded:

            >>> import os
            >>> cl = Ontology("resources/cl.ont")
            >>> with open('run/cl.obo', 'w') as f:
            ...     lines_count = f.write(cl.obo)


    Todo:
        * Add a __repr__ method
    """

    def __init__(self, path=None, imports=True, import_depth=-1):
        """
        """

        self.pool = multiprocessing.dummy.Pool()

        self.path = path
        self.meta = dict()
        self.terms = dict()
        self.imports = list()

        if path is not None:


            if path.startswith('http') or path.startswith('ftp'):
                handle = rq.urlopen(path)
            else:
                if not os.path.exists(path):
                    raise OSError('Ontology file {} could not be found'.format(path))
                else:
                    handle = open(path, 'r')


            self.parse(handle)

            self.adopt()

            if imports and import_depth:
                self.resolve_imports(import_depth)

            self.reference()

        self.pool.close()
        self.pool.join()
        del self.pool

    @property
    def json(self):
        """Returns the ontology serialized in json format.

        Example:
            >>> j = uo.json
            >>> all(term.id in j for term in uo)
            True

        Note:
            It is possible to save and load an ontology to and from
            json format, although it is cleaner to save and load
            an ontology in Obo format (as the json export doesn't store
            metadata, only terms).

        """
        return json.dumps(self.terms, indent=4, sort_keys=True,
                          default=lambda o: o.__deref__.__dict__)

    @property
    def obo(self):
        """Returns the ontology serialized in obo format.
        """
        obo = ""

        for accession in sorted(self.terms.keys()):
            obo += '\n'
            obo += self.terms[accession].obo

        return obo

    def reference(self):
        """Make relationships point to classes of ontology instead of ontology id"""
        for termkey,termval in self.terms.items():
            for relkey, relval in termval.relations.items():

                relvalref = [self.terms[x] if x in self.terms.keys()
                             else pronto.term.Term(x, '','') if not isinstance(x, pronto.term.Term)
                             else x for x in relval]
                self.terms[termkey].relations[relkey] = pronto.term.TermList(relvalref)

    def parse(self, stream):
        for parser in pronto.parser.Parser.instances.values():
            if parser.hook(stream=stream, path=self.path):
                try:
                    self.meta, self.terms, self.imports = parser.parse(stream, self.pool)
                    return
                except TimeoutError:
                    warnings.warn("Parsing of {} timed out".format(self.path),
                                   pronto.utils.ProntoWarning)



    def __getitem__(self, item):
        return self.terms[item]

    def __contains__(self, item):
        if isinstance(item, pronto.term.Term):
            return item.id in self.terms.keys()
        elif isinstance(item, str) or isinstance(item, unicode):
            return item in self.terms.keys()
        else:
            raise TypeError("'in <ontology>' requires string or Term as left operand, not {}".format(type(item)))

    def __iter__(self):
        terms_accessions = sorted(self.terms.keys())
        return (self.terms[i] for i in terms_accessions)

    def __len__(self):
        return len(self.terms)

    def adopt(self):
        """Make terms aware of their children via 'can_be' and 'has_part' relationships"""

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
            if isinstance(parent, pronto.term.Term):
                parent = parent.id
            if parent in self:
                if not rel in self[parent].relations.keys():

                    self[parent].relations[rel] = pronto.term.TermList()

                self[parent].relations[rel].append(child)

    def include(self, *terms):
        """Add new terms to the current ontology.

        Raises:
            TypeError: when the object(s) passed to the function is (are)
                not either a TermList or a Term.

        Note:
            This will also recursively include terms in the term's relations
            dictionnary, but it is considered bad practice to do so. If you
            want to create your own ontology, you should only add an ID (such
            as 'ONT:001') to your terms relations, and let the Ontology link
            terms with each other.

        :Example:

        Create a new ontology from scratch:

        >>> from pronto import Term
        >>> t1 = Term('ONT:001','my 1st term',
        ...           'this is my first term')
        >>> t2 = Term('ONT:002', 'my 2nd term',
        ...           'this is my second term',
        ...           {'part_of': ['ONT:001']})
        >>> ont = Ontology()
        >>> ont.include(t1, t2)

        >>> 'ONT:002' in ont
        True
        >>> ont['ONT:001'].children
        [<ONT:002: my 2nd term>]

        """
        ref_needed = False
        for term in terms:
            if isinstance(term, pronto.term.TermList):
                ref_needed = ref_needed or self._include_term_list(term)
            elif isinstance(term, pronto.term.Term):
                ref_needed = ref_needed or self._include_term(term)
            else:
                raise TypeError('include only accepts <Term> or <TermList> as arguments')

        self.adopt()
        self.reference()

    def resolve_imports(self, import_depth):
        """Imports required ontologies."""
        for i in set(self.imports):
            try:

                if os.path.exists(i) or i.startswith('http') or i.startswith('ftp'):
                    self.merge(Ontology(i, import_depth=import_depth-1))


                else: # try to look at neighbouring ontologies
                    self.merge(Ontology( os.path.join(os.path.dirname(self.path), i),
                                         import_depth=import_depth-1))

            except (IOError, OSError, URLError, HTTPError) as e:
                warnings.warn("{} occured when during import of "
                              "{}".format(type(e).__name__, i),
                              pronto.utils.ProntoWarning)

    def _include_term_list(self, termlist):
        """Add terms from a TermList to the ontology.
        """
        ref_needed = False
        for term in termlist:
            ref_needed = ref_needed or self._include_term(term)
        return reference_needed

    def _include_term(self, term):
        """Add a single term to the current ontology

        It is needed to dereference any term in the term's relationship
        and then to build the reference again to make sure the other
        terms referenced in the term's relations are the one contained
        in the ontology (to make sure changes to one term in the ontology
        will be applied to every other term related to that term).
        """
        ref_needed = False

        if term.relations:

            for k,v in term.relations.items():
                for i,t in enumerate(v):

                    if isinstance(t, pronto.term.Term):

                        if not t.id in self:
                            self._include_term(t)

                        term.relations[k][i] = t.id

                    ref_needed = True

        self.terms[term.id] = term
        return ref_needed

    def merge(self, other):
        """Merges another ontology into the current one.

        :Example:

        >>> from pronto import Ontology
        >>> nmr = Ontology('http://nmrml.org/cv/v1.0.rc1/nmrCV.owl', False)
        >>> po = Ontology('https://raw.githubusercontent.com/Planteome'
        ... '/plant-ontology/master/po.obo', False)
        >>> 'NMR:1000271' in nmr
        True
        >>> 'NMR:1000271' in po
        False
        >>> po.merge(nmr)
        >>> 'NMR:1000271' in po
        True

        """
        if isinstance(other, Ontology):
            self.terms.update(other.terms)
            self.reference()
        else:
            raise TypeError("'merge' requires an Ontology as argument, not {}".format(type(other)))

