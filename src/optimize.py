import re
import io
import time
import logging
from contextlib import redirect_stdout

import numpy as np
import xarray as xr

from src.util import create_folder

from src.config import SOLVER
from src.config import SOLVER_DEFAULTS
from src.config import CHUNK_SIZE
from src.config import NUM_PROCESSES

from src.load_data import load_pv
from src.load_data import load_wind
from src.load_data import load_land_sea_mask

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
    "runtime",
    "runtime_solver",
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


def optimize_pixel(
    wind_input_flow, pv_input_flow, model_file=None, solver_name=SOLVER, **solver_params
):
    """Optimize one pixel.

    Parameters
    ----------
    wind_input_flow : xr.DataArray
        wind time series
    pv_input_flow : xr.DataArray
        PV time series
    model_file :
        writes a LP file for further use in Gurobi command line tools (might be ignored for some
        solvers, see documentation of linopy)
    solver_name : str
        name of solver, passed to linopy (e.g. gurobi, highs, cplex, ...)
    solver_params: dict
        passed to linopy for solver

    """
    logging.info("Start optimization...")

    t0 = time.time()

    # TODO model parameters should be packed into a named tuple or so and then passed to this
    # function as parameter

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

    if solver_name in SOLVER_DEFAULTS:
        solver_params = {**SOLVER_DEFAULTS[solver_name], **solver_params}

    with io.StringIO() as buf, redirect_stdout(buf):
        network.optimize(
            solver_name=solver_name,
            **solver_params,
        )
        # XXX do we need the optimizer's log output?
        output = buf.getvalue()

    logging.debug(f"Solver output: \n\n{output}")

    solution = network.model.solution

    # Parse log output to get run time from solver.
    patterns = (
        # Gurobi (gurobipy might provide this value directly, but linopy does not pass it through)
        r"Solved in \d+ iterations and ([0-9.]+) seconds \([0-9.]+ work units\)",
        # Cplex
        r"Total time on \d+ threads = ([0-9.]+) sec. \([0-9.]+ ticks\)",
    )
    for pattern in patterns:
        output_match = re.search(pattern, output)
        if output_match:
            runtime_solver = float(output_match.group(1))
            break
    else:
        # if the pattern is not found, let's simply ignore it...
        runtime_solver = float("nan")

    logging.info(f"Solver runtime: {runtime_solver}")
    solution["runtime_solver"] = runtime_solver
    solution["runtime"] = time.time() - t0

    solution = solution.expand_dims(x=pv_input_flow.x, y=pv_input_flow.y)

    return solution, network


def optimize_pixel_by_coord(x, y, model_file=None, **solver_params):
    """Optimize a single pixel instead of a chunk of pixels at once. Helpful for quick
    experiments."""
    logging.info("Load renewable time series...")
    wind_input_flow = load_wind().isel(x=[x], y=[y]).load()
    pv_input_flow = load_pv().isel(x=[x], y=[y]).load()

    return optimize_pixel(
        wind_input_flow=wind_input_flow,
        pv_input_flow=pv_input_flow,
        model_file=model_file,
        **solver_params,
    )


def optimize_network_chunk_ploomber(product, upstream, chunk):
    # XXX this is a temporary wrapper to avoid breaking the old scripts without ploomber
    optimize_network_chunk(*chunk)


def optimize_network_chunk(x_start_idx, y_start_idx, product=None, upstream=None):
    """This function computes the result for a chunk of pixels in a simple for-loop and stores the
    result in a single NetCDF file. Multiple instances of this function can be run in parallel in
    separate processes."""
    logger = logging.getLogger(f"optimization_{x_start_idx}_{y_start_idx}")
    logger.info(f"Starting computation for chunk {x_start_idx},{y_start_idx}...")

    logger.info("Load renewable time series...")

    t0 = time.time()

    x_slice = slice(x_start_idx, x_start_idx + CHUNK_SIZE[0])
    y_slice = slice(y_start_idx, y_start_idx + CHUNK_SIZE[1])

    wind_input_flow = load_wind().isel(x=x_slice, y=y_slice).load()
    pv_input_flow = load_pv().isel(x=x_slice, y=y_slice).load()
    land_sea_mask = load_land_sea_mask().load()

    logging.info(f"Loading time series files took {time.time() - t0}")

    # this makes the for loop easier
    param = xr.Dataset({"wind_input_flow": wind_input_flow, "pv_input_flow": pv_input_flow})

    i = 0
    solutions = []

    # XXX no idea if groupby is really the best option to loop through two dimensions, but it seems
    # to work for now.

    # the number of pixel in the chunk we are processing here
    num_pixels = param.sizes["x"] * param.sizes["y"]

    for param_x_coord, param_x in param.groupby("x"):
        for param_y_coord, param_y in param_x.groupby("y"):
            i += 1
            # exclude pixels which are fully covered by sea area...
            pixel_name = (
                f"pixel {param_x_coord}/{param_y_coord} (number {i}/{num_pixels}) "
                f"for chunk {x_start_idx},{y_start_idx}"
            )
            if land_sea_mask.sel(longitude=param_x_coord, latitude=param_y_coord) == 0.0:
                logger.info(f"Skipping because not on land area: {pixel_name}...")
                # adding empty solutions should make merging easier
                emtpy_solution = xr.Dataset({k: np.nan for k in OUTPUT_VARS})
                emtpy_solution = emtpy_solution.expand_dims(x=[param_x_coord], y=[param_y_coord])
                solutions.append(emtpy_solution)
                continue

            t0 = time.time()
            logger.info(f"Computing {pixel_name}...")

            param = param_y.expand_dims(x=1, y=1).drop_vars(("lon", "lat"))

            solution, _ = optimize_pixel(
                wind_input_flow=param.wind_input_flow,
                pv_input_flow=param.pv_input_flow,
            )

            solutions.append(solution[OUTPUT_VARS])

            runtime = time.time() - t0
            logging.info(
                f"Pixel runtime for pixel {param_x_coord}/{param_y_coord} "
                f"took: {runtime}s (about {runtime / NUM_PROCESSES}s per pixel)"
            )

    # TODO check if xr.concat() would be faster (supports only one dimension)
    out = xr.combine_by_coords(solutions)

    path = create_folder("network_solution")
    out.to_netcdf(path / f"network_solution_{x_start_idx}_{y_start_idx}.nc")
    logger.info(f"Chunk {x_start_idx},{y_start_idx} done!")
