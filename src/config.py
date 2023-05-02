import os
import pathlib

NUM_PROCESSES = 8

# used for downloading, calculation of time series etc
MONTHS = range(1, 13)
YEARS = (2012,)

# 43.23m/s is the maximum in the current wind data set
MAX_WIND_SPEED = 45


REPO_ROOT_DIR = pathlib.Path(__file__).parent.parent

simulation = "-simulation" if "SIMULATION" in os.environ and os.environ["SIMULATION"] else ""

DATA_DIR = REPO_ROOT_DIR / f"data{simulation}"

LOG_FILE = DATA_DIR / "logfile.log"

INPUT_DIR = DATA_DIR / "input"

INTERIM_DIR = DATA_DIR / "interim"

OUTPUT_DIR = DATA_DIR / "output"

FIGURES_DIR = DATA_DIR / "figures"

FIGSIZE = (12, 7.5)
