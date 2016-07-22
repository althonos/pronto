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

import sys
import os


sys.path.append(os.getcwd())
#print(sys.path)

import pronto

try:
    import urllib.request as rq
except ImportError:
    import urllib2 as rq


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
        except (KeyboardInterrupt, SystemExit):
           raise
        except:
           continue

    del ontid
    del ontology

content = rq.urlopen(OBO_CATALOG).read()
catalog = json.loads(content.decode('utf-8'))

for x in catalog["ontologies"]:
    y = task(x)
    del y




