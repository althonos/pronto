# coding: utf-8
"""
Test lots of ontologies from the OBO Foundry.
"""

OBO_CATALOG = 'http://www.obofoundry.org/registry/ontologies.jsonld'

BLOCKLIST = ('chebi.owl')

import json
import pronto
import signal
import time
import multiprocessing
import multiprocessing.pool


try:
    import urllib.request as rq
except ImportError:
    import urllib2 as rq


def timer(signum, frame):
    #print('Quitter called with signal', signum)
    raise IOError("        Couldn't parse ontology within time limit !")

def task(ontology):
    ontid = ontology["id"]
    print('Testing: {}'.format(ontid))
    for product in ontology["products"]:

        if product['id'] in BLOCKLIST:
            continue

        print('    file: {}'.format(product["id"]))
        signal.alarm(300)
        try:
            t = time.time()
            ont = pronto.Ontology(product["ontology_purl"])
            print("      {} terms extracted in {}s.".format(len(ont)), round(t-time.time(), 1))
            signal.alarm(0)
            del ont
            return
        except IOError as e:
            print(e)
            return

signal.signal(signal.SIGALRM, timer)

content = rq.urlopen(OBO_CATALOG).read()
catalog = json.loads(content.decode('utf-8'))

pool = multiprocessing.pool.Pool(multiprocessing.cpu_count() * 4)

pool.map(task, catalog["ontologies"])




