import os
from pathlib import Path

from idefix_cli._commons import files_from_patterns
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
gpatterns = frozenset(("Makefile", "idefix"))


def _add_clean_args(parser):
    parser.add_argument(
        "directory", nargs="?", default=".", help="the root directory to clean"
    )
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


def clean(directory, clean_all: bool = False, dry: bool = False) -> int:
    with pushd(directory):
        patterns = bpatterns.union(kokkos_files)
        if clean_all:
            patterns = patterns.union(gpatterns)

        targets = files_from_patterns(Path.cwd(), *patterns)

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
