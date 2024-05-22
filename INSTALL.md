How to install
==============

*syfop-global-costs* is used by cloning the repository and installing dependencies in a conda
environment.  We recommend to install the dependencies using
[micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html). Tested on Ubuntu
20.04.6 LTS. Comes without warranty for any other OS.

Run the following commands:

```
git clone https://github.com/inwe-boku/syfop-global-costs/
cd syfop-global-costs/
micromamba create -n syfop-global-costs
micromamba activate syfop-global-costs
```

# TODO remove PYTHONPATH from run.sh
# TODO create env.yml with precise & tested versions

Install dependencies:

```
# Python 3.10 is required, because cplex does not support Python 3.11 yet
micromamba install -c conda-forge python=3.10 numpy pandas jupyter cdsapi netcdf4 atlite pip
micromamba install -c conda-forge -c bioconda snakemake
micromamba install -c conda-forge xarray linopy=0.3.8 pint pint-xarray highs networkx netgraph
pip install git+https://github.com/inwe-boku/syfop
```

Request an API key for the [CDS API](https://cds.climate.copernicus.eu/api-how-to) and store it
`~/.cdsapirc` as [described here](https://cds.climate.copernicus.eu/api-how-to).

see syfop repo for a dokumentation on how to install cplex
