"""read an Idefix inifile and print it to json format"""

from __future__ import annotations

import json
from pathlib import Path

import inifix

from idefix_cli.lib import print_error


def add_arguments(parser) -> None:
    parser.add_argument("inifile", type=str, help="target inifile")
    parser.add_argument(
        "--indent", type=int, help="indentation in spaces (default is flat output)"
    )


def command(inifile: str, indent: int | None = None) -> int:
    pinifile = Path(inifile)
    if not pinifile.is_file():
        print_error(f"no such file {inifile}")
        return 1
    with open(pinifile, "rb") as fh:
        payload = inifix.load(fh)
    print(json.dumps(payload, indent=indent))
    return 0
