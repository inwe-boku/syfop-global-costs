"""
"""

import logging

import xarray as xr

from src.config import YEARS
from src.config import MONTHS
from src.config import INTERIM_DIR

from src.logging_config import setup_logging


def _load_renewable_timeseries(technology):
    fnames = (
        INTERIM_DIR / f"{technology}" / f"{technology}_{year}-{month:02d}.nc"
        for year in YEARS
        for month in MONTHS
    )
    return xr.open_mfdataset(fnames)["specific generation"]


def main():
    assert len(MONTHS) == 12
    years = "-".join(str(year) for year in YEARS)

    for technology in ("pv", "wind"):
        logging.info(f"Loading {technology} time series...")
        renewable_timeseries = _load_renewable_timeseries(technology)
        logging.info(f"Writing {technology} time series...")
        renewable_timeseries.to_netcdf(INTERIM_DIR / f"{technology}" / f"{technology}_{years}.nc")
        del renewable_timeseries


if __name__ == "__main__":
    setup_logging()
    main()
