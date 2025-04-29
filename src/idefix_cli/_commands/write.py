"""write an Idefix inifile from a json string"""

import json
import sys
from argparse import ArgumentParser
from contextlib import ExitStack
from io import TextIOBase
from pathlib import Path

import inifix

from idefix_cli.lib import print_error

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def add_arguments(parser: ArgumentParser) -> None:
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

    tocatch = ExceptionGroup if inifix.__version_tuple__ >= (6, 1) else ValueError
    try:
        inifix.validate_inifile_schema(data, sections="require")
    except tocatch:
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
