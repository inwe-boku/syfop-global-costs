import cdsapi
import logging

from src.config import INPUT_DIR


logging.info("Downloading land/sea mask...")

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels',
    {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': 'land_sea_mask',
            # time stamp is pretty arbitrary, shouldn't make a difference, but it API requires it
            'time': '00:00',
            'day': '01',
            'month': '01',
            'year': '2023',
        },
    INPUT_DIR / 'era5' / 'land_sea_mask.nc')
