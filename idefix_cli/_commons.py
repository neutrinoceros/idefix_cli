from __future__ import annotations

import os
import platform
import re
import sys
from configparser import ConfigParser
from functools import wraps
from glob import glob
from itertools import chain
from pathlib import Path
from textwrap import indent
from typing import Any
from typing import Callable
from typing import cast
from typing import TypeVar
from typing import Union

from packaging.version import Version
from rich.console import Console

# workaround mypy not being confortable around decorator preserving signatures
# adapted from
# https://github.com/python/mypy/issues/1551#issuecomment-253978622
TFun = TypeVar("TFun", bound=Callable[..., Any])

VERSION_STR = r"\d+\.\d+\.\d+"
VERSION_REGEXP = re.compile(VERSION_STR)
# This is how sections are formatted in the changelog,
# e.g., '## [0.8.1] - 2021-06-24'
VERSECT_REGEXP = re.compile(rf"## \[{VERSION_STR}\]\s*-?\s*\d\d\d\d-\d\d-\d\d\s*\n")


if sys.version_info >= (3, 11):
    from contextlib import chdir
    from enum import StrEnum
else:
    # vendored from Python 3.11b1
    from contextlib import AbstractContextManager

    class chdir(AbstractContextManager):
        """Non thread-safe context manager to change the current working directory."""

        def __init__(self, path):
            self.path = path
            self._old_cwd = []

        def __enter__(self):
            self._old_cwd.append(os.getcwd())
            os.chdir(self.path)

        def __exit__(self, *excinfo):
            os.chdir(self._old_cwd.pop())

    from enum import Enum as _Enum

    # vendored from Python 3.11.0
    class _ReprEnum(_Enum):
        """
        Only changes the repr(), leaving str() and format() to the mixed-in type.
        """

    class StrEnum(str, _ReprEnum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:
                raise TypeError(f"too many arguments for str(): {values!r}")
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError(f"{values[0]!r} is not a string")
            if len(values) >= 2:
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError(f"encoding must be a string, not {values[1]!r}")
            if len(values) == 3:
                # check that errors argument is a string
                if not isinstance(values[2], str):
                    raise TypeError("errors must be a string, not %r" % (values[2]))
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def _generate_next_value_(name, start, count, last_values):
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()


if platform.system().lower().startswith("win"):
    # Windows
    env_var = "APPDATA"
    default_usr_dir = "AppData"

    class _Tree(StrEnum):
        TRUNK = "|"
        FORK = "|-"
        ANGLE = "'-"
        BRANCH = "-"

else:
    # POSIX
    env_var = "XDG_CONFIG_HOME"
    default_usr_dir = ".config"

    class _Tree(StrEnum):  # type: ignore [no-redef]
        TRUNK = "│"
        FORK = "├"
        ANGLE = "└"
        BRANCH = "─"


XDG_CONFIG_HOME = os.environ.get(
    env_var,
    os.path.join(os.path.expanduser("~"), default_usr_dir),
)
del env_var, default_usr_dir


class requires_idefix:
    def __call__(self, f: TFun) -> TFun:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            if (IDEFIX_DIR := os.getenv("IDEFIX_DIR")) is None:
                print_err(
                    "this functionality requires $IDEFIX_DIR to be defined",
                )
                return 10
            elif not os.path.isdir(IDEFIX_DIR):
                print_err(
                    f"env variable $IDEFIX_DIR isn't properly defined: {IDEFIX_DIR} is not a directory",
                )
                return 20
            return f(*args, **kwargs)

        return cast(TFun, wrapper)


# setup a very large console to prevent rich from wrapping long error messages
# since it usually has the side effect of truncating file names.
# This workaround also helps keeping error messages reproducible in CI.

ErrorMessage = Union[str, Exception]


def print_err(message: ErrorMessage) -> None:
    err_console = Console(width=500, file=sys.stderr)
    err_console.print(f":boom:[bold red3] {message}[/]")


def print_warning(message: ErrorMessage) -> None:
    err_console = Console(width=500, file=sys.stderr)
    err_console.print(f":exclamation:[italic magenta] {message}[/]")


def print_subcommand(cmd: list[str], *, loc: Path | None = None) -> None:
    msg = " ".join(cmd)

    header = "running"
    if loc is not None and loc.resolve() != Path.cwd():
        header += f" (from {loc}{os.sep})"

    console = Console(width=500, highlight=False)
    console.print(f":rocket:[italic cornflower_blue] {header}[/] [bold]{msg}[/]")


def files_from_patterns(source, *patterns, recursive: bool = False) -> list[str]:
    raw = sorted(
        chain.from_iterable(
            glob(os.path.join(source, p), recursive=recursive) for p in patterns
        )
    )
    retv = set()
    for fp in raw:
        if os.path.isdir(fp):
            # it is important to append os.path.sep to directory names so
            # it's clear that they are not files when listed with idfx clean --dry
            fp += os.path.sep
        retv.add(os.path.abspath(fp))
    return list(retv)


@requires_idefix()
def get_idefix_version() -> Version:
    """
    Attempt to retrieve Idefix's version. Default to Version("0")
    """
    # We rely on parsing the CHANGELOG file to determine the most recent release at
    # any given point. This is more reliable than checking for the closest ancestor
    # in git tags because the development branch usually doesn't decend from releases.
    # Another reason why this seems reasonable is that tarball releases are supposed
    # to ship a CHANGELOG file as well.
    changelog = os.path.join(os.environ["IDEFIX_DIR"], "CHANGELOG.md")
    if not os.path.isfile(changelog):
        # this is inevitable if the user is checked in a version that predates
        # the introduction of a changelog (Idefix v0.7.0)
        return Version("0")

    with open(changelog) as fh:
        for line in fh:
            if not re.match(VERSECT_REGEXP, line):
                continue
            match = re.search(VERSION_REGEXP, line)
            assert match is not None
            return Version(match.group())

    raise RuntimeError(
        "Something went wrong while trying to determine Idefix's version."
    )


def get_user_config_file() -> str:
    """Return the local configuration file (idefix.cfg) if it exists, or the global one."""
    for parent_dir in (".", XDG_CONFIG_HOME):
        if os.path.isfile(conf_file := os.path.join(parent_dir, "idefix.cfg")):
            break
    return os.path.abspath(conf_file)


def get_user_configuration() -> ConfigParser:
    cf = ConfigParser()
    if os.path.isfile(conf_file := get_user_config_file()):
        cf.read(conf_file)
    return cf


def get_user_conf_requirement(section_name: str, option_name: str, /) -> str:
    usr_conf = get_user_configuration()
    return usr_conf.get(section_name, option_name, fallback="")


def get_filetree(file_list: list[str], root: str, origin: str) -> str:
    ret: list[str] = []
    try:
        ret.append(os.path.relpath(root, start=origin))
    except ValueError:
        # ValueError is raised if root and origin are on different mounts,
        # which is common on Windows where 'C:' and 'D:' are both used
        ret.append(os.path.abspath(root))

    for file in file_list[:-1]:
        ret.append(f"{_Tree.FORK}{_Tree.BRANCH*2} {os.path.relpath(file, start=root)}")
        if os.path.isdir(file):
            ret.append(f"{_Tree.TRUNK}   {_Tree.ANGLE}{_Tree.BRANCH*2} (...)")
    ret.append(
        f"{_Tree.ANGLE}{_Tree.BRANCH*2} {os.path.relpath(file_list[-1], start=root)}"
    )
    return indent("\n".join(ret), " ")
