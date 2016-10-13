#!/bin/bash

INSTALLPATH="/TL/epigenetics2/work/pebert/conda/envs/piedpiper"

cd ${INSTALLPATH} &&
mkdir -p ./etc/conda/activate.d &&
mkdir -p ./etc/conda/deactivate.d &&
touch ./etc/conda/activate.d/env_vars.sh &&
touch ./etc/conda/deactivate.d/env_vars.sh

PIEDPIPERBIN="/home/pebert/work/code/mpggit/piedpiper/bin"
PIEDPIPERLIB="/home/pebert/work/code/mpggit/piedpiper"

echo "#!/bin/sh" > ./etc/conda/activate.d/env_vars.sh

echo "" >> ./etc/conda/activate.d/env_vars.sh

echo "export PATH=${PIEDPIPERBIN}:\$PATH" >> ./etc/conda/activate.d/env_vars.sh

echo "export PYTHONPATH=${PIEDPIPERLIB}:\$PYTHONPATH" >> ./etc/conda/activate.d/env_vars.sh

echo "" >> ./etc/conda/activate.d/env_vars.sh

echo "export DRMAA_LIBRARY_PATH=/usr/lib/libdrmaa.so" >> ./etc/conda/activate.d/env_vars.sh

echo "export SGE_ROOT=/TL/deep-gridengine" >> ./etc/conda/activate.d/env_vars.sh

echo "export SGE_CELL=deep" >> ./etc/conda/activate.d/env_vars.sh

# UNSET the environment variables upon deactivation

echo "#!/bin/sh" > ./etc/conda/deactivate.d/env_vars.sh

echo "" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset DRMAA_LIBRARY_PATH" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset SGE_ROOT" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset SGE_CELL" >> ./etc/conda/deactivate.d/env_vars.sh

echo "Environment configured"


