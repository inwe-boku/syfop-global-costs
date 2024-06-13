import os

from src.paths import INTERIM_DIR


def create_folder(path, prefix=INTERIM_DIR):
    if prefix is not None:
        path = prefix / path
    os.makedirs(path, exist_ok=True)
    return path


def iter_chunk_indices(
    x_idx_from_to,
    y_idx_from_to,
    chunk_size,
):
    x_range = range(x_idx_from_to[0], x_idx_from_to[1], chunk_size[0])
    y_range = range(y_idx_from_to[0], y_idx_from_to[1], chunk_size[1])

    # this could be a generator using yield, but ploomber does not suppot generators
    return [(x_start_idx, y_start_idx) for x_start_idx in x_range for y_start_idx in y_range]
