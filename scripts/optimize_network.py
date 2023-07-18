import os

import subprocess
from multiprocessing import Pool

from src.util import get_chunk_indices

from src.config import NUM_PROCESSES


def run_subprocess(params):
    x_start_idx, y_start_idx = params
    command = ["python", "scripts/optimize_network_chunk.py", str(x_start_idx), str(y_start_idx)]
    subprocess.run(command, check=True)


def run_chunk_processes(x_range, y_range):
    """ """
    pool = Pool(processes=NUM_PROCESSES)

    for x_start_idx in x_range:
        for y_start_idx in y_range:
            pool.apply_async(run_subprocess, ((x_start_idx, y_start_idx),))

    pool.close()
    pool.join()


def run_jobs_slurm(x_range, y_range):
    for x_start_idx in x_range:
        for y_start_idx in y_range:
            command = [
                "python",
                "scripts/optimize_network_chunk.py",
                str(x_start_idx),
                str(y_start_idx),
            ]
            subprocess.run(command, check=True)


if __name__ == "__main__":
    # this is just a heuristic if we should run via slurm or just multiple processes
    runner = run_jobs_slurm if 'VSC_CLUSTER_ID' in os.environ else run_chunk_processes
    runner(*get_chunk_indices())
