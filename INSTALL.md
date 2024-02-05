How to install
==============

*syfop-global-costs* is used by cloning the repositories and installing dependencies using
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html). Tested on Ubuntu
20.04.6 LTS. Comes without warranty for any other OS.


Run the following commands:

```
git clone https://github.com/inwe-boku/syfop-global-costs/
cd syfop-global-costs/
git clone https://github.com/inwe-boku/syfop
micromamba create -n syfop-global-costs
micromamba activate syfop-global-costs
```

TODO syfop could be a git submodule

At the moment, there is no package built for *[syfop](https://github.com/inwe-boku/syfop)*,
therefore we simply use it directly from a GIT clone in a sub folder. The PYTHONPATH
is set accordingly in [run.sh](run.sh).

Install dependencies:

```
# Python 3.10 is required, because cplex does not support Python 3.11 yet
micromamba install -c conda-forge python=3.10 xarray numpy pandas jupyter cdsapi linopy networkx netcdf4 atlite pip
micromamba install -c conda-forge -c bioconda snakemake
pip install cdsapi
```

TODO create env.yml with precise & tested versions



Installation of Gurobi
----------------------

TODO


Installation of CPLEX
---------------------

To install cplex follow [these instructions](https://community.ibm.com/community/user/ai-datascience/blogs/xavier-nodet1/2020/07/09/cplex-free-for-students):

> For quick access to CPLEX Optimization Studio through this program, go to http://ibm.biz/CPLEXonAI. Click on Software, then you'll find, in the ILOG CPLEX Optimization Studio card, a link to register. Once your registration is accepted, you will see a link to download of the AI version.

Note that after clicking the download link, you need to select "HTTP" as download method if you
don't want to use the *Download director*. Select the version of the CPLEX Optimization Studio which
suits your OS and then click download.

Make the file executable, run it and follow the instructions of the installer:

```
chmod +x ~/Downloads/cplex_studio2211.linux_x86_64.bin
~/Downloads/cplex_studio2211.linux_x86_64.bin
```

It does not seem to make a difference if a conda environment is activated before running the installer.

Note that you don't need root permissions if you install it to your home folder, e.g.
`/home/YOUR_USER/cplex_studio2211`.

The installer will print out a command to install the Python package to access CPLEX via a Python
API. Activate the conda environment and then install the cplex package:

```
micromamba activate syfop-global-costs
python /home/YOUR_USER/cplex_studio2211/python/setup.py install
```

CPLEX is not compiled to be used in a conda environment and therefore he library search path needs to be adjusted for CPLEX to avoid the following error:

```
libstdc++.so.6: version `GLIBCXX_3.4.29' not found
```

A detailed explanation of the problem can be found in [this stackoverflow
answer](https://stackoverflow.com/a/77940023/859591).

To fix the search path, run the following commands:

```
micromamba activate syfop-global-costs

# patchelf can also be used from the system, if already installed or if you have root access
# do something like: sudo apt get install patchelf
micromamba install -c conda-forge patchelf

patchelf --set-rpath '$ORIGIN/../../../..'  $CONDA_PREFIX/lib/python3.10/site-packages/cplex/_internal/libcplex2211.so
```

Note that there is an alternative workaround in [run.sh](run.sh), which is not necessary if the
patching procedure above was successful.
