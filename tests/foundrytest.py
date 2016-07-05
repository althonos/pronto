# coding: utf-8
"""
Test lots of ontologies from the OBO Foundry.
"""

OBO_CATALOG = 'http://www.obofoundry.org/registry/ontologies.jsonld'

import json
import pronto
import signal

try:
    import urllib.request as rq
except ImportError:
    import urllib2 as rq


def timer(signum, frame):
    #print('Quitter called with signal', signum)
    raise IOError("        Couldn't parse ontology within time limit !")

signal.signal(signal.SIGALRM, timer)



content = rq.urlopen(OBO_CATALOG).read()
catalog = json.loads(content.decode('utf-8'))

for ontology in catalog["ontologies"]:
    ontid = ontology["id"]

    print('Testing: {}'.format(ontid))

    for product in ontology["products"]:
        print('    file: {}'.format(product["id"]))

        signal.alarm(60)

        try:
            if product["ontology_purl"].endswith('obo'):
                ont = pronto.obo.Obo(product["ontology_purl"])
            elif product["ontology_purl"].endswith('owl'):
                ont = pronto.owl.OwlXML(product["ontology_purl"])
            else:
                print('Unknown ontology format.')
                continue
            print("      {} terms extracted.".format(len(ont)))

            signal.alarm(0)

        except IOError as e:
            print(e)
            continue
