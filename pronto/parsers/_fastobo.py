import functools
import typing
import warnings
from typing import Union
from operator import attrgetter

import fastobo

from ..entity import EntityData
from ..metadata import Metadata, Subset
from ..definition import Definition
from ..ontology import Ontology
from ..term import Term, TermData
from ..pv import PropertyValue, LiteralPropertyValue, ResourcePropertyValue
from ..xref import Xref
from ..synonym import Synonym, SynonymData, SynonymType
from ..relationship import Relationship, RelationshipData
from ..utils.warnings import NotImplementedWarning

# --- Type Hint --------------------------------------------------------------

DefClause = Union[fastobo.term.DefClause, fastobo.typedef.DefClause]

# --- Parser interface -------------------------------------------------------


class FastoboParser:

    ont: "Ontology"

    @staticmethod
    def extract_xref(xref: fastobo.xref.Xref) -> Xref:
        """Get a `Xref` from a fastobo.xref.Xref.
        """
        return _extract_xref(xref)

    @staticmethod
    def extract_synonym_data(syn: fastobo.syn.Synonym) -> SynonymData:
        """Get a `SynonymData` from a `fastobo.syn.Synonym`.
        """
        return _extract_synonym_data(syn)

    @staticmethod
    def extract_definition(clause: DefClause) -> Definition:
        """Get a `Definition` object from a `DefClause`.
        """
        return _extract_definition(clause)

    @staticmethod
    def extract_property_value(pv: fastobo.pv.AbstractPropertyValue) -> PropertyValue:
        """Get a `PropertyValue` from a `fastobo.pv.AbstractPropertyValue`.
        """
        return _extract_property_value(pv)

    # --- Frame processing ---------------------------------------------------

    def extract_metadata(self, header: fastobo.header.HeaderFrame) -> Metadata:
        """Extract a `Metadata` from a `HeaderFrame`.
        """
        metadata = Metadata()
        for clause in header:
            process_clause_header(clause, metadata)
        return metadata

    __non_one_clause = {k: attrgetter(k) for k in ("union_of", "intersection_of")}

    def enrich_term(self, frame: fastobo.term.TermFrame) -> Term:
        """Given a `TermFrame`, create a new `Term` or enrich an existing one.
        """
        # Create a term, or get the existing one if any
        id_ = str(frame.id)
        try:
            term = self.ont.create_term(id_)
        except ValueError:
            term = self.ont.get_term(id_)
        data = term._data()
        # Process all clauses in the frame
        for clause in frame:
            process_clause_term(clause, data)
        # check cardinality of constrained clauses
        for attr, getter in self.__non_one_clause.items():
            if len(getter(data)) == 1:
                raise ValueError(f"{attr!r} cannot have a cardinality of 1")
        # return the enriched term
        return term

    def enrich_relationship(self, frame: fastobo.typedef.TypedefFrame) -> Relationship:
        """Given a `TypedefFrame`, create or enrich a `Relationship`.
        """
        # Create a relationship, or get the existing one if any
        id_ = str(frame.id)
        try:
            rship = self.ont.create_relationship(id_)
        except ValueError:
            rship = self.ont.get_relationship(id_)
        data = rship._data()
        # Process all clauses in the frame
        for clause in frame:
            process_clause_typedef(clause, data)
        # check cardinality of constrained clauses
        for attr, getter in self.__non_one_clause.items():
            if len(getter(data)) == 1:
                raise ValueError(f"{attr!r} cannot have a cardinality of 1")
        # return the enriched relationship
        return rship


# --- Miscellaneous AST nodes ------------------------------------------------


def _extract_definition(clause: DefClause) -> Definition:
    return Definition(clause.definition, map(_extract_xref, clause.xrefs))


def _extract_property_value(pv: fastobo.pv.AbstractPropertyValue) -> PropertyValue:
    if isinstance(pv, fastobo.pv.LiteralPropertyValue):
        return LiteralPropertyValue(str(pv.relation), pv.value, str(pv.datatype))
    elif isinstance(pv, fastobo.pv.ResourcePropertyValue):
        return ResourcePropertyValue(str(pv.relation), str(pv.value))
    else:
        msg = "'pv' must be AbstractPropertyValue, not {}"
        raise TypeError(msg.format(type(pv).__name__))


def _extract_synonym_data(syn: fastobo.syn.Synonym) -> SynonymData:
    xrefs = map(_extract_xref, syn.xrefs)
    type_ = str(syn.type) if syn.type is not None else None
    return SynonymData(syn.desc, syn.scope, type_, xrefs)


def _extract_xref(xref: fastobo.xref.Xref) -> Xref:
    return Xref(str(xref.id), xref.desc)


# --- Header clauses ---------------------------------------------------------


