configfile: "config/params.yaml"
configfile: "config/config.yaml"


# Convention for files: Use the following pattern:
# something_with_underscores_prefix-WILDCARD_another_prefix-ANOTHER_WILDCARD
# that means:
#  - underscores to separate words
#  - a prefix word before wildcards
#  - a dash between the prefix and the wildcard
#  - no dashes or underscores in wildcards
#  - no other dashes in file names
#
# This should make the Snakemake filename pattern matching pretty unambiguous. Feel free to define
# additional wildcard_constraints.

wildcard_constraints:
    year="\d+",
    technology="[a-z]+",
    renewable_scenario="[a-z]+",


# testmode is a fast run with test data, see config/config.yaml
data_dir = "data" + ("-test" if config["testmode"] else "") + "/"

# Crazy hack: make the snakemake config object globally available to python code in src.
# see src/snakemake_config.py for details
import src.snakemake_config
src.snakemake_config.config = config


# this might allow parallel cdsapi downloads on the VSC, one per node
# XXX but it might be a bit too much to use a separate node just to download some files, right?
# https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#resources
resource_scopes:
    cdsapi="local",


# TODO do we need to add source files as input files to trigger the computation? Snakemake should
# keep track of it, but somehow it doesn't, right? --list-code-changes does not show changes.
# TODO do we need to add some of the config options as parameters to the rules?


rule all:
    localrule: True
    input:
        expand(
            data_dir + "output/network_solution/network_solution_renewables-{renewable_scenario}.nc",
            renewable_scenario=config['renewable_params'].keys(),
        )


rule download_land_sea_mask:
    localrule: True
    output:
        data_dir + "input/land_sea_mask/land_sea_mask.nc"
    run:
        from src.download import download_land_sea_mask
        download_land_sea_mask(input, output)


rule download_era5:
    output:
        # note: this is set to protected because we probably want to download it only once, but
        # removing it accidentally is kind of a PITA.
        protected(data_dir + "input/era5/global-{year}-{month}.nc"),

    # Speed here is probably mostly limited by network throughput, so more cores won't help much.
    # At the same time, /tmp might run out of space easily if we download too much at the same
    # time. We could change the location of temporary files, but we would have to take care about
    # removing them afterwards. Weirdly, atlite does not remove temp files if the location is not
    # the default one.
    # Also the download bar looks ugly on the screen if there are multiple downloads at once.
    # Therefore we require this rule to use 1 unit of the resource cdsapi and set 1 available
    # cdsapi resource in the profiles for nora and VSC in the profiles in config/*.
    # TODO this does work any longer, but why? Jobs do run in parallel again! git blame can help?
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
        era5 = data_dir + "input/era5/global-{year}-{month}.nc",
    output:
        # remove the temp() here if you want to keep the monthly time series, probably makes only
        # sense if you are experimenting with one month only.
        renewable_timeseries = temp(
            data_dir + "interim/{technology}/" +
            "{technology}_renewables-{renewable_scenario}-month_{year}-{month}.nc"),
    resources:
        mem="22GB",       # measured 20.1GB (PV) and 14.8GB (wind) on nora
        runtime="15min",  # 3min for PV and 24s for wind on nora
    run:
        from src.renewable_timeseries import generate_renewable_timeseries
        generate_renewable_timeseries(
            input,
            output,
            technology=wildcards.technology,
            year=wildcards.year,
            month=wildcards.month,
            renewable_params=config['renewable_params'][wildcards.renewable_scenario],
        )


rule concat_renewable_timeseries:
    # concatenates monthly files to a yearly file
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
        data_dir + "interim/renewable_timeseries/"
            "{technology}_renewables-{renewable_scenario}_{year}.nc",
    resources:
        mem="75GB",       # measured 68.1GB on nora (for both, PV and wind)
        runtime="20min",  # 9min on nora (for both, PV and wind)
    run:
        from src.renewable_timeseries import concat_renewable_timeseries
        concat_renewable_timeseries(
            inputs=input,
            outputs=output,
            technology=wildcards.technology
        )


rule optimize_network:
    input:
        download_land_sea_mask = rules.download_land_sea_mask.output,
        pv = expand(
            rules.concat_renewable_timeseries.output,
            year=config['year_era5'],
            technology=['pv'],
            allow_missing=True,
        ),
        wind = expand(
            rules.concat_renewable_timeseries.output,
            year=config['year_era5'],
            technology=['wind'],
            allow_missing=True,
        ),
    output:
        # TODO rename this to chunks
        # TODO make this temporary files?
        network_solution = data_dir + "interim/network_solution/network_solution_renewables-{renewable_scenario}_chunk-{x_idx}-{y_idx}.nc"
    wildcard_constraints:
        x_idx="\d+",
        y_idx="\d+",
    resources:
        runtime="20min",    # 3min on nora, but multiple parallel jobs might slow down things
        mem="8GB",          # less than a GB on nora, but make it larger (we had weird RAM issues on the VSC?)
    run:
        from src.optimize import optimize_network_chunk
        optimize_network_chunk(
            inputs=input,
            outputs=output,
            pv_timeseries_fname=input.pv[0],
            wind_timeseries_fname=input.wind[0],
            x_start_idx=int(wildcards.x_idx),
            y_start_idx=int(wildcards.y_idx),
            chunk_size=config['chunk_size'],
            time_period_h=config['time_period_h'],
        )


rule plot_network:
    # plot the graph of the network to a PNG file
    # note that this is file is not run automatically, but only if you run this rule explicitly:
    #
    #   ./run.sh plot_network
    input:
        wind = expand(
            rules.optimize_network.input.wind,
            renewable_scenario='default',
        ),
        pv = expand(
            rules.optimize_network.input.pv,
            renewable_scenario='default',
        ),
    output:
        data_dir + "output/network.png",
    run:
        from src.plot_network import plot_network
        plot_network(
            inputs=input,
            outputs=output,
            pv_timeseries_fname=input.pv[0],
            wind_timeseries_fname=input.wind[0],
        )


rule concat_solution_chunks:
    input:
        expand(
            rules.optimize_network.output.network_solution,
            x_idx=range(*config['x_idx_from_to'], config['chunk_size'][0]),
            y_idx=range(*config['y_idx_from_to'], config['chunk_size'][1]),
            allow_missing=True,
        )
    output:
        # minor duplication: also in rules.all.input, because rule "all" needs to be the first one
        # in the Snakefile to be executed as default rule. At the same time we can refer only to
        # rules defined above already. So we cannot refer to an output file in rule "all" from
        # another rule.
        data_dir + "output/network_solution/network_solution_renewables-{renewable_scenario}.nc",

    resources:
        runtime="60s",    # 12s measured on nora
        mem="2GB",     # 640MB measured on nora

    run:
        from src.optimize import concat_solution_chunks
        concat_solution_chunks(input, output)
