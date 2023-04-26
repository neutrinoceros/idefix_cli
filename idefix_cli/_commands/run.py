"""run an Idefix problem"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from copy import deepcopy
from enum import auto
from multiprocessing import cpu_count
from pathlib import Path
from subprocess import CalledProcessError, check_call
from tempfile import NamedTemporaryFile
from time import sleep, time
from typing import Final

import inifix
from rich.prompt import Confirm

from idefix_cli.lib import (
    files_from_patterns,
    get_config_file,
    get_option,
    print_err,
    print_subcommand,
    print_success,
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

MAIN_LOG_FILE = "idefix.0.log"
TIME_INTEGRATOR_LOG_LINE = re.compile(
    "^TimeIntegrator:\\s*(?P<time>.+) \\|\\s*(?P<cycle>\\d+) \\|"
)
JOB_COMPLETED = re.compile("Main: Job completed")


def spawn_idefix(cmd: list[str], *, step_count: int) -> int:
    if step_count < 0:
        # infinite steps: simple call
        return subprocess.call(cmd)

    if sys.platform.startswith("win"):
        print_err("idfx run --one isn't supported on Windows")
        return -3
    else:
        from signal import SIGUSR2  # not available on Windows

    # spawn idefix in the background and kill it (or exit) as soon as completion is detected
    if os.path.exists(MAIN_LOG_FILE):
        os.remove(MAIN_LOG_FILE)
    prog = subprocess.Popen(cmd)
    start_wait = time()
    while not os.path.exists(MAIN_LOG_FILE):
        # idefix is not necessarily well behaved regarding retcodes,
        # so we don't have a simple way to check wether the process
        # has returned already or not, creating the opportunity for
        # an infinite loop here, hence the timeout mechanism
        if (time() - start_wait) > 60:
            return -2
        sleep(0.1)

    complete = False
    last_edit = -1.0
    while not complete:
        if last_edit != (new_edit := os.stat(MAIN_LOG_FILE).st_mtime):
            with open(MAIN_LOG_FILE) as fh:
                for line in fh:
                    if JOB_COMPLETED.match(line):
                        complete = True
                        break
                    if (match := TIME_INTEGRATOR_LOG_LINE.match(line)) is None:
                        continue
                    if int(match["cycle"]) == step_count:
                        prog.send_signal(SIGUSR2)
                        complete = True
                        break
            last_edit = new_edit
        sleep(0.01)
    return -1


class RebuildMode(StrEnum):
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
def build_idefix(directory) -> int:
    ncpus = 2 ** min(3, cpu_count().bit_length())
    cmd = ["make", "-j", str(ncpus)]
    print_subcommand(cmd, loc=Path(directory))
    try:
        with chdir(directory):
            return check_call(cmd)
    except CalledProcessError as exc:
        print_err("failed to build idefix")
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
    tstop_group = parser.add_mutually_exclusive_group()
    tstop_group.add_argument(
        "--duration",
        action="store",
        type=float,
        help="run for specified time (in code units) DEPRECATED",
    )
    tstop_group.add_argument(
        "--tstop",
        action="store",
        type=float,
        help="override TimeIntegrator.tstop",
    )
    time_group = parser.add_mutually_exclusive_group()
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
        help="override TimeIntegrator.first_dt",
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
        default=-1,
        help="multiplier for --one (use `--one --times 2` to run for 2 steps)",
    )


def command(
    *unknown_args: str,
    directory: str = ".",
    inifile: str = "idefix.ini",
    tstop: float | None = None,
    duration: float | None = None,
    time_step: float | None = None,
    one_step: list[str] | None = None,
    multiplier: int = -1,
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
        output_types = set(one_step) - {"log"}
        if time_step is None:
            conf["TimeIntegrator"].setdefault("first_dt", 1e-6)
            time_step = conf["TimeIntegrator"]["first_dt"]

        conf.setdefault("Output", {})
        output_sec = conf["Output"]
        if not isinstance(output_sec, dict):
            print_err(
                "configuration file seems malformed, "
                "expected 'Output' to be a section title, not a parameter name."
            )
            return 1

        output_sec["log"] = 1

        if len(output_types) > 0:
            for entry in output_types:
                output_sec[entry] = 0  # output on every time step

        multiplier = max(1, multiplier)

    if time_step is not None:
        conf["TimeIntegrator"]["first_dt"] = time_step
    if duration is not None:
        print_warning("The --duration argument is deprecated. Use --tstop instead.")
        conf["TimeIntegrator"]["tstop"] = duration
    elif tstop is not None:
        conf["TimeIntegrator"]["tstop"] = tstop

    rebuild_mode_str: str = get_option("idfx run", "recompile") or "always"

    try:
        rebuild_mode = RebuildMode(rebuild_mode_str)
    except ValueError:
        print_warning(
            f"Expected [idfx run].recompile to be any of {[str(_) for _ in RebuildMode]}"
            f"Got {rebuild_mode} from {get_config_file()}\n"
        )
        print_warning("Falling back to 'prompt' mode.")
        rebuild_mode = RebuildMode.PROMPT

    build_is_required: bool
    if rebuild_mode is RebuildMode.ALWAYS:
        build_is_required = True
    elif rebuild_mode is RebuildMode.PROMPT:
        if exe.is_file():
            last_build_time = os.stat(exe).st_mtime
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
                (file, edit_time - last_build_time)
                for file, edit_time in source_edit_times
            )
            if updated_since_compilation := tuple(
                file for file, td in time_deltas if td > 0
            ):
                print_warning(
                    "The following files were updated since last successful compilation:",
                )
                print("\n".join(updated_since_compilation), file=sys.stderr)
                build_is_required = Confirm.ask(
                    "Would you like to rebuild before running the program ?"
                )
            else:
                build_is_required = False
    else:
        assert_never(rebuild_mode)

    if build_is_required and (ret := build_idefix(directory)) != 0:
        return ret

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
        ret = spawn_idefix(cmd, step_count=multiplier)

    if ret < 0:
        # special retcodes from spawn_idefix
        if ret == -1:
            print_success("Sucessfully stopped idefix mid-air")
        elif ret == -2:
            print_err("idefix timed out (startup took more than a minute)")
        elif ret == -3:
            # unsupported operation
            ret = 1
        ret = 0
    elif ret == 0:
        # Idefix newer than 1.0 intentionally always returns 0, even on failure
        with open(d / MAIN_LOG_FILE) as fh:
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
