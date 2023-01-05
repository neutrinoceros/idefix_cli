"""
configure Idefix

This command uses (c)cmake as a backend, or Python (configure.py) with legacy versions of Idefix.
Some shortcuts are supported to emulate configure.py's interface, and are automatically
translated into CMake flags. Namely:

  -mhd         -> -DIdefix_MHD=ON
  -mpi         -> -DIdefix_MPI=ON
  -openmp      -> -DKokkos_ENABLE_OPENMP=ON
  -gpu         -> -DKokkos_ENABLE_CUDA=ON
  -arch MYARCH -> -DKokkos_ARCH_MYARCH=ON
  -cxx MYCXX   -> -DCMAKE_CXX_COMPILER=MYCXX

Any additional argument is passed directly to cmake.
Use the -i/--interactive flag to enable ccmake as the backend.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from enum import auto
from enum import Enum
from pathlib import Path
from typing import Any
from typing import NoReturn

from packaging.version import Version

from idefix_cli.lib import get_config_file
from idefix_cli.lib import get_idefix_version
from idefix_cli.lib import get_option
from idefix_cli.lib import print_err
from idefix_cli.lib import print_subcommand
from idefix_cli.lib import print_warning
from idefix_cli.lib import requires_idefix

if sys.version_info >= (3, 11):
    from typing import assert_never
    from contextlib import chdir
else:
    from typing_extensions import assert_never
    from idefix_cli.lib import chdir


VERSION_REGEXP = re.compile(r"\d+\.\d+\.\d+")

CMAKE_MIN_VERSIONS: dict[str, Version] = {
    "cmake": Version("3.16.0"),
    "idefix": Version("0.9.0"),
}


class EngineRequirement(Enum):
    CMAKE = auto()
    PYTHON = auto()


ErrorMessage = Any  # just needs to be printable


class IdefixEnvError(OSError):
    pass


def validate_cmake_support() -> None:
    msg = f"cmake is required from {get_config_file()}, but "
    errors: list[str] = []
    warnings: list[str] = []
    idefix_ver = get_idefix_version()

    if idefix_ver < CMAKE_MIN_VERSIONS["idefix"]:
        # try a simpler heuristic to allow usage in between 0.8.x and 0.9.0
        if os.path.isfile(os.path.join(os.environ["IDEFIX_DIR"], "CMakeLists.txt")):
            warnings.append(
                "looks like your version of Idefix predates 0.9.0, but already has "
                "cmake support. Results may be unstable."
            )
        else:
            errors.append(
                f"cmake setup requires idefix {CMAKE_MIN_VERSIONS['idefix']} or newer, "
                f"found {idefix_ver}"
            )

    if shutil.which("cmake") is None:
        errors.append("couldn't find cmake executable")
    else:
        cmake_ver_str: str = subprocess.run(
            ["cmake", "--version"], capture_output=True
        ).stdout.decode()
        if (match := re.search(VERSION_REGEXP, cmake_ver_str)) is None:
            errors.append("couldn't parse result from `cmake --version`")

        elif (cmake_ver := Version(match.group())) < CMAKE_MIN_VERSIONS["cmake"]:
            errors.append(
                f"cmake setup requires cmake {CMAKE_MIN_VERSIONS['cmake']} or newer, "
                f"found {cmake_ver}"
            )

    for msg in warnings:
        print_warning(msg)

    if len(errors) == 0:
        return

    if len(errors) == 1:
        msg += errors[0]
    else:
        msg += "\n- " + "\n- ".join(errors)

    raise IdefixEnvError(msg)


def has_minimal_cmake_support() -> bool:
    try:
        validate_cmake_support()
    except IdefixEnvError:
        return False
    else:
        return True


def is_python_required() -> bool:
    req_v1 = get_option("idefix_cli", "conf_system")  # deprecated
    req_v2 = get_option("idfx conf", "engine")
    req = req_v2 or req_v1
    return req == "python"


@requires_idefix()
def has_python_support() -> bool:
    return os.path.isfile(os.path.join(os.environ["IDEFIX_DIR"], "configure.py"))


@requires_idefix()
def validate_python_support() -> None:
    if has_python_support():
        return

    msg = "Running a version of Idefix that doesn't provide $IDEFIX_DIR/configure.py . "
    if is_python_required():
        msg += f"This configuration engine was required from {get_config_file()}"
    raise IdefixEnvError(msg)


def get_valid_conf_engine() -> EngineRequirement:
    cmake_is_valid = has_minimal_cmake_support()
    python_is_valid = has_python_support()
    if cmake_is_valid:
        return EngineRequirement.CMAKE
    elif python_is_valid:
        return EngineRequirement.PYTHON
    else:
        raise IdefixEnvError(
            "Could not determine a working configuration engine. "
            "Most likely, your version of Idefix requires CMake, "
            "which is currently not installed. "
            "Please consult Idefix's documentation, "
            "or try to update idefix-cli if it didn't help."
        )


def substitute_cmake_flags(args: list[str]) -> list[str]:
    subs: dict[str, str] = {
        "-mhd": "-DIdefix_MHD=ON",
        "-mpi": "-DIdefix_MPI=ON",
        "-openmp": "-DKokkos_ENABLE_OPENMP=ON",
        "-gpu": "-DKokkos_ENABLE_CUDA=ON",
    }
    return [subs.get(_) or _ for _ in args]


def substitute_cmake_archs(args: list[str]) -> list[str]:
    if not (
        "-arch" in args or any(re.match(r"-D\s?Kokkos_ARCH_\w+=ON", _) for _ in args)
    ):
        if arch_req := get_option("compilation", "CPU"):
            args.extend(["-arch", arch_req])
        if arch_req := get_option("compilation", "GPU"):
            args.extend(["-arch", arch_req])
            if "-gpu" not in args:
                args.append("-gpu")

    parser = ArgumentParser()
    parser.add_argument("-arch", nargs="+", required=False)
    _args, unknown_args = parser.parse_known_args(args)

    if _args.arch is None:
        return args

    return unknown_args + [f"-DKokkos_ARCH_{_.upper()}=ON" for _ in _args.arch]


def substitute_cmake_cxx(args: list[str]) -> list[str]:
    if not (
        "-cxx" in args or any(re.match(r"-DCMAKE_CXX_COMPILER=\w+", _) for _ in args)
    ):
        if compiler_req := get_option("compilation", "compiler"):
            args.extend(["-cxx", compiler_req])

    parser = ArgumentParser()
    parser.add_argument("-cxx")
    _args, unknown_args = parser.parse_known_args(args)

    if _args.cxx is None:
        return args

    return unknown_args + [f"-DCMAKE_CXX_COMPILER={_args.cxx}"]


def substitute_cmake_args(args: list[str]) -> list[str]:
    # compatibility layer to enable configure.py's arguments with cmake
    # order matters
    args = substitute_cmake_archs(args)
    args = substitute_cmake_flags(args)
    args = substitute_cmake_cxx(args)
    return args


def add_arguments(parser) -> None:
    parser.add_argument("--dir", dest="directory", default=".", help="target directory")

    parser.add_argument(
        "-i",
        "--interactive",
        dest="interactive",
        action="store_true",
        help="Use ccmake over cmake (no effect with python configuration engine)",
    )


def _validate_engine(query: str) -> tuple[EngineRequirement | None, ErrorMessage]:
    if query == "cmake":
        engine_req = EngineRequirement.CMAKE
        validate_selected_engine = validate_cmake_support
    elif query == "python":
        engine_req = EngineRequirement.PYTHON
        validate_selected_engine = validate_python_support
    else:
        msg = (
            f"Got unknown value engine={engine_req!r} "
            f"from {get_config_file()}, "
            "expected 'cmake' or 'python'"
        )
        return None, msg

    try:
        validate_selected_engine()
    except IdefixEnvError as exc:
        return None, exc
    else:
        return engine_req, None


def _get_engine() -> tuple[EngineRequirement | None, ErrorMessage]:
    if not (engine_str := get_option("idfx conf", "engine")):
        if engine_str := get_option("idefix_cli", "conf_system"):
            engine_req, msg = _validate_engine(engine_str)
            if msg is None:
                msg = (
                    "[idefix_cli].conf_system is deprecated, use [idfx conf].engine instead. "
                    f"Please edit your configuration file {get_config_file()}"
                )
            return engine_req, msg

    if not engine_str:
        try:
            engine_req = get_valid_conf_engine()
        except IdefixEnvError as exc:
            return None, exc
        else:
            msg = None
    else:
        engine_req, msg = _validate_engine(engine_str)

    return engine_req, msg


@requires_idefix()
def command(*args: str, directory: str, interactive: bool) -> int | NoReturn:
    python_cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py")]
    cmake_cmd = ["ccmake" if interactive else "cmake", os.environ["IDEFIX_DIR"]]

    clargs = list(args)
    engine_req, st = _get_engine()
    if engine_req is None:
        print_err(st)
        return 1
    elif st is not None:
        print_warning(st)

    if engine_req is EngineRequirement.CMAKE:
        cmd = cmake_cmd
        clargs = substitute_cmake_args(clargs)
    elif engine_req is EngineRequirement.PYTHON:
        cmd = python_cmd
    else:
        assert_never(engine_req)

    cmd.extend(clargs)
    print_subcommand(cmd, loc=Path(directory))

    with chdir(directory):
        os.execvp(cmd[0], cmd)
