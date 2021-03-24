import json
from pathlib import Path
from typing import Optional

from inifix import load

from idefix_cli._commons import print_err


def _add_read_args(parser):
    parser.add_argument("inifile", type=str, help="target inifile")
    parser.add_argument(
        "--indent", type=int, help="indentation in spaces (default is flat output)"
    )


def read(inifile: str, indent: Optional[int] = None) -> int:
    inifile = Path(inifile)
    if not inifile.is_file():
        print_err(f"no such file {inifile}")
        return 1
    print(json.dumps(load(inifile), indent=indent))
    return 0
