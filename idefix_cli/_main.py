from __future__ import annotations

import argparse
import inspect
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

        _command = getattr(module, "command", None)
        _add_arguments = getattr(module, "add_arguments", None)

        if _command is _add_arguments is None:
            raise RuntimeError(
                f"command plugin {command_name} is missing required functions "
                "'command' and 'add_arguments'"
            )
        elif _command is None:
            raise RuntimeError(
                f"command plugin {command_name} is missing a 'command' function"
            )
        elif _add_arguments is None:
            raise RuntimeError(
                f"command plugin {command_name} is missing a 'add_arguments' function"
            )

        sig = inspect.signature(_add_arguments)
        if (params := list(sig.parameters.keys())) != ["parser"]:
            raise RuntimeError(
                f"command plugin {command_name}.add_arguments function's signature is invalid. "
                f"Expected a single argument named 'parser', found {params}"
            )

        if not module.__doc__:
            # default is None, but we also invalidate empty strings
            raise RuntimeError(
                f"command plugin {command_name} is missing a module docstring"
            )

        # optional plugin hooks
        kwargs = getattr(module, "parser_kwargs", {})

        sub_parser = sparsers.add_parser(command_name, help=module.__doc__, **kwargs)
        module.add_arguments(sub_parser)
        retv.update({command_name: module.command})
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
        return cmd(*unknown_args, **vars(known_args))  # type: ignore

    elif unknown_args:
        print_err(f"received unknown arguments {tuple(unknown_args)!r}.")
        return 1

    retv = cmd(**vargs)
    retv = cast(int, retv)
    return retv
