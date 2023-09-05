import os
import cdsapi
import logging

import xarray as xr

from src.util import create_folder
from src.config import INPUT_DIR


logging.info("Downloading land/sea mask...")

c = cdsapi.Client()

# If no bounding box is provided, we we get a NetCDF file which has a longitude with values from 0°
# to 360° instead of -180°-180°. I think I have filed a bug some years ago, but cannot find it
# any longer.
# However, it is still broken - see fix below.
north, west, south, east = 90, 180, -90, -180

# Format for downloading ERA5: North/West/South/East
bounding_box = "{}/{}/{}/{}".format(north, west, south, east)

path = create_folder("land_sea_mask", prefix=INPUT_DIR)
fname = path / "land_sea_mask.nc"

c.retrieve(
    "reanalysis-era5-single-levels",
    {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": "land_sea_mask",
        # time stamp is pretty arbitrary, shouldn't make a difference, but it API requires it
        "time": "00:00",
        "day": "01",
        "month": "01",
        "year": "2023",
        "area": bounding_box,
    },
    fname,
)


# For unknown reasons the longitude is 539.75°, which 360° too much, it should be 179.25°.
# This is probably a cdsapi bug and requires a workaround, because the coordinates need to match
# the other ERA5 data.
land_sea_mask = xr.open_dataset(fname)
longitude = xr.DataArray(land_sea_mask.longitude)
assert longitude[-1] == 539.75, "csdapi bug has been fixed or changed, workaround needs adaption"
longitude[-1] = longitude[-1] - 360
land_sea_mask["longitude"] = longitude
# I think we cannot write directly to the same file
fname_tmp = fname.parent / "land_sea_mask_tmp.nc"
land_sea_mask.to_netcdf(fname_tmp)
land_sea_mask.close()
os.replace(fname_tmp, fname)
