# coding: utf-8
"""
pronto.utils
============

This module contains some functions that are used in different parts
of the pronto library, as well as the definition of ProntoWarning.

Todo:
    * Maybe add a ProntoError class ?
"""


#def memoize(obj):
#    cache = obj.cache = {}
#
#    @functools.wraps(obj)
#    def memoizer(*args, **kwargs):
#        if args not in cache:
#            cache[args] = obj(*args, **kwargs)
#        return cache[args]
#
#    return memoizer



import functools
import errno
import os
import signal


class TimeoutError(IOError):
    pass


def timeout(seconds=60, error_message=os.strerror(errno.ETIME)):

    def decorator(func):

        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            try:
                signal.signal(signal.SIGALRM, _handle_timeout)
                signal.alarm(seconds)
            except ValueError:
                pass
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper

    return decorator


class ProntoWarning(Warning):
    """A warning raised by pronto.

    Example:

        >>> from pronto import Ontology
        >>> import warnings
        >>> with warnings.catch_warnings(record=True) as w:
        ...    # the following ontology always has import issues (no URI)
        ...    ims = Ontology('https://raw.githubusercontent.com/beny/imzml/master/data/imagingMS.obo')
        >>> print(w[-1].category)
        <class 'pronto.utils.ProntoWarning'>

    """
    pass


def explicit_namespace(attr, nsmap):
    """Explicits the namespace in an attribute name.

    Example:

        >>> from pronto.utils import explicit_namespace
        >>> ns = {'owl':'http://www.w3.org/2002/07/owl#'}
        >>> explicit_namespace('owl:Class', ns)
        '{http://www.w3.org/2002/07/owl#}Class'

    """
    prefix, term = attr.split(':', 1)
    return '{'+nsmap[prefix]+'}'+term

def parse_comment(comment):
    """Parse an rdfs:comment to extract information.

    Owl contains comment which can contain additional metadata (specially
    when the Owl file was converted from Obo to Owl). This function parses
    the comment to try to extract those metadata.

    Arguments:
        - comment (str): if containing different sections (such as 'def:',
            'functional form' or 'altdef:'), the value of those sections will
            be returned in a dictionnary. If there are not sections, the
            comment is interpreted as a description

    Todo:
        * Add more parsing special cases

    """
    if comment is None:
        return {}

    commentlines = comment.split('\n')
    parsed = {}

    for (index, line) in enumerate(commentlines):

        line = line.strip()

        if line.startswith('Functional form:'):
            if not 'other' in parsed.keys():
                parsed['other'] = {}
            parsed['other']['functional form'] = "\n".join(commentlines[index:])
            break

        if line.startswith('def:'):
            parsed['desc'] = line.split('def:')[-1].strip()

        elif ': ' in line:
            ref, value = line.split(': ', 1)
            if not 'other' in parsed.keys():
                parsed['other'] = {}
            if not ref in parsed['other']:
                parsed['other'][ref.strip()] = []
            parsed['other'][ref.strip()].append(value)

        else:
            if not 'desc' in parsed.keys():
                parsed['desc'] = "\n".join(commentlines[index:])
                break

    if not 'desc' in parsed.keys() and 'other' in parsed.keys():
        if 'tempdef' in parsed['other'].keys():
            parsed['desc'] = parsed['other']['tempdef']
            del parsed['other']['tempdef']
        if 'altdef' in parsed['other'].keys():
            parsed['desc'] = parsed['other']['altdef']
            del parsed['other']['altdef']


    return parsed

def format_accession(accession, nsmap=None):
    """Formats an accession URI/string to the YY:XXXXXXX token format.

    Arguments:
        - accession (str): the URI to be formatted
        - nsmap (dict): namespaces that can be found at the beginning of the
            accession that we want to get rid of.

    Example:

        >>> from pronto.utils import format_accession
        >>> format_accession('UO_1000003')
        'UO:1000003'
        >>> ns = {'obo':'http://purl.obolibrary.org/obo/'}
        >>> format_accession('http://purl.obolibrary.org/obo/IAO_0000601', ns)
        'IAO:0000601'

    """

    if nsmap is not None:
        for v in nsmap.values():
            accession = accession.replace(v, '')

    if not accession.startswith('_'):
        accession = accession.replace('_', ':')

    return accession




