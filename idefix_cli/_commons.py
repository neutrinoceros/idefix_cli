import contextlib
import os
import sys
from functools import wraps
from multiprocessing import cpu_count
from subprocess import check_call


def requires_idefix(func):
    @wraps(func)
    def _func(*args, **kwargs):
        if os.getenv("IDEFIX_DIR") is None:
            print("This requires $IDEFIX_DIR to be defined.")
            sys.exit(1)
        return func(*args, **kwargs)

    return _func


def always_iterable(obj, base_type=(str, bytes)):
    # this is directly ported from more_itertools
    # https://github.com/more-itertools/more-itertools
    # Licence MIT
    if obj is None:
        return iter(())

    if (base_type is not None) and isinstance(obj, base_type):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))


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
