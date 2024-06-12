import yaml
import pathlib
import multiprocessing

from src import snakemake_config


REPO_ROOT_DIR = pathlib.Path(__file__).parent.parent

testdir = "-test" if snakemake_config.config['testmode'] else ""

DATA_DIR = REPO_ROOT_DIR / f"data{testdir}"

LOG_FILE = DATA_DIR / "logfile.log"

INPUT_DIR = DATA_DIR / "input"

INTERIM_DIR = DATA_DIR / "interim"

OUTPUT_DIR = DATA_DIR / "output"

FIGURES_DIR = DATA_DIR / "figures"

# temp folder used for file API to solvers, used for cplex
# this path is passed to linopy if the parameter io_api is not set to 'direct', i.e. lp/mps files
# are written to disk in order to pass the model to the solver.
# TODO there is a weird issue on the VSC, /tmp is out of space for larger runs, maybe disk is not
# freed after the files have been deleted because they are still open? use /local as workaround
# here if you get out-of-disk-space errors.
SOLVER_DIR = None


# solver used per default for the optimization problem
SOLVER = "cplex"

# default parameters per solver
SOLVER_DEFAULTS = {
    # basis_fn can be set to a filename ending in *.sol, the resulting file can be then used
    # for warmstart_fn but it does not speed up the optimization - it is a bit slower. I assume
    # that the overhead for reading the file is larger then the benefit.

    "gurobi": {
        # this makes sense because of the numeric error warning
        "BarHomogeneous": 1,

        # these parameters have been found with grbtune - Gurobi's command line tuning tool
        "ScaleFlag": 0,
        "Method": 2,
        "Aggregate": 2,
        "AggFill": 0,
        "PrePasses": 8,
    },
    "cplex": {
        # this does not seem to speedup things
        # warmstart_fn=str(INTERIM_DIR / 'solution.sol'),
        # Basis_fn=model_file,

        # cplex parameters found with cplex tuning:
        "simplex.perturbation.constant": 1e-6,
        "simplex.perturbation.indicator": True,

        # use Barrier algorithm in one thread
        # per default cplex would run Barrier, Dual and Primal in parallel mode, but in our case
        # Barrier always wins, so we can disable this to safe some CPU hours
        # See also:
        # https://www.ibm.com/docs/en/icos/12.9.0?topic=parameters-algorithm-continuous-linear-problems
        "threads": 1,
        "lpmethod": 4,

        # This seems to speed up things, found by guessing.
        # https://www.ibm.com/docs/en/icos/12.9.0?topic=parameters-barrier-starting-point-algorithm
        "barrier.startalg": 2,

        # Turn off crossover: major speedup but non-basic solution is different...? (why?)
        # https://www.ibm.com/docs/en/icos/12.9.0?topic=parameters-barrier-crossover-algorithm
        # https://www.ibm.com/docs/en/cofz/12.8.0?topic=parameters-solution-type-lp-qp
        # 'solutiontype': 2,
    },
}


# Number of sub processes run in parallel (on VSC this is per node)
NUM_PROCESSES = multiprocessing.cpu_count() - 3
