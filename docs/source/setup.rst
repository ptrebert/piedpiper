.. role:: bash(code)
   :language: bash

Setup
=====

Prerequisites
#############
To use Pied Piper for large-scale production pipelines, it is strongly recommended (if not indispensable) to install
the DRMAA bindings for Python. Otherwise it is not possible to run the pipelines on a compute cluster
(via Grid Engine or the like).

To **install DRMAA**, please follow the instructions at PyPi's DRMAA_ site
or just try :bash:`[sudo] pip3 install drmaa` (assuming that your `pip` does not default to Python3).

.. _DRMAA: https://pypi.python.org/pypi/drmaa/0.7.6

Next, **install Ruffus**, the actual workhorse, by following the instructions on the Ruffus_ website or just try :bash:`[sudo] pip3 install ruffus --upgrade` (assuming that your `pip` does not default to Python3).

.. _Ruffus: http://www.ruffus.org.uk/installation.html

Environment paths
#################
In order to run jobs on a compute cluster via a DRMAA-compatible batch-queuing system (in the following, all examples assume SGE_ to be that system), several environment variables have to set. In the case of SGE_, that is:

* SGE_ROOT (environment specific, default is "/gridware/sge")
* SGE_CELL (environment specific, default is "default")
* DRMAA_LIBRARY_PATH (commonly "/usr/lib/libdrmaa.so")

Contact the administrator of the compute cluster to find out the correct values for these variables. Export these variables in the shell environment where you execute Pied Piper. The following is an example stating the specific values for the development environment of Pied Piper:

.. code-block:: bash

   export DRMAA_LIBRARY_PATH=/usr/lib/libdrmaa.so
   export SGE_ROOT=/TL/deep-gridengine
   export SGE_CELL=deep





.. _SGE: https://en.wikipedia.org/wiki/Oracle_Grid_Engine