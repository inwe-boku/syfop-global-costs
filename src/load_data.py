import glob

import xarray as xr

from src.config import YEARS
from src.config import MONTHS
from src.config import INPUT_DIR
from src.config import INTERIM_DIR


def load_land_sea_mask():
    return xr.open_dataset(INPUT_DIR / "era5" / "land_sea_mask.nc").lsm


def load_network_solution():
    # XXX at some point we might want to replace this with the concatenated version of the
    # solution, but it is still very useful for incomplete solutions
    fnames = glob.glob(str(INTERIM_DIR / "network_solution" / "*.nc"))
    solution = xr.open_mfdataset(fnames)
    return solution


def _load_renewable_timeseries(technology):
    fnames = (
        INTERIM_DIR / f"{technology}" / f"{technology}_{year}-{month:02d}.nc"
        for year in YEARS
        for month in MONTHS
    )
    return xr.open_mfdataset(fnames)["specific generation"]


def load_pv():
    technology = "pv"
    return _load_renewable_timeseries(technology)


def load_wind():
    technology = "wind"
    return _load_renewable_timeseries(technology)
