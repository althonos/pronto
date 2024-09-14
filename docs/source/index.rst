``pronto`` |Stars|
==================

.. |Stars| image:: https://img.shields.io/github/stars/althonos/pronto.svg?style=social&maxAge=3600&label=Star
   :target: https://github.com/althonos/pronto/stargazers

*A Python frontend to ontologies.*

|Actions| |License| |Source| |Docs| |Coverage| |Sanity| |PyPI| |Bioconda| |Versions| |Wheel| |Changelog| |Issues| |DOI| |Downloads|

.. |Actions| image:: https://img.shields.io/github/actions/workflow/status/althonos/pronto/test.yml?branch=master&style=flat-square&maxAge=300
   :target: https://github.com/althonos/pronto/actions

.. |License| image:: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square&maxAge=2678400
   :target: https://choosealicense.com/licenses/mit/

.. |Source| image:: https://img.shields.io/badge/source-GitHub-303030.svg?maxAge=2678400&style=flat-square
   :target: https://github.com/althonos/pronto/

.. |Docs| image:: https://img.shields.io/readthedocs/pronto?style=flat-square&maxAge=3600
   :target: http://pronto.readthedocs.io/en/stable/?badge=stable

.. |Coverage| image:: https://img.shields.io/codecov/c/gh/althonos/pronto?style=flat-square&maxAge=3600
   :target: https://www.codecov.com/gh/althonos/pronto/

.. |Sanity| image:: https://img.shields.io/codacy/grade/157b5fd24e5648ea80580f28399e79a4.svg?style=flat-square&maxAge=3600
   :target: https://codacy.com/app/althonos/pronto

.. |PyPI| image:: https://img.shields.io/pypi/v/pronto.svg?style=flat-square&maxAge=3600
   :target: https://pypi.python.org/pypi/pronto

.. |Bioconda| image:: https://img.shields.io/conda/vn/bioconda/pronto?style=flat-square&maxAge=3600
   :target: https://anaconda.org/bioconda/pronto

.. |Versions| image:: https://img.shields.io/pypi/pyversions/pronto.svg?style=flat-square&maxAge=3600
   :target: https://pypi.org/project/pronto/#files

.. |Wheel| image:: https://img.shields.io/pypi/wheel/pronto?style=flat-square&maxAge=3600
   :target: https://pypi.org/project/pronto/#files

.. |Changelog| image:: https://img.shields.io/badge/keep%20a-changelog-8A0707.svg?maxAge=2678400&style=flat-square
   :target: https://github.com/althonos/pronto/blob/master/CHANGELOG.md

.. |Issues| image:: https://img.shields.io/github/issues/althonos/pronto.svg?style=flat-square&maxAge=600
   :target: https://github.com/althonos/pronto/issues

.. |DOI| image:: https://img.shields.io/badge/doi-10.5281%2Fzenodo.595572-purple?style=flat-square&maxAge=2678400
   :target: https://doi.org/10.5281/zenodo.595572

.. |Downloads| image:: https://img.shields.io/pypi/dm/pronto?style=flat-square&color=303f9f&maxAge=86400&label=downloads
   :target: https://pepy.tech/project/pronto


``pronto`` is a Python agnostic library designed to work with ontologies. At the
moment, it can parse `OBO`_, `OBO Graphs`_ or
`OWL in RDF/XML format <https://www.w3.org/TR/2012/REC-owl2-mapping-to-rdf-20121211/>`_,
ntologies on the local host or from an network location, and export
ontologies to `OBO`_ or `OBO Graphs`_ (in `JSON`_ format).

.. _OBO: https://owlcollab.github.io/oboformat/doc/GO.format.obo-1_4.html
.. _OBO Graphs: https://github.com/geneontology/obographs
.. _JSON: http://www.json.org/

Setup
-----

Run ``pip install pronto`` in a shell to download the latest release and all
its dependencies from PyPi, or have a look at the
:doc:`Installation page <guide/install>` to find other ways to install ``pronto``.

.. note::

    ``pronto`` requires ``fastobo``, an efficient and faultless parser
    for the OBO language implemented in Rust. Most platforms, such as Linux
    x86-64, OSX and Windows x86-64 provide precompiled packages, but other
    less frequent platforms will require a working Rust toolchain. See the
    ``fastobo``
    `Installation page <https://fastobo.readthedocs.io/en/latest/install.html>`_
    and the `Rust Forge tutorial <https://forge.rust-lang.org/other-installation-methods.html>`_
    for more information about this topic.

Library
-------

.. toctree::
   :maxdepth: 2

   User Guide <guide/index>
   API Reference <api/index>


Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
