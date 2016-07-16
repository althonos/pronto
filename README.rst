**pronto** : Python frontend to Ontologies
==========================================

|Version| |Py versions| |Build Status| |Dev repo| |Codacy grade| |License|

Overview
^^^^^^^^

Pronto is a python module to parse, create, browse and export ontologies
from some popular formats. For now, **obo** and **owl/xml** are available,
but more formats are to be added in the future (you can even add your
own to work with the current API).

Installation
^^^^^^^^^^^^

Installing with pip is the easiest:

.. code:: bash

    pip install pronto          # if you have the admin rights
    pip install pronto --user   # if you want to install it for only one user

If for some reason you do not like ``pip``, you can also clone the
repository and install it with the setup script (still requires
``setuptools``):

.. code:: bash

    git clone https://github.com/althonos/pronto
    cd pronto
    python3 setup.py install    # may also require admin rights

Usage
^^^^^

The class Ontology is likely the one you'll use the most
if all you want is to browse ontologies. It can be used to import 
ontologies in .owl (sometimes seen as .ont) and .obo formats,
merge, and export ontologies to a rudimentary obo file.

Instantiate an obo ontology and getting a term by accession number:

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    term = ont['REF:ACCESSION']

Display an ontology in obo format and in json format:

.. code:: python

    import pronto
    ont = pronto.Ontology('https://net.path.should/work/too.owl')
    print(ont.obo)
    print(ont.json)

Merge two ontologies:

.. code:: python

    import pronto
    nmr = pronto.Ontology('https://raw.githubusercontent.com/nmrML/nmrML/'
                          'master/ontologies/nmrCV.owl')
    ms  = pronto.Ontology('http://psidev.cvs.sourceforge.net/viewvc/psidev/psi'
                          '/psi-ms/mzML/controlledVocabulary/psi-ms.obo')

    ms.merge(nmr) # MS ontology keeps its metadata but now contains NMR terms
                  # as well.

    assert('NMR:1000004' in ms)

Explore every term of an ontology and print those with children:

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    for term in ont:
        if term.children:
            print(term)

Get grandchildrens of an ontology term:

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    print(ont['RF:XXXXXXX'].children.children)

TODO
^^^^
-  test with many different ontologies
-  extract data from OwlXML where attributes are ontologic terms
-  extract metadatas from OwlXML
-  add other owl serialized formats
-  (maybe) add serialization to owl





.. |Build Status| image:: https://img.shields.io/travis/althonos/pronto.svg?style=flat&maxAge=2592000
   :target: https://travis-ci.org/althonos/pronto

.. |Py versions| image:: https://img.shields.io/pypi/pyversions/pronto.svg?style=flat&maxAge=2592000
   :target: https://pypi.python.org/pypi/pronto/

.. |Version| image:: https://img.shields.io/pypi/v/pronto.svg?style=flat&maxAge=2592000
   :target: https://pypi.python.org/pypi/pronto

.. |Dev repo| image:: https://img.shields.io/badge/repository-GitHub-blue.svg?style=flat&maxAge=2592000
   :target: https://github.com/althonos/pronto

.. |License| image:: https://img.shields.io/pypi/l/pronto.svg?style=flat&maxAge=2592000
   :target: https://www.gnu.org/licenses/gpl-3.0.html

.. |Codacy Grade| image:: https://img.shields.io/codacy/grade/157b5fd24e5648ea80580f28399e79a4.svg?style=flat&maxAge=2592000
   :target: https://codacy.com/app/althonos/pronto
