import logging
import xarray as xr

import matplotlib.pyplot as plt

from src.task import task

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


@task
def plot_network(
    pv_timeseries_fname,
    wind_timeseries_fname,
    inputs=None,
    outputs=None,
):
    logging.info(f"Plotting network...")

    logging.info(f"Loading time series...")
    wind_input_profile = xr.open_dataarray(wind_timeseries_fname).isel(x=[0], y=[0])
    pv_input_profile = xr.open_dataarray(pv_timeseries_fname).isel(x=[0], y=[0])

    logging.info(f"Creating network...")
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

    logging.info(f"Drawing network...")
    network.draw()
    plt.savefig(outputs[0])
