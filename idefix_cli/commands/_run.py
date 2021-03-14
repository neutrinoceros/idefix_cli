from pathlib import Path
from subprocess import check_call
from uuid import uuid4

from inifix.idefix_conf import IdefixConf

from idefix_cli._commons import _make, print_err, pushd


def _add_run_args(parser):

    parser.add_argument("directory", help="target directory")
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


def _get_patched_inifile(
    directory: str,
    inifile: str = "idefix.ini",
    duration: float = None,
    time_step: float = None,
) -> Path:
    conf = IdefixConf(inifile)

    # conf["Output"]["dmp"] = 0.0  # force dump file to be written at every timestep

    to_write = False
    if time_step not in (None, conf["TimeIntegrator"]["first_dt"]):
        conf["TimeIntegrator"]["first_dt"] = time_step
        to_write = True
    if duration not in (None, conf["TimeIntegrator"]["tstop"]):
        conf["TimeIntegrator"]["tstop"] = duration
        to_write = True

    if not to_write:
        return Path(inifile)
    name = "{}_{}.ini_".format(inifile.stem, uuid4())
    new_inifile = Path(directory) / name

    conf.write(new_inifile)
    return new_inifile


def run(
    directory: str,
    inifile: str = "idefix.ini",
    duration: float = None,
    time_step: float = None,
    one_step: bool = False,
) -> int:

    input_inifile = inifile
    for loc in [Path.cwd(), Path(directory)]:
        inifile = (loc / input_inifile).resolve()
        if inifile.is_file():
            break
    else:
        print_err("could not find inifile {input_inifile}")
        return 1
    if one_step:
        if time_step is None:
            time_step = IdefixConf(inifile)["TimeIntegrator"]["first_dt"]
        duration = time_step

    d = Path(directory)
    if not (d / "idefix").is_file():
        if not (d / "Makefile").is_file():
            print_err(
                "No idefix instance or Makefile found in the target directory. "
                "Run `idfx setup` first."
            )
            return 1
        _make(directory)

    if (duration, time_step) != (None, None):
        ninifile = _get_patched_inifile(directory, inifile, duration, time_step)
        if ninifile != inifile:
            inifile = ninifile
            print("Running patched inifile {}".format(inifile))

    with pushd(d):
        check_call(["./idefix", "-i", inifile])
    return 0
