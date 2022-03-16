"""run an Idefix problem"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

import inifix
from rich.prompt import Confirm

from idefix_cli._commons import _make
from idefix_cli._commons import files_from_patterns
from idefix_cli._commons import print_err
from idefix_cli._commons import print_warning
from idefix_cli._commons import pushd


def add_arguments(parser) -> None:

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


def command(
    directory: str,
    inifile: str = "idefix.ini",
    duration: float | None = None,
    time_step: float | None = None,
    one_step: bool | None = False,
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

    compilation_required = False
    d = Path(directory)
    if not (d / "idefix").is_file():
        if not (d / "Makefile").is_file():
            print_err(
                "No idefix instance or Makefile found in the target directory. "
                "Run `idfx conf` first."
            )
            return 1

        compilation_required = True

    else:
        last_compilation_time = os.stat(d / "idefix").st_mtime
        source_patterns = (
            "**/*.hpp",
            "**/*.cpp",
            "**/*.h",
            "**/*.c",
            "**/CMakeLists.txt",
        )

        files_to_check = files_from_patterns(d, *source_patterns)
        idefix_dir = Path(os.environ["IDEFIX_DIR"])
        try:
            with pushd(idefix_dir):
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
            compilation_required = Confirm.ask(
                "Would you like to recompile before running the program ?"
            )

    if compilation_required and (ret := _make(directory)) != 0:
        return ret

    conf = inifix.load(pinifile)
    if time_step is not None:
        conf["TimeIntegrator"]["first_dt"] = time_step
    if duration is not None:
        conf["TimeIntegrator"]["tstop"] = duration

    with pushd(d), NamedTemporaryFile() as tmp_inifile:
        inifix.dump(conf, tmp_inifile.name)
        ret = subprocess.call(["./idefix", "-i", tmp_inifile.name])
        if ret != 0:
            print_err("idefix terminated with an error.")
    return ret
