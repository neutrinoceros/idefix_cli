import contextlib
import os
import platform
import re
import sys
from configparser import ConfigParser
from datetime import datetime
from functools import wraps
from getpass import getuser
from glob import glob
from itertools import chain
from multiprocessing import cpu_count
from socket import gethostname
from subprocess import CalledProcessError
from subprocess import check_call
from time import ctime
from typing import Any
from typing import Callable
from typing import cast
from typing import Optional
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
VERSECT_REGEXP = re.compile(fr"## \[{VERSION_STR}\] - \d\d\d\d-\d\d-\d\d\s*\n")

if platform.system().lower().startswith("win"):
    # Windows
    env_var = "APPDATA"
    default_usr_dir = "AppData"
else:
    # POSIX
    env_var = "XDG_CONFIG_HOME"
    default_usr_dir = ".config"

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
                    "this functionality requires $IDEFIX_DIR to be defined.",
                )
                return 10
            elif not os.path.isdir(IDEFIX_DIR):
                print_err(
                    f"env variable $IDEFIX_DIR isn't properly defined: {IDEFIX_DIR} is not a directory.",
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
    err_console.print(f"[bold white on red]ERROR[/] {message}")


def print_warning(message: ErrorMessage) -> None:
    err_console = Console(width=500, file=sys.stderr)
    err_console.print(f"[red]WARNING[/] {message}")


@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


@requires_idefix()
def _make(directory) -> int:
    ncpus = str(min(8, cpu_count() // 2))
    try:
        with pushd(directory):
            return check_call(["make", "-j", ncpus])
    except CalledProcessError as exc:
        print_err("failed to compile idefix")
        return exc.returncode


def files_from_patterns(source, *patterns):
    return sorted(chain.from_iterable(glob(os.path.join(source, p)) for p in patterns))


@requires_idefix()
def get_git_data() -> dict[str, str]:
    data = {
        "user": getuser(),
        "host": gethostname(),
        "date": ctime(datetime.now().timestamp()),
    }
    try:
        # this import may fail in envs where the git executable is not present,
        # so we'll avoid keeping it at the top level to minimize breakage
        import git
    except ImportError as exc:
        print_warning(f"failed to load gitpython (got 'ImportError: {exc}')")
    else:
        repo = git.Repo(os.environ["IDEFIX_DIR"])
        data = {
            "sha": repo.head.object.hexsha,
        } | data
    if (version := get_idefix_version()) is None:
        version_str = "unknown version"
    else:
        version_str = str(version)
    data = {"latest ancestor version": version_str} | data
    return data


@requires_idefix()
def get_idefix_version() -> Optional[Version]:
    # We rely on parsing the CHANGELOG file to determine the most recent release at
    # any given point. This is more reliable than checking for the closest ancestor
    # in git tags because the development branch usually doesn't decend from releases.
    # Another reason why this seems reasonable is that tarball releases are supposed
    # to ship a CHANGELOG file as well.
    changelog = os.path.join(os.environ["IDEFIX_DIR"], "CHANGELOG.md")
    if not os.path.isfile(changelog):
        # this is inevitable if the user is checked in a version that predates
        # the introduction of a changelog (Idefix v0.7.0)
        return None

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


def get_user_config_file() -> Optional[str]:
    for parent_dir in [".", XDG_CONFIG_HOME]:
        if os.path.isfile(conf_file := os.path.join(parent_dir, "idefix.cfg")):
            return os.path.abspath(conf_file)
    return None


def get_user_configuration() -> Optional[ConfigParser]:
    if (conf_file := get_user_config_file()) is None:
        return None

    cf = ConfigParser()
    cf.read(conf_file)
    return cf
