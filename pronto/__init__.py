# coding: utf-8
"""
**pronto**: a Python frontend to ontologies
===========================================

"""

from __future__ import absolute_import

__all__ = ["Ontology", "Term", "TermList", "Relationship", "Parser"]
__version__='0.5.0'
__author__='Martin Larralde'
__author_email__ = 'martin.larralde@ens-cachan.fr'

try:
    from .ontology import Ontology
    from .term import Term, TermList
    from .relationship import Relationship
    from .parser import Parser
except ImportError: # can occur when running setup.py
    pass            # with missing dependencies





