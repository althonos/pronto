``pronto``
==========

*Python frontend to ontologies.*

|PyPI| |Conda| |Py versions| |Codacy grade| |Dev repo| |Build status| |License| |DOI| |coverage|


.. |PyPI| image:: https://img.shields.io/pypi/v/pronto.svg?style=flat-square&maxAge=2592000
   :target: https://pypi.python.org/pypi/pronto
.. |Conda| image:: https://img.shields.io/conda/vn/bioconda/pronto.svg?style=flat-square&maxAge=2592000
   :target: https://anaconda.org/bioconda/pronto
.. |Py versions| image:: https://img.shields.io/pypi/pyversions/pronto.svg?style=flat-square&maxAge=2592000
   :target: https://travis-ci.org/althonos/pronto
.. |Codacy grade| image:: https://img.shields.io/codacy/grade/157b5fd24e5648ea80580f28399e79a4.svg?style=flat-square&maxAge=2592000
   :target: https://codacy.com/app/althonos/pronto
.. |Build status| image:: https://img.shields.io/travis/althonos/pronto.svg?style=flat-square&maxAge=2592000
   :target: https://travis-ci.org/althonos/pronto
.. |License| image:: https://img.shields.io/pypi/l/pronto.svg?style=flat-square&maxAge=2592000
   :target: https://choosealicense.com/licenses/mit/
.. |Dev repo| image:: https://img.shields.io/badge/source-GitHub-303030.svg?style=flat-square&maxAge=2592000
   :target: https://github.com/althonos/pronto
.. |DOI| image:: https://img.shields.io/badge/doi-10.5281%2Fzenodo.595572-blue?style=flat-square&maxAge=2592000
   :target: https://zenodo.org/badge/latestdoi/23304/althonos/pronto
.. |coverage| image:: https://img.shields.io/codacy/coverage/157b5fd24e5648ea80580f28399e79a4.svg?style=flat-square&maxAge=2592000
   :target: https://www.codacy.com/app/althonos/pronto/dashboard


``pronto`` is a Python agnostic library designed to work with ontologies. At the
moment, it can parse `OBO <https://owlcollab.github.io/oboformat/doc/GO.format.obo-1_4.html>`_
open ontologies on the local host or from an network location, and export
ontologies to OBO format.


Setup
-----

Run ``pip install pronto`` in a shell to download the latest release and all
its dependencies from PyPi, or have a look at the
:doc:`Installation page <install>` to find other ways to install ``pronto``.

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

   Installation <install>
   Examples <examples>
   Api Reference <api>
   To-do <todo>
   Changelog <changes>
   About <about>


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
