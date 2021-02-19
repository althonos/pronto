"""A Python frontend to ontologies.

**pronto** is a Python agnostic library designed to work with ontologies. At
the moment, it can parse ontologies in the OBO, OBO Graphs or OWL in RDF/XML
format, on either the local host or from an network location, and export
ontologies to OBO or OBO Graphs (in JSON format).

Caution:
    Only classes and modules reachable from the top-level package ``pronto``
    are considered public and are guaranteed stable over `Semantic Versioning
    <https://semver.org/>`_. Use submodules (other than `~pronto.warnings`)
    at your own risk!

Note:
    ``pronto`` implements proper *type checking* for most of the methods and
    properties exposed in the public classes. This reproduces the behaviour
    of the Python standard library, to avoid common errors. This feature does
    however increase overhead, but can be disabled by executing Python in
    optimized mode (with the ``-O`` flag). *Parsing performances are not
    affected.*

"""

from .definition import Definition
from .entity import Entity
from .metadata import Metadata, Subset
from .ontology import Ontology
from .pv import LiteralPropertyValue, PropertyValue, ResourcePropertyValue
from .relationship import Relationship, RelationshipData, RelationshipSet
from .synonym import Synonym, SynonymData, SynonymType
from .term import Term, TermData, TermSet
from .utils import warnings
from .xref import Xref

# Using `__name__` attribute instead of directly using the name as a string
# so the linter doesn't complaint about unused imports in the top module
__all__ = [
    # modules
    "warnings",
    # classes
    Ontology.__name__,
    Entity.__name__,
    Term.__name__,
    TermData.__name__,
    TermSet.__name__,
    Metadata.__name__,
    Subset.__name__,
    Definition.__name__,
    Relationship.__name__,
    RelationshipData.__name__,
    RelationshipSet.__name__,
    Synonym.__name__,
    SynonymData.__name__,
    SynonymType.__name__,
    PropertyValue.__name__,
    LiteralPropertyValue.__name__,
    ResourcePropertyValue.__name__,
    Xref.__name__,
]

__author__ = "Martin Larralde <martin.larralde@embl.de>"
__license__ = "MIT"
__version__ = "2.4.1"

# Update the docstring with a link to the right version of the documentation
# instead of the latest.
if __doc__ is not None:
    __doc__ += f"""See Also:
    Online documentation for this version of the library on
    `Read The Docs <https://pronto.readthedocs.io/en/v{__version__}/>`_
    """
