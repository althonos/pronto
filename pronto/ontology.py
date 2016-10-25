# coding: utf-8
"""
pronto.ontology
===============

This submodule contains the definition of the Ontology class.


Multiprocessing
---------------

Ontology parsing relies on multiprocessing, which means it
isn't possible to use Ontology parsing within daemons. Still,
once the parsing is done, it is possible to use Ontologies
within processes or threads as all object implemented in pronto
are pickable.


"""
from __future__ import unicode_literals

import json
import os
import warnings
import six
#import functools

import six.moves.urllib.request as rq
from six.moves.urllib.error import URLError, HTTPError

try:
    from lxml.etree import XMLSyntaxError as ParseError
except ImportError:
    from xml.etree.ElementTree import ParseError

from . import __version__
from .term   import Term, TermList
from .parser import Parser
from .utils  import ProntoWarning, output_bytes


class Ontology(object):
    """An ontology.

    Ontologies inheriting from this class will be able to use the same API as
    providing they generated the expected structure in the :func:`_parse`
    method.

    Examples:
        Import an ontology from a remote location:

            >>> from pronto import Ontology
            >>> envo = Ontology("https://raw.githubusercontent.com/"
            ... "EnvironmentOntology/envo/master/src/envo/envo.obo")

        Merge two local ontologies and export the merge:

            >>> uo = Ontology("resources/uo.obo", False)
            >>> cl = Ontology("resources/cl.ont", False)
            >>> uo.merge(cl)
            >>> with open('run/merge.obo', 'w') as f:
            ...     lines_count = f.write(uo.obo)

        Export an ontology with its dependencies embedded:

            >>> cl = Ontology("resources/cl.ont")
            >>> with open('run/cl.obo', 'w') as f:
            ...     lines_count = f.write(cl.obo)


    Todo:
        * Add a __repr__ method to Ontology
    """

    def __init__(self, path=None, imports=True, import_depth=-1, timeout=2):
        """
        """
        self.path = path
        self.meta = {}
        self.terms = {}
        self.imports = ()

        if path is not None:


            if path.startswith('http') or path.startswith('ftp'):
                handle = rq.urlopen(path, timeout=timeout)
            else:
                if not os.path.exists(path):
                    raise OSError('Ontology file {} could not be found'.format(path))
                else:
                    handle = open(path, 'rb')


            self.parse(handle)

            handle.close()

            self.adopt()

            if imports and import_depth:
                self.resolve_imports(import_depth)

            self.reference()

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

        return json.dumps( self.terms, indent=4, sort_keys=True,
                          default=lambda o: o.__deref__)

    @property
    @output_bytes
    def obo(self):
        """Returns the ontology serialized in obo format.
        """

        meta = self._obo_meta()
        try: meta = meta.decode('utf-8')
        except AttributeError: pass
        meta = [meta] if meta else []

        if six.PY2:
            try: # if 'namespace' in self.meta:
                return "\n\n".join( meta + [t.obo.decode('utf-8') for t in self if t.id.startswith(self.meta['namespace'][0])])
            except KeyError:
                return "\n\n".join( meta + [t.obo.decode('utf-8') for t in self])

        elif six.PY3:
            try: # if 'namespace' in self.meta:
                return "\n\n".join( meta + [t.obo for t in self if t.id.startswith(self.meta['namespace'][0])])
            except KeyError:
                return "\n\n".join( meta + [t.obo for t in self])

 
    @output_bytes
    def _obo_meta(self):
        """Generates the obo metadata header

        Generated following specs of the official format guide:
        ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml

        Todo:
            * Change the `auto-generated-by` tag to be **auto-generated-by pronto pronto.__version__**

        """

        metatags = ["format-version", "data-version", "date", "saved-by", "auto-generated-by",
                "import", "subsetdef", "synonymtypedef", "default-namespace", "namespace-id-rule",
                "idspace", "treat-xrefs-as-equivalent", "treat-xrefs-as-genus-differentia",
                "treat-xrefs-as-is_a", "remark", "ontology"]

        obo_meta = "\n".join(

            [ # official obo tags
                "{}: {}".format(k, x)
                        for k in metatags[:-1]
                            if k in self.meta
                                for x in self.meta[k]
            ] + [ # eventual other metadata added to remarks
                "remark: {}: {}".format(k, x)
                    for k,v in sorted(six.iteritems(self.meta), key=lambda x: x[0])
                        for x in v
                            if k not in metatags
            ] +      ["ontology: {}".format(x) for x in self.meta["ontology"]] if "ontology" in self.meta
                else ["ontology: {}".format(self.meta["namespace"][0].lower())] if "namespace" in self.meta
                else []

        )

        return obo_meta

    def reference(self):
        """Make relationships point to classes of ontology instead of ontology id

        This is done automatically when using the :obj:`merge` and :obj:`include`
        methods as well as the :obj:`__init__` method, but it should be called in
        case of manual changes of the relationships of a Term.
        """

        for termkey,termval in six.iteritems(self.terms):

            relvalref = { relkey: TermList(
                                    [self.terms[x] if x in self.terms
                                        else Term(x, '', '')
                                            if not isinstance(x, Term)
                                        else x for x in relval]
                               )
                        for relkey, relval in six.iteritems(termval.relations) }


            self.terms[termkey].relations.update(relvalref)

    def parse(self, stream):
        """Parse the given file using available Parser instances
        """
        for parser in Parser._instances.values():
            if parser.hook(stream=stream, path=self.path):
                # try:
                self.meta, self.terms, self.imports = parser.parse(stream)
                return
                # except TimeoutError:
                #     warnings.warn("Parsing of {} timed out".format(self.path),
                #                    pronto.utils.ProntoWarning)

    def __getitem__(self, item):
        """Overloaded object.__getitem__

        Method was overloaded to allow accessing to any Term of the Ontology
        using the Python dictionary syntax.

        Example:
            >>> cl['CL:0002380']
            <CL:0002380: oospore>
            >>> cl['CL:0002380'].relations
            {Relationship(is_a): [<CL:0000605: fungal asexual spore>]}

        """
        return self.terms[item]

    def __contains__(self, item):
        """Check if the ontology contains a term

        It is possible to check if an Ontology contains a Term
        using an id or a Term object.

        Raises:
            TypeError: if argument (or left operand) is
                neither a string nor a Term

        Example:
            >>> 'CL:0002404' in cl
            True
            >>> from pronto import Term
            >>> Term('TST:001', 'tst') in cl
            False

        """

        if isinstance(item, str) or isinstance(item, six.text_type):
            return item in self.terms
        elif isinstance(item, Term):
            return item.id in self.terms
        else:
            raise TypeError("'in <Ontology>' requires string or Term as left operand, not {}".format(type(item)))

    def __iter__(self):
        """Returns an iterator over the Terms of the Ontology

        For convenience of implementation, the returned object is actually
        a generator object that returns each term of the ontology, sorted in
        alphabetic order of their id.

        Example:
            >>> for k in uo:
            ...    if 'basepair' in k.name:
            ...       print(k)
            <UO:0000328: kilobasepair>
            <UO:0000329: megabasepair>
            <UO:0000330: gigabasepair>

        """
        terms_accessions = sorted(self.terms.keys())
        return (self.terms[i] for i in terms_accessions)

    def __len__(self):
        """Returns the number of terms in the Ontology.
        """
        return self.terms.__len__()

    def adopt(self):
        """Make terms aware of their children via complementary relationships

        This is done automatically when using the :obj:`merge` and :obj:`include`
        methods as well as the :obj:`__init__` method, but it should be called in
        case of manual editing of the parents or children of a Term.
        """

        relationships = [
            (parent, relation.complement(), term.id)
                for term in self
                    for relation in term.relations
                        for parent in term.relations[relation]
                            if relation.complement() is not None and relation.direction=="bottomup"
        ]

        # for term in self:

        #     for relation in term.relations.keys():

        #         if relation.complement() is not None and relation.direction=="bottomup":
        #             for parent in term.relations[relation]:
        #                 relationships.append( (parent, relation.complement(), term.id) )

            #if 'is_a' in term.relations.keys():
            #    for parent in term.relations['is_a']:
            #        relationships.append( (parent, 'can_be', term.id ) )

            #if 'part_of' in term.relations.keys():
            #    for parent in term.relations['part_of']:
            #        relationships.append( (parent, 'has_part', term.id ) )

            #if 'is_part' in term.relations.keys():
            #    for parent in term.relations['is_part']:
            #        relationships.append( (parent, 'part_of', term.id ) )

        for parent, rel, child in relationships:
            #if isinstance(parent, .Term):
            try:
                parent = parent.id
            except AttributeError:
                pass

            if parent in self:
                try:
                    if not child in self[parent].relations[rel]:
                        self[parent].relations[rel].append(child)
                except KeyError:
                    self[parent].relations[rel] = [child]
                    #self[parent].relations[rel].add(child)

                #if not child.id in self[parent].relations[rel]:
                #    self[parent].relations[rel].append(child)

    def include(self, *terms):
        """Add new terms to the current ontology.

        Raises:
            TypeError: when the arguments is (are) neither a TermList nor a Term.

        Note:
            This will also recursively include terms in the term's relations
            dictionnary, but it is considered bad practice to do so. If you
            want to create your own ontology, you should only add an ID (such
            as 'ONT:001') to your terms relations, and let the Ontology link
            terms with each other.

        Examples:
            Create a new ontology from scratch

            >>> from pronto import Term, Relationship
            >>> t1 = Term('ONT:001','my 1st term',
            ...           'this is my first term')
            >>> t2 = Term('ONT:002', 'my 2nd term',
            ...           'this is my second term',
            ...           {Relationship('part_of'): ['ONT:001']})
            >>> ont = Ontology()
            >>> ont.include(t1, t2)

            >>> 'ONT:002' in ont
            True
            >>> ont['ONT:001'].children
            [<ONT:002: my 2nd term>]

        """
        ref_needed = False

        for term in terms:

            if isinstance(term, TermList):
                ref_needed = ref_needed or self._include_term_list(term)
            elif isinstance(term, Term):
                ref_needed = ref_needed or self._include_term(term)
            else:
                raise TypeError('include only accepts <Term> or <TermList> as arguments')

        self.adopt()
        self.reference()

    def resolve_imports(self, import_depth):
        """Import required ontologies.
        """

        # pool = pronto.utils.ProntoPool()
        # cls = type(self)
        # #ontologize = functools.partial(Ontology, import_depth=import_depth-1)

        # for x in pool.map(pronto.utils._ontologize, ((cls,x,import_depth) for x in self.imports)):
        #     #if x is not None:
        #     try:
        #         self.merge(x)
        #     except TypeError:
        #         warnings.warn(*x)

        # pool.close()

        for i in self.imports:
            try:

                if os.path.exists(i) or i.startswith('http') or i.startswith('ftp'):
                    self.merge(Ontology(i, import_depth=import_depth-1))


                else: # try to look at neighbouring ontologies
                    self.merge(Ontology( os.path.join(os.path.dirname(self.path), i),
                                         import_depth=import_depth-1))

            except (IOError, OSError, URLError, HTTPError, ParseError) as e:
                warnings.warn("{} occured during import of "
                              "{}".format(type(e).__name__, i),
                              ProntoWarning)

    def _include_term_list(self, termlist):
        """Add terms from a TermList to the ontology.
        """
        ref_needed = False
        for term in termlist:
            ref_needed = ref_needed or self._include_term(term)
        return ref_needed

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

            for k,v in six.iteritems(term.relations):
                for i,t in enumerate(v):

                    #if isinstance(t, Term):
                    try:

                        if not t.id in self:
                            self._include_term(t)

                        term.relations[k][i] = t.id

                    except AttributeError:
                        pass

                    ref_needed = True

        self.terms[term.id] = term
        return ref_needed

    def merge(self, other):
        """Merges another ontology into the current one.

        Raises:
            TypeError: When argument is not an Ontology object.

        Example:
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
        if not isinstance(other, Ontology):
            raise TypeError("'merge' requires an Ontology as argument, not {}".format(type(other)))

        self.terms.update(other.terms)
        self._empty_cache()
        self.adopt()
        self.reference()

    def _empty_cache(self, termlist=None):
        """Empty associated cache of each Term object

        This method is called when merging Ontologies or including
        new terms in the Ontology to make sure the cache of each
        term is cleaned and avoid returning wrong memoized values
        (such as Term.rchildren() TermLists, which get memoized for
        performance concerns)
        """
        if termlist is None:
            for term in self.terms.values():
                term._empty_cache()
        else:
            for term in termlist:
                try:
                    self.terms[term.id]._empty_cache()
                except AttributeError:
                    self.terms[term]._empty_cache()

    def __getstate__(self):

        meta = frozenset( (k, frozenset(v)) for k,v in six.iteritems(self.meta) )
        imports = self.imports
        path = self.path
        terms = frozenset(term for term in self)
        return (meta, imports, path, terms)

    def __setstate__(self, state):

        self.meta = {k:list(v) for (k,v) in state[0] }
        self.imports = state[1]
        self.path = state[2]
        self.terms = {t.id:t for t in state[3]}
        self.reference()
