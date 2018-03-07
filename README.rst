filehandles
===========

.. image:: https://img.shields.io/pypi/l/filehandles.svg
   :target: https://choosealicense.com/licenses/mit/
   :alt: License information

.. image:: https://img.shields.io/pypi/v/filehandles.svg
   :target: https://pypi.org/project/filehandles/
   :alt: Current library version

.. image:: https://img.shields.io/pypi/pyversions/filehandles.svg
   :target: https://pypi.org/project/filehandles/
   :alt: Supported Python versions

.. image:: https://api.travis-ci.org/MoseleyBioinformaticsLab/filehandles.svg?branch=master
   :target: https://travis-ci.org/MoseleyBioinformaticsLab/filehandles
   :alt: Travis CI status

.. image:: https://codecov.io/gh/MoseleyBioinformaticsLab/filehandles/branch/master/graphs/badge.svg?branch=master
   :target: https://codecov.io/gh/MoseleyBioinformaticsLab/filehandles
   :alt: Code coverage information


The ``filehandles`` package is a Python library that facilitates processing of
files by removing boilerplate code that you need to write to open files from
directories, zip archives, tar archives, URL addresses of files, etc. It also
automatically closes open file handle after it has been processed.


Links
~~~~~

   * mwtab @ GitHub_
   * mwtab @ PyPI_


Installation
~~~~~~~~~~~~

The ``filehandles`` package runs under Python 2.7 and Python 3.4+. Use pip_ to install.


Install
-------

.. code:: bash

   python3 -m pip install filehandles


Upgrade
-------

.. code:: bash

   python3 -m pip install filehandles --upgrade


Quickstart
~~~~~~~~~~

>>> from filehandles import filehandles
>>>
>>> for fh in filehandles('path/to/files'):
...     # utilize file handle
...     text = fh.readline()
>>>


.. _GitHub: https://github.com/MoseleyBioinformaticsLab/filehandles
.. _PyPI: https://pypi.org/project/filehandles
.. _pip: https://pip.pypa.io
.. _BSD: https://choosealicense.com/licenses/bsd-3-clause-clear/