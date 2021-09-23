import argparse
import sys
from importlib import import_module
from pkgutil import walk_packages
from types import FunctionType
from typing import cast
from typing import Optional

from idefix_cli import __version__
from idefix_cli import commands
from idefix_cli._commons import print_err


def _setup_commands(parser: argparse.ArgumentParser) -> dict[str, FunctionType]:
    # https://github.com/python/mypy/issues/1422
    path: str = commands.__path__  # type: ignore

    sparsers = parser.add_subparsers(dest="command")
    retv: dict[str, FunctionType] = {}
    for module_info in walk_packages(path, commands.__name__ + "."):
        module = import_module(module_info.name)

        command_name = module_info.name.split(".")[-1].removeprefix("_")

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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="idfx")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    commands = _setup_commands(parser)

    args, rest = parser.parse_known_args(argv)

    if rest and args.command != "setup":
        print_err(f"unknown arguments ({', '.join(rest)}).")
        return 1

    if args.command is None:
        # calling `idfx` without any argument is equivalent to `idfx --help`
        # except that the return value non zero.
        parser.print_help(sys.stderr)
        return 1

    vargs = vars(args)
    cmd = vargs.pop("command")
    retv = commands[cmd](**vargs)
    retv = cast(int, retv)
    return retv
