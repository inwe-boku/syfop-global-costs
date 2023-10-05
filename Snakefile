# TODO:
# - grouping for SLURM
# - set max threads?
# - set max CPUS here not via CLI?
# - how to config parameters in a central place?
#   - year used
#   - turbine height
#   - turbine model


configfile: "config/params.yaml"


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


rule download_era5:
    output:
        "data/input/era5/global-{year}-{month}.nc",
    run:
        from src.download import download_era5
        download_era5(
            inputs=input,
            outputs=output,
            year=wildcards.year,
            month=wildcards.month,
        )


rule generate_renewable_timeseries:
    input:
        # note: this task also downloads inputs if necessary
        era5 = "data/input/era5/global-{year}-{month}.nc",
    output:
        renewable_timeseries = temp("data/interim/{technology}/{technology}-month_{year}-{month}.nc"),
    run:
        from src.renewable_timeseries import generate_renewable_timeseries
        generate_renewable_timeseries(
            input,
            output,
            technology=technology,
            year=wildcards.year,
            month=wildcards.month,
        )


rule concat_renewable_timeseries:
    # concats monthly files to a yearly file
    input:
        expand(
            rules.generate_renewable_timeseries.output,
            month=[f"{m:02d}" for m in range(1, 13)],
            allow_missing=True
        )
    output:
        "data/interim/renewable_timeseries/{technology}_{year}.nc",
    run:
        from src.renewable_timeseries import concat_renewable_timeseries
        concat_renewable_timeseries(
            inputs=input,
            outputs=output,
            technology=technology
        )


rule optimize_network:
    input:
        rules.download_land_sea_mask.output,
        expand(
            rules.concat_renewable_timeseries.output,
            year=config['year_era5'],
            technology=['pv', 'wind']
        ),

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
            x_idx=range(*config['x_idx_from_to'], config['chunk_size'][0]),
            y_idx=range(*config['y_idx_from_to'], config['chunk_size'][1])
        )
    output:
        # It's a bit weird to refer to rule "all" here, but "all" needs to be the first rule in the
        # Snakefile to be the default rule. At the same time we can refer only to rules defined
        # above already. So we cannot refer to an output file in rule "all" from another rule. At
        # least there is no duplication between paths.
        rules.all.input,
    run:
        from src.optimize import concat_solution_chunks
        concat_solution_chunks(input, output)
