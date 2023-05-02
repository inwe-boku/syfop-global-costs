import logging

import atlite

from src import config
from src.util import create_folder


def download_era5(year, month):
    time_period = f"{year}-{month:02d}"

    path = create_folder("era5", prefix=config.INPUT_DIR)
    fname = f"global-{time_period}"

    logging.info(f"Preparing ERA5 data {fname}...")

    cutout = atlite.Cutout(
        path / fname,
        module="era5",
        x=slice(-180, 180),
        y=slice(-90, 90),
        # chunks={"time": 100},
        time=time_period,
    )

    cutout.prepare()

    return cutout
