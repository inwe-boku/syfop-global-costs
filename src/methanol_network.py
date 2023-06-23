from syfop.util import const_time_series
from syfop.node import Node, NodeScalableInputProfile, NodeFixOutputProfile, Storage
from syfop.network import Network


# note: for now we don't distinguish between KW and KWh (per time stamp), this is okayish since we
# have hourly time stamps


def create_methanol_network(
    pv_input_flow,
    pv_cost,
    wind_input_flow,
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

    #
    methanol_demand_timeseries = const_time_series(0.0, time_coords=pv_input_flow.time)
    # FIXME what is the unit here?
    methanol_demand_timeseries[-1] = methanol_demand

    solar_pv = NodeScalableInputProfile(
        name="solar_pv",
        input_flow=pv_input_flow,
        costs=pv_cost,
        output_unit="KW",
    )
    wind = NodeScalableInputProfile(
        name="wind",
        input_flow=wind_input_flow,
        costs=wind_cost,
        output_unit="KW",
    )
    electricity = Node(
        name="electricity",
        inputs=[solar_pv, wind],
        input_commodities="electricity",
        costs=0,
        storage=Storage(**storage_params["electricity"]),
        output_unit="KW",
    )
    curtail_electricity = Node(
        name="curtail_electricity",
        inputs=[electricity],
        input_commodities="electricity",
        costs=0,
        output_unit="KW",
    )
    electrolizer = Node(
        name="electrolizer",
        inputs=[electricity],
        input_commodities="electricity",
        costs=1 / electrolizer_convert_factor * electrolizer_cost,
        convert_factor=electrolizer_convert_factor,
        output_unit="t",
        storage=Storage(**storage_params["hydrogen"]),
    )
    co2 = Node(
        name="co2",
        inputs=[electricity],
        input_commodities="electricity",
        costs=co2_cost,
        convert_factor=co2_convert_factor,
        output_unit="t",
        storage=Storage(**storage_params["co2"]),
    )

    methanol_synthesis = Node(
        name="methanol_synthesis",
        inputs=[co2, electrolizer],
        input_commodities=["co2", "hydrogen"],
        costs=methanol_synthesis_cost,
        convert_factor=methanol_synthesis_convert_factor,
        output_unit="KW",
        input_proportions=methanol_synthesis_input_proportions,

        # we just set a minimum methanol production per year but do not care
        # when is generated, this is modelled via a free storage:
        storage=Storage(
            **{
                "costs": 0.0,
                "max_charging_speed": 1,
                "storage_loss": 0,
                "charging_loss": 0,
            }
        ),
    )

    methanol_demand = NodeFixOutputProfile(
        name="methanol_demand",
        inputs=[methanol_synthesis],
        input_commodities=["methanol"],
        output_flow=methanol_demand_timeseries,
        costs=0,  # XXX why does this cost something if it is fixed and not scalable?
        output_unit="KW",
    )

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
        time_coords=pv_input_flow.time,
    )

    return network
