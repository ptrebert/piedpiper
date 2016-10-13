#!/bin/bash

# CHANGE: specify location of created Pied Piper environment
CONDAENVPATH="${HOME}/tools/conda/env"
INSTALLPATH="${CONDAENVPATH}/piedpiper"

cd ${INSTALLPATH} &&
mkdir -p ./etc/conda/activate.d &&
mkdir -p ./etc/conda/deactivate.d &&
touch ./etc/conda/activate.d/env_vars.sh &&
touch ./etc/conda/deactivate.d/env_vars.sh

# CHANGE: checkout/clone location of Pied Piper git repository
PIEDPIPERGIT="${HOME}/repos/git"
# NOT CHANGE: these variables can be left unchanged unless you know what you are doing
PIEDPIPERBIN="${PIEDPIPERGIT}/piedpiper/bin"
PIEDPIPERLIB="${PIEDPIPERGIT}/piedpiper"


#
# Following lines:
# Adapt environment activation script to set Pied Piper paths
# and necessary environment variables for DRMAA/SGE

echo "#!/bin/sh" > ./etc/conda/activate.d/env_vars.sh

echo "" >> ./etc/conda/activate.d/env_vars.sh

echo "export PATH=${PIEDPIPERBIN}:\$PATH" >> ./etc/conda/activate.d/env_vars.sh

echo "export PYTHONPATH=${PIEDPIPERLIB}:\$PYTHONPATH" >> ./etc/conda/activate.d/env_vars.sh

echo "" >> ./etc/conda/activate.d/env_vars.sh

echo "export DRMAA_LIBRARY_PATH=/usr/lib/libdrmaa.so" >> ./etc/conda/activate.d/env_vars.sh

echo "export SGE_ROOT=/gridware/sge" >> ./etc/conda/activate.d/env_vars.sh

echo "export SGE_CELL=default" >> ./etc/conda/activate.d/env_vars.sh

#
# Following lines:
# Unset the environment variables upon deactivation (exit of environment)

echo "#!/bin/sh" > ./etc/conda/deactivate.d/env_vars.sh

echo "" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset PYTHONPATH" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset DRMAA_LIBRARY_PATH" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset SGE_ROOT" >> ./etc/conda/deactivate.d/env_vars.sh

echo "unset SGE_CELL" >> ./etc/conda/deactivate.d/env_vars.sh

echo "Environment configured"


