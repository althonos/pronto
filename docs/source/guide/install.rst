Installation
============

PyPi
^^^^

``pronto`` is hosted on GitHub, but the easiest way to install it is to download
the latest release from its `PyPi repository <https://pypi.python.org/pypi/pronto>`_.
It will install all dependencies then install the ``pronto`` module:

.. code:: console

	$ pip install --user pronto

Conda
^^^^^

Pronto is also available as a `recipe <https://anaconda.org/bioconda/pronto>`_
in the `bioconda <https://bioconda.github.io/>`_ channel. To install, simply
use the `conda` installer:

.. code:: console

	 $ conda install -c bioconda pronto


GitHub + ``pip``
^^^^^^^^^^^^^^^^

If, for any reason, you prefer to download the library from GitHub, you can clone
the repository and install the repository by running (with the admin rights):

.. code:: console

	$ pip install --user https://github.com/althonos/pronto/archive/master.zip

Keep in mind this will install the development version of the library, so not
everything may work as expected compared to a stable versioned release.


GitHub + ``setuptools``
^^^^^^^^^^^^^^^^^^^^^^^

If you do not have ``pip`` installed, you can still clone the repository and
run the ``setup.py`` file manually, although you will need to install the
project dependencies yourself:

.. code:: console

	$ git clone https://github.com/althonos/pronto
	$ cd pronto
	# python setup.py install
