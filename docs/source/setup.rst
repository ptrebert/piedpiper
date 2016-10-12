.. role:: bash(code)
   :language: bash

Setup
=====
Pied Piper is developed and used in a Debian Linux environment. You may try to run it on a different OS, but full functionality has never been tested. All setup instructions given here thus assume a Linux environment. In general, the easiest way to setup Pied Piper is to use a dedicated environment (see point `Conda environment`_ below). The setup folder contains all necessary files.

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

* export SGE_ROOT= (environment specific, default is "/gridware/sge")
* export SGE_CELL= (environment specific, default is "default")

Additionally, the path to the DRMAA shared library has to be exported as follows:
* export DRMAA_LIBRARY_PATH= (commonly "/usr/lib/libdrmaa.so")

Contact the system administrator to find out the correct values for these variables. Export these variables in the shell environment where you execute Pied Piper. The following is an example stating the specific values for the (DEEP specific) development environment of Pied Piper:

.. code-block:: bash

   export DRMAA_LIBRARY_PATH=/usr/lib/libdrmaa.so
   export SGE_ROOT=/TL/deep-gridengine
   export SGE_CELL=deep


Conda environment
#################
You can simplify the above setup procedure by making use of the excellent Conda_ package manager (an awesome tool!).
At the moment, Pied Piper has not been packaged, i.e., setup involves several steps:

Step-by-step guide:
0. Clone the Pied Piper repository to a suitable location like *HOME*: :bash:`git clone https://github.molgen.mpg.de/pebert/piedpiper`
1. Install the Miniconda_ base package suitable for you architecture by following the guide on the website
2. Make sure the setup was successful by typing :bash:`conda --help` (which should not give an error) at the shell
3. Locate the *setup* directory in the location where you downloaded/cloned the Pied Piper repository
4. Inside the *setup* folder, you find the file *conda_env_piedpiper.yml*
5. Install the piedpiper environment by calling :bash:`conda env create -f conda_env_piedpiper.yml`
6. Prepare for the tricky part...
7. In the *setup* folder, locate the bash script called *conda_env_piedpiper_default.sh*
8. Open this bash script in your favourite text editor (most likely VIM :-) )
9. This script contains the information about the necessary environment variables (for more details, see the point `Environment paths`_ above) and needs to be adapted to your system





.. _SGE: https://en.wikipedia.org/wiki/Oracle_Grid_Engine
.. _Conda: http://conda.pydata.org/docs
.. _Miniconda: http://conda.pydata.org/miniconda.html