import datetime
import typing
import weakref
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

import fastobo

from .definition import Definition
from .xref import Xref
from .synonym import Synonym, _SynonymData
from .relationship import Relationship
from .utils.repr import make_repr

if typing.TYPE_CHECKING:
    from .ontology import Ontology


class _TermData():  # noqa: R0902, R0903
    """Internal data storage of `Term` information.
    """

    id: str
    anonymous: bool
    name: Optional[str]
    alternate_ids: Set[str]
    definition: Optional[Definition]
    comment: Optional[str]
    synonyms: Set[_SynonymData]
    subsets: Set[str]
    namespace: Optional[str]
    xrefs: Set[Xref]
    intersection_of: Set[Union[str, Tuple[Relationship, str]]]
    union_of: Set[str]
    disjoint_from: Set[str]
    relationships: Dict[str, Set[str]]
    obsolete: bool
    replaced_by: Set[str]
    consider: Set[str]
    builtin: bool
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]
    annotations: Dict[str, List[str]]

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    def __init__(
        self,
        id,
        anonymous=False,
        name=None,
        alternate_ids=None,
        definition=None,
        comment=None,
        synonyms=None,
        subsets=None,
        namespace=None,
        xrefs=None,
        intersection_of=None,
        union_of=None,
        disjoint_from=None,
        relationships=None,
        obsolete=False,
        replaced_by=None,
        consider=None,
        builtin=False,
        created_by=None,
        creation_date=None,
        annotations=None,
    ):
        self.id = id
        self.anonymous = anonymous
        self.name = name
        self.alternate_ids = alternate_ids or set()
        self.definition = definition
        self.comment = comment
        self.synonyms = synonyms or set()
        self.subsets = subsets or set()
        self.namespace = namespace or None
        self.xrefs = xrefs or set()
        self.intersection_of = intersection_of or set()
        self.union_of = union_of or set()
        self.disjoint_from = disjoint_from or set()
        self.relationships = relationships or dict()
        self.obsolete = obsolete
        self.replaced_by = replaced_by or set()
        self.consider = consider or set()
        self.builtin = builtin
        self.created_by = created_by
        self.creation_date = creation_date
        self.annotations = annotations or dict()


