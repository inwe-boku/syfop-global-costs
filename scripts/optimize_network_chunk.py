"""Takes two indices as input and computes a chunk in the size of NxM where N,M is stored
in CHUNK_SIZE
"""

import re
import io
import sys
import time
import logging
from contextlib import redirect_stdout

import xarray as xr

from src.util import create_folder

from src.config import YEARS
from src.config import MONTHS
from src.config import INPUT_DIR
from src.config import CHUNK_SIZE
from src.config import INTERIM_DIR
from src.config import NUM_PROCESSES

from src.logging_config import setup_logging
from src.methanol_network import create_methanol_network

from src.model_parameters import pv_cost
from src.model_parameters import wind_cost
from src.model_parameters import methanol_demand
from src.model_parameters import storage_params
from src.model_parameters import co2_cost
from src.model_parameters import co2_convert_factor
from src.model_parameters import electrolizer_cost
from src.model_parameters import electrolizer_convert_factor
from src.model_parameters import methanol_synthesis_cost
from src.model_parameters import methanol_synthesis_convert_factor
from src.model_parameters import methanol_synthesis_input_proportions


# variables to be saved in the final NetCDF file
OUTPUT_VARS = [
    "size_solar_pv",
    "size_wind",
    "size_storage_electricity",
    "size_storage_electrolizer",
    "size_electrolizer",
    "size_storage_co2",
    "size_co2",
    "size_storage_methanol_synthesis",
    "size_methanol_synthesis",
]


def filter_solution(solution, x, y):
    """Filter solution Dataset object: Storing all variables would be too much data, because each
    solution contains many time series."""
    return solution[OUTPUT_VARS].expand_dims(x=x, y=y)


def optimize_network_single(param):
    """Optimize one pixel."""
    logging.info("Start optimization...")

    t0 = time.time()

    wind_input_flow = param.wind_input_flow
    pv_input_flow = param.pv_input_flow
    network = create_methanol_network(
        pv_input_flow=pv_input_flow,
        pv_cost=pv_cost,
        wind_input_flow=wind_input_flow,
        wind_cost=wind_cost,
        methanol_demand=methanol_demand,
        storage_params=storage_params,
        co2_cost=co2_cost,
        co2_convert_factor=co2_convert_factor,
        electrolizer_cost=electrolizer_cost,
        electrolizer_convert_factor=electrolizer_convert_factor,
        methanol_synthesis_cost=methanol_synthesis_cost,
        methanol_synthesis_convert_factor=methanol_synthesis_convert_factor,
        methanol_synthesis_input_proportions=methanol_synthesis_input_proportions,
    )

    logging.info(f"Creating network took {time.time() - t0}")

    with io.StringIO() as buf, redirect_stdout(buf):
        # basis_fn can be set to a filename ending in *.sol, the resulting file can be then used
        # for warmstart_fn but it does not speed up the optimization - it is a bit slower. I assume
        # that the overhead for reading the file is larger then the benefit.
        network.optimize(
            "gurobi",
            warmstart_fn=None,
            # basis_fn=INTERIM_DIR / 'model.lp',
            basis_fn=None,
            # this has been found wiht grbtune - Gurobi's command line tuning tool
            Method=2,
            ScaleFlag=0,
            PreDual=1,
            PrePasses=1,
        )
        # XXX do we need the optimizer's log output?
        output = buf.getvalue()

    logging.debug(f"Solver output: \n\n{output}")

    solution = filter_solution(network.model.solution, x=pv_input_flow.x, y=pv_input_flow.y)

    # TODO this works only for Gurobi
    # Parse log output to get run time from solver. gurobipy might provide this value directly, but
    # linopy does not pass it through. If the pattern is not found, let's simply ignore it.
    pattern = r"Solved in \d+ iterations and ([0-9.]+) seconds \([0-9.]+ work units\)"
    output_match = re.search(pattern, output)
    runtime_solver = float(output_match.group(1)) if output_match else float("nan")

    solution["runtime_solver"] = runtime_solver
    solution["runtime"] = time.time() - t0

    return solution


def optimize_network_chunk(x_start_idx, y_start_idx):
    logger = logging.getLogger(f"optimization_{x_start_idx}_{y_start_idx}")
    logger.info(f"Starting computation for chunk {x_start_idx},{y_start_idx}...")

    logger.info("Load renewable time series...")

    t0 = time.time()
    wind_raw = xr.open_mfdataset(
        [
            INTERIM_DIR / "wind" / f"wind_{year}-{month:02d}.nc"
            for month in MONTHS
            for year in YEARS
        ]
    )
    pv_raw = xr.open_mfdataset(
        [INTERIM_DIR / "pv" / f"pv_{year}-{month:02d}.nc" for month in MONTHS for year in YEARS]
    )

    x_slice = slice(x_start_idx, x_start_idx + CHUNK_SIZE[0])
    y_slice = slice(y_start_idx, y_start_idx + CHUNK_SIZE[1])

    wind_input_flow = wind_raw.isel(x=x_slice, y=y_slice)
    wind_input_flow = wind_input_flow["specific generation"].load()

    pv_input_flow = pv_raw.isel(x=x_slice, y=y_slice)
    pv_input_flow = pv_input_flow["specific generation"].load()

    logging.info(f"Loading time series files took {time.time() - t0}")

    land_sea_mask = xr.load_dataset(INPUT_DIR / "era5" / "land_sea_mask.nc").lsm.load()

    param = xr.Dataset({"wind_input_flow": wind_input_flow, "pv_input_flow": pv_input_flow})

    i = 0
    solutions = []

    # XXX no idea if groupby is really the best option to loop through two dimensions, but it seems
    # to work for now.

    # the number of pixel in the chunk we are processing here
    num_pixels = param.sizes["x"] * param.sizes["y"]

    for param_x_coord, param_x in param.groupby("x"):
        for param_y_coord, param_y in param_x.groupby("y"):
            # exclude pixels which are fully covered by sea area...
            pixel_name = (
                f"pixel {param_x_coord}/{param_y_coord} (number {i}/{num_pixels}) "
                f"for chunk {x_start_idx},{y_start_idx}"
            )
            if land_sea_mask.sel(longitude=param_x_coord, latitude=param_y_coord) == 0.0:
                logger.info(f"Skipping because not on land area: {pixel_name}...")
                continue

            t0 = time.time()
            logger.info(f"Computing {pixel_name}...")

            param = param_y.expand_dims(x=1, y=1).drop_vars(("lon", "lat"))
            solutions.append(optimize_network_single(param))

            runtime = time.time() - t0
            logging.info(
                f"Pixel runtime for pixel {param_x_coord}/{param_y_coord} "
                f"took: {runtime}s (about {runtime / NUM_PROCESSES}s per pixel)"
            )
            i += 1

    # TODO check if xr.concat() would be faster (supports only one dimension)
    out = xr.combine_by_coords(solutions)

    path = create_folder("network_solution")
    out.to_netcdf(path / f"network_solution_{x_start_idx}_{y_start_idx}.nc")
    logger.info(f"Chunk {x_start_idx},{y_start_idx} done!")


if __name__ == "__main__":
    # TODO do we need to write log files to different files for each chunk or is it okay if
    # multiple processes log to one file at the same time?
    setup_logging()
    optimize_network_chunk(int(sys.argv[1]), int(sys.argv[2]))
