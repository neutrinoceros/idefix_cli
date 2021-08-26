import argparse
import sys
from typing import Optional

from idefix_cli import __version__
from idefix_cli._commons import print_err
from idefix_cli.commands._clean import _add_clean_args
from idefix_cli.commands._clean import clean
from idefix_cli.commands._clone import _add_clone_args
from idefix_cli.commands._clone import clone
from idefix_cli.commands._read import _add_read_args
from idefix_cli.commands._read import read
from idefix_cli.commands._run import _add_run_args
from idefix_cli.commands._run import run
from idefix_cli.commands._setup import setup
from idefix_cli.commands._stamp import _add_stamp_args
from idefix_cli.commands._stamp import stamp
from idefix_cli.commands._write import _add_write_args
from idefix_cli.commands._write import write


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="idfx")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")

    clean_parser = subparsers.add_parser("clean", help="clean up generated files")
    _add_clean_args(clean_parser)

    clone_parser = subparsers.add_parser("clone", help="clone a problem directory")
    _add_clone_args(clone_parser)

    read_parser = subparsers.add_parser(
        "read", help="read an Idefix inifile and print it to json format"
    )
    _add_read_args(read_parser)

    run_parser = subparsers.add_parser("run", help="run an Idefix problem")
    _add_run_args(run_parser)

    # this is a thin wrapper, we don't add any argument (atm)
    # so the reference isn't used, but we'll keep it for symetry
    setup_parser = subparsers.add_parser(  # noqa: F841
        "setup",
        help="setup an Idefix problem",
        add_help=False,  # because it's a wrapper, we want to pass down even the "--help" flag
    )

    stamp_parser = subparsers.add_parser(
        "stamp", help="print relevant data for reproduction to stdout"
    )
    _add_stamp_args(stamp_parser)

    write_parser = subparsers.add_parser(
        "write", help="write an Idefix inifile a from json string"
    )
    _add_write_args(write_parser)

    args, rest = parser.parse_known_args(argv)

    if rest and args.command != "setup":
        print_err(f"unknown arguments ({', '.join(rest)}).")
        return 1

    if args.command is None:
        # calling `idfx` without any argument is equivalent to `idfx --help`
        # except that the return value non zero.
        parser.print_help(sys.stderr)
        return 1

    if args.command == "clean":
        return clean(args.directory, args.all, args.dry)

    if args.command == "clone":
        return clone(
            source=args.source,
            dest=args.dest,
            shallow=args.shallow,
            extra=args.extra,
        )

    if args.command == "read":
        return read(args.inifile, args.indent)

    if args.command == "run":
        return run(
            args.directory,
            args.inifile,
            args.duration,
            args.time_step,
            args.one_step,
        )

    if args.command == "setup":
        # this one doesn't return because it yields control
        # to a different process.
        # and it's not testable for the same reason
        setup(rest)  # pragma: no cover

    if args.command == "stamp":
        return stamp(args.todict)

    if args.command == "write":
        return write(args.dest, args.source, args.force)
