import os
from glob import glob
from itertools import chain
from pathlib import Path

from idefix_cli._commons import pushd

# bpatterns are those targeted by `make clean`, which is equivalent to
# rm -f *.o *.cuda *.host
bpatterns = frozenset(("*.o", "*.cuda", "*.host"))

# additional generated files
kokkos_files = frozenset(
    (
        "KokkosCore_config.h",
        "KokkosCore_config.tmp",
        "KokkosCore_Config*.tmp",
        "KokkosCore_Config*.hpp",
        "libkokkos.a",
    )
)

# only cleared if `--all` flag is passed
gpatterns = frozenset(("*.ini_", "Makefile", "idefix"))


def _add_clean_args(parser):
    parser.add_argument("directory", help="the root directory to clean")
    parser.add_argument(
        "--all",
        action="store_true",
        help="also clean generated Makefiles, idefix excutable files and .ini_ files",
    )
    parser.add_argument(
        "--dry-run",
        "--dry",
        dest="dry",
        action="store_true",
        help="print a list of targets, no file is removed",
    )


def clean(directory, clean_all: bool = False, dry: bool = False):
    with pushd(directory):
        patterns = bpatterns.union(kokkos_files)
        if clean_all:
            patterns = patterns.union(gpatterns)

        targets = sorted(
            chain.from_iterable(glob(str(Path.cwd() / p)) for p in patterns)
        )

        if dry:
            if not targets:
                print("Nothing to remove.")
                return 0
            print("The following files would be removed.")
            print("\n".join(targets))
            return 0

        for t in targets:
            os.remove(t)

    return 0
