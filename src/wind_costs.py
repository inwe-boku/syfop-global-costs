import pandas as pd

# CAPEX of reference turbine for each wind class and year in EUR/kW
CAPEX_R = pd.DataFrame(
    {
        1: [1080, 1034, 988, 914, 840, 811, 782],
        2: [1295, 1228, 1161, 1086, 1010, 977, 943],
        3: [1395, 1328, 1261, 1186, 1110, 1077, 1043],
    },
    index=[2020, 2025, 2030, 2035, 2040, 2045, 2050],
)

# Share of CAPEX used for tower (see Table 5)
TOWER_SHARE = {
    1: 20.0e-2,
    2: 23.7e-2,
    3: 29.0e-2,
}

# height of reference turbine (see Table 5)
HEIGHT_REF = {
    1: 110,
    2: 130,
    3: 150,
}

# above 130m tower height is cheaper (1.6%/m instead of 2.1%/m)
HEIGHT_CHEAPER = 130

# below 130m costs de/increase 2.1%/m relative to the reference height
COST_PER_M_LOW = 0.021

# above 130m costs de/increase 1.6%/m relative to the reference height
COST_PER_M_HIGH = 0.016


def wind_costs(wind_class, height, year):
    """
    """
    height_ref = HEIGHT_REF[wind_class]

    if HEIGHT_CHEAPER >= height and HEIGHT_CHEAPER >= height_ref:
        tower_factor = COST_PER_M_LOW * (height - height_ref)
    elif HEIGHT_CHEAPER <= height and HEIGHT_CHEAPER <= height_ref:
        tower_factor = COST_PER_M_HIGH * (height - height_ref)
    else:
        tower_factor = COST_PER_M_LOW * (HEIGHT_CHEAPER - height_ref) + COST_PER_M_HIGH * (
            height - HEIGHT_CHEAPER
        )
    tower_factor += 1

    tower_factor = max(tower_factor, 0.5)

    capex_r = CAPEX_R[wind_class][year]

    capex = (
        TOWER_SHARE[wind_class] * tower_factor * capex_r
        + (1 - TOWER_SHARE[wind_class]) * capex_r
    )

    return capex
