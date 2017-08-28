# coding: utf-8
"""
a Python frontend to ontologies
"""

from __future__ import absolute_import

__version__='0.8.0'
__author__='Martin Larralde'
__author_email__ = 'martin.larralde@ens-cachan.fr'
__all__ = [
    "Ontology", "Term", "TermList", "Relationship", "Synonym", "SynonymType"
]



# try:
from .ontology import Ontology
from .term import Term, TermList
from .relationship import Relationship
from .synonym import Synonym, SynonymType
