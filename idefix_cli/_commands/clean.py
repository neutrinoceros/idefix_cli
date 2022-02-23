"""remove compilation files"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from shutil import rmtree
from shutil import which

from rich.prompt import Confirm

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
    with pushd(directory):
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
        print("\n".join(targets))

        if not dry and Confirm.ask("\nPerform cleaning ?"):
            for t in targets:
                if os.path.isdir(t):
                    rmtree(t)
                else:
                    os.remove(t)

    return 0
