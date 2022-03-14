"""setup an Idefix problem"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from typing import NoReturn

from packaging.version import Version

from idefix_cli._commons import get_idefix_version
from idefix_cli._commons import get_user_conf_requirement
from idefix_cli._commons import get_user_config_file
from idefix_cli._commons import print_err
from idefix_cli._commons import print_warning
from idefix_cli._commons import requires_idefix

VERSION_REGEXP = re.compile(r"\d+\.\d+\.\d+")

CMAKE_MIN_VERSIONS: dict[str, Version] = {
    "cmake": Version("3.16.0"),
    "idefix": Version("0.9.0"),
}


class IdefixEnvError(OSError):
    pass


def validate_cmake_support() -> None:
    msg = f"cmake is required from {get_user_config_file()}, but "
    errors: list[str] = []
    warnings: list[str] = []
    idefix_ver = get_idefix_version()

    if idefix_ver is None or idefix_ver < CMAKE_MIN_VERSIONS["idefix"]:
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
        cmake_ver: str = subprocess.run(
            ["cmake", "--version"], capture_output=True
        ).stdout.decode()
        if (match := re.search(VERSION_REGEXP, cmake_ver)) is None:
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


def is_cmake_required() -> bool:
    req = get_user_conf_requirement("idefix_cli", "conf_system")
    return req is not None and req == "cmake"


def is_python_required() -> bool:
    req = get_user_conf_requirement("idefix_cli", "conf_system")
    return req is not None and req == "python"


@requires_idefix()
def has_python_support() -> bool:
    return os.path.isfile(os.path.join(os.environ["IDEFIX_DIR"], "configure.py"))


@requires_idefix()
def validate_python_support() -> None:
    if has_python_support():
        return

    msg = "Running a version of Idefix that doesn't provide $IDEFIX_DIR/configure.py . "
    if is_python_required():
        msg += f"This configuration system was required from {get_user_config_file()}"
    raise IdefixEnvError(msg)


def get_valid_conf_system() -> str:
    cmake_is_valid = has_minimal_cmake_support()
    python_is_valid = has_python_support()
    if cmake_is_valid:
        return "cmake"
    elif python_is_valid:
        return "python"
    else:
        raise IdefixEnvError(
            "Could not determine a working configuration system. "
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
        arch_req = get_user_conf_requirement("compilation", "CPU")
        if arch_req is not None:
            args.extend(["-arch", arch_req])
        arch_req = get_user_conf_requirement("compilation", "GPU")
        if arch_req is not None:
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
        compiler_req = get_user_conf_requirement("compilation", "compiler")
        if compiler_req is not None:
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


parser_kwargs = dict(
    add_help=False
)  # because it's a wrapper, we want to pass down even the "--help" flag


def add_arguments(parser) -> None:
    parser.add_argument(
        "-i",
        "--interactive",
        dest="interactive",
        action="store_true",
        help="Use ccmake over cmake " "(no effect with python configuration system)",
    )


@requires_idefix()
def command(*args: str, interactive: bool) -> int | NoReturn:
    python_cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py")]
    cmake_cmd = ["ccmake" if interactive else "cmake", os.environ["IDEFIX_DIR"]]
    system_req = get_user_conf_requirement("idefix_cli", "conf_system")

    if system_req is None:
        try:
            system_req = get_valid_conf_system()
        except IdefixEnvError as exc:
            print_err(exc)
            return 1
    else:
        try:
            validate_selected_system = {
                "cmake": validate_cmake_support,
                "python": validate_python_support,
            }[system_req]
        except KeyError:
            print_err(
                f"Got unknown value conf_system={system_req!r} "
                f"from {get_user_config_file()}, "
                "expected 'cmake' or 'python'"
            )
            return 1

        try:
            validate_selected_system()
        except IdefixEnvError as exc:
            print_err(exc)
            return 1

    clargs = list(args)
    if system_req == "cmake":
        cmd = cmake_cmd
        clargs = substitute_cmake_args(clargs)
    else:
        assert system_req == "python"
        cmd = python_cmd

    cmd.extend(clargs)
    print(f"INFO: running '{' '.join(cmd)}'")
    os.execvp(cmd[0], cmd)
