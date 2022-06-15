"""run an Idefix problem"""
from __future__ import annotations

import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile

import inifix
from rich.prompt import Confirm

from idefix_cli._commons import _make
from idefix_cli._commons import files_from_patterns
from idefix_cli._commons import print_err
from idefix_cli._commons import print_warning

if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from idefix_cli._commons import chdir


def add_arguments(parser) -> None:

    parser.add_argument("--dir", dest="directory", default=".", help="target directory")
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
        nargs="*",
        help="run only for one time step. "
        "Accepts arbitrary output type name(s) (e.g. dmp or vtk).",
    )
    parser.add_argument(
        "--time-step",
        dest="time_step",
        action="store",
        type=float,
        help="patch the inifile TimeIntegrator.first_dt parameter",
    )
    parser.add_argument(
        "--nproc",
        action="store",
        type=int,
        default=1,
        help=(
            "run idefix in parallel over selected number of ALU. "
            "Requires the code to be configured for MPI."
        ),
    )


def command(
    *unknown_args: str,
    directory: str = ".",
    inifile: str = "idefix.ini",
    duration: float | None = None,
    time_step: float | None = None,
    one_step: list[str] | None = None,
    nproc: int = 1,
) -> int:
    d = Path(directory)
    exe = d / "idefix"
    if not exe.is_file() and not (d / "Makefile").is_file():
        print_err(
            f"No idefix executable or Makefile found in the target directory {d} "
            "Run `idfx conf` first."
        )
        return 1

    input_inifile = inifile
    for loc in [Path.cwd(), Path(directory)]:
        pinifile = (loc / input_inifile).resolve()
        if pinifile.is_file():
            break
    else:
        print_err(f"could not find inifile {input_inifile}")
        return 1

    with open(pinifile, "rb") as fh:
        conf = inifix.load(fh)
        base_conf = deepcopy(conf)

    if one_step is not None:
        if time_step is None:
            time_step = conf["TimeIntegrator"]["first_dt"]
        duration = time_step
        if len(one_step) > 0:
            for entry in one_step:
                conf["Output"][entry] = duration

    compilation_is_required: bool
    if not exe.is_file():
        compilation_is_required = True
    else:
        last_compilation_time = os.stat(exe).st_mtime
        source_patterns = (
            "**/*.hpp",
            "**/*.cpp",
            "**/*.h",
            "**/*.c",
            "**/CMakeLists.txt",
        )

        files_to_check = files_from_patterns(d, *source_patterns, recursive=True)
        idefix_dir = Path(os.environ["IDEFIX_DIR"])
        try:
            with chdir(idefix_dir):
                git_indexed_idefix_files = [
                    os.path.abspath(_)
                    for _ in subprocess.run(["git", "ls-files"], capture_output=True)
                    .stdout.decode()
                    .split("\n")
                ]
        except subprocess.CalledProcessError:
            # emmit no warning here as Idefix might not be installed as a git copy
            pass
        else:
            files_to_check.extend(
                list(
                    set(git_indexed_idefix_files).intersection(
                        set(files_from_patterns(idefix_dir / "src", *source_patterns))
                    )
                )
            )

        source_edit_times = tuple(
            (file, os.stat(file).st_mtime) for file in files_to_check
        )
        time_deltas = tuple(
            (file, edit_time - last_compilation_time)
            for file, edit_time in source_edit_times
        )
        if updated_since_compilation := tuple(
            file for file, td in time_deltas if td > 0
        ):
            print_warning(
                "The following files were updated since last compilation:",
            )
            print("\n".join(updated_since_compilation), file=sys.stderr)
            compilation_is_required = Confirm.ask(
                "Would you like to recompile before running the program ?"
            )
        else:
            compilation_is_required = False

    if compilation_is_required and (ret := _make(directory)) != 0:
        return ret

    if time_step is not None:
        conf["TimeIntegrator"]["first_dt"] = time_step
    if duration is not None:
        conf["TimeIntegrator"]["tstop"] = duration

    if conf != base_conf:
        tmp_inifile = NamedTemporaryFile()
        with open(tmp_inifile.name, "wb") as fh:
            inifix.dump(conf, fh)
        inputfile = tmp_inifile.name
    else:
        inputfile = str(pinifile.relative_to(d.resolve()))

    cmd = ["./idefix", "-i", inputfile, *unknown_args]

    if nproc > 1:
        cmd = ["mpirun", "-n", str(nproc), *cmd]

    msg = f"INFO: running '{' '.join(cmd)}'"
    if d.resolve() != Path.cwd():
        msg += f" (from {d}{os.sep})"
    print(msg)

    with chdir(d):
        ret = subprocess.call(cmd)
        if ret != 0:
            print_err("idefix terminated with an error.")
    return ret
