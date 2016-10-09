.. PiedPiper documentation master file, created by
   sphinx-quickstart on Sat Oct  8 15:34:55 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pied Piper!
======================

.. figure:: images/piedpiper.png
   :scale: 40 %
   :alt: The Pied Piper of Hamelin
   :align: center

.. Adapted from *The Pied Piper of Hamelin* (image in public domain)

.. note:: This software should not be confused with the `Pied Piper`_ platform that specializes in middle-out compression.

The Pied Piper pipeline runner is a small script tailored to be used on top of Ruffus_ for medium to large-scale
data processing on compute clusters. As such, it has been extensively used to run Ruffus pipelines via SGE_ on a
small compute cluster (32 nodes) for various bioinformatics projects.

**Pied Piper is for you if...**

* you are proficient in Python programming (to implement pipelines in Ruffus_)
* you are not afraid of regular expressions
* you run pipelines requiring different environments for different tools (e.g., mixing Python2 and Python3 tools)
* you want to switch effortlessly between a compute cluster and a single server
* you work at the shell level only (and in a Linux-only environment)
* you look for a solution that works with the Python standard library only (except for Ruffus and DRMAA)
* you run pipelines that essentially follow the form *input file* - transformation - *output file*
* you just want to get the job done

**Pied Piper is not for you if...**

* you need a graphical interface and "clickable" pipelines (use Galaxy_ for that)
* you need support for pipelines written in YAML, JSON or CWL_
* you look for a fancy feature creep

**Limitations**

* scaling *ad infinitum* has not been tested; so far, the most complex project that was successfully implemented in a Ruffus pipeline resulted in ~250.000 intermediate or result files, but with only several dozen tasks running in parallel. There are reports_ that Ruffus at least scales to running hundreds of tasks in parallel.
* a bottleneck is the start-up, i.e., checking which tasks need to be run
* if you are entirely new to large-scale data processing, first make sure that your hardware can actually handle the load of parallelism. In particular, I/O stress can be a crippling factor for the storage hardware. Pied Piper is used on a cluster that reads from/writes to a parallel file system (BeeGFS_) that is designed for such a scenario.

**Alternatives**

* one of the top dogs in the field is SnakeMake_
* check out Pypiper_ together with Looper_
* you may want to consider a tool making use of the Common Workflow Language (CWL_), an initiative that is likely to have an impact in any field requiring large-scale data analysis (bioinformatics, astronomy etc.)
* concerning the above, Toil_ looks like a good candidate


**Contents:**

.. toctree::
   :maxdepth: 1

   setup
   license

**Indices and tables**

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Pied Piper: http://www.piedpiper.com/
.. _Ruffus: http://ruffus.readthedocs.io/en/latest/
.. _SGE: https://en.wikipedia.org/wiki/Oracle_Grid_Engine
.. _Galaxy: https://galaxyproject.org/
.. _CWL: http://www.commonwl.org/
.. _Pypiper: http://databio.org/pypiper/
.. _Looper: http://databio.org/looper/
.. _SnakeMake: https://bitbucket.org/snakemake/snakemake/wiki/Home
.. _Toil: http://toil.readthedocs.io/en/latest/
.. _reports: https://groups.google.com/d/msg/ruffus_discuss/docWxubPJiU/F4rk_NnMAgAJ
.. _BeeGFS: http://www.beegfs.com/content/