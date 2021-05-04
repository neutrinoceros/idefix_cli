import os
import shutil
import sys
from glob import glob
from tempfile import TemporaryDirectory
from typing import Optional

from idefix_cli._commons import files_from_patterns

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
        print(f"Error: source directory not found {source}", file=sys.stderr)
        return 1
    if os.path.exists(dest):
        print(f"Error: destination directory exists {dest}", file=sys.stderr)
        return 1

    if extra is None:
        extra = []

    with TemporaryDirectory() as tmpdir:
        # using a context manager to guarantee atomicity:
        # either it's a full success or we don't copy anything
        for file in files_from_patterns(source, *minimal_target, *extra):
            fdest = os.path.join(tmpdir, os.path.basename(file))
            if shallow:
                os.symlink(file, fdest)
            else:
                shutil.copy(file, fdest)
        # using shutil.move over os.replace because the former works with
        # cross-devices links while the latter doesn't, which is important in
        # large facilities.
        shutil.move(tmpdir, dest)

    if shallow:
        objs = f"symlinks to {source}"
    else:
        objs = "files"
    output_files = "\n".join(list(glob(os.path.join(dest, "*"))))
    print(f"Created the following {objs}\n{output_files}")
    return 0
