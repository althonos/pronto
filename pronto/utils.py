# coding: utf-8
"""
pronto.utils
============

This module contains some functions that are used in different parts
of the pronto library, as well as the definition of ProntoWarning.

Todo:
    * Maybe add a ProntoError class ?
"""

#import functools
#import errno
#import os
#import signal
#import itertools
import six
import atexit

import multiprocessing
import multiprocessing.pool
import multiprocessing.queues

from six.moves.urllib.error import URLError, HTTPError

try:
    from lxml.etree import XMLSyntaxError as ParseError
except ImportError: # pragma: no cover
    from xml.etree.ElementTree import ParseError

class TimeoutError(IOError):
    pass



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


# def timeout(seconds=60, error_message=os.strerror(errno.ETIME)):

#     def decorator(func):

#         def _handle_timeout(signum, frame):
#             raise TimeoutError(error_message)

#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):

#             try:
#                 signal.signal(signal.SIGALRM, _handle_timeout)
#                 signal.alarm(seconds)
#             except ValueError:
#                 pass
#             try:
#                 result = func(*args, **kwargs)
#             finally:
#                 signal.alarm(0)
#             return result
#         return wrapper

#     return decorator

class classproperty(object):
    """
    A decorator that allows to set properties on class level.

    """

    def __init__(self, fget):
        self.__doc__ = fget.__doc__
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


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

    def __init__(self, *args, **kwargs):

        super(ProntoWarning, self).__init__(*args, **kwargs)
        #self.__suppress_context__ = True


class _NoDaemonProcess(multiprocessing.Process): # pragma: no cover
    # make 'daemon' attribute always return False

    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class ProntoPool(multiprocessing.pool.Pool): # pragma: no cover
    """A non-daemonized pool provided for convenience.

    Allows to perform ontology parsing through a pool of non-daemonized
    workers while inheriting all methods and attributes of multiprocessing.pool.Pool.
    """

    #Example:
    #
    #    >>> from pronto import Ontology
    #    >>> from pronto.utils import ProntoPool
    #    >>> enm = [ #ontologies from the eNanoMapper project
    #    ... "http://purl.enanomapper.net/onto/external/chebi-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/bao-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/bfo-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/ccont-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/cheminf-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/chmo-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/efo-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/envo-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/go-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/hupson-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/iao-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/ncit-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/npo-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/oae-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/obcs-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/obi-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/pato-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/sio-slim.owl",
    #    ... "http://purl.enanomapper.org/onto/external/uo-slim.owl"]
    #    >>> pool = ProntoPool()
    #
    #    >>> from functools import partial
    #    >>> enm_onto = pool.map(partial(Ontology, timeout=None), enm)
    #    >>> pool.close()

    _instances = []
    Process = _NoDaemonProcess

    def __init__(self, *args, **kwargs):
        super(ProntoPool, self).__init__(*args, **kwargs)
        self._instances.append(self)

    @classmethod
    def _close_all(cls):
        for pool in cls._instances:
            pool.close()

        for pool in cls._instances:
            pool.join()
atexit.register(ProntoPool._close_all)


# class SharedCounter(object):
#     """ A synchronized shared counter.

#     The locking done by multiprocessing.Value ensures that only a single
#     process or thread may read or write the in-memory ctypes object. However,
#     in order to do n += 1, Python performs a read followed by a write, so a
#     second process may read the old value before the new one is written by
#     the first process. The solution is to use a multiprocessing.Lock to
#     guarantee the atomicity of the modifications to Value.

#     This class comes almost entirely from Eli Bendersky's blog:
#     http://eli.thegreenplace.net/2012/01/04/shared-counter-with-
#         pythons-multiprocessing/

#     --------------------------------------------------------------------------

#     Solution of issue:
#         https://github.com/vterron/lemon/issues/11
#     implemented in:
#         https://github.com/vterron/lemon/commit/9ca6b4b1212228dbd4f69b88aaf88b12952d7d6f

#     """

#     def __init__(self, n = 0):
#         self.count = multiprocessing.Value('i', n)

