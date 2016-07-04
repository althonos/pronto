Installation
============

PyPi
^^^^

Pronto is hosted on GitHub, but the easiest way to install it is to download the
latest release from PyPi. It will install all dependencies of Pronto and then
install the pronto module.

.. code:: bash

	pip install pronto 


GitHub + ``pip``
^^^^^^^^^^^^^^^^

If, for any reason, you prefer to download the library from GitHub, you can clone
the repository and install the repository either by running (with the admin rights):

.. code:: bash
	
	git clone https://github.com/althonos/pronto
	cd pronto
	make install 


GitHub + ``setuptools``
^^^^^^^^^^^^^^^^^^^^^^^

If you do not have **pip** installed (the Makefile uses pip to install dependencies
and then install pronto), you can do the following (after having properly installed
all the dependencies):

.. code:: bash
	
	git clone https://github.com/althonos/pronto
	cd pronto
	python setup.py install 
