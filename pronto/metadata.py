import datetime
import functools
import typing
from typing import Dict, List, Optional, Set, Tuple, Union

from .synonym import SynonymType
from .pv import PropertyValue
from .utils.impl import set
from .utils.meta import roundrepr, typechecked


@roundrepr
@functools.total_ordering
class Subset(object):
    """A definition of a subset in an ontology.
    """

    name: str
    description: str

    __slots__ = ("__weakref__", "name", "description")

    @typechecked()
    def __init__(self, name: str, description: str):
        self.name: str = name
        self.description: str = description

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Subset):
            return self.name == other.name
        return False

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Subset):
            return typing.cast(bool, NotImplemented)
        return self.name < other.name

    def __hash__(self) -> int:
        return hash((Subset, self.name))


class Metadata(object):
    """A mapping containing metadata about the current ontology.
    """

    format_version: Optional[str]
    data_version: Optional[str]
    ontology: Optional[str]
    date: Optional[datetime.datetime]
    default_namespace: Optional[str]
    namespace_id_rule: Optional[str]
    owl_axioms: List[str]
    saved_by: Optional[str]
    auto_generated_by: Optional[str]
    subsetdefs: Set[Subset]
    imports: Set[str]
    synonymtypedefs: Set[SynonymType]
    idspaces: Dict[str, Tuple[str, Optional[str]]]  # FIXME: better typing?
    remarks: Set[str]
    annotations: Set[PropertyValue]
    unreserved: Dict[str, Set[str]]

    def __init__(
        self,
        format_version: Optional[str] = "1.4",
        data_version: Optional[str] = None,
        ontology: Optional[str] = None,
        date: Optional[datetime.datetime] = None,
        default_namespace: Optional[str] = None,
        namespace_id_rule: Optional[str] = None,
        owl_axioms: Optional[List[str]] = None,
        saved_by: Optional[str] = None,
        auto_generated_by: Optional[str] = None,
        subsetdefs: Set[Subset] = None,
        imports: Optional[Dict[str, str]] = None,
        synonymtypedefs: Set[SynonymType] = None,
        idspaces: Dict[str, Tuple[str, Optional[str]]] = None,
        remarks: Set[str] = None,
        annotations: Set[PropertyValue] = None,
        **unreserved: Set[str],
    ):
        """Create a new `Metadata` instance.

        Arguments:
            format_version (str): the OBO format version of the referenced
                ontology. **1.4** is the default since ``pronto`` can only
                parse and write OBO documents of that format version.
            data_version (str or None): the OBO data version of the ontology,
                which is then expanded to the ``versionIRI`` if translated to
                OWL.

        """
        self.format_version = format_version
        self.data_version = data_version
        self.ontology = ontology
        self.date = date
        self.default_namespace = default_namespace
        self.namespace_id_rule = namespace_id_rule
        self.owl_axioms = owl_axioms or list()
        self.saved_by = saved_by
        self.auto_generated_by = auto_generated_by
        self.subsetdefs = set(subsetdefs) if subsetdefs is not None else set()
        self.imports = set(imports) if imports is not None else set()
        self.synonymtypedefs = (
            set(synonymtypedefs) if synonymtypedefs is not None else set()
        )
        self.idspaces = idspaces or dict()
        self.remarks = remarks or set()
        self.annotations = annotations or set()
        self.unreserved = unreserved

    def __bool__(self) -> bool:
        """Return `False` if the instance does not contain any metadata.
        """
        return any(bool(getattr(self, x)) for x in self.__annotations__)
