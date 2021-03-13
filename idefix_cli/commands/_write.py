import argparse
import json
import sys
from pathlib import Path

from inifix import dump


def _add_write_args(parser):
    parser.add_argument("dest", type=str, help="dest inifile")
    parser.add_argument(
        "source",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="json input",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force writing even if savefile already exists",
    )


def write(dest: str, source, force: bool = False):
    dest = Path(dest)
    if dest.is_file() and not force:
        print(
            "Error: destination {} is a file (use -f/--force to overwrite)".format(dest)
        )
        return 1
    dump(json.load(source), dest)
    return 0
