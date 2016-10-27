# coding: utf-8
"""
**pronto**: a Python frontend to ontologies
===========================================

"""

from __future__ import absolute_import

__all__ = ["Ontology", "Term", "TermList", "Relationship", "Parser"]
__version__='0.4.2'
__author__='Martin Larralde'
__author_email__ = 'martin.larralde@ens-cachan.fr'

from .ontology import Ontology
from .term import Term, TermList
from .relationship import Relationship
from .parser import Parser




