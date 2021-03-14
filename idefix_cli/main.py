import argparse
import sys
from typing import Optional

from idefix_cli import __version__
from idefix_cli.commands._clean import _add_clean_args, clean
from idefix_cli.commands._read import _add_read_args, read
from idefix_cli.commands._run import _add_run_args, run
from idefix_cli.commands._setup import _add_setup_args, setup
from idefix_cli.commands._stamp import _add_stamp_args, stamp
from idefix_cli.commands._write import _add_write_args, write


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="idfx")
    parser.add_argument("-v", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")

    clean_parser = subparsers.add_parser("clean", help="clean up generated files")
    _add_clean_args(clean_parser)

    read_parser = subparsers.add_parser(
        "read", help="read an Idefix inifile and print it to json format"
    )
    _add_read_args(read_parser)

    run_parser = subparsers.add_parser("run", help="run an Idefix problem")
    _add_run_args(run_parser)

    setup_parser = subparsers.add_parser("setup", help="setup an Idefix problem")
    _add_setup_args(setup_parser)

    stamp_parser = subparsers.add_parser(
        "stamp", help="print relevant data for reproduction to stdout"
    )
    _add_stamp_args(stamp_parser)

    write_parser = subparsers.add_parser(
        "write", help="write an Idefix inifile a from json string"
    )
    _add_write_args(write_parser)

    args = parser.parse_args(argv)

    if args.command is None:
        # calling `idfx` without any argument is equivalent to `idfx --help`
        # except that the return value non zero.
        parser.print_help(sys.stderr)
        return 1

    if args.command == "clean":
        return clean(args.directory, args.all, args.dry)

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
        return setup(
            args.directory,
            args.arch,
            args.use_gpu,
            args.cxx,
            args.openmp,
            args.mpi,
            args.mhd,
            args.make,
        )

    if args.command == "stamp":
        return stamp(args.todict)

    if args.command == "write":
        return write(args.dest, args.source, args.force)
