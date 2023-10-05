# TODO:
# - grouping for SLURM
# - set max threads?
# - set max CPUS here not via CLI?
# - how to config parameters in a central place?
#   - year used
#   - turbine height
#   - turbine model



rule all:
    # TODO does this rule need to be local?
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
        rules.generate_renewable_timeseries.output.pv,
        rules.generate_renewable_timeseries.output.wind
    output:
        pv = "data/interim/pv/pv_{year}.nc",
        wind = "data/interim/wind/wind_{year}.nc",
    shell: "python scripts/concat_renewable_timeseries.py"


rule optimize_network:
    input:
        rules.download_land_sea_mask.output,
        expand(rules.concat_renewable_timeseries.output.pv, year=2011),
        expand(rules.concat_renewable_timeseries.output.wind, year=2011),

        # TODO add more source files and input data files
        "src/optimize.py",
    output:
        # TODO rename this to chunks
        network_solution = "data/interim/network_solution/network_solution_{x_idx}_{y_idx}.nc"
    resources:
        runtime = 180,
        mem_mb = 8000,
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
            rules.optimize_network.output.network_solution,
            x_idx=range(740, 800, 5), y_idx=range(560, 620, 5)
        )

    output:
        # It's a bit weird to refer to rule "all" here, but "all" needs to be the first rule in the
        # Snakefile to be the default rule. At the same time we can refer only to rules defined
        # above already. So we cannot refer to an output file in rule "all" from another rule. At
        # least there is no duplication between paths.
        rules.all.input,

    shell: "python scripts/concat_solution_chunks.py"
