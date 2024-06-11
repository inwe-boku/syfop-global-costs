"""Takes two indices as input and computes a chunk in the size of NxM where N,M is given
by chunk_size.

This script is only needed to compute a single chunk on CMD (not a common use case) or if chunk
computation is executed in another subprocess (see comments in optimize_network.py).

"""

import sys

from src.logging_config import setup_logging
from src.optimize import optimize_network_chunk


# TODO do we need to write log files to different files for each chunk or is it okay if
# multiple processes log to one file at the same time?
setup_logging()

optimize_network_chunk(
    inputs=[],
    outputs=[],
    year=2011,
    x_start_idx=int(sys.argv[1]),
    y_start_idx=int(sys.argv[2]),
    chunk_size=[5, 5],
)
