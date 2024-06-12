import os
import logging

import cdsapi
import atlite
import xarray as xr

from src import config
from src.task import task
from src.util import create_folder



def _create_era5_cutout(inputs, outputs, year, month):
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


def create_era5_cutout(inputs, outputs, year, month):
    # here we assume that files have been downloaded already.
    return _create_era5_cutout(inputs, outputs, year, month)


@task
def download_era5(inputs, outputs, year, month):
    return _create_era5_cutout(inputs, outputs, year, month)


@task
def download_land_sea_mask(inputs, outputs):
    logging.info("Downloading land/sea mask...")

    fname = outputs[0]

    c = cdsapi.Client()

    # If no bounding box is provided, we we get a NetCDF file which has a longitude with values
    # from 0° to 360° instead of -180°-180°. I think I have filed a bug some years ago, but cannot
    # find it any longer.
    # However, it is still broken - see fix below.
    north, west, south, east = 90, 180, -90, -180

    # Format for downloading ERA5: North/West/South/East
    bounding_box = "{}/{}/{}/{}".format(north, west, south, east)

    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "format": "netcdf",
            "variable": "land_sea_mask",
            # time stamp is pretty arbitrary, shouldn't make a difference, but the API requires it
            "time": "00:00",
            "day": "01",
            "month": "01",
            "year": "2023",
            "area": bounding_box,
        },
        fname,
    )

    # For unknown reasons the longitude is 539.75°, which is 360° too much, it should be 179.25°.
    # This is probably a cdsapi bug and requires a workaround, because the coordinates need to
    # match the other ERA5 data.
    land_sea_mask = xr.open_dataset(fname)
    longitude = land_sea_mask.longitude.values
    assert (
        longitude[-1] == 539.75
    ), "csdapi bug has been fixed or changed, workaround needs adaption"
    longitude[-1] = longitude[-1] - 360
    land_sea_mask["longitude"] = longitude
    # I think we cannot write directly to the same file
    fname_tmp = f"{fname}.tmp"
    land_sea_mask.to_netcdf(fname_tmp)
    land_sea_mask.close()
    os.replace(fname_tmp, fname)
