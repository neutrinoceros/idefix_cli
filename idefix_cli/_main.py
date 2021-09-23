from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pkgutil import walk_packages
from types import FunctionType
from typing import cast
from typing import NoReturn

from idefix_cli import __version__
from idefix_cli import _commands
from idefix_cli._commons import print_err


def _setup_commands(parser: argparse.ArgumentParser) -> dict[str, FunctionType]:
    # https://github.com/python/mypy/issues/1422
    path: str = _commands.__path__  # type: ignore

    sparsers = parser.add_subparsers(dest="command")
    retv: dict[str, FunctionType] = {}
    for module_info in walk_packages(path, _commands.__name__ + "."):
        module = import_module(module_info.name)

        _, _, command_name = module_info.name.rpartition(".")

        # plugin validation
        # TODO: could validate signatures too
        if not hasattr(module, "add_arguments"):
            raise RuntimeError(
                f"command plugin {command_name} is missing an 'add_arguments' function."
            )
        if not hasattr(module, "command"):
            raise RuntimeError(
                f"command plugin {command_name} is missing a 'command' function."
            )

        # optional plugin hooks
        kwargs = getattr(module, "parser_kwargs", {})

        sub_parser = sparsers.add_parser(command_name, help=module.__doc__, **kwargs)
        module.add_arguments(sub_parser)  # type: ignore
        retv.update({command_name: module.command})  # type: ignore
    return retv


def main(argv: list[str] | None = None) -> int | NoReturn:
    parser = argparse.ArgumentParser(prog="idfx")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    commands = _setup_commands(parser)

    known_args, unknown_args = parser.parse_known_args(argv)

    vargs = vars(known_args)
    cmd_name = vargs.pop("command")

    if cmd_name is None:
        # calling `idfx` without any argument is equivalent to `idfx --help`
        # except that the return value non zero.
        parser.print_help(sys.stderr)
        return 1

    cmd = commands[cmd_name]
    if cmd_name == "conf":
        return cmd(*unknown_args)  # type: ignore

    elif unknown_args:
        print_err(f"received unknown arguments {tuple(unknown_args)!r}.")
        return 1

    retv = cmd(**vargs)
    retv = cast(int, retv)
    return retv
