from syfop.units import ureg
from syfop.util import const_time_series
from syfop.node import Node, NodeScalableInput, NodeFixOutput, Storage
from syfop.network import Network

from src.config import SOLVER_DIR


def create_methanol_network(
    pv_input_profile,
    pv_cost,
    wind_input_profile,
    wind_cost,
    methanol_demand,
    storage_params,
    co2_cost,
    co2_convert_factor,
    electrolizer_cost,
    electrolizer_convert_factor,
    methanol_synthesis_cost,
    methanol_synthesis_convert_factor,
    methanol_synthesis_input_proportions,
):

    # We have a time series where the whole demand is during the last time stamp and a free
    # methanol storage. This is equivalent to a yearly production goal where we don't care when the
    # methanol is produced.
    methanol_demand_timeseries = (
        const_time_series(0.0, time_coords=pv_input_profile.time) * ureg.t / ureg.h
    )
    methanol_demand_timeseries[-1] = methanol_demand

    solar_pv = NodeScalableInput(
        name="solar_pv",
        input_profile=pv_input_profile,
        costs=pv_cost,
    )
    wind = NodeScalableInput(
        name="wind",
        input_profile=wind_input_profile,
        costs=wind_cost,
    )
    electricity = Node(
        name="electricity",
        inputs=[solar_pv, wind],
        input_commodities="electricity",
        costs=0,
        storage=Storage(**storage_params["electricity"]),
    )
    curtail_electricity = Node(
        name="curtail_electricity",
        inputs=[electricity],
        input_commodities="electricity",
        costs=0,
        size_commodity="electricity",
    )
    electrolizer = Node(
        name="electrolizer",
        inputs=[electricity],
        input_commodities="electricity",
        costs=1 / electrolizer_convert_factor * electrolizer_cost,
        convert_factor=electrolizer_convert_factor,
        storage=Storage(**storage_params["hydrogen"]),
    )
    co2 = Node(
        name="co2",
        inputs=[electricity],
        input_commodities="electricity",
        costs=co2_cost,
        convert_factor=co2_convert_factor,
        storage=Storage(**storage_params["co2"]),
    )

    methanol_synthesis = Node(
        name="methanol_synthesis",
        inputs=[co2, electrolizer],
        input_commodities=["co2", "hydrogen"],
        costs=methanol_synthesis_cost,
        convert_factors={
            "methanol": ("hydrogen", methanol_synthesis_convert_factor),
        },
        input_proportions=methanol_synthesis_input_proportions,
        # we just set a minimum methanol production per year but do not care
        # when is generated, this is modelled via a free storage:
        storage=Storage(
            **{
                "costs": 0.0 * ureg.EUR / ureg.t,  # XXX should this be per kWh?
                "max_charging_speed": 1,
                "storage_loss": 0,
                "charging_loss": 0,
            }
        ),
    )

    methanol_demand = NodeFixOutput(
        name="methanol_demand",
        inputs=[methanol_synthesis],
        input_commodities=["methanol"],
        output_flow=methanol_demand_timeseries,
    )

    units = {
        "methanol": ureg.t / ureg.h,
    }

    network = Network(
        [
            solar_pv,
            wind,
            electricity,
            curtail_electricity,
            electrolizer,
            co2,
            methanol_synthesis,
            methanol_demand,
        ],
        units=units,
        time_coords=pv_input_profile.time,
        solver_dir=SOLVER_DIR,
    )

    return network