#     def increment(self, n = 1):
#         """ Increment the counter by n (default = 1) """
#         with self.count.get_lock():
#             self.count.value += n

#     @property
#     def value(self):
#         """ Return the value of the counter """
#         return self.count.value


# class Queue(multiprocessing.queues.Queue):
#     """ A portable implementation of multiprocessing.JoinableQueue.

#     Because of multithreading / multiprocessing semantics, Queue.qsize() may
#     raise the NotImplementedError exception on Unix platforms like Mac OS X
#     where sem_getvalue() is not implemented. This subclass addresses this
#     problem by using a synchronized shared counter (initialized to zero) and
#     increasing / decreasing its value every time the put() and get() methods
#     are called, respectively. This not only prevents NotImplementedError from
#     being raised, but also allows us to implement a reliable version of both
#     qsize() and empty().

#     --------------------------------------------------------------------------

#     Solution of issue:
#         https://github.com/vterron/lemon/issues/11
#     implemented in:
#         https://github.com/vterron/lemon/commit/9ca6b4b1212228dbd4f69b88aaf88b12952d7d6f

#     """

#     def __init__(self, *args, **kwargs):
#         try:
#             super(Queue, self).__init__(*args,**kwargs)
#         except TypeError:
#             super(Queue, self).__init__(*args, ctx=multiprocessing.get_context(), **kwargs)
#         self.size =  SharedCounter(0)

#     def put(self, *args, **kwargs):
#         super(Queue, self).put(*args, **kwargs)
#         #self.size.increment(1)

#     def get(self, *args, **kwargs):
#         x = super(Queue, self).get(*args, **kwargs)
#         #self.size.increment(-1)
#         return x

#     #def task_done(self, *args, **kwargs):
#     #    self.size.increment(-1)
#     #    return

#     @staticmethod
#     def _feed(self, *args, **kwargs):
#         """Avoid making a fuss if the Queue was closed with elements in it"""
#         try:
#             super(Queue, self)._feed(*args, **kwargs)
#         except BrokenPipeError:
#             pass

#     def qsize(self):
#         """ Reliable implementation of multiprocessing.Queue.qsize() """
#         return self.size.value

#     def empty(self):
#         """ Reliable implementation of multiprocessing.Queue.empty() """
#         return not self.qsize() > 0

#     def _empty_queue(self):
#         while not super(Queue, self).empty():
#             self.get()


def _ontologize(x):
    Ontology, path, import_depth = x
    try:
        return Ontology(path, import_depth=import_depth-1)
    except (IOError, OSError, URLError, HTTPError, ParseError) as e:
        return ("{} occured during import of {}".format(type(e).__name__, path),
                ProntoWarning)

def explicit_namespace(attr, nsmap):
    """Explicits the namespace in an attribute name.

    Parameters
        attr (str): the attribute with its abbreviated namespace
        nsmap (dict): the namespace map

    Example:
        >>> from pronto.utils import explicit_namespace
        >>> ns = {'owl':'http://www.w3.org/2002/07/owl#'}
        >>> explicit_namespace('owl:Class', ns)
        '{http://www.w3.org/2002/07/owl#}Class'

    """
    prefix, term = attr.split(':', 1)
    return "".join(['{', nsmap[prefix], '}', term])

def format_accession(accession, nsmap=None):
    """Formats an accession URI/string to the YY:XXXXXXX token format.

    Parameters:
        accession (str): the URI to be formatted
        nsmap (dict): namespaces that can be found at the beginning of the
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

def unique_everseen(iterable):
    """List unique elements, preserving order. Remember all elements ever seen."""
    # unique_everseen('AAAABBBCCDAABBB')    --> A B C D
    seen = set()
    seen_add = seen.add

    for element in six.moves.filterfalse(seen.__contains__, iterable):
        seen_add(element)
        yield element

def output_bytes(f):
    if six.PY2:
        def new_f(*args, **kwargs):
            return f(*args, **kwargs).encode("utf-8")
    else:
        new_f = f
    return new_f
