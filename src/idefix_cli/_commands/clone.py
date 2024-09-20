"""clone a problem directory"""

from __future__ import annotations

import os
import shutil
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory

from idefix_cli.lib import (
    files_from_patterns,
    get_option,
    make_file_tree,
    print_error,
    print_warning,
)

BASE_INCLUDE = frozenset(
    (
        "*.ini",
        "*.hpp",
        "*.cpp",
        "*.h",
        "*.c",
        "*.py",
        "CMakeLists.txt",
    )
)


def get_include_from_conf() -> list[str]:
    raw = get_option("idfx clone", "include")
    return raw.split()


def add_arguments(parser) -> None:
    parser.add_argument(
        "source", default=".", help="the problem directory to be cloned."
    )
    parser.add_argument(
        "dest",
        help="destination directory (cannot exist).",
    )
    parser.add_argument(
        "--shallow",
        action="store_true",
        help="build symlinks instead of actual copies.",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        help="a list of additional file names (or patterns) that should be included in the clone.",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="a list of file names (or patterns) that should be excluded from the clone. "
        "(takes precedent over --include in case of collisions)",
    )


def command(
    source: str,
    dest: str,
    shallow: bool = False,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> int:
    if not os.path.isdir(source):
        print_error(f"source directory not found {source}")
        return 1
    if not os.listdir(source):
        print_error(f"{source} appears to be empty")
        return 1
    if os.path.exists(dest):
        print_error(f"destination directory exists {dest}")
        return 1

    if include is None:
        include = []

    files_and_dirs_to_copy = files_from_patterns(
        source,
        *BASE_INCLUDE,
        *include,
        *get_include_from_conf(),
        excludes=exclude,
    )
    if not files_and_dirs_to_copy:
        print_error(f"did not find any file to copy from {source}")
        return 1

    if dest.endswith(os.path.sep):
        print_warning(
            f"directory {dest} will be created. "
            f"Drop the trailing {os.path.sep!r} char to turn off this warning."
        )
        dest = dest[:-1]

    def recursive_write(tmpdir: str, files_and_dirs: list[str]) -> None:
        for fd in files_and_dirs:
            fdest = os.path.join(tmpdir, os.path.basename(fd))
            if shallow:
                os.symlink(fd, fdest)
            elif os.path.isfile(fd):
                shutil.copy(fd, fdest)
            elif os.path.isdir(fd):
                subdir = os.path.join(tmpdir, os.path.basename(fd))
                os.mkdir(subdir)
                files_and_dirs = [os.path.join(fd, _) for _ in os.listdir(fd)]
                recursive_write(subdir, files_and_dirs)
            else:
                raise RuntimeError(
                    "If you see this error message, please report to "
                    "https://github.com/neutrinoceros/idefix_cli/issues/new"
                )

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with TemporaryDirectory(dir=os.path.dirname(dest)) as tmpdir:
        # using a context manager to guarantee atomicity:
        # either it's a full success or we don't copy anything
        # The temporary directory is created next to the final destination
        # so we can safely use os.replace (atomic) without worrying about
        # possibly sparse filesystems.
        recursive_write(tmpdir, files_and_dirs_to_copy)
        os.replace(tmpdir, dest)

    output_files = list(glob(os.path.join(dest, "*")))
    if shallow:
        objs = "symlinks"
        lencol1 = max(len(_) for _ in output_files)
        lines = [f"{_.ljust(lencol1 + 1)} -> {os.readlink(_)}" for _ in output_files]
        files_repr = "\n".join(lines)
    else:
        objs = "files"
        parent = str(Path(dest).parent)
        files_repr = make_file_tree(output_files, parent_dir=dest, origin=parent)
    print(f"Created the following {objs}\n{files_repr}")
    return 0
