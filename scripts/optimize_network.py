import subprocess
from multiprocessing import Pool

from src.util import get_chunk_indices

from src.config import NUM_PROCESSES


def run_subprocess(params):
    x_start_idx, y_start_idx = params
    command = ["python", "scripts/optimize_network_chunk.py", str(x_start_idx), str(y_start_idx)]
    subprocess.run(command, check=True)


def run_chunk_processes(x_range, y_range):
    pool = Pool(processes=NUM_PROCESSES)

    for x in x_range:
        for y in y_range:
            pool.apply_async(run_subprocess, ((x, y),))

    pool.close()
    pool.join()


if __name__ == "__main__":
    run_chunk_processes(*get_chunk_indices())
