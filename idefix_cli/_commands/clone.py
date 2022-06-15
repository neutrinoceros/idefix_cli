"""clone a problem directory"""
from __future__ import annotations

import os
import shutil
from glob import glob
from tempfile import TemporaryDirectory

from rich import print

from idefix_cli._commons import files_from_patterns
from idefix_cli._commons import print_err
from idefix_cli._commons import print_warning

minimal_target = frozenset(
    (
        "idefix.ini",
        "*.hpp",
        "*.cpp",
        "*.h",
        "*.c",
        "CMakeLists.txt",
    )
)


def add_arguments(parser) -> None:
    parser.add_argument(
        "source", default=".", help="the problem directory to be cloned."
    )
    parser.add_argument(
        "dest",
        help="destination directory (must not exist, unless the --force flag is used.).",
    )
    parser.add_argument(
        "--shallow",
        action="store_true",
        help="build symlinks instead of actual copies (not implemented yet).",
    )
    parser.add_argument(
        "--extra",
        nargs="+",
        help="a list of additional file names (or patterns) that should be included in the clone.",
    )


def command(
    source: str,
    dest: str,
    shallow: bool = False,
    extra: list[str] | None = None,
) -> int:
    if not os.path.isdir(source):
        print_err(f"source directory not found {source}")
        return 1
    if not os.listdir(source):
        print_err(f"{source} appears to be empty.")
        return 1
    if os.path.exists(dest):
        print_err(f"destination directory exists {dest}")
        return 1

    if extra is None:
        extra = []

    files_to_generate = files_from_patterns(source, *minimal_target, *extra)
    if not files_to_generate:
        print_err(f"did not find any file to copy from {source}")
        return 1

    if dest.endswith(os.path.sep):
        print_warning(
            f"directory {dest} will be created. "
            f"Drop the trailing {os.path.sep!r} char to turn off this warning."
        )
        dest = dest[:-1]

    with TemporaryDirectory(dir=os.path.dirname(dest)) as tmpdir:
        # using a context manager to guarantee atomicity:
        # either it's a full success or we don't copy anything
        # The temporary directory is created next to the final destination
        # so we can safely use os.replace (atomic) without worrying about
        # possibly sparse filesystems.
        for file in files_to_generate:
            fdest = os.path.join(tmpdir, os.path.basename(file))
            if shallow:
                os.symlink(file, fdest)
            else:
                shutil.copy(file, fdest)
        os.replace(tmpdir, dest)

    output_files = list(glob(os.path.join(dest, "*")))
    if shallow:
        objs = "symlinks"
        lencol1 = max(len(_) for _ in output_files)
        lines = [f"{_.ljust(lencol1 + 1)} -> {os.readlink(_)}" for _ in output_files]
    else:
        objs = "files"
        lines = output_files
    print(f"Created the following {objs}\n" + "\n".join(lines))
    return 0
