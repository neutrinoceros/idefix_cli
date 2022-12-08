import argparse
import inspect
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import FunctionType
from typing import Any
from typing import Dict
from typing import Final
from typing import List
from typing import Tuple

from idefix_cli import __version__
from idefix_cli._commons import get_user_conf_requirement
from idefix_cli._commons import print_err

CommandMap = Dict[str, Tuple[FunctionType, bool]]


BASE_COMMAND_PATH: Final[str] = str(Path(__file__).parent / "_commands")


def _get_command_paths() -> List[str]:
    dirs = [BASE_COMMAND_PATH]
    if (
        ext_dir := get_user_conf_requirement("idefix_cli", "extension_dir")
    ) is not None:
        dirs.append(ext_dir)

    paths = []
    for _dir in dirs:
        paths.extend(
            [
                os.path.join(_dir, modfile)
                for modfile in sorted(os.listdir(_dir))
                if modfile.endswith(".py")
            ]
        )
    return paths


def _setup_commands(parser: argparse.ArgumentParser) -> CommandMap:
    path: str

    sparsers = parser.add_subparsers(dest="command")
    cmddict: CommandMap = {}
    paths = _get_command_paths()
    # breakpoint()

    for module_path in paths:
        command_name, _, _ = os.path.basename(module_path).partition(".")
        module = SourceFileLoader(command_name, module_path).load_module()

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
        sig = inspect.signature(module.command)

        accepts_unknown_args = any(
            param.kind is param.VAR_POSITIONAL for param in sig.parameters.values()
        )
        cmddict.update({command_name: (module.command, accepts_unknown_args)})
    return cmddict


def main(argv: "List[str] | None" = None) -> Any:
    # the return value is deleguated to sub commands so its type is arbitrary
    # In practice it should be either 'int' or 'typing.NoReturn'
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

    cmd, accepts_unknown_args = commands[cmd_name]
    if unknown_args and not accepts_unknown_args:
        print_err(f"received unknown arguments {tuple(unknown_args)!r}")
        return 1

    return cmd(*unknown_args, **vars(known_args))
