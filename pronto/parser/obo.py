"""
pronto.parser

This module contains all the parsers used to parse an ontology. The base class
Parser can be derived to provide additional parsers to ontology files.
"""

import multiprocessing
import atexit

import pronto.term
import pronto.relationship
from pronto.parser import Parser



class _OboClassifier(multiprocessing.Process):

    def __init__(self, queue, results):

        super(_OboClassifier, self).__init__()

        self.queue = queue
        self.results = results

    def run(self):

        #def _classify(queue, results):

        while True:


            term = self.queue.get()

            if term is None:
                self.queue.task_done()
                break

            relations = {}

            if 'relationship' in term:
                pronto.relationship.Relationship.lock.acquire()
                try:
                    _process_relationship(term)
                finally:
                    pronto.relationship.Relationship.lock.release()

            if 'is_a' in term.keys():
                term[pronto.relationship.Relationship('is_a')] = term['is_a']
                del term['is_a']

            # New relations may be created when extracting relationship,
            # this need to be investigated to come with a less 'hacky' solution
            #while True:

            #pronto.relationship.Relationship.lock.acquire()
            #try:
            for key in list(term.keys()):
                if isinstance(key, pronto.relationship.Relationship):
                    relations = _extract_relationship(term, key, relations)

            #term = {k:v for k,v in term.items() if not isinstance(k, pronto.relationship.Relationship)}

            #finally:
            #    pronto.relationship.Relationship.lock.release()



            desc = _extract_description(term)
            tid, name = _extract_name_and_id(term)

            #if not tid:
            #    return {}

            self.queue.task_done()

            self.results.put((tid, name, desc, relations, term))

        #return {tid: pronto.term.Term(tid, name, desc, relations, term)}






class OboParser(Parser):
    """A parser for the Obo format.
    """

    def __init__(self):
        super(OboParser, self).__init__()
        self.extension = '.obo'
        #self._rawterms = list()

        #self._rawterms = multiprocessing.JoinableQueue()
        #self._terms = multiprocessing.Queue()

        for k in range(multiprocessing.cpu_count()):
            self.processes.append(_OboClassifier(self._rawterms, self._terms))

        for p in self.processes:
            p.start()

        #for k in range(12):
        #    p = _OboClassifier(self._rawterms, self._terms)
            #p = multiprocessing.Process(target=_classify, args=(self._rawterms, self._terms))
            #p.start()
        #    self.processes.append(p)

        self._tempterm = dict()
        self._typedef = list()
        self._meta = dict()

    def hook(self, *args, **kwargs):
        """Returns True if the file is an Obo file (extension is .obo)"""
        if 'path' in kwargs:
            return kwargs['path'].endswith(self.extension)

    def read(self, stream):
        """Read the stream and extract information in a 'raw' format."""
        #self._rawterms, = multiprocessing.JoinableQueue()
        self._typedef, self._meta = list(), dict()

        #self._rawterms = multiprocessing.JoinableQueue()
        #self._terms = multiprocessing.Queue()

        #self.processes = [_OboClassifier(self._rawterms, self._terms) for k in range(12)]

        #for p in self.processes:
        #    p.start()

        IN = 'meta'
        for line in stream:
            try:
                line = line.strip().decode('utf-8')
            except AttributeError:
                line = line.strip()
            IN = self._check_section(line) or IN
            if ': ' in line:
                self._parse_line_statement(line, IN)

        self._rawterms.put(self._tempterm)


        while self._terms.qsize() > 0 or self._rawterms.qsize() > 0:
            d = self._terms.get()
            self.terms[d[0]] = pronto.term.Term(
                d[0], d[1], d[2], {pronto.relationship.Relationship(k):v for k,v in d[3].items()}, d[4]
            )

        #for p in self.processes:
        #    p.terminate()

        #self._rawterms.close()
        #self._terms.close()
            #self._rawterms.put(None)

    def makeTree(self, pool):
        """Create the proper ontology Tree from raw terms"""
        pass
        #for t in pool.map(_classify, self._rawterms):
        #    self.terms.update(t)

    def metanalyze(self):
        """Analyze metadatas extracted from the beginning of the file."""

        for key,value in self._meta.items():
            if key != 'remark':
                self._parse_statement(key, value)
            else:
                for remark in value:
                    self._parse_remark(remark)

    def manage_imports(self):
        """Get metadatas concerning imports."""
        if 'import' in self.meta.keys():
            self.imports = self.meta['import']
        self.imports = list(set(self.imports))

    def _parse_remark(self, remark):
        """Parse a remark and add results to self.meta."""
        if ': ' in remark:
            key_remark, value_remark = remark.split(': ', 1)
            if not key_remark in self.meta:
                self.meta[key_remark] = []
            self.meta[key_remark].append(value_remark)
        else:
            if 'remark' not in self.meta:
                self.meta['remark'] = []
            self.meta['remark'].append(remark)

    def _parse_statement(self, key, value):
        """Parse a ``key: value`` statement in the ontology file."""
        if not isinstance(value, list):
            value = [value]
        if not key in self.meta.keys():
            self.meta[key] = []
        self.meta[key].extend(value)

    def _get_dict_to_update(self, IN):
        """Returns the right dictionnary to use"""
        if IN=='meta':
            return self._meta
        elif IN=='term':
            return self._tempterm
        elif IN=='typedef':
            return self._typedef[-1]

    def _check_section(self, line):
        """Check if current section must be changed."""
        if '[Term]' in line:
            if self._tempterm:
                self._rawterms.put(self._tempterm)
            #self._rawterms.append({})
            self._tempterm = dict()
            return 'term'
        elif '[Typedef]' in line:
            self._typedef.append({})
            return 'typedef'

    def _parse_line_statement(self, line, IN):
        k, v = line.split(': ', 1)
        to_update = self._get_dict_to_update(IN)
        if k not in to_update.keys():
            to_update[k] = v
        else:
            if not isinstance(to_update[k], list):
                to_update[k] = [to_update[k]]
            to_update[k].append(v)





def _process_relationship(term):

    # If term is a str
    try:

        name, value = term['relationship'].split(' ', 1)

        name = pronto.relationship.Relationship(name)

        if name not in term.keys():
            term[name] = []
        term[name].append(value)

    # If term is a list
    except AttributeError:

        for r in term['relationship']:
            name, value = r.split(' ', 1)

            name = pronto.relationship.Relationship(name)

            if name not in term.keys():
                term[name] = []
            term[name].append(value)

    del term['relationship']

def _extract_relationship(term, rship, relations):

    #if rship.obo_name in term.keys():
    if isinstance(term[rship], list):
        relations[rship.obo_name] = [ x.split(' !')[0] for x in term[rship] ]
    else:
        relations[rship.obo_name] = [ term[rship].split(' !')[0]]
    del term[rship]

    return relations

def _extract_description(term):
    if 'def' in term.keys():
        desc = term['def']
        del term['def']
        return desc
    else:
        return ''

def _extract_name_and_id(term):
    if 'id' not in term.keys():
        return '', ''
    if 'name' in term.keys():
        tid, name = term['id'], term['name']
        del term['name']
        del term['id']
        return tid, name
    else:
        tid = term['id'][0]
        name = ''
        del term['id']
        return tid, name


OboParser()
