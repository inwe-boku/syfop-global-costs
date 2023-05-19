import os

from src.config import CHUNK_SIZE
from src.config import INTERIM_DIR


def create_folder(path, prefix=INTERIM_DIR):
    if prefix is not None:
        path = prefix / path
    os.makedirs(path, exist_ok=True)
    return path


def get_chunk_indices():
    # TODO move this to config!
    x_start = 0
    x_end = 20
    y_start = 0
    y_end = 20

    x_range = range(x_start, x_end, CHUNK_SIZE[0])
    y_range = range(y_start, y_end, CHUNK_SIZE[1])

    return x_range, y_range
