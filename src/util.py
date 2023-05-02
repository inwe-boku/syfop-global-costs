import os

from src.config import INTERIM_DIR


def create_folder(path, prefix=INTERIM_DIR):
    if prefix is not None:
        path = prefix / path
    os.makedirs(path, exist_ok=True)
    return path
