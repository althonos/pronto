# coding: utf-8
"""
Test lots of ontologies from the OBO Foundry.
"""

OBO_CATALOG = 'http://www.obofoundry.org/registry/ontologies.jsonld'

	     #lag         #lag         #lag
BLOCKLIST = ('chebi.owl', 'chebi.obo', 'pr.owl',
             #HTTPError  #lxmlError   #utf8Error
             'agro.owl', 'dinto.owl', 'envo.obo')

import json
import signal
import time
import multiprocessing
import multiprocessing.pool
import sys
import os

#from memory_profiler import profile

sys.path.append(os.getcwd())
#print(sys.path)

import pronto

try:
    import urllib.request as rq
except ImportError:
    import urllib2 as rq


def timer(signum, frame):
    #print('Quitter called with signal', signum)
    raise IOError("        Couldn't parse ontology within time limit !")

#@profile
def task(ontology):
    ontid = ontology["id"]
    print('Testing: {}'.format(ontid))

    if not 'products' in ontology:
        return

    for product in ontology["products"]:

        if product['id'] in BLOCKLIST:
            continue

        print('    file: {}'.format(product["id"]))

        t = time.time()
        try:
           ont = pronto.Ontology(product["ontology_purl"])
           print("      {} terms extracted in {}s.".format(len(ont), round(time.time()-t, 1)))
           del ont
        except OSError:
           continue
    
    del ontid
    del ontology

#signal.signal(signal.SIGALRM, timer)

content = rq.urlopen(OBO_CATALOG).read()
catalog = json.loads(content.decode('utf-8'))

#pool = multiprocessing.pool.Pool(multiprocessing.cpu_count() * 4)

#pool.
for x in catalog["ontologies"]:
    y = task(x)
    del y




