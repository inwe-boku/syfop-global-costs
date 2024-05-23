#!/bin/bash

# The purpose of this script is to set environment variables and to start Snakemake. Depending on
# the hostname, a Snakemake file will be guessed.
#
# Usage:
#
#  ./run.sh
#
# or
#
#  ./run.sh some_custom=snakemake_parameter
#
# -----------------------------------------------------------------------------------------------


# This absolute path won't work on the VSC (see README.md), but Gurobi does not work on VSC anyway,
# so it does not really matter..
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/gurobi1001/linux64/lib
export GRB_LICENSE_FILE=$HOME/gurobi.lic


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

if [ $(hostname) == "nora" ]; then
    echo "Running on nora..."
    export SNAKEMAKE_PROFILE=config/nora
elif [ -v VSC_CLUSTER_ID ]; then
    echo "Running via SLURM on VSC..."
    export SNAKEMAKE_PROFILE=config/vsc
fi


snakemake $@
