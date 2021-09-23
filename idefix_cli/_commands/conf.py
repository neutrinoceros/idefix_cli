"""setup an Idefix problem"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import NoReturn

from packaging.version import Version

from idefix_cli._commons import get_idefix_version
from idefix_cli._commons import get_user_config_file
from idefix_cli._commons import get_user_configuration
from idefix_cli._commons import print_err
from idefix_cli._commons import print_warning
from idefix_cli._commons import requires_idefix

VERSION_REGEXP = re.compile(r"\d+\.\d+\.\d+")

CMAKE_MIN_VERSIONS: dict[str, Version] = {
    "cmake": Version("3.16.0"),
    "idefix": Version("0.9.0"),
}


class CMakeEnvError(OSError):
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

    raise CMakeEnvError(msg)


def has_minimal_cmake_support() -> bool:
    try:
        validate_cmake_support()
    except CMakeEnvError:
        return False
    else:
        return True


def get_conf_system_requirement() -> str | None:
    if (usr_conf := get_user_configuration()) is None:
        return None

    return usr_conf.get("idefix_cli", "conf_system", fallback=None)


def is_cmake_required() -> bool:
    req = get_conf_system_requirement()
    return req is not None and req == "cmake"


def has_cmake_preference() -> bool:
    if (usr_conf := get_user_configuration()) is None:
        return True

    if "compilation" not in usr_conf.sections():
        return True

    comp_options = usr_conf["compilation"]
    return not any(_ in comp_options for _ in ("CPU", "GPU", "compiler"))


def substitute_cmake_args(*args: str) -> tuple[str, ...]:
    # compatibility layer to enable configure.py's arguments with cmake
    subs: dict[str, str] = {
        "-mhd": "-DIdefix_MHD=ON",
        "-mpi": "-DIdefix_MPI=ON",
        "-openmp": "-DKokkos_ENABLE_OPENMP=ON",
    }
    return tuple(subs.get(_, _) for _ in args)


parser_kwargs = dict(
    add_help=False
)  # because it's a wrapper, we want to pass down even the "--help" flag


def add_arguments(parser):
    "Nothing to do here, this command is a pure wrapper"
    return


@requires_idefix()
def command(*args: str) -> int | NoReturn:
    python_cmd = ["python3", os.path.join(os.environ["IDEFIX_DIR"], "configure.py")]
    cmake_cmd = ["cmake", os.environ["IDEFIX_DIR"]]
    system_req = get_conf_system_requirement()

    if system_req == "cmake":
        try:
            validate_cmake_support()
        except CMakeEnvError as exc:
            print_err(exc)
            return 1
        cmd = cmake_cmd
    elif system_req == "python":
        cmd = python_cmd
    elif system_req is None:
        if has_minimal_cmake_support():
            cmd = cmake_cmd
        else:
            cmd = python_cmd
    else:
        print_err(
            f"Got unknown value conf_system={system_req!r} "
            f"from {get_user_config_file()}, "
            "expected 'cmake' or 'python'"
        )
        return 1

    if cmd == cmake_cmd:
        args = substitute_cmake_args(*args)

    cmd.extend(args)
    os.execvp(cmd[0], cmd)
