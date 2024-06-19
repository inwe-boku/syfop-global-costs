This list documents open issues which might need a fix (but there was no time yet).


Parameters for the model
------------------------

The parameters for the model in `src.model_parameters` are roughly the ones from the [Brazil
paper](https://doi.org/10.1038/s41467-022-30850-2). But they should be thoroughly checked before a
real simulation run is done. I think there is something wrong with the unit for methanol. This
should be in KWh not in tons. The costs might actually refer to the costs per KWh, so some of the
values might be completely wrong atm. Also all the `convert_factors` should be checked.


Optimize number of parallel jobs
--------------------------------

At the moment the resources (required RAM for one job) are defined in Snakefile after roughly
measuring the peaks for one job. Snakemake will then run as many jobs in parallel as possible. But
in practice it seems as if neither RAM nor CPU capacities are fully used.

It might be worth to re-evaluate the configuration of resources and check how many jobs are
actually run in parallel on nora or one one node on the VSC.


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
ValueError in file /data/users/my_user/syfop-global-costs/Snakefile, line 104:
dimension spatial on 0th function argument to apply_ufunc with dask='parallelized' consists of multiple chunks, but is also a core dimension. To fix, either rechunk into a single array chunk along this dimension, i.e., ``.chunk(dict(spatial=-1))``, or pass ``allow_rechunk=True`` in ``dask_gufunc_kwargs`` but beware that this may significantly increase memory usage.
  File "/data/users/my_user/syfop-global-costs/Snakefile", line 104, in __rule_generate_renewable_timeseries
  File "/data/users/my_user/syfop-global-costs/src/task.py", line 70, in task_func
  File "/data/users/my_user/syfop-global-costs/src/renewable_timeseries.py", line 81, in generate_renewable_timeseries
  File "/data/users/my_user/syfop-global-costs/src/renewable_timeseries.py", line 24, in wind
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/convert.py", line 521, in wind
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/convert.py", line 174, in convert_and_aggregate
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/atlite/aggregate.py", line 19, in aggregate_matrix
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 1266, in apply_ufunc
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 312, in apply_dataarray_vfunc
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/site-packages/xarray/core/computation.py", line 767, in apply_variable_ufunc
  File "/home/my_user/micromamba/envs/syfop-global-costs/lib/python3.10/concurrent/futures/thread.py", line 58, in run
[2024-06-17 14:26:11,424] WARNING - snakemake.logging - Shutting down, this might take some time.
[2024-06-17 14:26:11,424] ERROR - snakemake.logging - Exiting because a job execution failed. Look above for error message
```

With the ERA5 data downloaded a couple of months ago everything works fine. Either the data changed
or some of the new versions of packages introduced the issue.

I think it did run successfully a couple of times, here you can see a couple of months downloaded
successfully:

```
-r-------- 1 my_user user 35G Jun 17 14:14 global-2011-01.nc
-rw-rw-r-- 1 my_user user 262 Jun 17 14:14 global-2011-01.nc.run.yaml
-r-------- 1 my_user user 32G Jun 17 18:11 global-2011-02.nc
-rw-rw-r-- 1 my_user user 263 Jun 17 18:11 global-2011-02.nc.run.yaml
-r-------- 1 my_user user 34G Jun 17 18:41 global-2011-06.nc
-rw-rw-r-- 1 my_user user 263 Jun 17 18:41 global-2011-06.nc.run.yaml
-r-------- 1 my_user user 36G Jun 17 17:18 global-2011-07.nc
-rw-rw-r-- 1 my_user user 263 Jun 17 17:18 global-2011-07.nc.run.yaml
-r-------- 1 my_user user 35G Jun 17 17:43 global-2011-09.nc
-rw-rw-r-- 1 my_user user 260 Jun 17 17:43 global-2011-09.nc.run.yaml
-r-------- 1 my_user user 34G Jun 17 17:07 global-2011-11.nc
-rw-rw-r-- 1 my_user user 262 Jun 17 17:07 global-2011-11.nc.run.yaml
-rw------- 1 my_user user 42K Jun 17 16:13 tmp2rbf6m1fglobal-2011-04.nc
-rw------- 1 my_user user 42K Jun 17 16:00 tmp82gyv6yhglobal-2011-03.nc
-rw------- 1 my_user user 42K Jun 17 16:14 tmpbh7o2a14global-2011-12.nc
-rw------- 1 my_user user 42K Jun 17 17:04 tmpe4lo9lskglobal-2011-10.nc
-rw------- 1 my_user user 42K Jun 17 16:26 tmpp3m5wg9uglobal-2011-08.nc
-rw------- 1 my_user user 42K Jun 17 15:57 tmpuch13t_1global-2011-05.nc
```

Some of the files failed due to memory issues (why are there multiple downloads running in
parallel? I thought I limited it to one download at a time using the resource `cdsapi`...?).


Note that the error above at 14:26 was not due to memory issues:

```
2024-06-12 19:13:19+02:00       my_user  1555485 85.8  0.0      0     0 pts/4    Zl+  19:10   2:41 [python3.10] <defunct>
2024-06-17 15:57:59+02:00  Low memory! Killing process 1228240 python3_10 owned by my_user
2024-06-17 15:57:59+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 15:57:59+02:00       my_user  1228240 15.5  0.0      0     0 pts/0    Zl+  14:26  14:18 [python3.10] <defunct>
2024-06-17 16:01:16+02:00  Low memory! Killing process 1228273 python3_10 owned by my_user
2024-06-17 16:01:16+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 16:01:16+02:00       my_user  1228273 13.9  0.0      0     0 pts/0    Zl+  14:26  13:15 [python3.10] <defunct>
2024-06-17 16:14:26+02:00  Low memory! Killing process 1228238 python3_10 owned by my_user
2024-06-17 16:14:26+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 16:14:26+02:00       my_user  1228238 13.7  0.0      0     0 pts/0    Zl+  14:26  14:51 [python3.10] <defunct>
2024-06-17 16:15:16+02:00  Low memory! Killing process 1228264 python3_10 owned by my_user
2024-06-17 16:15:16+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 16:15:16+02:00       my_user  1228264 16.2  0.0      0     0 pts/0    Zl+  14:26  17:43 [python3.10] <defunct>
2024-06-17 16:26:38+02:00  Low memory! Killing process 1228249 python3_10 owned by my_user
2024-06-17 16:26:38+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 16:26:38+02:00       my_user  1228249  8.0  0.0      0     0 pts/0    Zl+  14:26   9:39 [python3.10] <defunct>
2024-06-17 17:05:10+02:00  Low memory! Killing process 1228258 python3_10 owned by my_user
2024-06-17 17:05:10+02:00       USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
2024-06-17 17:05:10+02:00       my_user  1228258  6.6  0.0      0     0 pts/0    Zl+  14:26  10:38 [python3.10] <defunct>
```

As a workaround, a ready data set of ERA5 data is available here on nora:

```
nora:/data/datasets/era5-global-wind-pv
```

You'll probably need to use the `--ignore-incomplete` flag to use the old files (see below).


Use of old files
----------------

For some reason Snakemake won't allow to use old ERA5 files. It complains that the files are
incomplete and suggests to rerun the relevant rules:

```
$ ./run.sh --dryrun
Running on nora...
Using profile config/nora for setting default command line arguments.
Building DAG of jobs...
IncompleteFilesException:
The files below seem to be incomplete. If you are sure that certain files are not incomplete, mark them as complete with

    snakemake --cleanup-metadata <filenames>

To re-generate the files rerun your command with the --rerun-incomplete flag.
Incomplete files:
data/input/land_sea_mask/land_sea_mask.nc
data/input/era5/global-2011-01.nc
data/input/era5/global-2011-02.nc
data/input/era5/global-2011-06.nc
data/input/era5/global-2011-07.nc
data/input/era5/global-2011-09.nc
data/input/era5/global-2011-11.nc
```

However, this rerunning the rules would take a lot of time and also it is broken (see previous
issue).

The suggested command `--cleanup-metadata` does not seem to have any effect. No idea why. `--touch`
doesn't seem to have any effect either (it throws the same error)

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
