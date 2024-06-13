How to install
==============

*syfop-global-costs* is used by cloning the repository and installing dependencies in a conda
environment. We recommend to install the dependencies using
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html). Tested on Ubuntu
20.04.6 LTS. Comes without warranty for any other OS.

Run the following commands:

```
git clone https://github.com/inwe-boku/syfop-global-costs/
cd syfop-global-costs/

```

Then install dependencies from the `conda-env.yml` file:

```
micromamba env create -f conda-env.yml
pip install git+https://github.com/inwe-boku/syfop
```

To install the latest versions of all dependencies manually instead of the fixed and tested
versions, run the following commands:

```
# Python 3.10 is required, because cplex does not support Python 3.11 yet
micromamba create -n syfop-global-costs
micromamba activate syfop-global-costs
micromamba install -c conda-forge python=3.10 numpy pandas jupyter cdsapi netcdf4 atlite pip
micromamba install -c conda-forge -c bioconda snakemake
micromamba install -c conda-forge xarray linopy=0.3.8 pint pint-xarray highs networkx netgraph
pip install git+https://github.com/inwe-boku/syfop

# optionally update the conda environment file:
# conda env export --no-builds > conda-env.yml
```

Request an API key for the [CDS API](https://cds.climate.copernicus.eu/api-how-to) and store it
`~/.cdsapirc` as [described here](https://cds.climate.copernicus.eu/api-how-to).

To use the optimization problem, you need to install a solver. We recommend to use CPlex. Find an
installation manual in the [documentation of syfop](https://syfop.readthedocs.io/latest/how-to-install.html#installation-of-cplex).


VSC
---

Here some more detailed installation instructions for the VSC:

[Install micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#automatic-install)
on the VSC in your home folder:

```
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
```

Log out and log in again.

```
cd $DATA/   # the data folder will be huge, we should work in $DATA
git clone https://github.com/inwe-boku/syfop-global-costs/

# alternatively, if you have an ssh key set up:
# git clone git@github.com:inwe-boku/syfop-global-costs

cd syfop-global-costs/
micromamba env create -f conda-env.yml   # if this fails, try to install the packages manually, see above
```

Install CPlex and the `.cdsapirc` file as described above.
