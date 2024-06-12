import re
import io
import time
import logging
from contextlib import redirect_stdout

import numpy as np
import xarray as xr

from src.util import create_folder

from src.task import task

from src.config import SOLVER
from src.config import SOLVER_DEFAULTS

from src import snakemake_config

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
    wind_input_profile, pv_input_profile, model_file=None, solver_name=SOLVER, **solver_params
):
    """Optimize one pixel.

    Parameters
    ----------
    wind_input_profile : xr.DataArray
        wind time series
    pv_input_profile : xr.DataArray
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
        pv_input_profile=pv_input_profile,
        pv_cost=pv_cost,
        wind_input_profile=wind_input_profile,
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

    solution = solution.expand_dims(x=pv_input_profile.x, y=pv_input_profile.y)

    return solution, network


def optimize_pixel_by_coord(x, y, year, model_file=None, **solver_params):
    """Optimize a single pixel instead of a chunk of pixels at once. Helpful for quick
    experiments."""
    raise NotImplementedError(
        "This is not working atm because load_pv/load_wind also requires a "
        "renewable_scenario string to find the files."
    )
    logging.info("Load renewable time series...")
    wind_input_profile = load_wind(year).isel(x=[x], y=[y]).load()
    pv_input_profile = load_pv(year).isel(x=[x], y=[y]).load()

    return optimize_pixel(
        wind_input_profile=wind_input_profile,
        pv_input_profile=pv_input_profile,
        model_file=model_file,
        **solver_params,
    )


@task
def optimize_network_chunk(
    x_start_idx,
    y_start_idx,
    chunk_size,
    pv_timeseries_fname,
    wind_timeseries_fname,
    time_period_h="1h",
    inputs=None,
    outputs=None,
):
    """This function computes the result for a chunk of pixels in a simple for-loop and stores the
    result in a single NetCDF file. Multiple instances of this function can be run in parallel in
    separate processes.

    Parameters
    ----------
    x_start_idx : int
        start index of the chunk to be optimized in x dimension
    y_start_idx : int
        start index of the chunk to be optimized in y dimension
    time_period_h : str
        time resolution, '1h' will leave input unchanged (=this is a runtime performance), see
        xarray.DataArray.resample() for other possible values

    """
    logger = logging.getLogger(f"optimization_{x_start_idx}_{y_start_idx}")
    logger.info(f"Starting computation for chunk {x_start_idx},{y_start_idx}...")

    logger.info("Load renewable time series...")

    t0 = time.time()

    x_slice = slice(x_start_idx, x_start_idx + chunk_size[0])
    y_slice = slice(y_start_idx, y_start_idx + chunk_size[1])

    def slice_and_load(fname):
        # input_profile is an xarray object with dims: x, y, time
        input_profile = xr.open_dataarray(fname)
        input_profile = input_profile.isel(x=x_slice, y=y_slice)
        if time_period_h != "1h":
            # this seems to load() the xarray object, but an additional load() takes only <1ms
            input_profile = input_profile.resample(time=time_period_h).mean()

            # resample().mean() is pretty slow, also in comparison to load()
            # This is a faster alternative, which selects every second hour:
            # input_profile.sel(time=slice(None, None, 2))
            # But for a 5x5 chunk, the speed up is only about 600ms. Probably not worth it.

        if snakemake_config.config["testmode"]:
            # we need an equidistant time series without NaN values for syfop, but the test mode
            # downloads crappy data so let's just throw away NaNs (introduced by the resampling
            # above) and then use only two time stamps - they are equidistant.
            input_profile = input_profile.dropna('time').isel(time=[0,1])

        return input_profile.load()

    wind_input_profile = slice_and_load(wind_timeseries_fname)
    pv_input_profile = slice_and_load(pv_timeseries_fname)

    land_sea_mask = load_land_sea_mask().load()

    logging.info(f"Loading time series files took {time.time() - t0}")

    # this makes the for loop easier
    param = xr.Dataset(
        {"wind_input_profile": wind_input_profile, "pv_input_profile": pv_input_profile}
    )

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
                wind_input_profile=param.wind_input_profile,
                pv_input_profile=param.pv_input_profile,
            )

            solutions.append(solution[OUTPUT_VARS])

            runtime = time.time() - t0
            logging.info(
                f"Pixel runtime for pixel {param_x_coord}/{param_y_coord} took: {runtime}s"
            )

    # TODO check if xr.concat() would be faster (supports only one dimension)
    out = xr.combine_by_coords(solutions)

    path = create_folder("network_solution")
    out.to_netcdf(path / f"network_solution_{x_start_idx}_{y_start_idx}.nc")
    logger.info(f"Chunk {x_start_idx},{y_start_idx} done!")


@task
def concat_solution_chunks(inputs, outputs):
    out = xr.open_mfdataset(inputs)
    out.to_netcdf(outputs[0])
