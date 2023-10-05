import yaml
import time
import socket
import subprocess

from functools import wraps
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


def task(func):
    @wraps(func)
    def task_func(inputs, outputs, **input_params):
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

        start_time = time.time()

        run_data = {
            # 'run_id': ???
            # params <--- some params are encoded indirectly via inputs
            # config
            # IDs of the inputs?
            "function": func.__name__,
            "input_params": input_params,
            # FIXME might be huge, any ideas?
            "input_files": list(inputs),
            "output_files": list(outputs),
            "start_time": datetime.now().astimezone().isoformat(),
            "runtime": float("nan"),
            "hostname": socket.gethostname(),
            "git_commit": get_git_hash(),
        }

        try:
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
