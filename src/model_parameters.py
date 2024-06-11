import numpy as np
from syfop.units import ureg
from src.wind_costs import wind_costs, OPEX_R

# Values are mostly taken from here:
# "Pathway to a land-neutral expansion of Brazilian renewable fuel production"
# https://zenodo.org/records/6471331


# XXX costs are per year - we implicitly assume that the model runs for one year


# We assume 8% discount rate and 20y life time.
# n = 20; i = 0.08; ((1+i)**n * i) / ((1+i)**n-1)
capital_recovery_factor = 0.10185221

battery_cost = 33 * ureg.EUR / ureg.kWh  # EUR/KWh/a
hydrogen_storage_cost = 74 * ureg.EUR / ureg.kg  # EUR/kg/a
co2_storage_cost = 0.049 * ureg.EUR / ureg.kg  # EUR/kg/a

electrolizer_cost = 30 * ureg.EUR / ureg.kW  # EUR/kW/a
pv_cost = 53 * ureg.EUR / ureg.kW  # EUR/kW/a
# wind_cost = 128  # EUR/kW/a

# XXX wind class 1 is pretty arbitrary, 2020 too
# height=80m is taken from atlite, since we use Vestas v90 at the moment
wind_cost = capital_recovery_factor * wind_costs(1, 80, 2020) + OPEX_R[2020]  # EUR/kW/a
wind_cost = wind_cost * ureg.EUR / ureg.kW

# electrolizer_efficiency_multiplier = 1
# electrolizer_efficiency = 0.63 * electrolizer_efficiency_multiplier
# 0.63 is the value for energy -> energy, if h2 is measured in tons, we use 0.019 according to Jo:
#     der wert von 0.019 entspricht einer effizienz von 0.63
#     wenn wir 0.69 rechnen wollen, multiplizieren wir 0.019 mit 069/0.63
#     1 KWh electricty * 0.019 = 1 kg H2
#
# 1kg_h2 = 33kWh, zur Herstellung: 1kg_h2 = 33/0.63kWh = 1/0.019 kWh
# --> 1 kWh = 0.019kg_h2
electrolizer_convert_factor = 0.019 * ureg.kg / ureg.kWh


# # # below here probably constant for all scenarios without sensitivity analysis # # #

# taken from result csv from brazil paper
# XXX this might be wrong! 42 EUR/KW/a not EUR/(t/h)/a
# methanol_synthesis_cost = 42.0 * ureg.EUR / ureg.kW  # in EUR/KW/a
methanol_synthesis_cost = 42.0 * ureg.EUR / (ureg.t / ureg.h)


balanceCO2H2 = 7.268519  # from gams file
# balanceCO2H2 * h2 = co2
methanol_synthesis_input_proportions = {
    "co2": 1 * ureg.kg / ureg.h,
    "hydrogen": balanceCO2H2 * ureg.kg / ureg.h,
}

methanolSysnthesisEff = 5.093 * 5.54 * 1e3
# XXX should be checked if this is correct
methanol_synthesis_convert_factor = methanolSysnthesisEff

storage_params = {
    "electricity": {
        "costs": battery_cost,
        "max_charging_speed": 0.4,  # taken from GAMS file (value from Jo)
        "storage_loss": 0.01,  # 0.99 from GAMS file
        "charging_loss": 0.1,  # 0.9 in gdx and result file
    },
    "co2": {
        "costs": 1e3 * co2_storage_cost,
        "max_charging_speed": 0.2,  # taken from GAMS file (value from Jo)
        "storage_loss": 0,
        "charging_loss": 0,
    },
    "hydrogen": {
        "costs": 1e3 * hydrogen_storage_cost,
        "max_charging_speed": 0.2,  # taken from GAMS file (value from Jo)
        "storage_loss": 0,
        "charging_loss": 0,
    },
}


# Investment costs for direct air capture
# Source:
#   https://www.cell.com/joule/pdf/S2542-4351(18)30225-3.pdf
#   Table 2, Scenario C

# Exchange rate from 2018, because the paper was published in 2018
# https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates
dollar_to_eur = 0.848

# Note: the paper assumes CRF of 7.5% and 12.5%. We use here about 10%, which is equivalent to 8%
# discount rate and 20 years of life time.
# n = 20; i = 0.08; ((1+i)**n * i) / ((1+i)**n-1)
co2_cost_lifetime = 694  # $/(t/year) for a certain life time
co2_cost_opex = 26  # $/t-CO2 (this assumes 90% utilization, i.e. variable costs are included)
co2_cost = (
    dollar_to_eur
    * ((capital_recovery_factor * co2_cost_lifetime + co2_cost_opex) * 8760)
    * ureg.EUR
    / (ureg.t / ureg.h)
)  # EUR/(t_CO2/h)/a

co2_electricity_input = 366  # kWh/t-CO2
co2_gas_input = 5.25  # GJ/t-CO2
gj_to_kwh = 1 / 3.6e-3
gas_efficiency = 1 / 3  # assumes heat pump COP3
co2_convert_factor = 1 / (gj_to_kwh * co2_gas_input * gas_efficiency + co2_electricity_input)
co2_convert_factor = co2_convert_factor * ureg.t / ureg.kWh  # XXX is the unit correct?

# TODO what is a reasonable value here? shouldn't the result be proportional to this choice?
methanol_demand = np.array(1000) * ureg.t / ureg.h
