#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/gurobi1001/linux64/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/pregner/micromamba/envs/test/lib
export GRB_LICENSE_FILE=/home/pregner/gurobi.lic

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

