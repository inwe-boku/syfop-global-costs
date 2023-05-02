import logging

import dask

from src import config
from src.util import create_folder
from src.download import download_era5
from src.renewable_timeseries import wind, pv
from src.logging_config import setup_logging


setup_logging()

for year in config.YEARS:
    for month in config.MONTHS:
        cutout = download_era5(year, month)

        time_period = f"{year}-{month:02d}"

        # TODO let's silence the large chunk warning for now, not sure if relevant...

        with dask.config.set(**{"array.slicing.split_large_chunks": False}):
            wind_timeseries = wind(cutout)
        path = create_folder("wind")
        wind_timeseries.to_netcdf(path / f"wind_{time_period}.nc")

        logging.info("Generate PV time series...")
        with dask.config.set(**{"array.slicing.split_large_chunks": False}):
            pv_timeseries = pv(cutout)
        path = create_folder("pv")
        pv_timeseries.to_netcdf(path / f"pv_{time_period}.nc")
