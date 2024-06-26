import logging

import dask
import scipy
import numpy as np
import xarray as xr

from src.task import task
from src.download import create_era5_cutout


def unstack_to_xy(timeseries, cutout):
    """ """
    out = timeseries.to_dataset()
    out = out.assign_coords(x=cutout.data.x, y=cutout.data.y)
    out = out.stack(tmp=("y", "x")).reset_index("dim_0", drop=True)
    out = out.rename(dim_0="tmp").unstack("tmp")[timeseries.name]

    return out


def wind(cutout, params):
    sparse_identity = scipy.sparse.identity(cutout.data.sizes["x"] * cutout.data.sizes["y"])
    wind = cutout.wind(**params, matrix=sparse_identity)
    wind = unstack_to_xy(wind, cutout)
    return wind


def iterate_time_chunks(cutout, chunksize=None):
    if chunksize is None:
        # use chunks
        chunksizes_time = cutout.data.chunksizes["time"]
    else:
        chunksizes_time = [chunksize] * (cutout.data.sizes["time"] // chunksize)
        if cutout.data.sizes["time"] % chunksize != 0:
            chunksizes_time.append(cutout.data.sizes["time"] % chunksize)

    chunk_idx_start = 0
    for chunk_idx_end in np.cumsum(chunksizes_time):
        chunk_time = cutout.data.time.isel(time=slice(chunk_idx_start, chunk_idx_end))
        cutout_chunk = cutout.sel(time=chunk_time)
        yield cutout_chunk
        chunk_idx_start = chunk_idx_end


def pv(cutout, params):
    sparse_identity = scipy.sparse.identity(cutout.data.sizes["x"] * cutout.data.sizes["y"])

    # TODO iterate through days in a loop or so because otherwise it requires too much RAM

    pv_timeseries = []
    for cutout_chunk in iterate_time_chunks(cutout, chunksize=48):
        # t0 = time.time()
        logging.info(f"Converting chunk {cutout_chunk.data.time[0].values}....")

        pv_timeseries_chunk = cutout_chunk.pv(**params, matrix=sparse_identity)
        pv_timeseries_chunk = unstack_to_xy(pv_timeseries_chunk, cutout_chunk)

        pv_timeseries.append(pv_timeseries_chunk)

        # runtime = time.time() - t0
        # print("runtime", runtime, "total runtime", 744//CHUNKSIZE * runtime)

    logging.info(f"Merging...")
    return xr.concat(pv_timeseries, dim="time")


@task
def generate_renewable_timeseries(inputs, outputs, technology, year, month, renewable_params):
    cutout = create_era5_cutout(inputs, outputs, year, month)

    if technology == "wind":
        generate = wind
    elif technology == "pv":
        generate = pv

    logging.info(f"Generate {technology} time series...")

    # TODO let's silence the large chunk warning for now, not sure if relevant...
    with dask.config.set(**{"array.slicing.split_large_chunks": False}):
        wind_timeseries = generate(cutout, renewable_params[technology])
    wind_timeseries.to_netcdf(outputs.renewable_timeseries)


@task
def concat_renewable_timeseries(inputs, outputs, technology):
    logging.info(f"Loading {technology} time series...")

    renewable_timeseries = xr.open_mfdataset(inputs)["specific generation"]

    logging.info(f"Writing {technology} time series...")
    renewable_timeseries.to_netcdf(outputs[0])
