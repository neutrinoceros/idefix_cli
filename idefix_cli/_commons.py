import contextlib
import os
import sys
from functools import wraps
from multiprocessing import cpu_count
from subprocess import check_call

from rich.console import Console

# setup a very large console to prevent rich from wrapping long error messages
# since it usually has the side effect of truncating file names.
# This workaround also helps keeping error messages reproducible in CI.


def print_err(message: str) -> None:
    err_console = Console(width=500, file=sys.stderr)
    err_console.print(f"[bold white on red]ERROR[/] {message}")


def requires_idefix(func):
    @wraps(func)
    def _func(*args, **kwargs):
        if os.getenv("IDEFIX_DIR") is None:
            print_err(
                "this functionality requires $IDEFIX_DIR to be defined.",
            )
            exit(1)
        return func(*args, **kwargs)

    return _func


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
