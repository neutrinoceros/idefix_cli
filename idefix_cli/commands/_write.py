import argparse
import json
import sys
from pathlib import Path

import inifix

from idefix_cli._commons import print_err


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


def write(dest: str, source, force: bool = False) -> int:
    try:
        data = json.load(source)
    except json.decoder.JSONDecodeError:
        print_err("input is not valid json.")
        return 1

    try:
        inifix.validate_inifile_schema(data)
    except ValueError:
        print_err("input is not Pluto inifile format compliant.")
        return 1

    dest = Path(dest)
    if dest.is_file() and not force:
        print_err(
            f"destination file {dest} already exists. Use -f/--force to overwrite."
        )
        return 1

    inifix.dump(data, dest)
    return 0