class Term(object):

    _ontology: Callable[[], 'Ontology']
    _termdata: Callable[[], _TermData]

    __slots__  = ("__weakref__",) + tuple(__annotations__)   # noqa: E0602

    def __init__(self, ontology: 'Ontology', termdata: '_TermData'):
        self._ontology = weakref.ref(ontology)
        self._termdata = weakref.ref(termdata)

    @classmethod
    def _from_ast(cls, frame: fastobo.term.TermFrame, ontology: 'Ontology'):

        ontology._terms[str(frame.id)] = termdata = _TermData(str(frame.id))
        term = cls(ontology, termdata)

        union_of = set()
        intersection_of = set()

        for clause in frame:
            if clause.raw_tag() == "is_anonymous":
                term.anonymous = clause.anonymous
            elif clause.raw_tag() == "name":
                term.name = clause.name
            elif clause.raw_tag() == "alt_id":
                term.alternate_ids.add(str(clause.alt_id))
            elif clause.raw_tag() == "def":
                term.definition = Definition._from_ast(clause)
            elif clause.raw_tag() == "intersection_of":
                pass # TODO in `fastobo-py`
            elif clause.raw_tag() == "union_of":
                union_of.add(str(clause.term))
            elif clause.raw_tag() == "disjoint_from":
                term.disjoint_from.add(str(clause.term))
            elif clause.raw_tag() == "relationship":
                pass # TODO in fastobo-py
            elif clause.raw_tag() == "builtin":
                term.builtin = clause.builtin
            elif clause.raw_tag() == "comment":
                term.comment = clause.comment
            elif clause.raw_tag() == "consider":
                pass # TODO in fastobo-py
            elif clause.raw_tag() == "created_by":
                pass # TODO in fastobo-py
            elif clause.raw_tag() == "creation_date":
                pass # TODO in fastobo-py
            elif clause.raw_tag() == "equivalent_to":
                term.equivalent_to.add(str(clause.term))
            elif clause.raw_tag() == "is_a":
                term.relationships.setdefault("is_a", set()).add(str(clause.term))
            elif clause.raw_tag() == "is_obsolete":
                term.obsolete = clause.obsolete
            elif clause.raw_tag() == "namespace":
                term.namespace = str(clause.namespace)
            elif clause.raw_tag() == "property_value":
                pass  # TODO in here
            elif clause.raw_tag() == "replaced_by":
                pass  # TODO in fastobo-py
            elif clause.raw_tag() == "subset":
                term.subsets.add(str(clause.subset))
            elif clause.raw_tag() == "synonym":
                termdata.synonyms.add(_SynonymData._from_ast(clause.synonym))
            elif clause.raw_tag() == "xref":
                term.xrefs.add(Xref._from_ast(clause.xref))
            else:
                raise ValueError(f"unexpected clause: {clause}")

        if len(union_of) == 1:
            raise ValueError("'union_of' cannot have a cardinality of 1")
        termdata.union_of = union_of
        if len(intersection_of) == 1:
            raise ValueError("'intersection_of' cannot have a cardinality of 1")
        termdata.intersection_of = intersection_of
        return term

    def _to_ast(self) -> fastobo.term.TermFrame:
        frame = fastobo.term.TermFrame(fastobo.id.parse(self.id))
        if self.anonymous:
            frame.append(fastobo.term.IsAnonymousClause(True))
        if self.name is not None:
            frame.append(fastobo.term.NameClause(self.name))
        if self.namespace is not None:
            ns = fastobo.id.parse(self.namespace)
            frame.append(fastobo.term.NamespaceClause(ns))
        for id in sorted(self.alternate_ids):
            frame.append(fastobo.term.AltIdClause(fastobo.id.parse(id)))
        if self.definition is not None:
            frame.append(self.definition._to_ast())
        if self.comment is not None:
            frame.append(fastobo.term.CommentClause(self.comment))
        for subset in sorted(self.subsets):
            frame.append(fastobo.term.SubsetClause(fastobo.id.parse(subset)))
        for synonym in sorted(self.synonyms):
            frame.append(fastobo.term.SynonymClause(synonym._to_ast()))
        for xref in sorted(self.xrefs):
            frame.append(fastobo.term.XrefClause(xref._to_ast()))
        if self.builtin:
            frame.append(fastobo.term.BuiltinClause(True))
        # for annotations in self.annotations:
        #     pass # TODO
        for other in sorted(self.relationships.get('is_a', ())): # FIXME
            frame.append(fastobo.term.IsAClause(fastobo.id.parse(other.id)))
        # for other in sorted(self.intersection_of):
        #     pass # TODO
        for member in sorted(self.union_of):
            frame.append(fastobo.term.UnionOfClause(member))

        return frame

    def __str__(self):
        return str(self._to_ast())

    def __repr__(self):
        return make_repr("Term", self.id, name=(self.name, None))

    # --- Data descriptors ---------------------------------------------------

    @property
    def alternate_ids(self) -> Set[str]:
        return self._termdata().alternate_ids

    @alternate_ids.setter
    def alternate_ids(self, ids: Set[str]):
        if __debug__:
            if not isinstance(ids, set) or any(not isinstance(x, str) for x in ids):
                msg = "'name' must be a set of str, not {}"
                raise TypeError(msg.format(type(ids).__name__))
        self._termdata().alternate_ids = ids

    @property
    def anonymous(self) -> bool:
        return self._termdata().anonymous

    @anonymous.setter
    def anonymous(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'anonymous' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._termdata().anonymous = value

    @property
    def builtin(self) -> bool:
        return self._termdata().builtin

    @builtin.setter
    def builtin(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'builtin' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._termdata().builtin = value

    @property
    def comment(self) -> Optional[str]:
        return self._termdata().comment

    @comment.setter
    def comment(self, value: Optional[str]):
        if __debug__:
            if value is not None and not isinstance(value, str):
                msg = "'comment' must be str or None, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._termdata().comment = value

    @property
    def definition(self) -> Optional[Definition]:
        return self._termdata().definition

    @definition.setter
    def definition(self, definition: Optional[Definition]):
        if __debug__:
            if definition is not None and not isinstance(definition, Definition):
                msg = "'definition' must be a Definition, not {}"
                raise TypeError(msg.format(type(definition).__name__))
        self._termdata().definition = definition

    @property
    def disjoint_from(self) -> Set['Term']:
        ontology, termdata = self._ontology(), self._termdata()
        return {Term(ontology, ontology._terms[id]) for id in termdata.disjoint_from}


    @property
    def id(self):
        return self._termdata().id

    # @id.setter
    # def id(self, value):
    #     raise RuntimeError("cannot set `id` of terms")
    #     self._termdata().id = value

    @property
    def name(self) -> Optional[str]:
        return self._termdata().name

    @name.setter
    def name(self, value: Optional[str]):
        if __debug__:
            if value is not None and not isinstance(value, str):
                msg = "'name' must be str or None, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._termdata().name = value

    @property
    def namespace(self) -> Optional[str]:
        return self._termdata().namespace

    @namespace.setter
    def namespace(self, ns: Optional[str]):
        if __debug__:
            if ns is not None and not isinstance(ns, str):
                msg = "'namespace' must be str or None, not {}"
                raise TypeError(msg.format(type(ns).__name__))
        self._termdata().namespace = ns

    @property
    def obsolete(self) -> bool:
        return self._termdata().obsolete

    @obsolete.setter
    def obsolete(self, value: bool):
        if __debug__:
            if not isinstance(value, bool):
                msg = "'obsolete' must be bool, not {}"
                raise TypeError(msg.format(type(value).__name__))
        self._termdata().obsolete = value

    @property
    def relationships(self):
        # FIXME
        ontology, termdata = self._ontology(), self._termdata()
        return {k: ontology[v] for k,v in termdata.relationships.items()}

    @property
    def subsets(self) -> Set[str]:
        return self._termdata().subsets

    @subsets.setter
    def subsets(self, subsets: Set[str]):
        if __debug__:
            if not isinstance(subsets, set) or any(not isinstance(x, str) for x in subsets):
                msg = "'subsets' must be a set of str, not {}"
                raise TypeError(msg.format(type(subsets).__name__))
        for subset in subsets:
            subsetdefs = self._ontology().metadata.subsetdefs
            if not any(subset == subsetdef.id for subsetdef in subsetdefs):
                raise ValueError(f"undeclared subset: {subset!r}")
        self._termdata().subsets = subsets

    @property
    def synonyms(self) -> Set[Synonym]:
        ontology, termdata = self._ontology(), self._termdata()
        return {Synonym(ontology, syndata) for syndata in termdata.synonyms}

    @synonyms.setter
    def synonyms(self, synonyms: Set[Synonym]):
        if __debug__:
            if not isinstance(synonyms, set) \
            or any(not isinstance(x, Synonym) for x in synonyms):
                msg = "'synonyms' must be a set of Synonym, not {}"
                raise TypeError(msg.format(type(synonyms).__name__))
        self._termdata().synonyms = synonyms

    @property
    def union_of(self) -> Set['Term']:
        cls, termdata, ont = type(self), self._termdata(), self._ontology()
        return set(cls(ont, id) for id in termdata.union_of)

    @union_of.setter
    def union_of(self, union_of: Set['Term']):
        if __debug__:
            if not isinstance(union_of, set) or any(not isinstance(x, Term) for x in union_of):
                msg = "'union_of' must be a set of Terms, not {}"
                raise TypeError(msg.format(type(union_of).__name__))
        if len(union_of) == 1:
            raise ValueError("'union_of' cannot have a cardinality of 1")
        self._termdata().union_of = {term.id for term in union_of}

    @property
    def xrefs(self) -> Set[Xref]:
        return self._termdata().xrefs

    @xrefs.setter
    def xrefs(self, xrefs: Set[Xref]):
        if __debug__:
            if not isinstance(xrefs, set) or any(not isinstance(x, Xref) for x in xrefs):
                msg = "'xrefs' must be a set of Xref, not {}"
                raise TypeError(msg.format(type(xrefs).__name__))
        self._termdata().xrefs = xrefs
