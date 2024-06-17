This list documents open issues which might need a fix (but there was no time yet).


Parameters for the model
------------------------

The parameters for the model in `src.model_parameters` are roughly the ones from the [Brazil
paper](https://doi.org/10.1038/s41467-022-30850-2). But they should be thoroughly checked before a
real simulation run is done. I think there is something wrong with the unit for methanol. This
should be in KWh not in tons. The costs might actually refer to the costs per KWh, so some of the
values might be completely wrong atm. Also all the `convert_factors` should be checked.


Methanol demand depends on time stamp interval
----------------------------------------------

At the moment we optimize for a given amount of methanol production per pixel over the time span of
the model (e.g. one year). We do this by defining a demand time series with all the amount of
methanol required in the last time stamp and a free methanol storage. However, this means that if
we define the methanol demand as 1000t/h during the last time stamp and then change the resolution
of the model via `time_period_h` to something else than `1h`, the demand will be scaled - which is
probably not what we want. I think this does not really need to be fixed, but one should be
careful or implement an automatic scaling in `src.methanol_network.create_methanol_network()`.


Wildcard for scenarios for model parameters
-------------------------------------------

At the moment there are wildcards only for the scenarios for generation of renewable time series,
i.e. one can define a list of different parameter sets for the generation of renewable time series
in the `params.yaml` file for `renewable_params`. The computation will automatically generate
renewable time series for all these scenarios.

However, there is no wildcard for the model parameters. All model parameters are currently defined
in `src/model_parameters.py`. It might make sense to add a section in the `params.yaml` file and
either move all model parameters there or just define the names of the scenarios there and then
pass it to `src.model_parameters` somehow. Maybe by introducing a function which returns the model
parameters for a given scenario name? I guess this depends a lot on the planned sensitivity
analysis what makes sense. In any case, one would need to add the scenario name as wild card also
in the Snakefile to the relevant rules.


New ERA5 downloads fail
-----------------------

When re-downloading the ERA5 data, for some reason it fails frequently with:

```
[2024-06-17 14:26:11,373] INFO - atlite.datasets.era5 - Requesting data for feature height...
[2024-06-17 14:26:11,374] INFO - atlite.datasets.era5 - Requesting data for feature runoff...
[2024-06-17 14:26:11,374] INFO - atlite.datasets.era5 - Requesting data for feature temperature...
[2024-06-17 14:26:11,379] INFO - atlite.datasets.era5 - Requesting data for feature influx...
[2024-06-17 14:26:11,377] INFO - atlite.datasets.era5 - Requesting data for feature runoff...
[2024-06-17 14:26:11,375] INFO - atlite.datasets.era5 - Requesting data for feature wind...
[2024-06-17 14:26:11,378] INFO - atlite.datasets.era5 - Requesting data for feature height...
[2024-06-17 14:26:11,380] INFO - atlite.datasets.era5 - Requesting data for feature temperature...
[2024-06-17 14:26:11,380] INFO - atlite.datasets.era5 - Requesting data for feature temperature...
[2024-06-17 14:26:11,383] INFO - atlite.datasets.era5 - Requesting data for feature runoff...
[2024-06-17 14:26:11,382] INFO - atlite.datasets.era5 - Requesting data for feature influx...
[2024-06-17 14:26:11,385] INFO - atlite.datasets.era5 - Requesting data for feature wind...
[2024-06-17 14:26:11,422] INFO - snakemake.logging - [Mon Jun 17 14:26:11 2024]
[2024-06-17 14:26:11,422] ERROR - snakemake.logging - Error in rule generate_renewable_timeseries:
    jobid: 0
    input: data/input/era5/global-2011-01.nc
    output: data/interim/wind/wind_renewables-default-month_2011-01.nc

[2024-06-17 14:26:11,423] ERROR - snakemake.logging - RuleException:
ValueError in file /data/users/pregner/syfop-global-costs/Snakefile, line 104:
dimension spatial on 0th function argument to apply_ufunc with dask='parallelized' consists of multiple chunks, but is also a core dimension. To fix, either rechunk into a single array chunk along this dimension, i.e., ``.chunk(dict(spatial=-1))``, or pass ``allow_rechunk=True`` in ``dask_gufunc_kwargs`` but beware that this may significantly increase memory usage.
  File "/data/users/pregner/syfop-global-costs/Snakefile", line 104, in __rule_generate_renewable_timeseries
  File "/data/users/pregner/syfop-global-costs/src/task.py", line 70, in task_func
  File "/data/users/pregner/syfop-global-costs/src/renewable_timeseries.py", line 81, in generate_renewable_timeseries
  File "/data/users/pregner/syfop-global-costs/src/renewable_timeseries.py", line 24, in wind
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/convert.py", line 521, in wind
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/convert.py", line 174, in convert_and_aggregate
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/aggregate.py", line 19, in aggregate_matrix
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 1266, in apply_ufunc
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 312, in apply_dataarray_vfunc
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 767, in apply_variable_ufunc
  File "/home/pregner/micromamba/envs/syfop-global-costs/lib/python3.10/concurrent/futures/thread.py", line 58, in run
[2024-06-17 14:26:11,424] WARNING - snakemake.logging - Shutting down, this might take some time.
[2024-06-17 14:26:11,424] ERROR - snakemake.logging - Exiting because a job execution failed. Look above for error message
```

With the ERA5 data downloaded a couple of months ago everything works fine. Either the data changed
or some of the new versions of packages introduced the issue.

I think it also did run successfully a couple of times. Maybe just memory issues?


Use of old files
----------------

For some reason Snakemake won't allow to use old ERA5 files. It complains that the files are
incomplete and suggests to rerun the relevant rules. However, this would take a lot of time and
also it is broken (see previous issue).

The command --cleanup-metadata does not seem to have any effect. No idea why.

However, the following command can be used to ignore the issue:


```
./run.sh --ignore-incomplete
```

Unfortunately, this has to be done for every run and it is not a good solution because other
incomplete files would be ignored as well.


Optimization fails for some pixels
----------------------------------

For some pixels the optimization fails to find a unique solution. Not sure why and it might depend
on the real parameters used. So maybe not worth it to look into details. That's why I never managed
to have successful global run of the optimization but only for a limited test set of pixels.

(Unfortunately I cannot reproduce atm and can't find the error message in the logs any longer. But
I am pretty sure the solver said something like "infeasible".)
