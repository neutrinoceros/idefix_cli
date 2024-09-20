from __future__ import annotations

import os
import platform
import re
import sys
import warnings
from collections.abc import Callable
from configparser import ConfigParser
from functools import wraps
from glob import glob
from itertools import chain
from pathlib import Path
from textwrap import indent
from typing import Any, TypeVar, cast

from packaging.version import Version
from termcolor import cprint

from idefix_cli._theme import get_symbol

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from idefix_cli._backports import StrEnum

# workaround mypy not being confortable around decorator preserving signatures
# adapted from
# https://github.com/python/mypy/issues/1551#issuecomment-253978622
TFun = TypeVar("TFun", bound=Callable[..., Any])

VERSION_STR = r"\d+\.\d+\.\d+"
VERSION_REGEXP = re.compile(VERSION_STR)
# This is how sections are formatted in the changelog,
# e.g., '## [0.8.1] - 2021-06-24'
VERSECT_REGEXP = re.compile(rf"## \[{VERSION_STR}\]\s*-?\s*\d\d\d\d-\d\d-\d\d\s*\n")


__all__ = [
    "requires_idefix",
    "print_error",
    "print_warning",
    "print_subcommand",
    "files_from_patterns",
    "get_idefix_version",
    "get_config_file",
    "get_configuration",
    "get_option",
    "make_file_tree",
]

# done as a separate statement to avoid adding a noqa to the whole __all__ def
__all__.append("chdir")


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
    """
    Decorate a function that requires Idefix to produce
    standardized error in case Idefix isn't installed properly.

    Examples:
        >>> @requires_idefix()
        ... def my_command():
        ...    pass
    """

    def __call__(self, f: TFun) -> TFun:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            if (IDEFIX_DIR := os.getenv("IDEFIX_DIR")) is None:
                print_error(
                    "this functionality requires $IDEFIX_DIR to be defined",
                )
                return 10
            elif not os.path.isdir(IDEFIX_DIR):
                print_error(
                    f"env variable $IDEFIX_DIR isn't properly defined: {IDEFIX_DIR} is not a directory",
                )
                return 20
            return f(*args, **kwargs)

        return cast(TFun, wrapper)


