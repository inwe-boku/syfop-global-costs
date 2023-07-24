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
    assert len(MONTHS) == 12
    years = "-".join(str(year) for year in YEARS)
    fname =INTERIM_DIR / f"{technology}" / f"{technology}_{years}.nc"
    return xr.open_dataarray(fname)


def load_pv():
    technology = "pv"
    return _load_renewable_timeseries(technology)


def load_wind():
    technology = "wind"
    return _load_renewable_timeseries(technology)
