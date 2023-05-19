import io
import sys
import logging
from contextlib import redirect_stdout

import xarray as xr

from src.util import create_folder

from src.config import MONTHS
from src.config import CHUNK_SIZE
from src.config import INTERIM_DIR

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
OUTPUT_VARS = ["size_wind", "size_solar_pv", "size_storage_co2"]


def filter_solution(solution, x, y):
    """Filter solution Dataset object: Storing all variables would be too much data, because each
    solution contains many time series."""
    return solution[OUTPUT_VARS].expand_dims(x=x, y=y)


def optimize_network_single(param):
    """Optimize one pixel."""
    logging.info("Start optimization...")

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

    with io.StringIO() as buf, redirect_stdout(buf):
        network.optimize("gurobi")
        # XXX do we need the optimizer's log output?
        # output = buf.getvalue()

    return filter_solution(network.model.solution, x=pv_input_flow.x, y=pv_input_flow.y)


def optimize_network_chunk(x_start_idx, y_start_idx):
    wind_raw = xr.open_mfdataset(
        [INTERIM_DIR / "wind" / f"wind_2012-{month:02d}.nc" for month in MONTHS]
    )
    pv_raw = xr.open_mfdataset(
        [INTERIM_DIR / "wind" / f"wind_2012-{month:02d}.nc" for month in MONTHS]
    )

    x_slice = slice(x_start_idx, x_start_idx + CHUNK_SIZE[0])
    y_slice = slice(y_start_idx, y_start_idx + CHUNK_SIZE[1])

    # TODO remove stupid workaround for leap year here and add assert
    wind_input_flow = wind_raw.isel(x=x_slice, y=y_slice, time=slice(None, 8760))
    wind_input_flow = wind_input_flow["specific generation"].load()

    pv_input_flow = pv_raw.isel(x=x_slice, y=y_slice, time=slice(None, 8760))
    pv_input_flow = pv_input_flow["specific generation"].load()

    param = xr.Dataset({"wind_input_flow": wind_input_flow, "pv_input_flow": pv_input_flow})

    i = 0
    solutions = []

    # XXX No idea if groupby is really the best option to loop through two dimensions, but it seems
    # to work for now.

    for param_x_coord, param_x in param.groupby("x"):
        for param_y_coord, param_y in param_x.groupby("y"):
            logging.info(f"Computing chunk number {i}...")

            param = param_y.expand_dims(x=1, y=1).drop_vars(("lon", "lat"))
            solutions.append(optimize_network_single(param))
            i += 1

    # TODO check if xr.concat() would be faster (supports only one dimension)
    out = xr.combine_by_coords(solutions)

    path = create_folder("network_solution")
    out.to_netcdf(path / f"network_solution_{x_start_idx}_{y_start_idx}.nc")


if __name__ == "__main__":
    setup_logging()
    optimize_network_chunk(int(sys.argv[1]), int(sys.argv[2]))