def print_err(message: str) -> None:
    warnings.warn(
        "idefix_cli.lib.print_err is deprecated. "
        "Use idefix_cli.lib.print_error instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    print_error(message)


def print_error(message: str, *, hint: str | None = None) -> None:
    """Print a fatal error message to stderr.
    Normally followed by `return 1`.

    Args:
        message (str): the error message
        hint (str): hint at a potential solution (optional)

    Returns:
        None

    Examples:
        >>> def my_command() -> int:
        ...    if "MYENVVAR" not in os.environ:
        ...        print_error("Missing MYENVVAR")
        ...        return 1
        ...    return 0
    """
    cprint(get_symbol("ERROR"), end=" ", file=sys.stderr)
    cprint(message, color="red", attrs=["bold"], file=sys.stderr)
    if hint is None:
        return
    cprint(get_symbol("HINT"), end=" ", file=sys.stderr)
    cprint(hint, color="magenta", attrs=["underline"], file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a non-fatal error message to stderr.

    Args:
        message (str): the error message

    Returns:
        None

    Examples:
        >>> def my_command() -> int:
        ...    if "MYENVVAR" not in os.environ:
        ...        print_warning("Missing MYENVVAR")
        ...    return 0
    """
    cprint(get_symbol("WARNING"), end=" ", file=sys.stderr)
    cprint(message, color="magenta", attrs=["underline"], file=sys.stderr)


def print_success(message: str) -> None:
    """Print some exciting news to stdout.

    Args:
        message (str): the message to be printed

    Returns:
        None

    Examples:
        >>> def my_command() -> int:
        ...    print_success("Successfully did nothing !")
        ...    return 0
    """
    cprint(get_symbol("SUCCESS"), end=" ")
    cprint(message, color="green")


def print_subcommand(cmd: list[str], *, loc: os.PathLike[str] | None = None) -> None:
    """Print a command, which is to be executed as a subprocess.

    Args:
        cmd (list[str]): equivalent argument to be passed to, e.g., subprocess.run
        loc (os.PathLike[str] | None): the directory (other than cwd)
            from which the command is meant to be executed.

    Returns:
        None

    Examples:
        >>> import os
        >>> import subprocess
        >>> from pathlib import Path
        >>> def my_command() -> int:
        ...    cmd = ["which", "gcc"]
        ...    print_subcommand(cmd, loc=Path.home())
        ...    subprocess.run(cmd)
        ...    return 0
        >>> my_command()
        🚀 running which gcc (from ...)
        ...
    """
    msg = " ".join(cmd)
    trailer = ""
    if loc is not None and Path(loc).resolve() != Path.cwd():
        trailer = f" (from {loc}{os.sep})"

    cprint(get_symbol("LAUNCH"), end=" ")
    cprint("running", color="blue", end=" ")
    cprint(msg, attrs=["bold"], end="")
    cprint(trailer)


def run_subcommand(
    cmd: list[str], *, loc: os.PathLike[str] | None = None, err: str | None = None
) -> int:
    """
    Convenience function to run subprocess while logging with print_subcommand

    Args:
        cmd (list[str]): equivalent argument to be passed to subprocess.run
        loc (os.PathLike[str] | None): the directory (other than cwd)
            from which the command is meant to be executed.
        err (str | None): error message to be printed in case the subprocess fails

    Returns:
      retcode (int): the return code of the subprocess
    """
    from subprocess import CalledProcessError, run

    chdir = __getattr__("chdir")
    if loc is None:
        loc = Path.cwd()
    print_subcommand(cmd, loc=loc)
    try:
        with chdir(loc):
            p = run(cmd, check=True)
    except CalledProcessError as exc:
        if err is None:
            err = f"failed to run {' '.join(cmd)!r}"
        print_error(err)
        return exc.returncode
    else:
        return p.returncode


def files_from_patterns(
    source,
    *patterns,
    recursive: bool = False,
    excludes: list[str] | None = None,
) -> list[str]:
    """
    Args:
        source (os.PathLike[str]): path to the directory to inspect
        patterns (str): file patterns (e.g. "*.py", "*.txt" ...)
        recursive (bool): set to True to recurse into the source directory
        excludes (list of str): file patterns to dismiss

    Returns:
        files (list[str]): files and directories sorted in alphabetical order.
            Directories names end with "/" (or "\" on Windows) to make them visually
            distinct from extension-less files.

    Examples:
        >>> from pathlib import Path
        >>> files_from_patterns(Path.home() / "myproject", "*.py", "*.txt") # doctest: +SKIP
        ["data.txt", "script1.py", "script2.py"]
    """
    include_globs = set(
        chain.from_iterable(
            glob(os.path.join(source, p), recursive=recursive) for p in patterns
        )
    )
    if excludes is None:
        exclude_globs = set()
    else:
        exclude_globs = set(
            chain.from_iterable(
                glob(os.path.join(source, p), recursive=recursive) for p in excludes
            )
        )
    retv = set()
    for fp in include_globs - exclude_globs:
        if os.path.isdir(fp):
            # it is important to append os.path.sep to directory names so
            # it's clear that they are not files when listed with idfx clean --dry
            fp += os.path.sep
        retv.add(os.path.abspath(fp))
    return sorted(retv)


@requires_idefix()
def get_idefix_version() -> Version:
    """
    Attempt to retrieve Idefix's version. Default to Version("0")

    Returns:
        version (packaging.version.Version): a Version object that supports
        meaningful comparison

    Examples:
        >>> from packaging.version import Version
        >>> if (version := get_idefix_version()) < Version("1.1"): # doctest: +SKIP
        ...     print_error(f"Idefix v{version} is too old (v1.1 or newer is required)")
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


def get_config_file() -> str:
    """
    Return absolute path to the active configuration file.
    If present, the local configuration is returned, otherwise the global one is
    to be considered active, even if non-existent.
    """
    for parent_dir in (".", XDG_CONFIG_HOME):
        if os.path.isfile(conf_file := os.path.join(parent_dir, "idefix.cfg")):
            break
    return os.path.abspath(conf_file)


def get_configuration() -> ConfigParser:
    """Parse the whole configuration file (local if present, else global)

    Returns:
        cf (configparser.ConfigParser): parsed configuration object (may be empty).

    Examples:
        >>> cf = get_configuration()
        >>> cf["compilation"]
        <Section: compilation>

    See also:
        get_option
    """
    cf = ConfigParser()
    if os.path.isfile(conf_file := get_config_file()):
        cf.read(conf_file)
    return cf


def get_option(section_name: str, option_name: str, /) -> str:
    """Parse a specific option from the configuration file  (local if present, else global)

    Args:
        section_name (str): the section where the option is expected
        option_name (str): the name of the option itself

    Returns:
        val (str): the raw string value (may be empty).

    Examples:
        >>> get_option("compilation", "compiler")
        'g++'
    """
    usr_conf = get_configuration()
    return usr_conf.get(section_name, option_name, fallback="")


def make_file_tree(file_list: list[str], parent_dir: str, origin: str) -> str:
    """Build a simple file tree

    Args:
        file_list (list[str]) : ...
        parent_dir (str) : ...
        origin (str) : ...

    Returns:
        file_tree (str): a string representation of the parent directory content

    Examples:
        >>> file_list = ["a.cpp", "a.hpp", "b.cpp", "b.hpp", "README.md"]
        >>> print(make_file_tree(file_list, parent_dir=".", origin="..")) # doctest: +SKIP
         my_directory
         ├── a.cpp
         ├── a.hpp
         ├── b.cpp
         ├── b.hppp
         └── README.md
    """
    ret: list[str] = []
    try:
        ret.append(os.path.relpath(parent_dir, start=origin))
    except ValueError:
        # ValueError is raised if root and origin are on different mounts,
        # which is common on Windows where 'C:' and 'D:' are both used
        ret.append(os.path.abspath(parent_dir))

    for file in file_list[:-1]:
        ret.append(
            f"{_Tree.FORK}{_Tree.BRANCH*2} {os.path.relpath(file, start=parent_dir)}"
        )
        if os.path.isdir(file):
            ret.append(f"{_Tree.TRUNK}   {_Tree.ANGLE}{_Tree.BRANCH*2} (...)")
    ret.append(
        f"{_Tree.ANGLE}{_Tree.BRANCH*2} {os.path.relpath(file_list[-1], start=parent_dir)}"
    )
    return indent("\n".join(ret), " ")


def prompt_ask(prompt: str, /) -> bool:
    """Repeatedly prompt a yes/no alternative until either 'y' or 'n' is received.
    Return the result as a boolean (yes=True). Case insensitive.
    """
    while True:
        v = input(f"{prompt} [y/n]: ").lower()
        if v == "y":
            return True
        if v == "n":
            return False
        print("Please enter y or n", file=sys.stderr)


def __getattr__(attr: str):
    # avoid leaking more than intended from the standard library
    if attr == "chdir":
        if sys.version_info >= (3, 11):
            from contextlib import chdir
        else:
            from idefix_cli._backports import chdir
        return chdir
    else:
        raise AttributeError(f"Unknown attribute {attr!r}")


def __dir__():
    return list(globals()) + ["chdir"]
