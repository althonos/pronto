# coding: utf-8
"""Definition of the `Ontology` class.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import io
import json
import os
import warnings
import operator
import six
import gzip
import datetime
import contextlib
import collections

from six.moves.urllib.error import URLError, HTTPError

from . import __version__
from .term import Term, TermList
from .parser import BaseParser
from .parser.owl import etree as _etree
from .utils import ProntoWarning, output_str
from .relationship import Relationship


class Ontology(collections.Mapping):
    """An ontology.

    Ontologies inheriting from this class will be able to use the same API as
    providing they generated the expected structure in the :func:`_parse`
    method.

    Attributes:
        meta (dict): the metatada contained in the `Ontology`.
        terms (dict): the terms of the ontology. Not very useful to
            access directly, since `Ontology` provides many useful
            shortcuts and features to access them.
        imports (list): a list of paths and/or URLs to additional
            ontologies the ontology depends on.
        path (str, optional): the path to the ontology, if any.


    Examples:
        Import an ontology from a remote location::

            >>> from pronto import Ontology
            >>> envo = Ontology("http://purl.obolibrary.org/obo/bfo.owl")

        Merge two local ontologies and export the merge::

            >>> uo = Ontology("tests/resources/uo.obo", False)
            >>> cl = Ontology("tests/resources/cl.ont.gz", False)
            >>> uo.merge(cl)
            >>> with open('tests/run/merge.obo', 'w') as f:
            ...     f.write(uo.obo) # doctest: +SKIP

        Export an ontology with its dependencies embedded::

            >>> cl = Ontology("tests/resources/cl.ont.gz")
            >>> with open('tests/run/cl.obo', 'w') as f:
            ...     f.write(cl.obo) # doctest: +SKIP

        Use the parser argument to force usage a parser::

            >>> cl = Ontology("tests/resources/cl.ont.gz",
            ...               parser='OwlXMLParser')

    """

    __slots__ = ("path", "meta", "terms", "imports", "_parsed_by", "typedefs")

    def __init__(self, handle=None, imports=True, import_depth=-1, timeout=2, parser=None):
        """Create an `Ontology` instance from a file handle or a path.

        Arguments:
            handle (io.IOBase or str): the location of the file (either
                a path on the local filesystem, or a FTP or HTTP URL),
                a readable file handle containing an ontology, or `None`
                to create a new ontology from scratch.
            imports (bool, optional): if `True` (the default), embed the
                ontology imports into the returned instance.
            import_depth (int, optional): The depth up to which the
                imports should be resolved. Setting this to 0 is
                equivalent to setting ``imports`` to `False`. Leave
                as default (-1) to handle all the imports.
            timeout (int, optional): The timeout in seconds for network
                operations.
            parser (~pronto.parser.BaseParser, optional): A parser
                instance to use. Leave to `None` to autodetect.

        """
        self.meta = {}
        self.terms = {}
        self.imports = ()
        self._parsed_by = None

        if handle is None:
            self.path = None
        elif hasattr(handle, 'read'):
            self.path = getattr(handle, 'name', None) \
                     or getattr(handle, 'url', None) \
                     or getattr(handle, 'geturl', lambda: None)()
            self.parse(handle, parser)
        elif isinstance(handle, six.string_types):
            self.path = handle
            with self._get_handle(handle, timeout) as handle:
                self.parse(handle, parser)
        else:
            actual = type(handle).__name__
            raise TypeError("Invalid type for 'handle': expected None, file "
                            "handle or string, found {}".format(actual))

        if handle is not None and self._parsed_by is None:
            raise ValueError("Could not find a suitable parser to parse {}".format(handle))

        self.adopt()
        self.resolve_imports(imports, import_depth, parser)
        self.reference()

    def __repr__(self):
        if self.path is not None:
            return "Ontology(\"{}\")".format(self.path)
        return super(Ontology, self).__repr__()

    def __contains__(self, item):
        """Check if the ontology contains a term.

        It is possible to check if an Ontology contains a Term
        using an id or a Term instance.

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
        if isinstance(item, six.string_types):
            return item in self.terms
        elif isinstance(item, Term):
            return item.id in self.terms
        else:
            raise TypeError("'in <Ontology>' requires string or Term as left "
                            "operand, not {}".format(type(item)))

    def __iter__(self):
        """Return an iterator over the Terms of the Ontology.

        For convenience of implementation, the returned instance is
        actually a generator that yields each term of the ontology,
        sorted in the definition order in the ontology file.

        Example:
            >>> for k in uo:
            ...    if 'basepair' in k.name:
            ...       print(k)
            <UO:0000328: kilobasepair>
            <UO:0000329: megabasepair>
            <UO:0000330: gigabasepair>
        """
        return six.itervalues(self.terms)

    def __getitem__(self, item):
        """Get a term in the `Ontology`.

        Method was overloaded to allow accessing to any Term of the
        `Ontology` using the Python dictionary syntax.

        Example:
            >>> cl['CL:0002380']
            <CL:0002380: oospore>
            >>> cl['CL:0002380'].relations
            {Relationship('is_a'): [<CL:0000605: fungal asexual spore>]}

        """
        return self.terms[item]

    def __len__(self):
        """Return the number of terms in the Ontology.
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
        """Parse the given file using available `BaseParser` instances.

        Raises:
            TypeError: when the parser argument is not a string or None.
            ValueError: when the parser argument is a string that does
                not name a `BaseParser`.

        """
        force, parsers = self._get_parsers(parser)

        try:
            stream.seek(0)
            lookup = stream.read(1024)
            stream.seek(0)
        except (io.UnsupportedOperation, AttributeError):
            lookup = None

        for p in parsers:
            if p.hook(path=self.path, force=force, lookup=lookup):
                self.meta, self.terms, self.imports, self.typedefs = p.parse(stream)
                self._parsed_by = p.__name__
                break

    def _get_parsers(self, name):
        """Return the appropriate parser asked by the user.

        Todo:
            Change `Ontology._get_parsers` behaviour to look for parsers
            through a setuptools entrypoint instead of mere subclasses.
        """

        parserlist = BaseParser.__subclasses__()
        forced = name is None

        if isinstance(name, (six.text_type, six.binary_type)):
            parserlist = [p for p in parserlist if p.__name__ == name]
            if not parserlist:
                raise ValueError("could not find parser: {}".format(name))

        elif name is not None:
            raise TypeError("parser must be {types} or None, not {actual}".format(
                types=" or ".join([six.text_type.__name__, six.binary_type.__name__]),
                actual=type(parser).__name__,
            ))

        return not forced, parserlist


    def adopt(self):
        """Make terms aware of their children.

        This is done automatically when using the `~Ontology.merge` and
        `~Ontology.include` methods as well as the `~Ontology.__init__`
        method, but it should be called in case of manual editing of the
        parents or children of a `Term`.

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

        relationships.sort(key=operator.itemgetter(2))

        for parent, rel, child in relationships:

            if rel is None:
                break

            try:
                parent = parent.id
            except AttributeError:
                pass

            if parent in self.terms:
                try:
                    if child not in self.terms[parent].relations[rel]:
                        self.terms[parent].relations[rel].append(child)
                except KeyError:
                    self[parent].relations[rel] = [child]

        del relationships

    def reference(self):
        """Make relations point to ontology terms instead of term ids.

        This is done automatically when using the :obj:`merge` and :obj:`include`
        methods as well as the :obj:`__init__` method, but it should be called in
        case of manual changes of the relationships of a Term.
        """
        for termkey, termval in six.iteritems(self.terms):
            termval.relations.update(
                (relkey, TermList(
                    (self.terms.get(x) or Term(x, '', '')
                    if not isinstance(x, Term) else x) for x in relval
                )) for relkey, relval in six.iteritems(termval.relations)
            )

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
        """Merge another ontology into the current one.

        Raises:
            TypeError: When argument is not an Ontology object.

        Example:
            >>> from pronto import Ontology
            >>> nmr = Ontology('tests/resources/nmrCV.owl', False)
            >>> po = Ontology('tests/resources/po.obo.gz', False)
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
                raise io.UnsupportedOperation("Cannot parse a remote zipped file (this is an urllib2 limitation)")

        elif os.path.exists(path):
            handle = gzip.GzipFile(path) if ZIPPED else open(path, 'rb')
        else:
            raise OSError('Ontology file {} could not be found'.format(path))

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
        """Add a single term to the current ontology.

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

                        if t.id not in self:
                            self._include_term(t)

                        v[i] = t.id

                    except AttributeError:
                        pass

                    ref_needed = True

        self.terms[term.id] = term
        return ref_needed

    def _empty_cache(self, termlist=None):
        """Empty the cache associated with each `Term` instance.

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
        """Generate the obo metadata header and updates metadata.

        When called, this method will create appropriate values for the
        ``auto-generated-by`` and ``date`` fields.

        Note:
            Generated following specs of the unofficial format guide:
            ftp://ftp.geneontology.org/pub/go/www/GO.format.obo-1_4.shtml
        """
        metatags = (
            "format-version", "data-version", "date", "saved-by",
            "auto-generated-by", "import", "subsetdef", "synonymtypedef",
            "default-namespace", "namespace-id-rule", "idspace",
            "treat-xrefs-as-equivalent", "treat-xrefs-as-genus-differentia",
            "treat-xrefs-as-is_a", "remark", "ontology"
        )

        meta = self.meta.copy()
        meta['auto-generated-by'] = ['pronto v{}'.format(__version__)]
        meta['date'] = [datetime.datetime.now().strftime('%d:%m:%Y %H:%M')]

        obo_meta = "\n".join(

            [ # official obo tags
                x.obo if hasattr(x, 'obo') \
                    else "{}: {}".format(k,x)
                        for k in metatags[:-1]
                            for x in meta.get(k, ())
            ] + [ # eventual other metadata added to remarksmock.patch in production code
                "remark: {}: {}".format(k, x)
                    for k,v in sorted(six.iteritems(meta), key=operator.itemgetter(0))
                        for x in v
                            if k not in metatags
            ] + (     ["ontology: {}".format(x) for x in meta["ontology"]]
                            if "ontology" in meta
                 else ["ontology: {}".format(meta["namespace"][0].lower())]
                            if "namespace" in meta
                 else [])

        )

        return obo_meta

    @property
    def json(self):
        """str: the ontology serialized in json format.
        """
        return json.dumps(self.terms, indent=4, sort_keys=True,
                          default=operator.attrgetter("__deref__"))

    @property
    def obo(self):
        """str: the ontology serialized in obo format.
        """
        meta = self._obo_meta()
        meta = [meta] if meta else []
        newline = "\n\n" if six.PY3 else "\n\n".encode('utf-8')

        try: # if 'namespace' in self.meta:
            return newline.join( meta + [
                r.obo for r in self.typedefs
            ] + [
                t.obo for t in self
                    if t.id.startswith(self.meta['namespace'][0])
            ])
        except KeyError:
            return newline.join( meta + [
                r.obo for r in self.typedefs
            ] + [
                t.obo for t in self
            ])
