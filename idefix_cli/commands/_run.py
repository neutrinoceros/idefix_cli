from pathlib import Path
from subprocess import call
from tempfile import NamedTemporaryFile
from typing import Optional

import inifix

from idefix_cli._commons import _make
from idefix_cli._commons import print_err
from idefix_cli._commons import pushd


def _add_run_args(parser):

    parser.add_argument("directory", nargs="?", default=".", help="target directory")
    parser.add_argument(
        "-i",
        dest="inifile",
        action="store",
        type=str,
        default="idefix.ini",
        help="target inifile",
    )
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument(
        "--duration",
        action="store",
        type=float,
        help="run for specified time (in code units)",
    )
    time_group.add_argument(
        "--one",
        "--one-step",
        dest="one_step",
        action="store_true",
        help="run only for one time step",
    )
    parser.add_argument(
        "--time-step",
        dest="time_step",
        action="store",
        type=float,
        help="patch the inifile TimeIntegrator.first_dt parameter",
    )


def run(
    directory: str,
    inifile: str = "idefix.ini",
    duration: Optional[float] = None,
    time_step: Optional[float] = None,
    one_step: Optional[bool] = False,
) -> int:

    input_inifile = inifile
    for loc in [Path.cwd(), Path(directory)]:
        pinifile = (loc / input_inifile).resolve()
        if pinifile.is_file():
            break
    else:
        print_err(f"could not find inifile {input_inifile}")
        return 1
    if one_step:
        if time_step is None:
            time_step = inifix.load(pinifile)["TimeIntegrator"]["first_dt"]
        duration = time_step

    d = Path(directory)
    if not (d / "idefix").is_file():
        if not (d / "Makefile").is_file():
            print_err(
                "No idefix instance or Makefile found in the target directory. "
                "Run `idfx setup` first."
            )
            return 1

        if (ret := _make(directory)) != 0:
            return ret

    conf = inifix.load(pinifile)
    if time_step is not None:
        conf["TimeIntegrator"]["first_dt"] = time_step
    if duration is not None:
        conf["TimeIntegrator"]["tstop"] = duration

    with pushd(d), NamedTemporaryFile() as tmp_inifile:
        conf.write(tmp_inifile.name)
        ret = call(["./idefix", "-i", tmp_inifile.name])
        if ret != 0:
            print_err("idefix terminated with an error.")
    return ret
