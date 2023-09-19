rule all:
    input:
        "data/output/network_solution/network_solution-DOES_NOT_EXIST.nc"


#rule download_land_sea_mask:
#      output:
#          "data/input/land_sea_mask/land_sea_mask.nc"
#      shell: "scripts.download_land_sea_mask.download_land_sea_mask"


#rule generate_renewable_timeseries:
#    # note: this task also downloads inputs if necessary
#    output:
#        era5 = "data/input/era5/global-2011-{month}.nc"
#        pv = "data/interim/pv/pv_2011-{month}.nc"
#        wind = "data/interim/wind/wind_2011-{month}.nc"
#    shell: "scripts/generate_renewable_timeseries.py"

#rule concat_renewable_timeseries:
#    input:
#        era5 = "data/input/era5/global-2011-{month}.nc"
#        pv = "data/interim/pv/pv_2011-{month}.nc"
#        wind = "data/interim/wind/wind_2011-{month}.nc"
#    output:
#        pv = "data/interim/pv/pv_2011.nc"
#        wind = "data/interim/wind/wind_2011.nc"
#    shell: python scripts/concat_renewable_timeseries.py


rule optimize_network:
    input:
        # TODO add more source files and input python files
        "data/input/land_sea_mask/land_sea_mask.nc",
        "src/optimize.py",
    output:
        # TODO rename this to chunks
        network_solution = "data/interim/network_solution/network_solution_{x_idx}_{y_idx}.nc"
    shell:
        """
        python -c '
from src.logging_config import setup_logging
from src.optimize import optimize_network_chunk
setup_logging()
optimize_network_chunk(int({wildcards.x_idx}), int({wildcards.y_idx}))
'
        """


rule concat_solution_chunks:
    input:
        expand(
            "data/interim/network_solution/network_solution_{x_idx}_{y_idx}.nc",
            x_idx=range(740, 742), y_idx=range(560, 563)
        )

    output:
        "data/output/network_solution/network_solution-DOES_NOT_EXIST.nc"

    shell: "scripts/concat_solution_chunks.py"
