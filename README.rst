**pronto** : Python frontend to Ontologies
==========================================

|PyPI| |Conda| |Py versions| |Build Status| |Dev repo| |Codacy grade| |License| |DOI| |coverage| |rtd|

Overview
^^^^^^^^

Pronto is a python module to parse, create, browse and export ontologies
from some popular formats. For now, **obo** and **owl/xml** are available,
but more formats are to be added in the future (you can even add your
own to work with the current API).

Installation
^^^^^^^^^^^^

Installing with ``pip`` is the easiest:

.. code:: bash

    pip install pronto          # if you have the admin rights
    pip install pronto --user   # if you want to install it for only one user


There is also a ``conda`` recipe in the `bioconda <https://bioconda.github.io/>`_
channel:

.. code:: bash

	 conda install -c bioconda pronto


If for some reason you do not like ``pip``, you can also clone the
repository and install it with the setup script (still requires
``setuptools``):

.. code:: bash

    git clone https://github.com/althonos/pronto
    cd pronto
    python setup.py install    # may also require admin rights


Usage
^^^^^

The ``Ontology`` class is the main entrypoint of ``pronto``. It can
be instantiated with a given ontology file (``.owl``, ``.ont`` or ``.obo``)
or from scratch, without any existing terms.

Open an ontology and get a term by accession:
'''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    term = ont['REF:ACCESSION']

Display an ontology in obo format and in json format:
'''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

    import pronto
    ont = pronto.Ontology('https://net.path.should/work/too.owl')
    print(ont.obo)
    print(ont.json)


Merge two ontologies:
'''''''''''''''''''''

Example here uses the `NMR controlled vocabulary <http://nmrml.org/cv/>`_ and the
`HUPO-PSI MS controlled vocabulary <http://www.psidev.info/groups/controlled-vocabularies>`_

.. code:: python

    import pronto
    nmr = pronto.Ontology('http://nmrml.org/cv/v1.1.0/nmrCV.owl')
    ms  = pronto.Ontology('https://raw.githubusercontent.com/HUPO-PSI/psi-ms-CV/master/psi-ms.obo')
    ms.merge(nmr)

.. code:: python

    >>> 'NMR:1000004' in ms
    True
    >>> ms.meta['coverage']
    'Mass spectrometer output files and spectra interpretation'


Find ontology terms with children
'''''''''''''''''''''''''''''''''

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    for term in ont:
        if term.children:
            print(term)


Get all the transitive children of an ontology term
'''''''''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

    import pronto
    ont = pronto.Ontology('path/to/file.obo')
    print(ont['RF:XXXXXXX'].rchildren())


Reference
^^^^^^^^^

If you wish to use this library in a scientific publication,
please cite it !
(see the `Zenodo record <https://zenodo.org/badge/latestdoi/23304/althonos/pronto>`_
to get a DOI or a BibTEX record).


.. |Build Status| image:: https://img.shields.io/travis/althonos/pronto.svg?style=flat&maxAge=3600
   :target: https://travis-ci.org/althonos/pronto
.. |Py versions| image:: https://img.shields.io/pypi/pyversions/pronto.svg?style=flat&maxAge=3600
   :target: https://pypi.python.org/pypi/pronto/
.. |PyPI| image:: https://img.shields.io/pypi/v/pronto.svg?style=flat&maxAge=3600
   :target: https://pypi.python.org/pypi/pronto
.. |Conda| image:: https://img.shields.io/conda/vn/bioconda/pronto.svg?style=flat&maxAge=2592000
   :target: https://anaconda.org/bioconda/pronto
.. |Dev repo| image:: https://img.shields.io/badge/source-GitHub-303030.svg?style=flat&maxAge=3600
   :target: https://github.com/althonos/pronto
.. |License| image:: https://img.shields.io/pypi/l/pronto.svg?style=flat&maxAge=3600
   :target: https://choosealicense.com/licenses/mit/
.. |Codacy Grade| image:: https://img.shields.io/codacy/grade/157b5fd24e5648ea80580f28399e79a4.svg?style=flat&maxAge=3600
   :target: https://codacy.com/app/althonos/pronto
.. |DOI| image:: https://zenodo.org/badge/62424052.svg
   :target: https://zenodo.org/badge/latestdoi/62424052
.. |coverage| image:: https://img.shields.io/codacy/coverage/157b5fd24e5648ea80580f28399e79a4.svg?maxAge=3600
   :target: https://www.codacy.com/app/althonos/pronto/dashboard
.. |rtd| image:: https://readthedocs.org/projects/pronto/badge/?version=latest
   :target: http://pronto.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
