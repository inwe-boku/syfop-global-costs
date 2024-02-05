#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/gurobi1001/linux64/lib
export GRB_LICENSE_FILE=/home/pregner/gurobi.lic

# Workaround for CPLEX: the library search path needs to be adjusted for CPLEX to avoid the
# following error:
#   libstdc++.so.6: version `GLIBCXX_3.4.29' not found
# Detailed explanation of the problem: https://stackoverflow.com/a/77940023/859591
# There are two ways to adjust the search path. If `libcplex2211.so` is patched using patchelf as
# explained in INSTALL.md, the LD_LIBRARY_PATH does not need to be changed. However, this is an
# alternative workaround to patching libcplex2211.so:
# export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH


BASEDIR=$(dirname "$0")
export PYTHONPATH=$PYTHONPATH:$BASEDIR

# this assumes that the syfop library is simple cloned as subdir
export PYTHONPATH=$PYTHONPATH:$BASEDIR/syfop

if [ $(hostname) == "nora" ]; then
    echo nora
    export SNAKEMAKE_PROFILE=config/nora
elif [ -v VSC_CLUSTER_ID ]; then
    export SNAKEMAKE_PROFILE=config/vsc
fi


snakemake $@

