# TODO:
# - grouping for SLURM
# - set max threads?
# - set max CPUS here not via CLI?
# - how to config parameters in a central place?
#   - year used
#   - turbine height
#   - turbine model



rule all:
    input:
        "data/output/network_solution/network_solution.nc"


rule download_land_sea_mask:
    input:
        "scripts/download_land_sea_mask.py"
    output:
        "data/input/land_sea_mask/land_sea_mask.nc"
    shell: "python {input} {output}"


rule generate_renewable_timeseries:
    # note: this task also downloads inputs if necessary
    output:
        era5 = "data/input/era5/global-{year}-{month:02}.nc",
        pv = "data/interim/pv/pv_{year}-{month:02}.nc",
        wind = "data/interim/wind/wind_{year}-{month:02}.nc",
    shell: "python scripts/generate_renewable_timeseries.py {wildcards.year} {wildcards.month}"


rule concat_renewable_timeseries:
    input:
        era5 = expand("data/input/era5/global-2011-{month:02}.nc", month=range(1,12)),
        pv = expand("data/interim/pv/pv_2011-{month:02}.nc", month=range(1,12)),
        wind = expand("data/interim/wind/wind_2011-{month:02}.nc", month=range(1,12)),
    output:
        pv = "data/interim/pv/pv_2011.nc",
        wind = "data/interim/wind/wind_2011.nc",
    shell: "python scripts/concat_renewable_timeseries.py"


rule optimize_network:
    input:
        "data/input/land_sea_mask/land_sea_mask.nc",
        expand("data/interim/pv/pv_2011-{month}.nc", month=range(1,12)),
        expand("data/interim/wind/wind_2011-{month}.nc", month=range(1,12)),
        # TODO add more source files and input data files
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
            x_idx=range(740, 800, 5), y_idx=range(560, 620, 5)
        )

    output:
        "data/output/network_solution/network_solution.nc"

    shell: "python scripts/concat_solution_chunks.py"
