import xarray as xr

from src.util import create_folder
from src.util import iter_chunk_indices

from src.config import INTERIM_DIR
from src.config import OUTPUT_DIR


def main():
    fnames = [
        INTERIM_DIR / "network_solution" / f"network_solution_{x_idx}_{y_idx}.nc"
        for x_idx, y_idx in iter_chunk_indices()
    ]

    out = xr.open_mfdataset(fnames)
    out.to_netcdf(create_folder("network_solution", prefix=OUTPUT_DIR) / "network_solution.nc")


if __name__ == "__main__":
    main()
