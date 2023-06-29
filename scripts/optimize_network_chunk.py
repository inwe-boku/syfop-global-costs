"""Takes two indices as input and computes a chunk in the size of NxM where N,M is stored
in CHUNK_SIZE
"""

import sys

from src.logging_config import setup_logging
from src.optimize import optimize_network_chunk


# TODO do we need to write log files to different files for each chunk or is it okay if
# multiple processes log to one file at the same time?
setup_logging()

optimize_network_chunk(int(sys.argv[1]), int(sys.argv[2]))
