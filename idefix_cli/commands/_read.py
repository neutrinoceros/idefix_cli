import json
from pathlib import Path

from inifix import load


def _add_read_args(parser):
    parser.add_argument("inifile", type=str, help="target inifile")
    parser.add_argument(
        "--indent", type=int, help="indentation in spaces (default is flat output)"
    )


def read(inifile: str, indent: int = None):
    inifile = Path(inifile)
    if not inifile.is_file():
        print("Error: not a file {}".format(inifile))
        return 1
    print(json.dumps(load(inifile), indent=indent))
    return 0
