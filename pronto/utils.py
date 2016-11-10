# coding: utf-8
"""
pronto.utils
============

This module contains some functions that are used in different parts
of the pronto library, as well as the definition of ProntoWarning.

Todo:
    * Maybe add a ProntoError class ?
"""

import six


class ProntoWarning(Warning):
    """A warning raised by pronto.

    Example:
        >>> from pronto import Ontology
        >>> import warnings
        >>> with warnings.catch_warnings(record=True) as w:
        ...    # the following ontology always has import issues (no URI in imports)
        ...    ims = Ontology('https://raw.githubusercontent.com/beny/imzml'
        ...                   '/master/data/imagingMS.obo')
        >>> print(w[-1].category)
        <class 'pronto.utils.ProntoWarning'>

    """
    pass

def unique_everseen(iterable):
    """List unique elements, preserving order. Remember all elements ever seen."""
    # unique_everseen('AAAABBBCCDAABBB')    --> A B C D
    seen = set()
    seen_add = seen.add

    for element in six.moves.filterfalse(seen.__contains__, iterable):
        seen_add(element)
        yield element

def output_str(f):
    if six.PY2:
        def new_f(*args, **kwargs):
            return f(*args, **kwargs).encode("utf-8")
    else:
        new_f = f
    return new_f