@functools.singledispatch
def process_clause_header(clause: fastobo.header.BaseHeaderClause, meta: Metadata):
    raise TypeError(f"unexpected type: {type(clause).__name__}")


@process_clause_header.register(fastobo.header.AutoGeneratedByClause)
def _process_clause_header_auto_generated_by(clause, meta):
    meta.auto_generated_by = clause.name


@process_clause_header.register(fastobo.header.DataVersionClause)
def _process_clause_header_data_version(clause, meta):
    meta.data_version = clause.version


@process_clause_header.register(fastobo.header.DateClause)
def _process_clause_header_date(clause, meta):
    meta.date = clause.date


@process_clause_header.register(fastobo.header.DefaultNamespaceClause)
def _process_clause_header_default_namespace(clause, meta):
    meta.default_namespace = str(clause.namespace)


@process_clause_header.register(fastobo.header.FormatVersionClause)
def _process_clause_header_format_version(clause, meta):
    meta.format_version = clause.version


@process_clause_header.register(fastobo.header.IdspaceClause)
def _process_clause_header_idspace(clause, meta):
    meta.idspace[str(clause.prefix)] = str(clause.url), clause.description


@process_clause_header.register(fastobo.header.ImportClause)
def _process_clause_header_import(clause, meta):
    meta.imports.add(clause.reference)


@process_clause_header.register(fastobo.header.OntologyClause)
def _process_clause_header_ontology(clause, meta):
    meta.ontology = clause.ontology


@process_clause_header.register(fastobo.header.OwlAxiomsClause)
def _process_clause_header_owl_axioms(clause, meta):
    meta.owl_axioms.append(clause.axioms)


@process_clause_header.register(fastobo.header.RemarkClause)
def _process_clause_header_remark(clause, meta):
    meta.remarks.add(clause.remark)


@process_clause_header.register(fastobo.header.SavedByClause)
def _process_clause_header_saved_by(clause, meta):
    meta.saved_by = clause.name


@process_clause_header.register(fastobo.header.SubsetdefClause)
def _process_clause_header_subsetdef(clause, meta):
    meta.subsetdefs.add(Subset(str(clause.subset), clause.description))


@process_clause_header.register(fastobo.header.SynonymTypedefClause)
def _process_clause_header_synonymtypedef(clause, meta):
    meta.synonymtypedefs.add(
        SynonymType(str(clause.typedef), clause.description, clause.scope)
    )


@process_clause_header.register(fastobo.header.TreatXrefsAsEquivalentClause)
@process_clause_header.register(fastobo.header.TreatXrefsAsGenusDifferentiaClause)
@process_clause_header.register(fastobo.header.TreatXrefsAsHasSubclassClause)
@process_clause_header.register(fastobo.header.TreatXrefsAsIsAClause)
@process_clause_header.register(fastobo.header.TreatXrefsAsRelationshipClause)
@process_clause_header.register(
    fastobo.header.TreatXrefsAsReverseGenusDifferentiaClause
)
def _process_clause_header_treat_xrefs(clause, meta):
    warnings.warn(
        f"cannot process `{clause}` macro", NotImplementedWarning, stacklevel=3
    )


@process_clause_header.register(fastobo.header.NamespaceIdRuleClause)
def _process_clause_header_namespace_id_rule(clause, meta):
    meta.namespace_id_rule = clause.rule


@process_clause_header.register(fastobo.header.UnreservedClause)
def _process_clause_header_unreserved(clause, meta):
    meta.unreserved.setdefault(clause.raw_tag(), set()).add(clause.raw_value())


# --- Term & Typedef clauses -------------------------------------------------


@functools.singledispatch
def process_clause_term(clause: fastobo.term.BaseTermClause, term: TermData):
    """Populate the proper `term` field with data extracted from `clause`.
    """
    raise TypeError(f"unexpected type: {type(clause).__name__}")


@functools.singledispatch
def process_clause_typedef(
    clause: fastobo.typedef.BaseTypedefClause, rel: RelationshipData
):
    """Populate the proper `rel` field with data extracted from `clause`.
    """
    raise TypeError(f"unexpected type: {type(clause).__name__}")


@process_clause_term.register(fastobo.term.AltIdClause)
@process_clause_typedef.register(fastobo.typedef.AltIdClause)
def _process_clause_entity_alt_id(clause, entity):
    entity.alternate_ids.add(str(clause.alt_id))


@process_clause_term.register(fastobo.term.BuiltinClause)
@process_clause_typedef.register(fastobo.typedef.BuiltinClause)
def _process_clause_entity_builtin(clause, entity):
    entity.builtin = clause.builtin


@process_clause_term.register(fastobo.term.CommentClause)
@process_clause_typedef.register(fastobo.typedef.CommentClause)
def _process_clause_entity_comment(clause, entity):
    entity.comment = clause.comment


