import yaml
import time
import socket
import importlib
import subprocess

from datetime import datetime


def get_git_hash():
    """Return a GIT ref of the current repository.
    If the d
    See git-describe for more information."""
    result = subprocess.run(
        ["git", "describe", "--tags", "--always", "--dirty"],
        capture_output=True,
    )
    return result.stdout.strip().decode()


def exec(func_path, inputs, outputs, **input_params):
    """
    Parameters
    ----------
    func_path
    inputs : list FIXME could this be a dict too?
    outputs : list
    allow_dirty_git : bool
    input_params : dict

    """
    # TODO setup logger and set log file or so?
    # TODO use click?

    module_name, func_name = func_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)

    start_time = time.time()

    run_data = {
        # 'run_id': ???
        # params <--- some params are encoded indirectly via inputs
        # config
        # IDs of the inputs?
        "function": func_path,
        "input_params": input_params,
        # FIXME might be huge, any ideas?
        "input_files": list(inputs),  # FIXME probably a dict if named outputs?
        "output_files": list(outputs),
        "start_time": datetime.now().astimezone().isoformat(),
        "runtime": float("nan"),
        "hostname": socket.gethostname(),
        "git_commit": get_git_hash(),
    }

    try:
        # TODO this needs to be a subprocess as workaround for the cplex/snakemake/pandas bug
        result = func(inputs=inputs, outputs=outputs, **input_params)
    finally:
        run_data["runtime"] = time.time() - start_time

        for output in outputs:
            fname = f"{output}.run.yaml"
            print(fname)
            with open(fname, "w") as f:
                # FIXME unsafe!
                yaml.dump(run_data, f)

    return result
