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
        # note: this is set to protected because we probably want to download it only once, but
        # removing it accidentally is kind of a PITA.
        protected("data/input/era5/global-{year}-{month}.nc"),

    # Speed here is probably mostly limited by network throughput, so more cores won't help much.
    # At the same time, /tmp might run out of space easily if we download too much at the same
    # time. We could change the location of temporary files, but we would have to take care about
    # removing them afterwards. Weirdly, atlite does not remove temp files if the location is not
    # the default one.
    # Also the download bar looks ugly on the screen if there are multiple downloads at once.
    # Therefore we require this rule to use 1 unit of the resource cdsapi and set 1 available
    # cdsapi resource in the profiles for nora and VSC in the profiles in config/*.
    resources:
        cdsapi=1
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
    threads: 2
    output:
        renewable_timeseries = temp("data/interim/{technology}/{technology}-month_{year}-{month}.nc"),
    run:
        from src.renewable_timeseries import generate_renewable_timeseries
        generate_renewable_timeseries(
            input,
            output,
            technology=wildcards.technology,
            year=wildcards.year,
            month=wildcards.month,
        )


rule concat_renewable_timeseries:
    # concats monthly files to a yearly file
    input:
        expand(
            rules.generate_renewable_timeseries.output,
            # This list comprehension here is a workaround for:
            # https://github.com/snakemake/snakemake/issues/2470
            # The formatting :02d does not work for inputs, so we add the zero padding here.
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
            technology=wildcards.technology
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
        #"src/optimize.py",
    output:
        # TODO rename this to chunks
        network_solution = "data/interim/network_solution/network_solution_{x_idx}_{y_idx}.nc"
    resources:
        runtime = 180,
        mem_mb = 8000,
    run:
        from src.optimize import optimize_network_chunk
        optimize_network_chunk(
            inputs=input,
            outputs=output,
            x_start_idx=int(wildcards.x_idx),
            y_start_idx=int(wildcards.y_idx),
            year=config['year_era5'],
            chunk_size=config['chunk_size'],
            time_period_h=config['time_period_h'],
        )


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
