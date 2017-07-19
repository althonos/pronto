# coding: utf-8
"""
**pronto**: a Python frontend to ontologies
===========================================

"""

from __future__ import absolute_import

__all__ = ["Ontology", "Term", "TermList", "Relationship"]
__version__='0.8.0'
__author__='Martin Larralde'
__author_email__ = 'martin.larralde@ens-cachan.fr'


try:
    from .ontology import Ontology
    from .term import Term, TermList
    from .relationship import Relationship
except ImportError:
    pass



