#!/bin/bash

set -exo pipefail

wget https://github.com/conda-forge/miniforge/releases/download/4.8.3-4/Miniforge3-4.8.3-4-MacOSX-x86_64.sh -O miniforge.sh
/bin/bash miniforge.sh -b -p /opt/conda
source /opt/conda/etc/profile.d/conda.sh
conda activate base
conda config --system --set auto_update_conda false
conda config --system --prepend channels ***REMOVED***
conda config --system --set custom_channels.***REMOVED*** https://${***REMOVED***}:${***REMOVED***}@conda.***REMOVED***
conda install -y mamba=0.2.12
mamba install -y conda-build conda-channel-client yq jq

yq -Y ". + {dependencies: [.dependencies[], \"python=${PYTHON_VERSION}\"] }" environment.yml > /tmp/environment.yml
mamba env create -f /tmp/environment.yml
conda activate $(yq -r .name environment.yml)
pip install --no-use-pep517 --no-deps --disable-pip-version-check -e .
pytest -nauto tests --doctest-modules src/