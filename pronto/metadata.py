
import datetime
from typing import Dict, Optional, Set

import fastobo

from .synonym import SynonymType


class Subset(object):

    name: str
    description: str

    __slots__ = ("__weakref__",) + tuple(__annotations__)  # noqa: E0602

    def __init__(self, name: str, description: str):
        self.name: str = name
        self.description: str = description

    def __eq__(self, other):
        if isinstance(other, Subset):
            return (self.name, self.description) == (other.name, other.description)
        else:
            return False

    def __lt__(self, other):
        if not isinstance(other, Subset):
            return NotImplemented
        return (self.name, self.description) < (other.name, other.description)

    def __hash__(self):
        return hash((self.name, self.description))


class Metadata(object):
    format_version: str
    data_version: Optional[str]
    ontology: Optional[str]
    date: Optional[datetime.datetime]
    default_namespace: Optional[str]
    saved_by: Optional[str]
    auto_generated_by: Optional[str]
    subsetdefs: Set[Subset]
    imports: Set[str]
    synonymtypedefs: Set[SynonymType]
    idspaces: Dict[str, str]
    remarks: Set[str]
    unreserved: Dict[str, Set[str]]

    @classmethod
    def _from_ast(cls, header: fastobo.header.HeaderFrame) -> 'Metadata':
        metadata = cls()
        for clause in header:
            if clause.raw_tag() == "format-version":
                metadata.format_version = clause.version
            elif clause.raw_tag() == "data-version":
                metadata.data_version = clause.version
            elif clause.raw_tag() == "ontology":
                metadata.ontology = clause.ontology
            elif clause.raw_tag() == "date":
                metadata.date = clause.date
            elif clause.raw_tag() == "saved-by":
                metadata.saved_by = clause.name
            elif clause.raw_tag() == "auto-generated-by":
                metadata.auto_generated_by = clause.name
            elif clause.raw_tag() == "subsetdef":
                subsetdef = Subset(str(clause.subset), clause.description)
                metadata.subsetdefs.add(subsetdef)
            elif clause.raw_tag() == "import":
                pass # TODO
            elif clause.raw_tag() == "synonymtypedef":
                scope = str(clause)
                type_ = SynonymType(str(clause.typedef), clause.description, clause.scope)
                metadata.synonymtypedefs.add(type_)
            elif clause.raw_tag() == "remark":
                metadata.remarks.add(clause.remark)
            elif clause.raw_tag() == "default-namespace":
                metadata.default_namespace = str(clause.namespace)
            elif clause.raw_tag() == "property_value":
                pass # TODO
            else:
                tag, value = clause.raw_tag(), clause.raw_value()
                metadata.unreserved.setdefault(tag, set()).add(value)
        return metadata

    def __init__(
        self,
        format_version: str = "1.4",
        data_version: Optional[str] = None,
        ontology: Optional[str] = None,
        date: Optional[datetime.datetime] = None,
        default_namespace: Optional[str] = None,
        saved_by: Optional[str] = None,
        auto_generated_by: Optional[str] = None,
        subsetdefs: Set[Subset] = None,
        imports: Set[str] = None,
        synonymtypedefs: Set[SynonymType] = None,
        idspace: Dict[str, str] = None,
        remarks: Set[str] = None,
        **unreserved: Set[str],
    ):
        self.format_version = format_version
        self.data_version = data_version
        self.ontology = ontology
        self.date = date
        self.default_namespace = default_namespace
        self.saved_by = saved_by
        self.auto_generated_by = auto_generated_by
        self.subsetdefs = set(subsetdefs) if subsetdefs is not None else set()
        self.imports = set(imports) if imports is not None else set()
        self.synonymtypedefs = set(synonymtypedefs) if synonymtypedefs is not None else set()
        self.idspace = idspace or {}
        self.remarks = remarks or set()
        self.unreserved = unreserved
