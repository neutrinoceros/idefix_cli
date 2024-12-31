"""write an Idefix inifile from a json string"""

import json
import sys
from contextlib import ExitStack
from io import TextIOBase
from pathlib import Path

import inifix

from idefix_cli.lib import print_error


def add_arguments(parser) -> None:
    parser.add_argument("dest", type=str, help="dest inifile")
    parser.add_argument(
        "source",
        nargs="?",
        default=sys.stdin,
        help="json input",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force writing even if savefile already exists",
    )


def command(dest: str, source: str | TextIOBase, force: bool = False) -> int:
    with ExitStack() as stack:
        if isinstance(source, TextIOBase):
            stream = source
        else:
            stream = stack.enter_context(open(source))

        try:
            data = json.load(stream)
        except json.decoder.JSONDecodeError:
            print_error("input is not valid json.")
            return 1

    try:
        inifix.validate_inifile_schema(data, sections="require")
    except ValueError:
        print_error("input is not Pluto inifile format compliant.")
        return 1

    pdest = Path(dest)
    if pdest.is_file() and not force:
        print_error(
            f"destination file {dest} already exists. Use -f/--force to overwrite."
        )
        return 1

    with open(pdest, "wb") as fh:
        inifix.dump(data, fh, sections="require")

    return 0
