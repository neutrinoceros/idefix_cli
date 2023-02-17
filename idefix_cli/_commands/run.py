"""run an Idefix problem"""
from __future__ import annotations

import os
import subprocess
import sys
from copy import deepcopy
from enum import auto
from multiprocessing import cpu_count
from pathlib import Path
from subprocess import CalledProcessError, check_call
from tempfile import NamedTemporaryFile
from typing import Final

import inifix
from rich.prompt import Confirm

from idefix_cli.lib import (
    files_from_patterns,
    get_config_file,
    get_option,
    print_err,
    print_subcommand,
    print_warning,
    requires_idefix,
)

if sys.version_info >= (3, 11):
    from contextlib import chdir
    from enum import StrEnum
    from typing import assert_never
else:
    from typing_extensions import assert_never

    from idefix_cli._backports import StrEnum
    from idefix_cli.lib import chdir


class RecompileMode(StrEnum):
    ALWAYS = auto()
    PROMPT = auto()


# known end messages in Idefix
KNOWN_SUCCESS: Final = (
    "Main: Job completed successfully.",
    "Main: Job's done",  # Idefix <= 1.0
)
KNOWN_FAIL: Final = (
    "Main: Job was interrupted before completion.",
    "Main: Job was aborted because of an unrecoverable error.",
)


@requires_idefix()
def make(directory) -> int:
    ncpus = 2 ** min(3, cpu_count().bit_length())
    cmd = ["make", "-j", str(ncpus)]
    print_subcommand(cmd, loc=Path(directory))
    try:
        with chdir(directory):
            return check_call(cmd)
    except CalledProcessError as exc:
        print_err("failed to compile idefix")
        return exc.returncode


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
    parser.add_argument(
        "--times",
        dest="multiplier",
        type=int,
        default=1,
        help="multiplier for --one (use `--one --times 2` to run for 2 steps)",
    )


def command(
    *unknown_args: str,
    directory: str = ".",
    inifile: str = "idefix.ini",
    duration: float | None = None,
    time_step: float | None = None,
    one_step: list[str] | None = None,
    multiplier: int = 1,
    nproc: int = 1,
) -> int:
    d = Path(directory).resolve()
    exe = d / "idefix"
    if not exe.is_file() and not (d / "Makefile").is_file():
        print_err(
            f"No idefix executable or Makefile found in the target directory {d} "
            "Run `idfx conf` first"
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

    # conf type validation
    conf.setdefault("TimeIntegrator", {})
    if not isinstance(conf["TimeIntegrator"], dict):
        print_err(
            "configuration file seems malformed, "
            "expected 'TimeIntegrator' to be a section title, not a parameter name."
        )
        return 1

    if one_step is not None:
        output_types = one_step

        if time_step is None:
            conf["TimeIntegrator"].setdefault("first_dt", 1e-6)
            time_step = conf["TimeIntegrator"]["first_dt"]

        duration = multiplier * time_step

        if len(output_types) > 0:
            conf.setdefault("Output", {})
            output_sec = conf["Output"]
            if not isinstance(output_sec, dict):
                print_err(
                    "configuration file seems malformed, "
                    "expected 'Output' to be a section title, not a parameter name."
                )
                return 1
            for entry in output_types:
                output_sec[entry] = time_step

    recompile_mode_str: str = get_option("idfx run", "recompile") or "always"

    try:
        recompile_mode = RecompileMode(recompile_mode_str)
    except ValueError:
        print_warning(
            f"Expected [idfx run].recompile to be any of {[str(_) for _ in RecompileMode]}"
            f"Got {recompile_mode} from {get_config_file()}\n"
        )
        print_warning("Falling back to 'prompt' mode.")
        recompile_mode = RecompileMode.PROMPT

    compilation_is_required: bool
    if recompile_mode is RecompileMode.ALWAYS:
        compilation_is_required = True
    elif recompile_mode is RecompileMode.PROMPT:
        if exe.is_file():
            last_compilation_time = os.stat(exe).st_mtime
            source_patterns = (
                "**/*.hpp",
                "**/*.cpp",
                "**/*.h",
                "**/*.c",
                "**/CMakeLists.txt",
                "**/Makefile.cmake",
            )
            files_to_check = files_from_patterns(d, *source_patterns, recursive=True)
            idefix_dir = Path(os.environ["IDEFIX_DIR"])
            try:
                with chdir(idefix_dir):
                    git_indexed_idefix_files = [
                        os.path.abspath(_)
                        for _ in subprocess.run(
                            ["git", "ls-files"], capture_output=True
                        )
                        .stdout.decode()
                        .split("\n")
                    ]
            except subprocess.CalledProcessError:
                # emmit no warning here as Idefix might not be installed as a git copy
                pass
            else:
                source_files = files_from_patterns(
                    idefix_dir / "src", *source_patterns, recursive=True
                )
                files_to_check.extend(
                    set(git_indexed_idefix_files).intersection(source_files)
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
                    "The following files were updated since last successful compilation:",
                )
                print("\n".join(updated_since_compilation), file=sys.stderr)
                compilation_is_required = Confirm.ask(
                    "Would you like to recompile before running the program ?"
                )
            else:
                compilation_is_required = False
    else:
        assert_never(recompile_mode)

    if compilation_is_required and (ret := make(directory)) != 0:
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

    print_subcommand(cmd, loc=d)
    with chdir(d):
        ret = subprocess.call(cmd)

    if ret == 0:
        # Idefix newer than 1.0 intentionally always returns 0, even on failure
        with open(d / "idefix.0.log") as fh:
            last_line = fh.read().strip().split("\n")[-1].strip()
        if last_line in KNOWN_FAIL:
            ret = 1
        elif last_line not in KNOWN_SUCCESS:
            print_warning(
                "Command completed with an unknown status. Please check log files."
            )

    if ret != 0:
        print_err(f"{cmd[0]} terminated with an error")

    return ret
