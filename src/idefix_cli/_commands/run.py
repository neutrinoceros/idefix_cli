"""run an Idefix problem"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from copy import deepcopy
from enum import auto
from math import prod
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep, time, time_ns
from typing import Final

import inifix
from packaging.version import Version

from idefix_cli.lib import (
    files_from_patterns,
    get_config_file,
    get_idefix_version,
    get_option,
    print_error,
    print_subcommand,
    print_success,
    print_warning,
    prompt_ask,
    requires_idefix,
    run_subcommand,
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


def _spawn_idefix_lt_1(cmd: list[str], *, ncycles: int) -> int:
    if get_idefix_version() >= Version("1.0"):
        raise RuntimeError("if you're seeing this error, please file a bug report")

    if ncycles < 0:
        # infinite steps: simple call
        return subprocess.call(cmd)

    if sys.platform.startswith("win"):
        print_error("idfx run --one isn't supported on Windows")
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
                    if int(match["cycle"]) == ncycles:
                        prog.send_signal(SIGUSR2)
                        complete = True
                        break
            last_edit = new_edit
        sleep(0.01)
    return -1


def get_command(
    inputfile: str, *, nproc: int, idefix_args: tuple[str, ...]
) -> list[str]:
    cmd = ["./idefix", "-i", inputfile, *idefix_args]

    if nproc < 0 and "-dec" in idefix_args:
        # try to guess the number of processes
        i0 = idefix_args.index("-dec")
        dec_args: list[int] = []
        for i in range(i0 + 1, len(idefix_args)):
            try:
                dec_args.append(int(idefix_args[i]))
            except ValueError:
                break
        if dec_args:
            nproc = prod(dec_args)
        else:
            print_warning(
                "Couldn't parse -dec parameters, "
                "this will likely result in idefix crashing at startup time "
                "(if it doesn't, please report this)"
            )

    if nproc > 1:
        cmd = ["mpirun", "-n", str(nproc), *cmd]
    return cmd


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


def get_cpu_count() -> int:
    # this function exists primarily to be mocked
    # instead of something we don't own
    base_cpu_count: int | None
    if sys.version_info >= (3, 13):
        base_cpu_count = os.process_cpu_count()
    else:
        if hasattr(os, "sched_getaffinity"):
            # this function isn't available on all platforms
            base_cpu_count = len(os.sched_getaffinity(0))
        else:
            # this proxy is good enough in most situations
            base_cpu_count = os.cpu_count()
    return base_cpu_count or 1


def get_highest_power_of_two(n_max: int) -> int:
    return 2 ** (n_max.bit_length() - 1)


@requires_idefix()
def build_idefix(directory) -> int:
    ncpus = min(8, get_highest_power_of_two(get_cpu_count()))
    cmd = ["make", "-j", str(ncpus)]
    return run_subcommand(cmd, loc=Path(directory), err="failed to build idefix")


class MultipleMaxCycles(Exception):
    pass


def parse_ncycles(unknown_args: tuple[str, ...], ncycles: int) -> tuple[str, ...]:
    if "-maxcycles" in unknown_args:
        # it is assumed that this function is only called when --one is passed
        raise MultipleMaxCycles

    if get_idefix_version() >= Version("1.0"):
        # -maxcycles is new in idefix 1.0.0
        # we support older versions with a far more fragile implementation
        # (see _spawn_idefix_lt_1)
        if ncycles != 1:
            print_warning(
                "the --times option is deprecated. "
                "Use idefix's -maxcycles argument instead."
            )
        return ("-maxcycles", str(ncycles), *unknown_args)
    else:
        return unknown_args


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
        "Arguments are interpreted as output types (see --output)",
    )
    parser.add_argument(
        "--out",
        dest="outputs",
        nargs="+",
        help=(
            "Output types (dmp, vtk, ...) to be produced on each cycle "
            "(requires -maxcycles, cannot be combined with --one-step)"
        ),
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
        default=-1,
        help=(
            "run idefix in parallel over selected number of ALU. "
            "Requires the code to be configured for MPI. "
            "This parameter can be left unspecified if -dec is passed."
        ),
    )
    parser.add_argument(
        "--times",
        dest="ncycles",
        type=int,
        default=None,
        help="ncycles for --one (use `--one --times 2` to run for 2 steps)",
    )


def command(
    *unknown_args: str,
    directory: str = ".",
    inifile: str = "idefix.ini",
    tstop: float | None = None,
    duration: float | None = None,
    time_step: float | None = None,
    one_step: list[str] | None = None,
    nproc: int = -1,
    ncycles: int | None = None,
    outputs: list[str] | None = None,
) -> int:
    if one_step is None:
        if ncycles is not None:
            print_error(
                "the --times parameter is invalid if --one/--one-step isn't passed too"
            )
            return 1
        ncycles = -1  # unlimited run
    elif ncycles is not None:
        if ncycles < 1:
            print_error(
                "the --times parameter expects a strictly "
                f"positive integer (got {ncycles})"
            )
            return 1
        try:
            unknown_args = parse_ncycles(unknown_args, ncycles=ncycles)
        except MultipleMaxCycles:
            print_error("-maxcycles cannot be combined with --one/--one-step")
            return 1
    else:
        try:
            unknown_args = parse_ncycles(unknown_args, ncycles=1)
        except MultipleMaxCycles:
            print_error("-maxcycles cannot be combined with --one/--one-step")
            return 1
        ncycles = -1  # unlimited run

    d = Path(directory).resolve()
    exe = d / "idefix"
    if not exe.is_file() and not (d / "Makefile").is_file():
        print_error(
            f"No idefix executable or Makefile found in the target directory {d}",
            hint="Run `idfx conf` first",
        )
        return 1

    input_inifile = inifile
    for loc in [Path.cwd(), Path(directory)]:
        pinifile = (loc / input_inifile).resolve()
        if pinifile.is_file():
            break
    else:
        print_error(f"could not find inifile {input_inifile}")
        return 1

    with open(pinifile, "rb") as fh:
        conf = inifix.load(fh)
        base_conf = deepcopy(conf)

    # conf type validation
    conf.setdefault("TimeIntegrator", {})
    if not isinstance(conf["TimeIntegrator"], dict):
        print_error(
            "configuration file seems malformed, "
            "expected 'TimeIntegrator' to be a section title, not a parameter name."
        )
        return 1

    if outputs and "-maxcycles" not in unknown_args:
        print_error("--out requires -maxcycles")
        return 1
    if outputs and one_step:
        print_error(
            "--one-step/--one cannot be followed by output "
            "types if --out is also passed"
        )
        return 1
    if one_step:
        outputs = one_step
    if outputs:
        output_types = set(outputs) - {"log"}
        if time_step is None:
            conf["TimeIntegrator"].setdefault("first_dt", 1e-6)
            time_step = conf["TimeIntegrator"]["first_dt"]

        conf.setdefault("Output", {})
        output_sec = conf["Output"]
        if not isinstance(output_sec, dict):
            print_error(
                "configuration file seems malformed, "
                "expected 'Output' to be a section title, not a parameter name."
            )
            return 1

        output_sec["log"] = 1

        if len(output_types) > 0:
            for entry in output_types:
                output_sec[entry] = 0  # output on every time step

    if time_step is not None:
        conf["TimeIntegrator"]["first_dt"] = time_step
    if tstop is not None:
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
                build_is_required = prompt_ask(
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

    cmd = get_command(inputfile, nproc=nproc, idefix_args=unknown_args)

    print_subcommand(cmd, loc=d)

    if get_idefix_version() >= Version("1.0.0"):
        tstart = time_ns()
        with chdir(d):
            ret = subprocess.call(cmd)

        logfile = d / MAIN_LOG_FILE
        if ret == 0 and logfile.is_file() and logfile.stat().st_mtime_ns > tstart:
            # Idefix >= 1.0 intentionally always returns 0, even on failure
            with open(d / MAIN_LOG_FILE) as fh:
                last_line = fh.read().strip().split("\n")[-1].strip()
            if last_line in KNOWN_FAIL:
                ret = 1
            elif last_line not in KNOWN_SUCCESS:
                print_warning(
                    "Command completed with an unknown status. Please check log files."
                )
        else:
            # Either the retcode is !=0 or no log files were produced, which may be
            # perfectly legit (-nolog and -nowrite exist). In any case, resist the
            # temptation to guess what happened.
            pass

    else:
        with chdir(d):
            ret = _spawn_idefix_lt_1(cmd, ncycles=ncycles)

        if ret < 0:
            # special retcodes from spawn_idefix
            if ret == -1:
                print_success("Sucessfully stopped idefix mid-air")
            elif ret == -2:
                print_error("idefix timed out (startup took more than a minute)")
            elif ret == -3:
                # unsupported operation
                ret = 1
            ret = 0

    if ret != 0:
        print_error(f"{cmd[0]} terminated with an error")

    return ret
