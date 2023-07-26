import os
import pathlib

# used for downloading, calculation of time series etc
MONTHS = range(1, 13)
YEARS = (2011,)

REPO_ROOT_DIR = pathlib.Path(__file__).parent.parent

simulation = "-simulation" if "SIMULATION" in os.environ and os.environ["SIMULATION"] else ""

DATA_DIR = REPO_ROOT_DIR / f"data{simulation}"

LOG_FILE = DATA_DIR / "logfile.log"

INPUT_DIR = DATA_DIR / "input"

INTERIM_DIR = DATA_DIR / "interim"

OUTPUT_DIR = DATA_DIR / "output"

FIGURES_DIR = DATA_DIR / "figures"

FIGSIZE = (12, 7.5)

# how many tiles in x/y are computed in one process at once and then stored in one file
CHUNK_SIZE = 5, 5

# Balkan
#X_IDX_FROM_TO = 750, 840
#Y_IDX_FROM_TO = 530, 560

# Denmark
X_IDX_FROM_TO = 740, 800
Y_IDX_FROM_TO = 560, 620

NUM_PROCESSES = 8
