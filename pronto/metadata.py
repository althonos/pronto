import datetime
import functools
import typing
from typing import Dict, List, Optional, Set, Tuple

from .pv import PropertyValue
from .synonym import SynonymType
from .utils.meta import roundrepr, typechecked

__all__ = ["Subset", "Metadata"]


@roundrepr
@functools.total_ordering
class Subset(object):
    """A definition of a subset in an ontology.

    Attributes:
        name (`str`): The name of the subset, as an OBO short identifier.
        description (`str`): A description of the subset, as defined in the
            metadata part of the ontology file.

    """

    name: str
    description: str

    __slots__ = ("__weakref__", "name", "description")

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

    @typechecked()
    def __init__(self, name: str, description: str):
        """Create a new subset with the given name and description."""
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

    Attributes:
        format_version (`str`): The OBO format version of the referenced
            ontology. **1.4** is the default since ``pronto`` can only
            parse and write OBO documents of that format version.
        data_version (`str` or `None`): The OBO data version of the ontology,
            which is then expanded to the ``versionIRI`` if translated to
            OWL.
        ontology (`str` or `None`): The identifier of the ontology, either as
            a short OBO identifier or as a full IRI.
        date (`~datetime.datetime` or `None`): The date the ontology was last
            modified, if any.
        default_namespace (`str` or `None`): The default namespace to use for
            entity frames lacking a ``namespace`` clause.
        namespace_id_rule (`str` or `None`): The production rule for
            identifiers in the current ontology document. *soft-deprecated,
            used mostly by OBO-Edit or other outdated tools*.
        owl_axioms (`list` of `str`): A list of OWL axioms that cannot be
            expressed in OBO language, serialized in OWL2 Functional syntax.
        saved_by (`str` or `None`): The name of the person that last saved the
            ontology file.
        auto_generated_by (`str` or `None`): The name of the software that was
            used to generate the file.
        subsetdefs (`set` of `str`): A set of ontology subsets declared in the
            ontology files.
        imports (`set` of `str`): A set of references to other ontologies that
            are imported by the current ontology. OBO requires all entities
            referenced in the file to be reachable through imports (excluding
            databases cross-references).
        synonymtypedefs (`set` of `~pronto.SynonymType`): A set of user-defined
            synonym types including a description and an optional scope.
        idspaces (`dict` of `str` to couple of `str`): A mapping between a
            local ID space and a global ID space, with an optional description
            of the mapping.
        remarks (`set` of `str`): A set of general comments for this file,
            which will be preserved by a parser/serializer as opposed to
            inline comments using ``!``.
        annotations (`set` of `PropertyValue`): A set of annotations relevant
            to the whole file. OBO property-values are semantically equivalent
            to  ``owl:AnnotationProperty`` in OWL2.
        unreserved (`dict` of `str` to `set` of `str`): A mapping of
            unreserved tags to values found in the ontology header.

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

    if typing.TYPE_CHECKING:
        __annotations__: Dict[str, str]

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
        """Return `False` if the instance does not contain any metadata."""
        return any(bool(getattr(self, x)) for x in self.__annotations__)
