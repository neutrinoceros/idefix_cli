"""remove compilation files"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import rmtree, which

from rich.prompt import Confirm

from idefix_cli.lib import files_from_patterns, make_file_tree

if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from idefix_cli.lib import chdir

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

cmake_files = frozenset(("CMakeCache.txt", "cmake_install.cmake", "build"))

# only cleared if `--all` flag is passed
gpatterns = frozenset(("Makefile", "idefix"))

GENERATED_DIRS = frozenset(("CMakeFiles",))


def add_arguments(parser) -> None:
    parser.add_argument(
        "directory", nargs="?", default=".", help="the target directory to clean"
    )
    parser.add_argument(
        "--all",
        dest="clean_all",
        action="store_true",
        help="also clean generated Makefiles, idefix excutable files",
    )
    parser.add_argument(
        "--dry-run",
        "--dry",
        dest="dry",
        action="store_true",
        help="skip prompt, exit without cleaning",
    )


def command(directory, clean_all: bool = False, dry: bool = False) -> int:
    origin = os.path.abspath(os.curdir)
    with chdir(directory):
        patterns = bpatterns | kokkos_files | cmake_files | GENERATED_DIRS
        if clean_all:
            patterns |= gpatterns

        # Guarantee that git indexed files are never cleaned
        if which("git") is not None:
            # we don't check the result of the process, meaning we trust git not to output
            # anything to stdout in case the current dir isn't part of a git repo
            git_files = set(
                subprocess.run(["git", "ls-files"], capture_output=True)
                .stdout.decode()
                .strip()
                .split("\n")
            )
        else:
            git_files = set()

        patterns -= git_files

        targets = files_from_patterns(Path.cwd(), *patterns)

        if not targets:
            print("Nothing to remove.")
            return 0

        print("The following files and directories can be removed")
        print(
            make_file_tree(
                targets, parent_dir=os.path.abspath(os.curdir), origin=origin
            )
        )

        if dry or not Confirm.ask("\nPerform cleaning ?"):
            return 0

        for t in targets:
            # won't prevent race conditions but useful in testing
            assert os.path.exists(t)
            if os.path.isdir(t):
                rmtree(t)
            else:
                os.remove(t)

    return 0
