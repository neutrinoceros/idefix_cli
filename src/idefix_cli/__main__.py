import inspect
import os
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from importlib.metadata import version
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any, Final, Literal

from idefix_cli._theme import theme_ctx
from idefix_cli.lib import get_config_file, get_option, print_error, print_warning

CommandMap = dict[str, tuple[FunctionType, bool]]


BASE_COMMAND_PATH: Final[str] = str(Path(__file__).parent / "_commands")


def _get_command_paths() -> list[str]:
    dirs = [BASE_COMMAND_PATH]

    if ext_dir := get_option("idefix_cli", "plugins_directory"):
        if os.path.isdir(ext_dir):
            dirs.append(ext_dir)
        else:
            path = os.path.abspath(get_config_file())
            print_warning(
                f"{ext_dir} is configured as your command extension "
                f"directory (from {path}) "
                "but no such directory exists."
            )

    paths = []
    for _dir in dirs:
        paths.extend(
            [
                os.path.join(_dir, modfile)
                for modfile in sorted(os.listdir(_dir))
                if modfile.endswith(".py") and modfile != "__init__.py"
            ]
        )
    return paths


def get_module_from_path(path: str, name: str) -> ModuleType:
    if (spec := spec_from_file_location(name, path)) is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _setup_commands(parser: ArgumentParser) -> CommandMap:
    sparsers = parser.add_subparsers(title="commands", dest="command")
    cmddict: CommandMap = {}
    paths = _get_command_paths()

    for module_path in paths:
        command_name, _ = os.path.splitext(os.path.basename(module_path))
        module = get_module_from_path(module_path, command_name)

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

        usage: str | None
        help, _, usage = module.__doc__.strip().partition("\n")
        usage = usage or None
        sub_parser = sparsers.add_parser(
            command_name,
            help=help,
            usage=usage,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        module.add_arguments(sub_parser)
        sig = inspect.signature(module.command)

        accepts_unknown_args = any(
            param.kind is param.VAR_POSITIONAL for param in sig.parameters.values()
        )
        cmddict.update({command_name: (module.command, accepts_unknown_args)})
    return cmddict


def cli(caller: Literal["idfx", "baballe"], argv: list[str] | None = None) -> Any:
    # the return value is deleguated to sub commands so its type is arbitrary
    # In practice it should be either 'int' or 'typing.NoReturn'
    parser = ArgumentParser(prog=caller, allow_abbrev=False)
    parser.add_argument(
        "-v", "--version", action="version", version=version("idefix-cli")
    )
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
        print_error(f"received unknown arguments {tuple(unknown_args)!r}")
        return 1

    return cmd(*unknown_args, **vars(known_args))


def main(caller: Literal["idfx", "baballe"], argv: list[str] | None = None) -> Any:
    theme_name = {"idfx": "default", "baballe": "baballe"}[caller]

    with theme_ctx(theme_name):
        return cli(caller, argv)


def idfx_entry_point(argv: list[str] | None = None) -> Any:
    return main(caller="idfx", argv=argv)


def baballe_entry_point(argv: list[str] | None = None) -> Any:
    return main(caller="baballe", argv=argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(caller="idfx"))
