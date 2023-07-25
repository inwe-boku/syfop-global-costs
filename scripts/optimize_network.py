"""Create the network for each pixel and run the optimization either in parallel subprocesses or
as SLURM jobs on the VSC."""

import argparse
import subprocess

from multiprocessing import Pool
from src.util import iter_chunk_indices
from src.config import NUM_PROCESSES
from src.logging_config import setup_logging


def worker(params):
    x_start_idx, y_start_idx = params
    command = ["python", "scripts/optimize_network_chunk.py", str(x_start_idx), str(y_start_idx)]
    subprocess.run(command, check=True)


def run_chunk_processes(chunks):
    """Run optimization for chunks in parallel subprocesses."""
    pool = Pool(processes=NUM_PROCESSES)

    for x_start_idx, y_start_idx in chunks:
        pool.apply_async(worker, ((x_start_idx, y_start_idx),))

    pool.close()
    pool.join()


def run_jobs_slurm(chunks):
    """Schedule SLURM jobs, each running parallel sub processes."""
    for i in range(0, len(chunks), NUM_PROCESSES):
        command = [
            "sbatch",
            "scripts/optimize_network.slrm",
            "--chunks" + "  ".join(f"{x},{y}" for (x, y) in chunks[i : i + NUM_PROCESSES]),
        ]
        subprocess.run(command, check=True)


def comma_splitter(xy_string):
    x, y = xy_string.split(",")
    return int(x), int(y)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vsc",
        action="store_true",
        help="VSC mode will schedule jobs via SLURM instead of starting workers as sub processes.",
    )
    parser.add_argument(
        "--chunks",
        nargs="*",
        type=comma_splitter,
        help="x/y start indices for chunks to be optimized in the form 'x1,y1 x2,y2 ...'. If not "
        "given, all chunks from config will be optimized.",
    )
    args = parser.parse_args()

    setup_logging()

    if args.chunks:
        chunks = args.chunks
    else:
        chunks = list(iter_chunk_indices())

    runner = run_jobs_slurm if args.vsc else run_chunk_processes
    runner(chunks)


if __name__ == "__main__":
    main()
