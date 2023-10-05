#!/bin/python3

"""
Copy data between machines.
not entirely bullet proof
"""

import os

import argparse
import subprocess
import os.path as op

if 'REMOTE_URI' in os.environ:
    ...
else:
    from src.config import REMOTE_URI
    from src.config import LOCAL_URI


#
LOCAL_URI = "."
REMOTE_URI = "vsc:/gpfs/data/fs71375/lumbric/syfop-global-costs"


def parse_cmd_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="trial run with no changes made",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="do warn if file exists already",
    )
    parser.add_argument(
        "-p",
        "--param",
        nargs="+",
        help="Parameter passed to rsync",
    )
    parser.add_argument(
        "command",
        choices=["push", "pull"],
        help="",
    )
    parser.add_argument(
        "path",
        # nargs="+", TODO not implemented yet
        help="",
    )

    return parser.parse_args()


def main():
    args = parse_cmd_args()

    # what if path is absolute?
    # slash at the end of args.path?
    # slash at the end of VSC_URI?
    # empty string as args.path?
    # slash only as args.path?
    # how about windows support? slashes?
    # check rsync is installed?

    # rename VSC to something else to be more generic?
    #

    # do we need to mkdir -p if directories do not exist?

    # warn if overwrite?

    src = LOCAL_URI + "/" + args.path
    dst = REMOTE_URI + "/" + args.path

    if args.command == "push":
        ...
    elif args.command == "pull":
        src, dst = dst, src
    else:
        raise ValueError(f"invalid value for parameter command: {args.command}")

    # FIXME this is broken for pull from VSC
    if not op.exists(src):
        raise ValueError()

    # FIXME this is broken for pull from VSC
    if op.isdir(src):
        src += "/"

    command = [
        "rsync",
        "-aP",
        "--delete",
    ]

    if args.dry_run:
        command += ["--dry-run"]

    if args.param:
        command += args.param

    command += [src, dst]

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