@process_clause_term.register(fastobo.term.ConsiderClause)
def _process_clause_term_consider(clause, entity):
    entity.consider.add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.ConsiderClause)
def _process_clause_typedef_consider(clause, entity):
    entity.consider.add(str(clause.typedef))


@process_clause_term.register(fastobo.term.CreatedByClause)
@process_clause_typedef.register(fastobo.typedef.CreatedByClause)
def _process_clause_entity_created_by(clause, entity):
    entity.created_by = clause.creator


@process_clause_term.register(fastobo.term.CreationDateClause)
@process_clause_typedef.register(fastobo.typedef.CreationDateClause)
def _process_clause_entity_creation_date(clause, entity):
    entity.creation_date = clause.date


@process_clause_term.register(fastobo.term.DefClause)
@process_clause_typedef.register(fastobo.typedef.DefClause)
def _process_clause_entity_definition(clause, entity):
    entity.definition = _extract_definition(clause)


@process_clause_term.register(fastobo.term.DisjointFromClause)
def _process_clause_term_disjoint_from(clause, entity):
    entity.disjoint_from.add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.DisjointFromClause)
def _process_clause_typedef_disjoint_from(clause, entity):
    entity.disjoint_from.add(str(clause.typedef))


@process_clause_typedef.register(fastobo.typedef.DisjointOverClause)
def _process_clause_typedef_disjoint_over(clause, entity):
    entity.disjoint_over.add(str(clause.typedef))


@process_clause_typedef.register(fastobo.typedef.DomainClause)
def _process_clause_typedef_domain(clause, entity):
    entity.domain = str(clause.domain)


@process_clause_term.register(fastobo.term.EquivalentToClause)
def _process_clause_term_equivalent_to(clause, entity):
    entity.equivalent_to.add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.EquivalentToClause)
def _process_clause_typedef_equivalent_to(clause, entity):
    entity.equivalent_to.add(str(clause.typedef))


@process_clause_typedef.register(fastobo.typedef.EquivalentToChainClause)
def _process_clause_typedef_equivalent_to_chain(clause, entity):
    warnings.warn(
        f"cannot process `{clause}` macro", NotImplementedWarning, stacklevel=3
    )


@process_clause_typedef.register(fastobo.typedef.ExpandAssertionToClause)
def _process_clause_typedef_expand_assertion_to(clause, entity):
    entity.expand_assertion_to.add(_extract_definition(clause))


@process_clause_typedef.register(fastobo.typedef.ExpandExpressionToClause)
def _process_clause_typedef_expand_expression_to(clause, entity):
    entity.expand_expression_to.add(_extract_definition(clause))


@process_clause_typedef.register(fastobo.typedef.HoldsOverChainClause)
def _process_clause_typedef_holds_over_chain(clause, entity):
    entity.holds_over_chain.add((str(clause.first), str(clause.last)))


@process_clause_term.register(fastobo.term.IntersectionOfClause)
def _process_clause_term_intersection_of(clause, entity):
    if clause.typedef is None:
        entity.intersection_of.add(str(clause.term))
    else:
        entity.intersection_of.add((str(clause.typedef), str(clause.term)))


@process_clause_typedef.register(fastobo.typedef.IntersectionOfClause)
def _process_clause_typedef_intersection_of(clause, entity):
    entity.intersection_of.add(str(clause.typedef))


@process_clause_typedef.register(fastobo.typedef.InverseOfClause)
def _process_clause_typedef_inverse_of(clause, entity):
    entity.inverse_of = str(clause.typedef)


@process_clause_term.register(fastobo.term.IsAClause)
def _process_clause_term_is_a(clause, entity):
    entity.relationships.setdefault("is_a", set()).add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.IsAClause)
def _process_clause_typedef_is_a(clause, entity):
    entity.relationships.setdefault("is_a", set()).add(str(clause.typedef))


@process_clause_term.register(fastobo.term.IsAnonymousClause)
@process_clause_typedef.register(fastobo.typedef.IsAnonymousClause)
def _process_clause_entity_is_anonymous(clause, entity):
    entity.anonymous = clause.anonymous


@process_clause_typedef.register(fastobo.typedef.IsAntiSymmetricClause)
def _process_clause_typedef_is_anti_symmetric(clause, entity):
    entity.antisymmetric = clause.antisymmetric


@process_clause_typedef.register(fastobo.typedef.IsAsymmetricClause)
def _process_clause_typedef_is_asymmetric(clause, entity):
    entity.asymmetric = clause.asymmetric


@process_clause_typedef.register(fastobo.typedef.IsClassLevelClause)
def _process_clause_typedef_is_class_level(clause, entity):
    entity.class_level = clause.class_level


