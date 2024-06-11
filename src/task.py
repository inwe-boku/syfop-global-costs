import yaml
import time
import socket
import subprocess

from functools import wraps
from datetime import datetime

from src.logging_config import setup_logging


def get_git_hash():
    """Return a GIT ref of the current repository. This can either be a tag or a commit hash. If
    there are modified files (uncommitted changes), '-dirty' will be appended to the GIT ref.  See
    git-describe for more information."""
    result = subprocess.run(
        ["git", "describe", "--tags", "--always", "--dirty"],
        capture_output=True,
    )
    return result.stdout.strip().decode()


def task(func):
    @wraps(func)
    def task_func(inputs, outputs, allow_dirty_git=False, **input_params):
        """

        Parameters
        ----------
        func_path
        inputs : list FIXME could this be a dict too?
        outputs : list
        allow_dirty_git : bool
        input_params : kwargs

        """
        # TODO would it make sense to use a Python library like click to get a CMD interface for
        # calling a function decorated with @task?

        # TODO can we check that this is a call from another function decorated with @task? It
        # would be nice to support nested calls, but ATM this is kinda weird, it would overwrite
        # the run yaml files and may cause other troubles.

        if not allow_dirty_git:
            ...

        # TODO this does not really make sense here, I guess tasks are run in the same python
        # process... How can we have a separate log file for each task?
        setup_logging()

        start_time = time.time()

        run_data = {
            # 'run_id': ???
            # config
            # IDs of the inputs?
            "function": func.__name__,
            # FIXME might be huge, any ideas how to handle it?
            "input_params": input_params,
            "input_files": list(inputs),
            "output_files": list(outputs),
            "start_time": datetime.now().astimezone().isoformat(),
            "runtime": float("nan"),
            "error_msg": "",
            "hostname": socket.gethostname(),
            "git_commit": get_git_hash(),
        }

        # TODO do we want to catch exceptions here and safe the error message and run time or not?
        result = func(inputs=inputs, outputs=outputs, **input_params)

        run_data["runtime"] = time.time() - start_time

        for output in outputs:
            fname = f"{output}.run.yaml"
            with open(fname, "w") as f:
                yaml.safe_dump(run_data, f)

        return result

    return task_func
