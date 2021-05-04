import contextlib
import os
import sys
from functools import wraps
from glob import glob
from itertools import chain
from multiprocessing import cpu_count
from subprocess import check_call
from typing import Any, Callable, TypeVar, cast

from rich.console import Console

# workaround mypy not being confortable around decorator preserving signatures
# adapted from
# https://github.com/python/mypy/issues/1551#issuecomment-253978622
TFun = TypeVar("TFun", bound=Callable[..., Any])


class requires_idefix:
    def __call__(self, f: TFun) -> TFun:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            if os.getenv("IDEFIX_DIR") is None:
                print_err(
                    "this functionality requires $IDEFIX_DIR to be defined.",
                )
                return 10
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


def _make(directory):
    ncpus = str(min(8, cpu_count()))
    with pushd(directory):
        check_call(["make", "-j", ncpus])


def files_from_patterns(source, *patterns):
    return sorted(chain.from_iterable(glob(os.path.join(source, p)) for p in patterns))
