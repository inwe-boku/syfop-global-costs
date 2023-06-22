import pandas as pd

# CAPEX of reference turbine for each wind class and year in EUR/kW (Table 4)
CAPEX_R = pd.DataFrame(
    {
        1: [1080, 1034, 988, 914, 840, 811, 782],
        2: [1295, 1228, 1161, 1086, 1010, 977, 943],
        3: [1395, 1328, 1261, 1186, 1110, 1077, 1043],
    },
    index=[2020, 2025, 2030, 2035, 2040, 2045, 2050],
)

# Operational costs (Table 4)
OPEX_R = {
    2020: 23.0,
    2025: 21.2,
    2030: 20.0,
    2035: 19.3,
    2040: 18.8,
    2045: 18.3,
    2050: 18.0,
}

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
    """Calculates CAPEX for a theoretical wind turbine using the method from:

    Satymov, R., Bogdanov, D., & Breyer, C. (2022). Global-local analysis of cost-optimal onshore
    wind turbine configurations considering wind classes and hub heights. In Energy (Vol. 256, p.
    124629). Elsevier BV. https://doi.org/10.1016/j.energy.2022.124629

    Parameters
    ----------
    wind_class : int
        whether turbine is for low / high wind speeds, value must be 1, 2 or 3
    height : float
        height of the turbine in m
    year : int
        year of costs, must be in 2020-2050 and dividable by 5

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
    tower_share = TOWER_SHARE[wind_class]

    capex = tower_share * tower_factor * capex_r + (1 - tower_share) * capex_r

    return capex
