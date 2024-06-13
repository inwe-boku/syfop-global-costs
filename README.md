syfop-global-costs
==================


How to run
==========

First install all dependencies, see [INSTALL.md](INSTALL.md).

Then run:

```
./run.sh
```

Note that this is built for [nora](https://nora.boku.ac.at/) (our institute's server) and the
[VSC](https://vsc.ac.at/).


Helpful commands and Snakemake parameters
=========================================

**Note:** All parameters for `run.sh` are simply passed to Snakemake. We will list a couple of very
useful calls here:

To disable parallelization of jobs for debugging purposes run:

```
./run.sh --cores 1
```

A snakemake dry run is helpful to test the Snakefile and list all jobs without running them:

```
./run.sh --dryrun
```

`syfop-global-costs` implements a testmode which downloads only very little data and does a
complete run on this reduced data set. It can be enabled in the configuration or by passing a
config option via command line:

```
./run.sh --config testmode=True
```

If you want to do computation necessary for a specific

```
./run.sh data/input/SOME_FILE
```

--touch
--force


**Note:** Some rules have to be killed with SIGKILL (eg. the downloads of ERA5 data).


Configuration and Parameters
============================

Configuration for the computation is done in these config files:

- `src/model_parameters.py`: parameters for the model as Python module - this might be moved ot
  params.yaml in future to allow easier sensitivity analysis
- `config/config.yaml`: general configuration for the computation
- `config/params.yaml`: parameters of the computation and simulation of renewable time series


Furthermore, there are two Snakemake profiles pre-defined:

- `config/nora/config.yaml`: parallel computation on our institute's server
- `config/vsc/config.yaml`: parallel computation on multiple nodes on the VSC


Solvers
-------

The optimization problem can be solved using different solvers. We recommend CPlex:

- CPlex: File API of linopy is quite slow, especially without SSD.
- Gurobi: fast, but probably can't be used on the VSC with an academic license.
- HiGHs: Open source, but slower than Gurobi and CPlex.

Installation instructions can be found [in the documentation of syfop](https://syfop.readthedocs.io/latest/how-to-install.html#install-solvers).


VSC
===

A couple of helpful hints to work with the [VSC](https://vsc.ac.at/). Some of these hints may apply
to Linux only (and probably for Mac OS), not sure if similar hints apply for Windows too.


Jobs
----

List all jobs currently queued or running submitted by yourself:

```
watch squeue -u $USER -l
```

Cancel all jobs submitted by yourself:

```
squeue -u $USER --format=%i|tail -n +5|xargs scancel
```

Go to the `syfop-global-costs` repo:

```
cd $DATA/syfop-global-costs/
```


SSH config
----------

Placing the following config snippet in `$HOME/.ssh/config` should make SSH to the VSC way more
convenient. It should also work [on Windows 10](https://superuser.com/a/1544127/110122] (not tested).

You can then simply type `ssh vsc` to connect - it will set your vsc user name use port 27, so you
can use public/private keys to log in (instead of a password) and set up jump proxies for the
nodes:

Replace `YOUR_VSC_USERNAME` with your vsc user name:

```
Host vsc
    HostName vsc4.vsc.ac.at
    # Port 27 necessary to allow pubkey... :face_screaming_in_fear:
    # https://wiki.vsc.ac.at/doku.php?id=doku:vpn_ssh_access#connecting_to_vsc-2_or_vsc-3_via_ssh-key
    Port 27
    User YOUR_VSC_USERNAME

Host n*-*
    # This allows to directly connect to a computation node of the VSC. The host
    # name needs to match the pattern above, e.g. "n4901-034". If it does, a jump
    # node will be used automatically (one cannot connect to it from outside).
    User YOUR_VSC_USERNAME
    ProxyJump vsc
```


Directly log in to a node
-------------------------

It can be helpful to directly log into a computation node via SSH to use `htop` to monitor RAM or
CPU usage (e.g. to see if parallelization is working as expected). SSH to a computation node does
not work directly, one needs a [jump server](https://en.wikipedia.org/wiki/Jump_server), i.e. one
needs to first login to a login node on the VSC (=`ssh vsc` using config from the previous section)
and then login from there to a computation node. This can be done in one step using the config from
above, e.g. n4908-006 for the computation node:

```
ssh n4908-006
```

Without the config above one can use the following command:

```
ssh -J vsc4.vsc.ac.at YOUR_VSC_USERNAME@n4901-035
```


Interactive session
-------------------

Instead of submitting a job which runs a script on a node, you can request an interactive session
on a node.

```
salloc -N 1
```

You can then login in as described above and do whatever you want:

More details: https://wiki.vsc.ac.at/doku.php?id=doku:slurm_interactive
