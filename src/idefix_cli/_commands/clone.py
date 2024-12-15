"""clone a problem directory"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from idefix_cli.lib import (
    files_from_patterns,
    get_option,
    make_file_tree,
    print_error,
    print_warning,
)

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


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


if sys.version_info >= (3, 12):

    class MemorizedPath(Path):
        def __init__(self, str_path: str) -> None:
            super().__init__(str_path)
            self._input = str_path

        @property
        def _has_trailing_sep(self) -> bool:
            return self._input.endswith(os.sep)

        def resolve(self, *args, **kwargs) -> Self:
            retv = super().resolve(*args, **kwargs)
            retv._input = self._input
            return retv

        def is_empty(self) -> bool:
            for _ in self.iterdir():
                return False
            return True
else:

    class MemorizedPath:
        def __init__(self, str_path: str) -> None:
            self._input = str_path
            self._path = Path(str_path)

        @property
        def _has_trailing_sep(self) -> bool:
            return self._input.endswith(os.sep)

        def resolve(self) -> Self:
            retv = object.__new__(self.__class__)
            retv.__init__(self._input)  # type: ignore[misc]
            retv._path = retv._path.resolve()
            return retv

        def is_dir(self) -> bool:
            return self._path.is_dir()

        def exists(self) -> bool:
            return self._path.exists()

        @property
        def parent(self):
            return self._path.parent

        @property
        def parents(self):
            return self._path.parents

        def glob(self, *args):
            return self._path.glob(*args)

        def __str__(self) -> str:
            return str(self._path)

        def is_empty(self) -> bool:
            for _ in self._path.iterdir():
                return False
            return True


def get_include_from_conf() -> list[str]:
    raw = get_option("idfx clone", "include")
    return raw.split()


def add_arguments(parser) -> None:
    parser.add_argument(
        "source",
        default="",
        type=lambda p: MemorizedPath(p).resolve(),
        help="the problem directory to be cloned.",
    )
    parser.add_argument(
        "dest",
        type=lambda p: MemorizedPath(p),
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
    source: MemorizedPath,
    dest: MemorizedPath,
    shallow: bool = False,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> int:
    if not source.is_dir():
        print_error(f"source directory not found {source}")
        return 1
    if source.is_empty():
        print_error(f"{source._input} appears to be empty")
        return 1
    if dest.exists():
        print_error(f"destination directory exists {dest._input}")
        return 1

    if include is None:
        include = []

    files_and_dirs_to_copy = files_from_patterns(
        str(source),
        *BASE_INCLUDE,
        *include,
        *get_include_from_conf(),
        excludes=exclude,
    )
    if not files_and_dirs_to_copy:
        print_error(f"did not find any file to copy from {source}")
        return 1

    if dest._has_trailing_sep:
        print_warning(
            f"directory {dest._input} will be created. "
            f"Drop the trailing {os.path.sep!r} char to turn off this warning."
        )

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

    dirs_to_manage: list[Path] = []
    parents = iter(list(dest.parents))
    while not (p := next(parents)).exists():
        dirs_to_manage.append(p)

    if dirs_to_manage:
        os.makedirs(dirs_to_manage[0])

    try:
        with TemporaryDirectory(dir=dest.parent) as tmpdir:
            # using a context manager to guarantee atomicity:
            # either it's a full success or we don't copy anything
            # The temporary directory is created next to the final destination
            # so we can safely use os.replace (atomic) without worrying about
            # possibly sparse filesystems.
            recursive_write(tmpdir, files_and_dirs_to_copy)
            if sys.version_info >= (3, 12):
                os.replace(tmpdir, dest)
            else:
                os.replace(tmpdir, dest._input)
    except Exception:
        # attempt to clean up. Don't try to avoid tracebacks here:
        # if this code runs, something has gone terribly wrong and it's
        # preferable to not hide the details.
        if dirs_to_manage:
            shutil.rmtree(dirs_to_manage[-1])
        raise

    if sys.version_info >= (3, 12):
        path_converter = lambda _: _  # noqa
    else:
        path_converter = str
    output_files = [str(_) for _ in dest.glob("*")]
    if shallow:
        objs = "symlinks"
        lencol1 = max(len(_) for _ in output_files)
        lines = [f"{_.ljust(lencol1 + 1)} -> {os.readlink(_)}" for _ in output_files]
        files_repr = "\n".join(lines)
    else:
        objs = "files"
        parent = path_converter(dest.parent)
        files_repr = make_file_tree(
            output_files, parent_dir=path_converter(dest), origin=parent
        )
    print(f"Created the following {objs}\n{files_repr}")
    return 0
