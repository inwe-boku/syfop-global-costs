import pathlib
from src import snakemake_config


REPO_ROOT_DIR = pathlib.Path(__file__).parent.parent

testdir = "-test" if snakemake_config.config['testmode'] else ""

DATA_DIR = REPO_ROOT_DIR / f"data{testdir}"

LOG_FILE = DATA_DIR / "logfile.log"

INPUT_DIR = DATA_DIR / "input"

INTERIM_DIR = DATA_DIR / "interim"

OUTPUT_DIR = DATA_DIR / "output"

FIGURES_DIR = DATA_DIR / "figures"
