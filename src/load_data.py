import glob

import xarray as xr

from src.paths import INPUT_DIR
from src.paths import INTERIM_DIR


def load_land_sea_mask():
    return xr.open_dataset(INPUT_DIR / "land_sea_mask" / "land_sea_mask.nc").lsm


def load_network_solution():
    # XXX at some point we might want to replace this with the concatenated version of the
    # solution, but it is still very useful for incomplete solutions
    fnames = glob.glob(str(INTERIM_DIR / "network_solution" / "*.nc"))
    solution = xr.open_mfdataset(fnames)
    return solution


def _load_renewable_timeseries(technology, year):
    fname = INTERIM_DIR / "renewable_timeseries" / f"{technology}_{year}.nc"
    return xr.open_dataarray(fname)


def load_pv(year):
    technology = "pv"
    return _load_renewable_timeseries(technology, year)


def load_wind(year):
    technology = "wind"
    return _load_renewable_timeseries(technology, year)
