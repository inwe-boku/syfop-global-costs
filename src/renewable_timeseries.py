import logging

import scipy
import numpy as np
import xarray as xr


def unstack_to_xy(timeseries, cutout):
    """ """
    out = timeseries.to_dataset()
    out = out.assign_coords(x=cutout.data.x, y=cutout.data.y)
    out = out.stack(tmp=("y", "x")).reset_index("dim_0", drop=True)
    out = out.rename(dim_0="tmp").unstack("tmp")[timeseries.name]

    return out


def wind(cutout):
    sparse_identity = scipy.sparse.identity(cutout.data.sizes["x"] * cutout.data.sizes["y"])
    wind = cutout.wind("Vestas_V90_3MW", matrix=sparse_identity)
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


def pv(cutout):
    sparse_identity = scipy.sparse.identity(cutout.data.sizes["x"] * cutout.data.sizes["y"])

    # TODO iterate through days in a loop or so because otherwise it requires too much RAM

    pv_timeseries = []
    for cutout_chunk in iterate_time_chunks(cutout, chunksize=48):
        # t0 = time.time()
        logging.info(f"Converting chunk {cutout_chunk.data.time[0].values}....")

        pv_timeseries_chunk = cutout_chunk.pv(
            panel="CSi", orientation={"slope": 30.0, "azimuth": 180.0}, matrix=sparse_identity
        )
        pv_timeseries_chunk = unstack_to_xy(pv_timeseries_chunk, cutout_chunk)

        pv_timeseries.append(pv_timeseries_chunk)

        # runtime = time.time() - t0
        # print("runtime", runtime, "total runtime", 744//CHUNKSIZE * runtime)

    logging.info(f"Merging...")
    return xr.concat(pv_timeseries, dim='time')
