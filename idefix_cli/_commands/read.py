"""read an Idefix inifile and print it to json format"""
from __future__ import annotations

import json
from pathlib import Path

import inifix

from idefix_cli._commons import print_err


def add_arguments(parser) -> None:
    parser.add_argument("inifile", type=str, help="target inifile")
    parser.add_argument(
        "--indent", type=int, help="indentation in spaces (default is flat output)"
    )


def command(inifile: str, indent: int | None = None) -> int:
    inifile = Path(inifile)
    if not inifile.is_file():
        print_err(f"no such file {inifile}")
        return 1
    with open(inifile, "rb") as fh:
        payload = inifix.load(fh)
    print(json.dumps(payload, indent=indent))
    return 0
