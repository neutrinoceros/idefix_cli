import argparse
import json
import sys
from pathlib import Path

import inifix


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
    try:
        data = json.load(source)
    except json.decoder.JSONDecodeError:
        print("Error: input is not valid json.", file=sys.stderr)
        return 1

    try:
        inifix.validate_inifile_schema(data)
    except ValueError:
        print("Error: input is not Pluto inifile format compliant.", file=sys.stderr)
        return 1

    dest = Path(dest)
    if dest.is_file() and not force:
        print(
            f"Error: destination file {dest} already exists. Use -f/--force to overwrite.",
            file=sys.stderr,
        )
        return 1

    inifix.dump(data, dest)
    return 0