@process_clause_typedef.register(fastobo.typedef.IsCyclicClause)
def _process_clause_typedef_is_cyclic(clause, entity):
    entity.cyclic = clause.cyclic


@process_clause_typedef.register(fastobo.typedef.IsFunctionalClause)
def _process_clause_typedef_is_functional(clause, entity):
    entity.functional = clause.functional


@process_clause_typedef.register(fastobo.typedef.IsInverseFunctionalClause)
def _process_clause_typedef_is_inverse_functional(clause, entity):
    entity.inverse_functional = clause.inverse_functional


@process_clause_typedef.register(fastobo.typedef.IsMetadataTagClause)
def _process_clause_typedef_is_metadata_tag(clause, entity):
    entity.metadata_tag = clause.metadata_tag


@process_clause_typedef.register(fastobo.typedef.IsObsoleteClause)
def _process_clause_typedef_is_obsolete(clause, entity):
    entity.obsolete = clause.obsolete


@process_clause_typedef.register(fastobo.typedef.IsReflexiveClause)
def _process_clause_typedef_is_reflexive(clause, entity):
    entity.reflexive = clause.reflexive


@process_clause_typedef.register(fastobo.typedef.IsSymmetricClause)
def _process_clause_typedef_is_symmetric(clause, entity):
    entity.symmetric = clause.symmetric


@process_clause_typedef.register(fastobo.typedef.IsTransitiveClause)
def _process_clause_typedef_is_transitive(clause, entity):
    entity.transitive = clause.transitive


@process_clause_term.register(fastobo.term.IsObsoleteClause)
@process_clause_typedef.register(fastobo.typedef.IsObsoleteClause)
def _process_clause_entity_is_obsolete(clause, entity):
    entity.obsolete = clause.obsolete


@process_clause_term.register(fastobo.term.NameClause)
@process_clause_typedef.register(fastobo.typedef.NameClause)
def _process_clause_entity_name(clause, entity):
    entity.name = clause.name


@process_clause_term.register(fastobo.term.NamespaceClause)
@process_clause_typedef.register(fastobo.typedef.NamespaceClause)
def _process_clause_entity_namespace(clause, entity):
    entity.namespace = str(clause.namespace)


@process_clause_header.register(fastobo.header.PropertyValueClause)
@process_clause_term.register(fastobo.term.PropertyValueClause)
@process_clause_typedef.register(fastobo.typedef.PropertyValueClause)
def _process_clause_entity_property_value(clause, entity):
    entity.annotations.add(_extract_property_value(clause.property_value))


@process_clause_typedef.register(fastobo.typedef.RangeClause)
def _process_clause_typedef_range(clause, entity):
    entity.range = str(clause.range)


@process_clause_term.register(fastobo.term.RelationshipClause)
def _process_clause_term_relationship(clause, entity):
    entity.relationships.setdefault(str(clause.typedef), set()).add(str(clause.term))


@process_clause_term.register(fastobo.typedef.RelationshipClause)
def _process_clause_typedef_relationship(clause, entity):
    entity.relationships.setdefault(str(clause.typedef), set()).add(str(clause.target))


@process_clause_term.register(fastobo.term.ReplacedByClause)
def _process_clause_term_replaced_by(clause, entity):
    entity.replaced_by.add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.ReplacedByClause)
def _process_clause_typedef_replaced_by(clause, entity):
    entity.replaced_by.add(str(clause.typedef))


@process_clause_term.register(fastobo.term.SubsetClause)
@process_clause_typedef.register(fastobo.typedef.SubsetClause)
def _process_clause_entity_subset(clause, entity):
    entity.subsets.add(str(clause.subset))


@process_clause_term.register(fastobo.term.SynonymClause)
@process_clause_typedef.register(fastobo.typedef.SynonymClause)
def _process_clause_entity_synonym(clause, entity):
    entity.synonyms.add(_extract_synonym_data(clause.synonym))


@process_clause_typedef.register(fastobo.typedef.TransitiveOverClause)
def _process_clause_typedef_transitive_over(clause, entity):
    entity.transitive_over.add(str(clause.typedef))


@process_clause_term.register(fastobo.term.UnionOfClause)
def _process_clause_term_union_of(clause, entity):
    entity.union_of.add(str(clause.term))


@process_clause_typedef.register(fastobo.typedef.UnionOfClause)
def _process_clause_typedef_union_of(clause, entity):
    entity.union_of.add(str(clause.term))


@process_clause_term.register(fastobo.term.XrefClause)
@process_clause_typedef.register(fastobo.typedef.XrefClause)
def _process_clause_entity_xref(clause, entity):
    entity.xrefs.add(_extract_xref(clause.xref))
