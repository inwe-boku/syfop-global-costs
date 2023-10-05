import logging

import atlite

from src import config
from src.task import task
from src.util import create_folder


@task
def download_era5(inputs, outputs, year, month):
    time_period = f"{year}-{month}"

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

    # TODO can we specify here some features (PV + wind) only to reduce size of stored data?
    cutout.prepare()

    return cutout
