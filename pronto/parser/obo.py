import pronto.term
from pronto.relationship import RSHIPS



class OboParser(object):
    """An ontology parsed from an obo file.
    """

    def parse(self, handle, pool):

        self.read(handle)
        self.makeTree(pool)
        self.metanalyze()
        self.manage_imports()

        return self.meta, self.terms, self.imports


    def read(self, handle):

        self._meta = {}
        self._rawterms = []
        self._typedef = []

        IN = 'meta'

        i = 0
        for line in handle: #.readlines():
            i += 1

            # maybe decode line
            try:
                line = line.strip().decode('utf-8')
            except AttributeError:
                line = line.strip()

            if '[Term]' in line:
                IN = 'terms'
                self._rawterms.append({})
            elif '[Typedef]' in line:
                IN = 'typedef'
                self._typedef.append({})

            if ': ' in line:

                k, v = line.split(': ', 1)

                if IN=='meta':
                    to_update = self._meta
                elif IN=='terms':
                    to_update = self._rawterms[-1]
                elif IN=='typedef':
                    to_update = self._typedef[-1]

                if k not in to_update.keys():
                    to_update[k] = v
                else:
                    if not isinstance(to_update[k], list):
                        to_update[k] = [to_update[k]]
                    to_update[k].append(v)

    def makeTree(self, pool):
        self.terms = {}
        for t in pool.map(self._classify, self._rawterms):
            self.terms.update(t)

    def _classify(self, term):

            relations = {}

            if 'relationship' in term:

                if isinstance(term['relationship'], list):
                    for r in term['relationship']:
                        name, value = r.split(' ', 1)

                        if name not in term.keys():
                            term[name] = []
                        term[name].append(value)

                else:
                    name, value = term['relationship'].split(' ', 1)

                    if name not in term.keys():
                        term[name] = []
                    term[name].append(value)

                del term['relationship']


            for rship in RSHIPS:

                if rship in term.keys():

                    if isinstance(term[rship], list):
                        relations[rship] = [ x.split(' !')[0] for x in term[rship] ]
                    else:
                        relations[rship] = [ term[rship].split(' !')[0]]

                    del term[rship]

            if 'def' in term.keys():
                desc = term['def']
                del term['def']
            else:
                desc = ''

            if 'name' in term.keys():
                tid, name = term['id'], term['name']
                del term['name']
                del term['id']
            else:
                tid = term['id'][0]
                name = ''
                del term['id']

            return {tid: pronto.term.Term(tid, name, desc, relations, term)}



    def metanalyze(self):

        self.meta = {}

        for key,value in self._meta.items():

            if key != 'remark':
                if not isinstance(value, list):
                    value = [value]

                if not key in self.meta.keys():
                    self.meta[key] = []
                self.meta[key].extend(value)

            else:

                for remark in value:
                    if ': ' in remark:
                        key_remark, value_remark = remark.split(': ', 1)

                        if not key_remark in self.meta:
                            self.meta[key_remark] = []

                            self.meta[key_remark].append(value_remark)
                    else:

                        if 'remark' not in self.meta:
                            self.meta['remark'] = []
                        self.meta['remark'].append(remark)

    def manage_imports(self):
        self.imports = self.meta['import'] \
                       if 'import' in self.meta.keys() \
                       else []
