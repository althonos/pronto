# coding: utf-8
"""
pronto.parser
=============

This module defines the Parser virtual class.
"""
from __future__ import absolute_import

__all__ = ["BaseParser", "OboParser", "OwlXMLParser"]

from .base import BaseParser
from .obo import OboParser
from .owl import OwlXMLParser
