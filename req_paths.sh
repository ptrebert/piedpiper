
VAR_DRMAA_LIB="/usr/lib/libdrmaa.so"
VAR_SGE_ROOT="/TL/deep-gridengine"
VAR_SGE_CELL="deep"

export DRMAA_LIBRARY_PATH=${VAR_DRMAA_LIB}
export SGE_ROOT=${VAR_SGE_ROOT}
export SGE_CELL=${VAR_SGE_CELL}

PY3_PIEDPIPER_LIB="/home/pebert/work/code/mpggit/piedpiper"
PY3_DRMAA_LIB="/TL/deep-share/archive00/software/packages/drmaa/v0.7.6/install/lib/python3.2/site-packages"
PY3_RUFFUS_LIB="/TL/deep-share/archive00/software/packages/ruffus/v2.6.3/install/lib/python3.2/site-packages"

export PYTHONPATH=${PY3_PIEDPIPER_LIB}:${PY3_DRMAA_LIB}:${PY3_RUFFUS_LIB}
