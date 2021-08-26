import contextlib
import os
import sys
from functools import wraps
from glob import glob
from itertools import chain
from multiprocessing import cpu_count
from subprocess import CalledProcessError
from subprocess import check_call
from typing import Any
from typing import Callable
from typing import cast
from typing import TypeVar

from rich.console import Console

# workaround mypy not being confortable around decorator preserving signatures
# adapted from
# https://github.com/python/mypy/issues/1551#issuecomment-253978622
TFun = TypeVar("TFun", bound=Callable[..., Any])


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


def print_err(message: str) -> None:
    err_console = Console(width=500, file=sys.stderr)
    err_console.print(f"[bold white on red]ERROR[/] {message}")


def print_warning(message: str) -> None:
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
