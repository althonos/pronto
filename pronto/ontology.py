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
import gzip
import contextlib
import collections

from six.moves.urllib.error import URLError, HTTPError

from .                   import __version__
from .term               import Term, TermList
from .parser             import Parser
from .parser.owl         import etree as _etree
from .utils              import ProntoWarning, output_str
from .relationship       import Relationship


class Ontology(collections.Mapping):
    """An ontology.

    Ontologies inheriting from this class will be able to use the same API as
    providing they generated the expected structure in the :func:`_parse`
    method.

    Examples:
        Import an ontology from a remote location::

            >>> from pronto import Ontology
            >>> envo = Ontology("https://raw.githubusercontent.com/"
            ... "EnvironmentOntology/envo/master/src/envo/envo.obo")

        Merge two local ontologies and export the merge::

            >>> uo = Ontology("tests/resources/uo.obo", False)
            >>> cl = Ontology("tests/resources/cl.ont", False)
            >>> uo.merge(cl)
            >>> with open('tests/run/merge.obo', 'w') as f:
            ...     lines_count = f.write(uo.obo)

        Export an ontology with its dependencies embedded::

            >>> cl = Ontology("tests/resources/cl.ont")
            >>> with open('tests/run/cl.obo', 'w') as f:
            ...     lines_count = f.write(cl.obo)

        Use the parser argument to force usage a parser::

            >>> cl = Ontology("tests/resources/cl.ont",
            ...               parser='OwlXMLTargetParser')


    Todo:
        * Add a __repr__ method to Ontology
    """
    __slots__ = ("path", "meta", "terms", "imports", "__parsedby__")
    
    def __init__(self, path=None, imports=True, import_depth=-1, timeout=2, parser=None):
        """
        """
        self.path = path
        self.meta = {}
        self.terms = {}
        self.imports = ()
        self.__parsedby__ = None

        if path is not None:

            with self._get_handle(path, timeout) as handle:
                self.parse(handle, parser)

            if self.__parsedby__ == None:
                raise ValueError("Could not find a suitable parser to parse {}".format(path))

            self.adopt()

            self.resolve_imports(imports, import_depth, parser)
            self.reference()

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
        if isinstance(item, (str, six.text_type)):
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

    def __len__(self):
        """Returns the number of terms in the Ontology.
        """
        return len(self.terms)

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

    def parse(self, stream, parser=None):
        """Parse the given file using available Parser instances

        Raises:
            TypeError: when the parser argument is not a string or None,
            ValueError: when the parser argument is a string that does
                not name a Parser

        """

        if parser is None:
            FORCE = False
            parsers = Parser._instances.values()
        elif isinstance(parser, (str, six.text_type)):
            if parser in Parser._instances:
                FORCE = True
                parsers = [Parser._instances[parser]]
            else:
                raise ValueError("could not find parser: {}".format(parser))
        else:
            raise TypeError("parser must be {types} or None, not {actual}".format(
                types = " or ".join([six.text_type.__name__, six.binary_type.__name__]),
                actual=type(parser).__name__,
            ))

        for p in parsers:
            if p.hook(stream=stream, path=self.path, force=FORCE):
                self.meta, self.terms, self.imports = p.parse(stream)
                self.__parsedby__ = type(p).__name__
                break

    def adopt(self):
        """Make terms aware of their children via complementary relationships

        This is done automatically when using the :obj:`merge` and :obj:`include`
        methods as well as the :obj:`__init__` method, but it should be called in
        case of manual editing of the parents or children of a Term.
        """

        valid_relationships = set(Relationship._instances.keys())

        relationships = [
            (parent, relation.complement(), term.id)
                for term in six.itervalues(self.terms)
                    for relation in term.relations
                        for parent in term.relations[relation]
                        	if relation.complementary
                        		and relation.complementary in valid_relationships
        ]

        relationships.sort(key=lambda x: x[2])

        for parent, rel, child in relationships:

            if rel is None:
                break

            try:
                parent = parent.id
            except AttributeError:
                pass

            if parent in self.terms:
                try:
                    if not child in self.terms[parent].relations[rel]:
                        self.terms[parent].relations[rel].append(child)
                except KeyError:
                    self[parent].relations[rel] = [child]

        del relationships

    def reference(self):
        """Make relationships point to classes of ontology instead of ontology id

        This is done automatically when using the :obj:`merge` and :obj:`include`
        methods as well as the :obj:`__init__` method, but it should be called in
        case of manual changes of the relationships of a Term.
        """
        for termkey,termval in six.iteritems(self.terms):
            for relkey, relval in six.iteritems(termval.relations):
                temprel = TermList()
                for x in relval:
                    try:
                        temprel.append(self.terms[x])
                    except KeyError:
                        if isinstance(x, Term):
                            temprel.append(x)
                        else:
                            temprel.append(Term(x,'',''))
                self.terms[termkey].relations[relkey] = temprel
                del temprel
                del relval

            # relvalref = { relkey: TermList(
            #                         [self.terms[x] if x in self.terms
            #                             else Term(x, '', '')
            #                                 if not isinstance(x, Term)
            #                             else x for x in relval]
            #                    )
            #             for relkey, relval in six.iteritems(termval.relations) }
            # self.terms[termkey].relations.update(relvalref)

    def resolve_imports(self, imports, import_depth, parser=None):
        """Import required ontologies.
        """
        if imports and import_depth:
            for i in list(self.imports):
                try:

                    if os.path.exists(i) or i.startswith(('http', 'ftp')):
                        self.merge(Ontology(i, import_depth=import_depth-1, parser=parser))

                    else: # try to look at neighbouring ontologies
                        self.merge(Ontology( os.path.join(os.path.dirname(self.path), i),
                                             import_depth=import_depth-1, parser=parser))

                except (IOError, OSError, URLError, HTTPError, _etree.ParseError) as e:
                    warnings.warn("{} occured during import of "
                                  "{}".format(type(e).__name__, i),
                                  ProntoWarning)

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
            >>>
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
            raise TypeError("'merge' requires an Ontology as argument,"
                            " not {}".format(type(other)))

        self.terms.update(other.terms)
        self._empty_cache()
        self.adopt()
        self.reference()

    @staticmethod
    @contextlib.contextmanager
    def _get_handle(path, timeout=2):

        REMOTE = path.startswith(('http', 'ftp'))
        ZIPPED = path.endswith('gz')

        if REMOTE:
            req = six.moves.urllib.request.Request(path, headers={'HTTP_CONNECTION': 'keep-alive'})
            if not ZIPPED or (ZIPPED and six.PY3):
                handle = six.moves.urllib.request.urlopen(req, timeout=timeout)
                if ZIPPED:
                    handle = gzip.GzipFile(fileobj=handle)
            else:
                raise NotImplementedError("Cannot parse a remote zipped file (this is an urllib2 limitation)")

        else:
            if os.path.exists(path):
                handle = open(path, 'rb')
            else:
                raise OSError('Ontology file {} could not be found'.format(path))
            if ZIPPED:
                handle = gzip.GzipFile(fileobj=handle)

        try:
            yield handle
        finally:
            handle.close()

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

    def _empty_cache(self, termlist=None):
        """Empty associated cache of each Term object

        This method is called when merging Ontologies or including
        new terms in the Ontology to make sure the cache of each
        term is cleaned and avoid returning wrong memoized values
        (such as Term.rchildren() TermLists, which get memoized for
        performance concerns)
        """
        if termlist is None:
            for term in six.itervalues(self.terms):
                term._empty_cache()
        else:
            for term in termlist:
                try:
                    self.terms[term.id]._empty_cache()
                except AttributeError:
                    self.terms[term]._empty_cache()

    @output_str
    def _obo_meta(self):
        """Generates the obo metadata header

        Generated following specs of the official format guide:
        ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml

        Todo:
            * Change the `auto-generated-by` tag to be **auto-generated-by pronto pronto.__version__**

        """
        metatags = [
            "format-version", "data-version", "date", "saved-by",
            "auto-generated-by","import", "subsetdef", "synonymtypedef",
            "default-namespace", "namespace-id-rule", "idspace",
            "treat-xrefs-as-equivalent", "treat-xrefs-as-genus-differentia",
            "treat-xrefs-as-is_a", "remark", "ontology"
        ]

        obo_meta = "\n".join(

            [ # official obo tags
                x.obo if hasattr(x, 'obo') \
                    else "{}: {}".format(k,x)
                        for k in metatags[:-1]
                            if k in self.meta
                                for x in self.meta[k]
            ] + [ # eventual other metadata added to remarks
                "remark: {}: {}".format(k, x)
                    for k,v in sorted(six.iteritems(self.meta), key=lambda x: x[0])
                        for x in v
                            if k not in metatags
            ] +      ["ontology: {}".format(x) for x in self.meta["ontology"]]
                            if "ontology" in self.meta
                else ["ontology: {}".format(self.meta["namespace"][0].lower())]
                            if "namespace" in self.meta
                else []

        )

        return obo_meta

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
    @output_str
    def obo(self):
        """Returns the ontology serialized in obo format.
        """
        meta = self._obo_meta()
        if not isinstance(meta, six.text_type):
            meta = meta.decode('utf-8')
        meta = [meta] if meta else []

        if six.PY2:
            try: # if 'namespace' in self.meta:
                return "\n\n".join( meta + [
                    t.obo.decode('utf-8')
                        for t in self
                            if t.id.startswith(self.meta['namespace'][0])
                ])
            except KeyError:
                return "\n\n".join( meta + [
                    t.obo.decode('utf-8') for t in self
                ])
        elif six.PY3:
            try: # if 'namespace' in self.meta:
                return "\n\n".join( meta + [
                    t.obo for t in self
                        if t.id.startswith(self.meta['namespace'][0])
                ])
            except KeyError:
                return "\n\n".join( meta + [
                    t.obo for t in self
                ])
