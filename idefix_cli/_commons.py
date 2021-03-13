import contextlib
import os
from functools import wraps
from multiprocessing import cpu_count
from subprocess import check_call


def requires_idefix(func):
    @wraps(func)
    def _func(*args, **kwargs):
        if os.getenv("IDEFIX_DIR") is None:
            print("This requires $IDEFIX_DIR to be defined.")
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
