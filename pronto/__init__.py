# coding: utf-8
"""
**pronto**: a Python frontend to ontologies
===========================================

"""



__version__='0.1.10'
__author__='Martin Larralde'
__author_email__ = 'martin.larralde@ens-cachan.fr'

from pronto.ontology import Ontology
from pronto.term import Term, TermList
from pronto.relationship import Relationship
from pronto.parser import Parser

__all__ = ["Ontology", "Term", "TermList", "Relationship", "Parser"]
