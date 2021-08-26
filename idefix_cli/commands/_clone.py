import os
import shutil
from glob import glob
from tempfile import TemporaryDirectory
from typing import Optional

from rich import print

from idefix_cli._commons import files_from_patterns
from idefix_cli._commons import print_err

minimal_target = frozenset(
    (
        "idefix.ini",
        "definitions.hpp",
        "setup.cpp",
    )
)


def _add_clone_args(parser) -> int:
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


def clone(
    source,
    dest,
    shallow: bool = False,
    extra: Optional[list[str]] = None,
) -> int:
    if not os.path.isdir(source):
        print_err(f"Error: source directory not found {source}")
        return 1
    if not os.listdir(source):
        print_err(f"Error: {source} appears to be empty.")
        return 1
    if os.path.exists(dest):
        print_err(f"Error: destination directory exists {dest}")
        return 1

    if extra is None:
        extra = []

    files_to_generate = files_from_patterns(source, *minimal_target, *extra)
    if not files_to_generate:
        print_err(f"Error: did not find any file to copy from {source}")
        return 1

    with TemporaryDirectory(dir=os.path.dirname(dest)) as tmpdir:
        # using a context manager to guarantee atomicity:
        # either it's a full success or we don't copy anything
        # The temporary directory is created next to the final destination
        # so we can safely use os.replace (atomic) without worrying about
        # possibly sparse filesystems.
        for file in files_from_patterns(source, *minimal_target, *extra):
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
    output_files = "\n".join(list(glob(os.path.join(dest, "*"))))
    print(f"Created the following {objs}\n" + "\n".join(lines))
    return 0
