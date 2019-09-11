__version__ = "1.0.0"
__author__ = "Martin Larralde"
__author_email__ = 'martin.larralde@ens-paris-saclay.fr'
__license__ = "MIT"

from .ontology import Ontology  # noqa: F401
from .term import Term  # noqa: F401
from .definition import Definition  # noqa: F401
from .relationship import Relationship  # noqa: F401
from .synonym import Synonym, SynonymType  # noqa: F401
from .xref import Xref  # noqa: F401
