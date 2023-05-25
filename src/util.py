import os

from src.config import CHUNK_SIZE
from src.config import INTERIM_DIR

from src.config import X_IDX_FROM_TO
from src.config import Y_IDX_FROM_TO


def create_folder(path, prefix=INTERIM_DIR):
    if prefix is not None:
        path = prefix / path
    os.makedirs(path, exist_ok=True)
    return path


def get_chunk_indices():
    x_range = range(X_IDX_FROM_TO[0], X_IDX_FROM_TO[1], CHUNK_SIZE[0])
    y_range = range(Y_IDX_FROM_TO[0], Y_IDX_FROM_TO[1], CHUNK_SIZE[1])

    return x_range, y_range
