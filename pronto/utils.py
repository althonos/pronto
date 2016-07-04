import functools
import re
import warnings


"""
def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]

    return memoizer
"""


class ProntoWarning(Warning):
    pass


def explicit_namespace(attr, nsmap):
	prefix, term = attr.split(':', 1)
	return '{'+nsmap[prefix]+'}'+term

def parse_comment(comment):
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
    """Formats an accession URI/string to the YY:XXXXXXX token format."""

    if nsmap is not None:
        for v in nsmap.values():
            accession = accession.replace(v, '')

    if not accession.startswith('_'):
        accession = accession.replace('_', ':')

    return accession




