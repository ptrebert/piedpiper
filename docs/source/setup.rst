.. role:: bash(code)
   :language: bash

Preliminaries
#############
To use Pied Piper for large-scale production pipelines, it is strongly recommended (if not indispensable) to install
the DRMAA bindings for Python. Otherwise it is not possible to run the pipelines on a compute cluster
(via Grid Engine or the like).

To **install DRMAA**, please follow the instructions at PyPi's DRMAA_ site
or just try :bash:`[sudo] pip3 install drmaa` (assuming that your `pip` does not default to Python3).

.. _DRMAA: https://pypi.python.org/pypi/drmaa/0.7.6

